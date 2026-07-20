"""Databricks wheel-task entry point for Bronze ingestion."""

from __future__ import annotations

import argparse

from pokeapi_lakehouse.bronze import ingest_endpoints
from pokeapi_lakehouse.config import LakehouseConfig
from pokeapi_lakehouse.endpoints import select_endpoints
from pokeapi_lakehouse.pokeapi_client import PokeApiClient


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", required=True)
    parser.add_argument("--schema", required=True)
    parser.add_argument("--endpoints", default="all")
    parser.add_argument("--max-workers", type=int, default=8)
    parser.add_argument("--timeout-seconds", type=float, default=30.0)
    parser.add_argument("--max-retries", type=int, default=3)
    parser.add_argument("--allow-partial", action="store_true")
    return parser


def main() -> None:
    from pyspark.sql import SparkSession

    args = _parser().parse_args()
    config = LakehouseConfig(args.catalog, args.schema, "unused_silver", "unused_gold")
    spark = SparkSession.builder.getOrCreate()
    client = PokeApiClient(
        timeout_seconds=args.timeout_seconds,
        max_retries=args.max_retries,
        max_workers=args.max_workers,
    )
    run_id = ingest_endpoints(
        spark=spark,
        catalog=config.catalog,
        schema=config.bronze_schema,
        endpoints=select_endpoints(args.endpoints),
        client=client,
        fail_on_partial=not args.allow_partial,
    )
    print(f"Bronze ingestion completed: run_id={run_id}")


if __name__ == "__main__":
    main()
