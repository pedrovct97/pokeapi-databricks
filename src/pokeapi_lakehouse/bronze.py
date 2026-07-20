"""PySpark orchestration for immutable, idempotent PokéAPI Bronze tables."""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from dataclasses import asdict
from datetime import UTC, datetime
from typing import Any

from pokeapi_lakehouse.endpoints import Endpoint
from pokeapi_lakehouse.pokeapi_client import FetchedResource, FetchFailure, PokeApiClient
from pokeapi_lakehouse.sql_queries import sql_query

_RESOURCE_ID = re.compile(r"/([0-9]+)/?$")

BRONZE_SCHEMA = """
endpoint string, resource_id long, resource_name string, source_url string,
http_status int, payload_json string, payload_sha256 string,
source_observed_at timestamp, ingested_at timestamp, run_id string
"""
FAILURE_SCHEMA = """
endpoint string, source_url string, error_type string, error_message string,
attempted_at timestamp, run_id string
"""
RUN_SCHEMA = """
run_id string, endpoint string, started_at timestamp, finished_at timestamp,
status string, discovered_count long, fetched_count long, inserted_count long,
failed_count long, error_message string
"""


def _resource_id(url: str) -> int | None:
    match = _RESOURCE_ID.search(url)
    return int(match.group(1)) if match else None


def _resource_name(payload_json: str) -> str | None:
    value = json.loads(payload_json).get("name")
    return value if isinstance(value, str) else None


def to_bronze_row(resource: FetchedResource, run_id: str, ingested_at: datetime) -> dict[str, Any]:
    payload_hash = hashlib.sha256(resource.payload_json.encode("utf-8")).hexdigest()
    return {
        "endpoint": resource.endpoint,
        "resource_id": _resource_id(resource.source_url),
        "resource_name": _resource_name(resource.payload_json),
        "source_url": resource.source_url,
        "http_status": resource.http_status,
        "payload_json": resource.payload_json,
        "payload_sha256": payload_hash,
        "source_observed_at": resource.source_observed_at,
        "ingested_at": ingested_at,
        "run_id": run_id,
    }


def validate_bronze_rows(rows: list[dict[str, Any]]) -> None:
    required = (
        "endpoint",
        "source_url",
        "http_status",
        "payload_json",
        "payload_sha256",
        "source_observed_at",
        "ingested_at",
        "run_id",
    )
    for index, row in enumerate(rows):
        null_fields = [field for field in required if row.get(field) is None]
        if null_fields:
            raise ValueError(f"linha {index} possui campos técnicos nulos: {null_fields}")
        if row["http_status"] != 200:
            raise ValueError(f"linha {index} possui status HTTP inesperado: {row['http_status']}")
        json.loads(row["payload_json"])
    keys = [(row["source_url"], row["payload_sha256"]) for row in rows]
    if len(keys) != len(set(keys)):
        raise ValueError("lote Bronze possui recursos duplicados")


def _merge_rows(spark: Any, table: str, rows: list[dict[str, Any]]) -> int:
    spark.sql(sql_query("create_bronze_table", table=table))
    if not rows:
        return 0
    frame = spark.createDataFrame(rows, schema=BRONZE_SCHEMA)
    frame.createOrReplaceTempView("pokeapi_bronze_batch")
    before = spark.table(table).count()
    spark.sql(sql_query("merge_bronze_table", table=table))
    inserted_count = int(spark.table(table).count() - before)

    quality = spark.sql(sql_query("quality_bronze_table", table=table)).first()
    if quality is None or quality.technical_null_count or quality.duplicate_count:
        raise ValueError(
            f"qualidade pós-escrita inválida em {table}: "
            f"nulos={quality.technical_null_count if quality else 'unknown'}, "
            f"duplicatas={quality.duplicate_count if quality else 'unknown'}"
        )
    return inserted_count


def _append_failures(spark: Any, table: str, failures: list[FetchFailure], run_id: str) -> None:
    spark.sql(sql_query("create_ingestion_failures", table=table))
    if not failures:
        return
    rows = [{**asdict(failure), "run_id": run_id} for failure in failures]
    frame = spark.createDataFrame(rows, schema=FAILURE_SCHEMA)
    frame.createOrReplaceTempView("pokeapi_ingestion_failures_batch")
    spark.sql(sql_query("insert_ingestion_failures", table=table))


def _append_runs(spark: Any, table: str, rows: list[dict[str, Any]]) -> None:
    spark.sql(sql_query("create_ingestion_runs", table=table))
    frame = spark.createDataFrame(rows, schema=RUN_SCHEMA)
    frame.createOrReplaceTempView("pokeapi_ingestion_runs_batch")
    spark.sql(sql_query("insert_ingestion_runs", table=table))


def ingest_endpoints(
    spark: Any,
    catalog: str,
    schema: str,
    endpoints: tuple[Endpoint, ...],
    client: PokeApiClient,
    fail_on_partial: bool = True,
) -> str:
    """Fetch selected endpoints and persist raw payloads plus run-level reconciliation."""
    run_id = str(uuid.uuid4())
    full_schema = f"{catalog}.{schema}"
    run_rows: list[dict[str, Any]] = []
    has_failures = False
    spark.conf.set("spark.sql.session.timeZone", "UTC")

    for endpoint in endpoints:
        started_at = datetime.now(UTC)
        try:
            resources, failures, discovered_count = client.fetch_endpoint(endpoint.name)
            ingested_at = datetime.now(UTC)
            rows = [to_bronze_row(resource, run_id, ingested_at) for resource in resources]
            validate_bronze_rows(rows)
            inserted_count = _merge_rows(spark, f"{full_schema}.{endpoint.table_name}", rows)
            _append_failures(spark, f"{full_schema}._ingestion_failures", failures, run_id)
            has_failures = has_failures or bool(failures)
            run_rows.append(
                {
                    "run_id": run_id,
                    "endpoint": endpoint.name,
                    "started_at": started_at,
                    "finished_at": datetime.now(UTC),
                    "status": "PARTIAL" if failures else "SUCCESS",
                    "discovered_count": discovered_count,
                    "fetched_count": len(resources),
                    "inserted_count": inserted_count,
                    "failed_count": len(failures),
                    "error_message": None,
                }
            )
        except Exception as exc:
            has_failures = True
            run_rows.append(
                {
                    "run_id": run_id,
                    "endpoint": endpoint.name,
                    "started_at": started_at,
                    "finished_at": datetime.now(UTC),
                    "status": "FAILED",
                    "discovered_count": 0,
                    "fetched_count": 0,
                    "inserted_count": 0,
                    "failed_count": 1,
                    "error_message": f"{type(exc).__name__}: {exc}"[:1000],
                }
            )

    _append_runs(spark, f"{full_schema}._ingestion_runs", run_rows)
    if has_failures and fail_on_partial:
        failed = [row["endpoint"] for row in run_rows if row["status"] != "SUCCESS"]
        raise RuntimeError(f"ingestão {run_id} terminou com falhas: {', '.join(failed)}")
    return run_id
