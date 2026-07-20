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
BRONZE_COMMENTS = {
    "endpoint": "Recurso REST v2 de origem.",
    "resource_id": "Identificador numérico extraído da URL, quando disponível.",
    "resource_name": "Nome presente no payload, quando disponível.",
    "source_url": "URL canônica do recurso coletado.",
    "http_status": "Status HTTP observado na coleta.",
    "payload_json": "Resposta JSON integral, sem regras de negócio.",
    "payload_sha256": "Hash SHA-256 do payload usado para versão e idempotência.",
    "source_observed_at": "Timestamp UTC de recebimento da resposta.",
    "ingested_at": "Timestamp UTC de formação do lote Bronze.",
    "run_id": "UUID da execução de ingestão.",
}


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
    if not rows:
        return 0
    frame = spark.createDataFrame(rows, schema=BRONZE_SCHEMA)
    frame.createOrReplaceTempView("pokeapi_bronze_batch")
    spark.sql(
        f"""
        CREATE TABLE IF NOT EXISTS {table}
        USING DELTA
        AS SELECT * FROM pokeapi_bronze_batch WHERE 1 = 0
        """
    )
    spark.sql(f"COMMENT ON TABLE {table} IS 'Payloads JSON imutáveis da PokéAPI REST v2'")
    for column, comment in BRONZE_COMMENTS.items():
        spark.sql(f"ALTER TABLE {table} ALTER COLUMN {column} COMMENT '{comment}'")
    before = spark.table(table).count()
    spark.sql(
        f"""
        MERGE INTO {table} AS target
        USING pokeapi_bronze_batch AS source
          ON target.source_url = source.source_url
         AND target.payload_sha256 = source.payload_sha256
        WHEN NOT MATCHED THEN INSERT *
        """
    )
    return int(spark.table(table).count() - before)


def _append_failures(spark: Any, table: str, failures: list[FetchFailure], run_id: str) -> None:
    if not failures:
        return
    rows = [{**asdict(failure), "run_id": run_id} for failure in failures]
    spark.createDataFrame(rows, schema=FAILURE_SCHEMA).write.mode("append").saveAsTable(table)


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

    spark.createDataFrame(run_rows, schema=RUN_SCHEMA).write.mode("append").saveAsTable(
        f"{full_schema}._ingestion_runs"
    )
    if has_failures and fail_on_partial:
        failed = [row["endpoint"] for row in run_rows if row["status"] != "SUCCESS"]
        raise RuntimeError(f"ingestão {run_id} terminou com falhas: {', '.join(failed)}")
    return run_id
