"""SQL-first orchestration for bilingual Gold products."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from typing import Any

from pokeapi_lakehouse import __version__
from pokeapi_lakehouse.sql_queries import sql_query
from pokeapi_lakehouse.time_utils import configure_brasilia_timezone, now_brasilia

GOLD_RUN_SCHEMA = """
gold_run_id string, product string, started_at timestamp, finished_at timestamp,
status string, published_count long, duration_ms long, transformer_version string,
error_message string
"""


def _upsert_run(spark: Any, table: str, row: dict[str, Any]) -> None:
    spark.sql(sql_query("create_gold_runs", table=table))
    spark.createDataFrame([row], schema=GOLD_RUN_SCHEMA).createOrReplaceTempView("gold_runs_batch")
    spark.sql(sql_query("merge_gold_runs", table=table))


def replace_with_compatibility_view(spark: Any, legacy: str, canonical: str) -> None:
    """Replace a validated legacy Gold object with a read-only compatibility view."""
    if spark.catalog.tableExists(legacy):
        object_type = spark.catalog.getTable(legacy).tableType.upper()
        command = "DROP VIEW" if "VIEW" in object_type else "DROP TABLE"
        spark.sql(f"{command} {legacy}")
    spark.sql(f"CREATE VIEW {legacy} AS SELECT * FROM {canonical}")


def _ensure_columns(spark: Any, table: str, columns: dict[str, str]) -> None:
    existing = {field.name for field in spark.table(table).schema.fields}
    for name, data_type in columns.items():
        if name not in existing:
            spark.sql(f"ALTER TABLE {table} ADD COLUMNS ({name} {data_type})")


def _column_definitions_from_create_sql(create_sql: str) -> dict[str, str]:
    """Extract nullable ADD COLUMNS definitions from this project's CREATE TABLE SQL."""
    definitions: dict[str, str] = {}
    for raw_line in create_sql.splitlines():
        line = raw_line.strip().rstrip(",")
        if " COMMENT " not in line or line.startswith(("CREATE ", "USING ", "COMMENT ", ")")):
            continue
        name, definition = line.split(maxsplit=1)
        definitions[name] = definition.replace(" NOT NULL", "")
    return definitions


def ensure_gold_table_schema(spark: Any, table: str, query_name: str) -> None:
    """Add missing Gold columns without dropping existing Delta tables.

    `CREATE TABLE IF NOT EXISTS` does not evolve existing tables. This helper keeps
    fresh tables strict via the DDL, but evolves already-created dev/prod tables by
    adding new columns as nullable before the stage/MERGE refresh populates them.
    """
    create_sql = sql_query(f"create_gold_{query_name}", table=table)
    _ensure_columns(spark, table, _column_definitions_from_create_sql(create_sql))


@dataclass(frozen=True)
class GoldContextProduct:
    name: str
    query_name: str
    sources: tuple[str, ...]


GAME_CONTEXT_PRODUCTS = (
    GoldContextProduct("dim_version_group", "version_group", ("version_group",)),
    GoldContextProduct(
        "dim_game_version",
        "game_version",
        ("version", "version_group", "generation"),
    ),
)


def _quality_passed(quality: Any) -> bool:
    return quality is not None and all(
        int(value or 0) == 0
        for value in (
            quality.technical_null_count,
            quality.range_violation_count,
            quality.duplicate_count,
        )
    )


