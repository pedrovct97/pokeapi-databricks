"""Databricks wheel-task entry point for the Silver pilot."""

from __future__ import annotations

import argparse

from pokeapi_lakehouse.config import LakehouseConfig
from pokeapi_lakehouse.silver import select_silver_entities, transform_silver


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", required=True)
    parser.add_argument("--bronze-schema", required=True)
    parser.add_argument("--silver-schema", required=True)
    parser.add_argument("--entities", default="all")
    return parser


def main() -> None:
    from pyspark.sql import SparkSession

    args = _parser().parse_args()
    config = LakehouseConfig(
        args.catalog,
        args.bronze_schema,
        args.silver_schema,
        "unused_gold",
    )
    run_id = transform_silver(
        spark=SparkSession.builder.getOrCreate(),
        catalog=config.catalog,
        bronze_schema=config.bronze_schema,
        silver_schema=config.silver_schema,
        entities=select_silver_entities(args.entities),
    )
    print(f"Silver transformation completed: silver_run_id={run_id}")


if __name__ == "__main__":
    main()
