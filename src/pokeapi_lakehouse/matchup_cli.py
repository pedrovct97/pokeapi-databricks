"""Databricks wheel-task entry point for one matchup Gold version-group partition."""

from __future__ import annotations

import argparse

from pokeapi_lakehouse.battle import transform_matchup_gold_partition
from pokeapi_lakehouse.config import LakehouseConfig


def main() -> None:
    from pyspark.sql import SparkSession

    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", required=True)
    parser.add_argument("--silver-schema", required=True)
    parser.add_argument("--gold-schema", required=True)
    parser.add_argument("--partition", required=True, help="Formato: version-group")
    args = parser.parse_args()
    config = LakehouseConfig(args.catalog, "unused_bronze", args.silver_schema, args.gold_schema)
    run_id = transform_matchup_gold_partition(
        SparkSession.builder.getOrCreate(),
        config.catalog,
        config.silver_schema,
        config.gold_schema,
        args.partition,
    )
    print(f"Matchup Gold partition completed: partition={args.partition}, gold_run_id={run_id}")


if __name__ == "__main__":
    main()
