"""Databricks wheel-task entry point for Gold products."""

from __future__ import annotations

import argparse

from pokeapi_lakehouse.config import LakehouseConfig
from pokeapi_lakehouse.gold import transform_gold_pokemon_catalog


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", required=True)
    parser.add_argument("--silver-schema", required=True)
    parser.add_argument("--gold-schema", required=True)
    return parser


def main() -> None:
    from pyspark.sql import SparkSession

    args = _parser().parse_args()
    config = LakehouseConfig(args.catalog, "unused_bronze", args.silver_schema, args.gold_schema)
    run_id = transform_gold_pokemon_catalog(
        SparkSession.builder.getOrCreate(),
        config.catalog,
        config.silver_schema,
        config.gold_schema,
    )
    print(f"Gold transformation completed: gold_run_id={run_id}")


if __name__ == "__main__":
    main()