def transform_gold_game_context(
    spark: Any, catalog: str, bronze_schema: str, gold_schema: str
) -> str:
    """Publish Gold dimensions for game/version dashboard context from immutable Bronze."""
    run_id = str(uuid.uuid4())
    bronze = f"{catalog}.{bronze_schema}"
    gold = f"{catalog}.{gold_schema}"
    runs_table = f"{gold}._gold_runs"
    failures: list[str] = []
    configure_brasilia_timezone(spark)

    for product in GAME_CONTEXT_PRODUCTS:
        started_at = now_brasilia()
        started_clock = time.perf_counter()
        target = f"{gold}.{product.name}"
        row: dict[str, Any] = {
            "gold_run_id": run_id,
            "product": product.name,
            "started_at": started_at,
            "finished_at": started_at,
            "status": "RUNNING",
            "published_count": 0,
            "duration_ms": 0,
            "transformer_version": __version__,
            "error_message": None,
        }
        _upsert_run(spark, runs_table, row)
        try:
            identifiers = {source: f"{bronze}.{source}" for source in product.sources}
            spark.sql(sql_query(f"create_gold_{product.query_name}", table=target))
            ensure_gold_table_schema(spark, target, product.query_name)
            spark.sql(
                sql_query(
                    f"stage_gold_{product.query_name}",
                    identifiers=identifiers,
                    literals={"run_id": run_id},
                )
            )
            spark.sql(sql_query(f"merge_gold_{product.query_name}", table=target))
            quality = spark.sql(
                sql_query(f"quality_gold_{product.query_name}", table=target)
            ).first()
            if not _quality_passed(quality):
                raise ValueError(
                    f"qualidade Gold inválida em {target}: "
                    f"nulos={quality.technical_null_count if quality else 'n/a'}, "
                    f"faixas={quality.range_violation_count if quality else 'n/a'}, "
                    f"duplicatas={quality.duplicate_count if quality else 'n/a'}"
                )
            row.update(
                finished_at=now_brasilia(),
                status="SUCCESS",
                published_count=spark.table(target).count(),
                duration_ms=round((time.perf_counter() - started_clock) * 1000),
            )
        except Exception as exc:
            failures.append(product.name)
            row.update(
                finished_at=now_brasilia(),
                status="FAILED",
                duration_ms=round((time.perf_counter() - started_clock) * 1000),
                error_message=f"{type(exc).__name__}: {exc}"[:1000],
            )
        _upsert_run(spark, runs_table, row)

    if failures:
        raise RuntimeError(f"contexto Gold de jogo {run_id} falhou: {', '.join(failures)}")
    return run_id


def transform_gold_pokemon_catalog(
    spark: Any, catalog: str, silver_schema: str, gold_schema: str
) -> str:
    """Publish one current catalog row per Pokémon and requested language."""
    run_id = str(uuid.uuid4())
    started_at = now_brasilia()
    started_clock = time.perf_counter()
    silver = f"{catalog}.{silver_schema}"
    gold = f"{catalog}.{gold_schema}"
    target = f"{gold}.dim_pokemon"
    legacy = f"{gold}.pokemon_catalog"
    runs_table = f"{gold}._gold_runs"
    row: dict[str, Any] = {
        "gold_run_id": run_id,
        "product": "dim_pokemon",
        "started_at": started_at,
        "finished_at": started_at,
        "status": "RUNNING",
        "published_count": 0,
        "duration_ms": 0,
        "transformer_version": __version__,
        "error_message": None,
    }
    configure_brasilia_timezone(spark)
    _upsert_run(spark, runs_table, row)
    try:
        spark.sql(sql_query("create_gold_pokemon_catalog", table=target))
        ensure_gold_table_schema(spark, target, "pokemon_catalog")
        identifiers = {
            name: f"{silver}.{name}"
            for name in (
                "pokemon",
                "pokemon_species",
                "pokemon_species_translation",
                "pokemon_type",
                "type_translation",
                "pokemon_stat",
                "pokemon_ability",
                "ability_translation",
                "pokemon_media",
            )
        }
        spark.sql(
            sql_query(
                "stage_gold_pokemon_catalog",
                identifiers=identifiers,
                literals={"run_id": run_id},
            )
        )
        spark.sql(sql_query("merge_gold_pokemon_catalog", table=target))
        quality = spark.sql(sql_query("quality_gold_pokemon_catalog", table=target)).first()
        if quality is None or any(
            int(value or 0) > 0
            for value in (
                quality.technical_null_count,
                quality.range_violation_count,
                quality.duplicate_count,
            )
        ):
            raise ValueError(
                "qualidade Gold inválida: "
                f"nulos={quality.technical_null_count if quality else 'n/a'}, "
                f"faixas={quality.range_violation_count if quality else 'n/a'}, "
                f"duplicatas={quality.duplicate_count if quality else 'n/a'}"
            )
        published_count = spark.table(target).count()
        replace_with_compatibility_view(spark, legacy, target)
        row.update(
            finished_at=now_brasilia(),
            status="SUCCESS",
            published_count=published_count,
            duration_ms=round((time.perf_counter() - started_clock) * 1000),
        )
    except Exception as exc:
        row.update(
            finished_at=now_brasilia(),
            status="FAILED",
            duration_ms=round((time.perf_counter() - started_clock) * 1000),
            error_message=f"{type(exc).__name__}: {exc}"[:1000],
        )
        _upsert_run(spark, runs_table, row)
        raise
    _upsert_run(spark, runs_table, row)
    return run_id
