"""Synchronize Unity Catalog table and column comments from YAML data contracts."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from importlib.resources import files
from typing import Any, cast

import yaml

from pokeapi_lakehouse.endpoints import ENDPOINTS


@dataclass(frozen=True)
class ColumnComment:
    """Comment metadata for one published column."""

    name: str
    description: str


@dataclass(frozen=True)
class TableComment:
    """Comment metadata for one Unity Catalog table."""

    layer: str
    domain: str
    logical_name: str
    table_name: str
    description: str
    columns: tuple[ColumnComment, ...]


@dataclass(frozen=True)
class CommentSyncResult:
    """Summary of a Unity Catalog metadata sync run."""

    statements: tuple[str, ...]
    applied_count: int
    skipped_tables: tuple[str, ...]
    skipped_columns: tuple[str, ...]


def _sql_string(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _quote_identifier(identifier: str) -> str:
    return "`" + identifier.replace("`", "``") + "`"


def _quote_table(full_name: str) -> str:
    return ".".join(_quote_identifier(part) for part in full_name.split("."))


def _layer_schema(layer: str, bronze_schema: str, silver_schema: str, gold_schema: str) -> str:
    if layer == "bronze":
        return bronze_schema
    if layer == "silver":
        return silver_schema
    if layer == "gold":
        return gold_schema
    raise ValueError(f"camada desconhecida no contrato: {layer}")


def _contract_resources() -> Iterable[Any]:
    contracts_root = files("pokeapi_lakehouse").joinpath("contracts")
    for layer in ("bronze", "silver", "gold"):
        layer_root = contracts_root.joinpath(layer)
        if not layer_root.is_dir():
            continue
        for contract in layer_root.iterdir():
            if contract.name.endswith(".yaml"):
                yield contract
        for domain_root in layer_root.iterdir():
            if not domain_root.is_dir():
                continue
            for contract in domain_root.iterdir():
                if contract.name.endswith(".yaml"):
                    yield contract


def _read_contract(resource: Any) -> dict[str, Any]:
    return cast(dict[str, Any], yaml.safe_load(resource.read_text(encoding="utf-8")))


def _columns(contract: dict[str, Any]) -> tuple[ColumnComment, ...]:
    return tuple(
        ColumnComment(name=column["name"], description=column["description"])
        for column in contract["columns"]
    )


def _table_names_for_contract(contract: dict[str, Any]) -> tuple[str, ...]:
    if contract["layer"] == "bronze" and contract["table"] == "<endpoint>":
        return tuple(endpoint.table_name for endpoint in ENDPOINTS)
    return (contract["table"],)


def load_table_comments(
    *, layers: set[str] | None = None, domains: set[str] | None = None
) -> tuple[TableComment, ...]:
    """Load table/column comments from packaged YAML data contracts."""

    comments: list[TableComment] = []
    for resource in _contract_resources():
        contract = _read_contract(resource)
        if layers is not None and contract["layer"] not in layers:
            continue
        if domains is not None and contract["domain"] not in domains:
            continue
        for table_name in _table_names_for_contract(contract):
            description = contract["description"]
            if contract["table"] == "<endpoint>":
                description = f"{description} — endpoint Bronze `{table_name}`"
            comments.append(
                TableComment(
                    layer=contract["layer"],
                    domain=contract["domain"],
                    logical_name=contract["logical_name"],
                    table_name=table_name,
                    description=description,
                    columns=_columns(contract),
                )
            )
    return tuple(comments)


def render_comment_statements(
    comment: TableComment,
    *,
    catalog: str,
    bronze_schema: str,
    silver_schema: str,
    gold_schema: str,
    existing_columns: set[str] | None = None,
) -> tuple[str, ...]:
    """Render COMMENT statements for one table contract."""

    schema = _layer_schema(comment.layer, bronze_schema, silver_schema, gold_schema)
    full_name = f"{catalog}.{schema}.{comment.table_name}"
    quoted_table = _quote_table(full_name)
    statements = [f"COMMENT ON TABLE {quoted_table} IS {_sql_string(comment.description)}"]
    for column in comment.columns:
        if existing_columns is not None and column.name not in existing_columns:
            continue
        statements.append(
            f"ALTER TABLE {quoted_table} ALTER COLUMN {_quote_identifier(column.name)} "
            f"COMMENT {_sql_string(column.description)}"
        )
    return tuple(statements)


def sync_uc_comments(
    spark: Any,
    *,
    catalog: str,
    bronze_schema: str,
    silver_schema: str,
    gold_schema: str,
    layers: set[str] | None = None,
    domains: set[str] | None = None,
    dry_run: bool = False,
    skip_missing: bool = True,
) -> CommentSyncResult:
    """Synchronize Unity Catalog table/column comments from packaged contracts.

    The function is idempotent: it always sets the expected comment value. When
    ``skip_missing`` is true, contracts for tables or columns not yet created in the
    current workspace are reported and skipped instead of failing the run.
    """

    statements: list[str] = []
    skipped_tables: list[str] = []
    skipped_columns: list[str] = []

    for comment in load_table_comments(layers=layers, domains=domains):
        schema = _layer_schema(comment.layer, bronze_schema, silver_schema, gold_schema)
        full_name = f"{catalog}.{schema}.{comment.table_name}"
        if skip_missing and not spark.catalog.tableExists(full_name):
            skipped_tables.append(full_name)
            continue

        existing_columns: set[str] | None = None
        if skip_missing:
            existing_columns = {field.name for field in spark.table(full_name).schema.fields}
            for column in comment.columns:
                if column.name not in existing_columns:
                    skipped_columns.append(f"{full_name}.{column.name}")

        table_statements = render_comment_statements(
            comment,
            catalog=catalog,
            bronze_schema=bronze_schema,
            silver_schema=silver_schema,
            gold_schema=gold_schema,
            existing_columns=existing_columns,
        )
        statements.extend(table_statements)
        if not dry_run:
            for statement in table_statements:
                spark.sql(statement)

    return CommentSyncResult(
        statements=tuple(statements),
        applied_count=0 if dry_run else len(statements),
        skipped_tables=tuple(skipped_tables),
        skipped_columns=tuple(skipped_columns),
    )
