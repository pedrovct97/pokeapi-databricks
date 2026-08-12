"""Databricks wheel-task entry point for matchup-dependent Gold serving marts."""

from __future__ import annotations

import argparse

from pokeapi_lakehouse.config import LakehouseConfig
from pokeapi_lakehouse.gold import transform_gold_matchup_serving_marts


def main() -> None:
    from pyspark.sql import SparkSession

    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", required=True)
    parser.add_argument("--gold-schema", required=True)
    args = parser.parse_args()
    config = LakehouseConfig(args.catalog, "unused_bronze", "unused_silver", args.gold_schema)
    run_id = transform_gold_matchup_serving_marts(
        SparkSession.builder.getOrCreate(),
        config.catalog,
        config.gold_schema,
    )
    print(f"Matchup serving marts completed: gold_run_id={run_id}")


if __name__ == "__main__":
    main()
