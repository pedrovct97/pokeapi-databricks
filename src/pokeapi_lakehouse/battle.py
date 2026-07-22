"""SQL-first orchestration for battle-oriented Gold products."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from typing import Any

from pokeapi_lakehouse import __version__
from pokeapi_lakehouse.gold import _upsert_run, replace_with_compatibility_view
from pokeapi_lakehouse.sql_queries import sql_query
from pokeapi_lakehouse.time_utils import configure_brasilia_timezone, now_brasilia


@dataclass(frozen=True)
class BattleProduct:
    name: str
    query_name: str
    legacy_name: str | None
    sources: tuple[str, ...]


BATTLE_PRODUCTS = (
    BattleProduct("dim_ruleset", "ruleset", None, ()),
    BattleProduct("dim_type", "type", None, ("type", "type_translation")),
    BattleProduct("dim_ability", "ability", None, ("ability", "ability_translation")),
    BattleProduct(
        "fact_type_matchup",
        "type_matchup_matrix",
        "type_matchup_matrix",
        ("type", "type_damage_relation"),
    ),
    BattleProduct(
        "fact_pokemon_battle_stats",
        "pokemon_battle_profile",
        "pokemon_battle_profile",
        ("pokemon_catalog", "type", "pokemon_type", "type_damage_relation", "pokemon_stat"),
    ),
    BattleProduct("dim_move", "battle_move", "battle_move", ("move", "move_translation")),
    BattleProduct(
        "bridge_pokemon_move",
        "pokemon_move_pool",
        "pokemon_move_pool",
        ("pokemon_move", "battle_move", "pokemon_catalog"),
    ),
    BattleProduct(
        "fact_pokemon_matchup",
        "pokemon_matchup",
        None,
        (
            "dim_pokemon",
            "fact_pokemon_battle_stats",
            "bridge_pokemon_move",
            "pokemon_type",
            "type_damage_relation",
        ),
    ),
)


def transform_battle_gold(spark: Any, catalog: str, silver_schema: str, gold_schema: str) -> str:
    """Publish battle foundations for the fixed Scarlet/Violet singles ruleset."""
    run_id = str(uuid.uuid4())
    silver = f"{catalog}.{silver_schema}"
    gold = f"{catalog}.{gold_schema}"
    runs_table = f"{gold}._gold_runs"
    failures: list[str] = []
    configure_brasilia_timezone(spark)

    for product in BATTLE_PRODUCTS:
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
            gold_sources = {"pokemon_catalog": "dim_pokemon", "battle_move": "dim_move"}
            identifiers = {
                source: (
                    f"{gold}.{gold_sources[source]}"
                    if source in gold_sources
                    else f"{gold}.{source}"
                    if source.startswith(("dim_", "fact_", "bridge_"))
                    else f"{silver}.{source}"
                )
                for source in product.sources
            }
            spark.sql(sql_query(f"create_gold_{product.query_name}", table=target))
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
