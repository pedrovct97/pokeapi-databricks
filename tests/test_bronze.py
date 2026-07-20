from datetime import UTC, datetime

import pytest

from pokeapi_lakehouse.bronze import to_bronze_row, validate_bronze_rows
from pokeapi_lakehouse.pokeapi_client import FetchedResource


def _resource(payload: str = '{"id": 25, "name": "pikachu"}') -> FetchedResource:
    return FetchedResource(
        endpoint="pokemon",
        source_url="https://pokeapi.co/api/v2/pokemon/25/",
        http_status=200,
        payload_json=payload,
        source_observed_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


def test_builds_traceable_bronze_row() -> None:
    ingested_at = datetime(2026, 1, 2, tzinfo=UTC)

    row = to_bronze_row(_resource(), "run-1", ingested_at)

    assert row["resource_id"] == 25
    assert row["resource_name"] == "pikachu"
    assert len(row["payload_sha256"]) == 64
    assert row["run_id"] == "run-1"
    validate_bronze_rows([row])


def test_accepts_nullable_business_identifiers_for_unnamed_resources() -> None:
    resource = FetchedResource(
        endpoint="characteristic",
        source_url="https://pokeapi.co/api/v2/characteristic/not-numeric/",
        http_status=200,
        payload_json='{"gene_modulo": 1}',
        source_observed_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    row = to_bronze_row(resource, "run-1", datetime.now(UTC))

    assert row["resource_id"] is None
    assert row["resource_name"] is None
    validate_bronze_rows([row])


def test_rejects_null_technical_field() -> None:
    row = to_bronze_row(_resource(), "run-1", datetime.now(UTC))
    row["source_url"] = None

    with pytest.raises(ValueError, match="campos técnicos nulos"):
        validate_bronze_rows([row])


def test_rejects_duplicate_resource_versions() -> None:
    row = to_bronze_row(_resource(), "run-1", datetime.now(UTC))

    with pytest.raises(ValueError, match="duplicados"):
        validate_bronze_rows([row, row.copy()])
