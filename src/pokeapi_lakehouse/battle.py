"""SQL-first orchestration for battle-oriented Gold products."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from typing import Any

from pokeapi_lakehouse import __version__
from pokeapi_lakehouse.gold import (
    _upsert_run,
    ensure_gold_table_schema,
    replace_with_compatibility_view,
)
from pokeapi_lakehouse.sql_queries import sql_query
from pokeapi_lakehouse.time_utils import configure_brasilia_timezone, now_brasilia


@dataclass(frozen=True)
class BattleProduct:
    name: str
    query_name: str
    legacy_name: str | None
    sources: tuple[str, ...]


BATTLE_FOUNDATION_PRODUCTS = (
    BattleProduct("dim_ruleset", "ruleset", None, ("dim_version_group",)),
    BattleProduct("dim_type", "type", None, ("type", "type_translation")),
    BattleProduct("dim_ability", "ability", None, ("ability", "ability_translation")),
    BattleProduct(
        "fact_type_matchup",
        "type_matchup_matrix",
        "type_matchup_matrix",
        ("type", "type_damage_relation", "dim_ruleset"),
    ),
    BattleProduct(
        "fact_pokemon_battle_stats",
        "pokemon_battle_profile",
        "pokemon_battle_profile",
        (
            "pokemon_catalog",
            "type",
            "pokemon_type",
            "type_damage_relation",
            "pokemon_stat",
            "dim_ruleset",
        ),
    ),
    BattleProduct("dim_move", "battle_move", "battle_move", ("move", "move_translation")),
    BattleProduct(
        "bridge_pokemon_move",
        "pokemon_move_pool",
        "pokemon_move_pool",
        ("pokemon_move", "battle_move", "pokemon_catalog", "dim_ruleset"),
    ),
)

MATCHUP_PRODUCT = BattleProduct(
    "fact_pokemon_matchup",
    "pokemon_matchup",
    None,
    (
        "dim_pokemon",
        "dim_game_version",
        "fact_pokemon_battle_stats",
        "bridge_pokemon_move",
        "pokemon_type",
        "type_damage_relation",
    ),
)
BATTLE_PRODUCTS = BATTLE_FOUNDATION_PRODUCTS


def _identifiers_for_product(product: BattleProduct, silver: str, gold: str) -> dict[str, str]:
    gold_sources = {"pokemon_catalog": "dim_pokemon", "battle_move": "dim_move"}
    return {
        source: (
            f"{gold}.{gold_sources[source]}"
            if source in gold_sources
            else f"{gold}.{source}"
            if source.startswith(("dim_", "fact_", "bridge_"))
            else f"{silver}.{source}"
        )
        for source in product.sources
    }


def transform_battle_gold(
    spark: Any,
    catalog: str,
    silver_schema: str,
    gold_schema: str,
) -> str:
    """Publish battle foundations; matchup is normally sharded by partition workers."""
    run_id = str(uuid.uuid4())
    silver = f"{catalog}.{silver_schema}"
    gold = f"{catalog}.{gold_schema}"
    runs_table = f"{gold}._gold_runs"
    failures: list[str] = []
    configure_brasilia_timezone(spark)

    for product in BATTLE_FOUNDATION_PRODUCTS:
        started_at = now_brasilia()
        started_clock = time.perf_counter()
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
            target = f"{gold}.{product.name}"
            identifiers = _identifiers_for_product(product, silver, gold)
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
            if quality is None or any(
                int(value or 0) > 0
                for value in (
                    quality.technical_null_count,
                    quality.range_violation_count,
                    quality.duplicate_count,
                )
            ):
                raise ValueError(
                    f"qualidade inválida em {target}: "
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
        raise RuntimeError(f"fundação Gold de batalha {run_id} falhou: {', '.join(failures)}")
    for product in BATTLE_PRODUCTS:
        if product.legacy_name is not None:
            replace_with_compatibility_view(
                spark, f"{gold}.{product.legacy_name}", f"{gold}.{product.name}"
            )
    return run_id


def _parse_matchup_partition(partition: str) -> tuple[str, str | None]:
    parts = partition.strip().split("|", maxsplit=1)
    version_group_name = parts[0]
    if not version_group_name.replace("-", "").isalnum():
        raise ValueError(f"version_group_name inválido: {version_group_name}")
    battle_level = parts[1] if len(parts) == 2 else None
    if battle_level is not None and battle_level not in {"50", "80", "100"}:
        raise ValueError(f"battle_level inválido: {battle_level}")
    return version_group_name, battle_level


def transform_matchup_gold_partition(
    spark: Any, catalog: str, silver_schema: str, gold_schema: str, partition: str
) -> str:
    """Publish one matchup partition identified by `version_group_name` or `version_group|level`."""
    version_group_name, battle_level = _parse_matchup_partition(partition)
    run_id = str(uuid.uuid4())
    silver = f"{catalog}.{silver_schema}"
    gold = f"{catalog}.{gold_schema}"
    runs_table = f"{gold}._gold_runs"
    target = f"{gold}.{MATCHUP_PRODUCT.name}"
    product_label = f"{MATCHUP_PRODUCT.name}:{partition}"
    started_at = now_brasilia()
    started_clock = time.perf_counter()
    row: dict[str, Any] = {
        "gold_run_id": run_id,
        "product": product_label,
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
        literals = {
            "run_id": run_id,
            "version_group_name": version_group_name,
        }
        if battle_level is not None:
            literals["battle_level"] = battle_level
        query_suffix = (
            "pokemon_matchup_partition_level" if battle_level else "pokemon_matchup_partition"
        )
        spark.sql(sql_query("create_gold_pokemon_matchup", table=target))
        ensure_gold_table_schema(spark, target, MATCHUP_PRODUCT.query_name)
        spark.sql(
            sql_query(
                f"stage_gold_{query_suffix}",
                identifiers=_identifiers_for_product(MATCHUP_PRODUCT, silver, gold),
                literals=literals,
            )
        )
        spark.sql(sql_query(f"merge_gold_{query_suffix}", table=target, literals=literals))
        quality = spark.sql(
            sql_query(f"quality_gold_{query_suffix}", table=target, literals=literals)
        ).first()
        if quality is None or any(
            int(value or 0) > 0
            for value in (
                quality.technical_null_count,
                quality.range_violation_count,
                quality.duplicate_count,
            )
        ):
            raise ValueError(
                f"qualidade inválida em {target} [{partition}]: "
                f"nulos={quality.technical_null_count if quality else 'n/a'}, "
                f"faixas={quality.range_violation_count if quality else 'n/a'}, "
                f"duplicatas={quality.duplicate_count if quality else 'n/a'}"
            )
        published = spark.sql(
            f"""
            SELECT COUNT(*) AS published_count FROM {target}
            WHERE version_group_name='{version_group_name}'
              {f"AND battle_level=CAST('{battle_level}' AS INT)" if battle_level else ""}
            """
        ).first()
        row.update(
            finished_at=now_brasilia(),
            status="SUCCESS",
            published_count=int(published.published_count if published else 0),
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
