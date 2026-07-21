"""SQL-first PySpark orchestration for the Silver pilot entities."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from pokeapi_lakehouse import __version__
from pokeapi_lakehouse.sql_queries import sql_query


@dataclass(frozen=True)
class SilverEntity:
    name: str
    bronze_name: str
    stage_view: str


SILVER_ENTITIES: dict[str, SilverEntity] = {
    "pokemon": SilverEntity("pokemon", "pokemon", "silver_pokemon_stage"),
    "move": SilverEntity("move", "move", "silver_move_stage"),
    "type": SilverEntity("type", "type", "silver_type_stage"),
    "stat": SilverEntity("stat", "stat", "silver_stat_stage"),
    "ability": SilverEntity("ability", "ability", "silver_ability_stage"),
    "pokemon_species": SilverEntity(
        "pokemon_species", "pokemon_species", "silver_pokemon_species_stage"
    ),
    "pokemon_type": SilverEntity("pokemon_type", "pokemon", "silver_pokemon_type_stage"),
    "pokemon_stat": SilverEntity("pokemon_stat", "pokemon", "silver_pokemon_stat_stage"),
    "pokemon_ability": SilverEntity("pokemon_ability", "pokemon", "silver_pokemon_ability_stage"),
    "pokemon_move": SilverEntity("pokemon_move", "pokemon", "silver_pokemon_move_stage"),
    "type_damage_relation": SilverEntity(
        "type_damage_relation", "type", "silver_type_damage_relation_stage"
    ),
    "language": SilverEntity("language", "language", "silver_language_stage"),
    "pokemon_species_translation": SilverEntity(
        "pokemon_species_translation", "pokemon_species", "silver_pokemon_species_translation_stage"
    ),
    "move_translation": SilverEntity("move_translation", "move", "silver_move_translation_stage"),
    "ability_translation": SilverEntity(
        "ability_translation", "ability", "silver_ability_translation_stage"
    ),
    "type_translation": SilverEntity("type_translation", "type", "silver_type_translation_stage"),
}

SILVER_RUN_SCHEMA = """
silver_run_id string, entity string, started_at timestamp, finished_at timestamp,
status string, source_count long, valid_count long, quarantined_count long,
inserted_count long, published_count long, duration_ms long,
transformer_version string, error_message string
"""


def select_silver_entities(names: str | None = None) -> tuple[SilverEntity, ...]:
    if names is None or not names.strip() or names.strip().lower() == "all":
        return tuple(SILVER_ENTITIES.values())
    requested = {name.strip().lower() for name in names.split(",") if name.strip()}
    unknown = requested - SILVER_ENTITIES.keys()
    if unknown:
        raise ValueError(f"entidades Silver desconhecidas: {', '.join(sorted(unknown))}")
    return tuple(entity for name, entity in SILVER_ENTITIES.items() if name in requested)


def _upsert_run(spark: Any, table: str, row: dict[str, Any]) -> None:
    spark.sql(sql_query("create_silver_runs", table=table))
    frame = spark.createDataFrame([row], schema=SILVER_RUN_SCHEMA)
    frame.createOrReplaceTempView("silver_runs_batch")
    spark.sql(sql_query("merge_silver_runs", table=table))


def _quality_result(spark: Any, entity: SilverEntity, table: str) -> None:
    result = spark.sql(sql_query(f"quality_silver_{entity.name}", table=table)).first()
    if result is None:
        raise ValueError(f"consulta de qualidade não retornou resultado para {entity.name}")
    if result.technical_null_count or result.range_violation_count or result.duplicate_count:
        raise ValueError(
            f"qualidade inválida em {table}: nulos={result.technical_null_count}, "
            f"faixas={result.range_violation_count}, duplicatas={result.duplicate_count}"
        )


def transform_silver(
    spark: Any,
    catalog: str,
    bronze_schema: str,
    silver_schema: str,
    entities: tuple[SilverEntity, ...],
) -> str:
    """Publish current, typed Silver snapshots from immutable Bronze versions."""
    silver_run_id = str(uuid.uuid4())
    bronze_namespace = f"{catalog}.{bronze_schema}"
    silver_namespace = f"{catalog}.{silver_schema}"
    runs_table = f"{silver_namespace}._silver_runs"
    quarantine_table = f"{silver_namespace}._quarantine"
    spark.conf.set("spark.sql.session.timeZone", "UTC")
    failures: list[str] = []

    spark.sql(sql_query("create_silver_quarantine", table=quarantine_table))
    for entity in entities:
        started_at = datetime.now(UTC)
        started_clock = time.perf_counter()
        run_row: dict[str, Any] = {
            "silver_run_id": silver_run_id,
            "entity": entity.name,
            "started_at": started_at,
            "finished_at": started_at,
            "status": "RUNNING",
            "source_count": 0,
            "valid_count": 0,
            "quarantined_count": 0,
            "inserted_count": 0,
            "published_count": 0,
            "duration_ms": 0,
            "transformer_version": __version__,
            "error_message": None,
        }
        _upsert_run(spark, runs_table, run_row)
        try:
            bronze_table = f"{bronze_namespace}.{entity.bronze_name}"
            silver_table = f"{silver_namespace}.{entity.name}"
            spark.sql(sql_query(f"create_silver_{entity.name}", table=silver_table))
            spark.sql(
                sql_query(
                    f"stage_silver_{entity.name}",
                    identifiers={"bronze_table": bronze_table},
                    literals={"run_id": silver_run_id},
                )
            )
            metrics = spark.sql(
                f"""SELECT COUNT(*) AS source_count,
                COALESCE(SUM(CASE WHEN is_valid THEN 1 ELSE 0 END), 0) AS valid_count,
                COALESCE(SUM(CASE WHEN NOT is_valid THEN 1 ELSE 0 END), 0)
                  AS quarantined_count
                FROM {entity.stage_view}"""
            ).first()
            if metrics is None:
                raise ValueError(f"staging vazio ou indisponível para {entity.name}")

            spark.sql(
                sql_query(
                    "insert_silver_quarantine",
                    table=quarantine_table,
                    identifiers={"stage_view": entity.stage_view},
                    literals={"entity": entity.name},
                )
            )
            before = spark.table(silver_table).count()
            spark.sql(sql_query(f"merge_silver_{entity.name}", table=silver_table))
            published_count = spark.table(silver_table).count()
            _quality_result(spark, entity, silver_table)
            if published_count != int(metrics.valid_count):
                raise ValueError(
                    f"reconciliação inválida para {entity.name}: "
                    f"válidos={metrics.valid_count}, publicados={published_count}"
                )
            run_row.update(
                finished_at=datetime.now(UTC),
                status="SUCCESS",
                source_count=int(metrics.source_count),
                valid_count=int(metrics.valid_count),
                quarantined_count=int(metrics.quarantined_count),
                inserted_count=published_count - before,
                published_count=published_count,
                duration_ms=round((time.perf_counter() - started_clock) * 1000),
            )
        except Exception as exc:
            failures.append(entity.name)
            run_row.update(
                finished_at=datetime.now(UTC),
                status="FAILED",
                duration_ms=round((time.perf_counter() - started_clock) * 1000),
                error_message=f"{type(exc).__name__}: {exc}"[:1000],
            )
        _upsert_run(spark, runs_table, run_row)

    selected_names = {entity.name for entity in entities}
    if not failures and selected_names == set(SILVER_ENTITIES):
        integrity_started = datetime.now(UTC)
        integrity_clock = time.perf_counter()
        integrity_row: dict[str, Any] = {
            "silver_run_id": silver_run_id,
            "entity": "_referential_integrity",
            "started_at": integrity_started,
            "finished_at": integrity_started,
            "status": "RUNNING",
            "source_count": 14,
            "valid_count": 0,
            "quarantined_count": 0,
            "inserted_count": 0,
            "published_count": 0,
            "duration_ms": 0,
            "transformer_version": __version__,
            "error_message": None,
        }
        _upsert_run(spark, runs_table, integrity_row)
        identifiers = {name: f"{silver_namespace}.{name}" for name in SILVER_ENTITIES}
        violations = spark.sql(
            sql_query("quality_silver_referential", identifiers=identifiers)
        ).collect()
        violation_count = sum(int(row.violation_count) for row in violations)
        integrity_row.update(
            finished_at=datetime.now(UTC),
            status="FAILED" if violations else "SUCCESS",
            valid_count=14 - len(violations),
            quarantined_count=violation_count,
            duration_ms=round((time.perf_counter() - integrity_clock) * 1000),
            error_message=(
                "; ".join(f"{row.rule_name}={row.violation_count}" for row in violations)[:1000]
                if violations
                else None
            ),
        )
        _upsert_run(spark, runs_table, integrity_row)
        if violations:
            failures.append("_referential_integrity")

    if failures:
        raise RuntimeError(f"transformação Silver {silver_run_id} falhou: {', '.join(failures)}")
    return silver_run_id
