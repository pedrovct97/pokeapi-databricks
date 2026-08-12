"""Databricks wheel-task entry point for Gold products."""

from __future__ import annotations

import argparse

from pokeapi_lakehouse.battle import transform_battle_gold
from pokeapi_lakehouse.config import LakehouseConfig
from pokeapi_lakehouse.gold import (
    transform_gold_game_context,
    transform_gold_pokemon_catalog,
    transform_gold_serving_marts,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", required=True)
    parser.add_argument("--bronze-schema", required=True)
    parser.add_argument("--silver-schema", required=True)
    parser.add_argument("--gold-schema", required=True)
    return parser


def main() -> None:
    from pyspark.sql import SparkSession

    args = _parser().parse_args()
    config = LakehouseConfig(args.catalog, args.bronze_schema, args.silver_schema, args.gold_schema)
    spark = SparkSession.builder.getOrCreate()
    context_run_id = transform_gold_game_context(
        spark,
        config.catalog,
        config.bronze_schema,
        config.gold_schema,
    )
    catalog_run_id = transform_gold_pokemon_catalog(
        spark,
        config.catalog,
        config.silver_schema,
        config.gold_schema,
    )
    battle_run_id = transform_battle_gold(
        spark,
        config.catalog,
        config.silver_schema,
        config.gold_schema,
    )
    serving_marts_run_id = transform_gold_serving_marts(
        spark,
        config.catalog,
        config.gold_schema,
    )
    print(
        "Gold transformation completed: "
        f"game_context_run_id={context_run_id}, "
        f"pokemon_catalog_run_id={catalog_run_id}, "
        f"battle_run_id={battle_run_id}, "
        f"serving_marts_run_id={serving_marts_run_id}"
    )


if __name__ == "__main__":
    main()
