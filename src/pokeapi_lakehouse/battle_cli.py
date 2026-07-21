"""Databricks wheel-task entry point for battle Gold products."""

from __future__ import annotations

import argparse

from pokeapi_lakehouse.battle import transform_battle_gold
from pokeapi_lakehouse.config import LakehouseConfig


def main() -> None:
    from pyspark.sql import SparkSession

    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", required=True)
    parser.add_argument("--silver-schema", required=True)
    parser.add_argument("--gold-schema", required=True)
    args = parser.parse_args()
    config = LakehouseConfig(args.catalog, "unused_bronze", args.silver_schema, args.gold_schema)
    run_id = transform_battle_gold(
        SparkSession.builder.getOrCreate(), config.catalog, config.silver_schema, config.gold_schema
    )
    print(f"Battle Gold transformation completed: gold_run_id={run_id}")


if __name__ == "__main__":
    main()
