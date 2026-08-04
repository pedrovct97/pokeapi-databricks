"""Databricks wheel-task entry point for Unity Catalog metadata sync."""

from __future__ import annotations

import argparse

from pokeapi_lakehouse.config import LakehouseConfig
from pokeapi_lakehouse.uc_metadata import sync_uc_comments


def _csv_set(value: str) -> set[str] | None:
    if value.strip().lower() == "all":
        return None
    return {item.strip().lower() for item in value.split(",") if item.strip()}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", required=True)
    parser.add_argument("--bronze-schema", required=True)
    parser.add_argument("--silver-schema", required=True)
    parser.add_argument("--gold-schema", required=True)
    parser.add_argument(
        "--layers", default="all", help="Camadas a sincronizar: all ou bronze,silver,gold"
    )
    parser.add_argument(
        "--domains",
        default="all",
        help="Domínios a sincronizar: all ou entity,table,bridge,fact,dim,metadata",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Imprime SQLs sem aplicar comentários"
    )
    parser.add_argument(
        "--fail-on-missing",
        action="store_true",
        help="Falha se uma tabela/coluna de contrato ainda não existir no workspace",
    )
    return parser


def main() -> None:
    from pyspark.sql import SparkSession

    args = _parser().parse_args()
    config = LakehouseConfig(
        args.catalog,
        args.bronze_schema,
        args.silver_schema,
        args.gold_schema,
    )
    result = sync_uc_comments(
        SparkSession.builder.getOrCreate(),
        catalog=config.catalog,
        bronze_schema=config.bronze_schema,
        silver_schema=config.silver_schema,
        gold_schema=config.gold_schema,
        layers=_csv_set(args.layers),
        domains=_csv_set(args.domains),
        dry_run=args.dry_run,
        skip_missing=not args.fail_on_missing,
    )
    for statement in result.statements:
        print(statement)
    print(
        "Unity Catalog metadata sync completed: "
        f"statements={len(result.statements)}, "
        f"applied={result.applied_count}, "
        f"skipped_tables={len(result.skipped_tables)}, "
        f"skipped_columns={len(result.skipped_columns)}, "
        f"dry_run={args.dry_run}"
    )


if __name__ == "__main__":
    main()
