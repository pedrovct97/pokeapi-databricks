"""Contratos de qualidade Bronze executados localmente com Great Expectations."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import great_expectations as gx
import pandas as pd
import pytest

from pokeapi_lakehouse.bronze import to_bronze_row
from pokeapi_lakehouse.pokeapi_client import FetchedResource


def _bronze_frame() -> pd.DataFrame:
    observed_at = datetime(2026, 1, 1, tzinfo=UTC)
    rows: list[dict[str, Any]] = []
    for resource_id, name in ((1, "bulbasaur"), (25, "pikachu")):
        payload = f'{{"id": {resource_id}, "name": "{name}"}}'
        resource = FetchedResource(
            endpoint="pokemon",
            source_url=f"https://pokeapi.co/api/v2/pokemon/{resource_id}/",
            http_status=200,
            payload_json=payload,
            source_observed_at=observed_at,
            response_bytes=len(payload.encode("utf-8")),
            duration_ms=25,
            attempt_count=1,
        )
        rows.append(to_bronze_row(resource, "gx-test-run", observed_at))
    return pd.DataFrame(rows)


def _validate(frame: pd.DataFrame) -> list[str]:
    context = gx.get_context(mode="ephemeral")
    source = context.data_sources.add_pandas(name="bronze_ci_source")
    asset = source.add_dataframe_asset(name="pokemon_bronze")
    definition = asset.add_batch_definition_whole_dataframe("ci_batch")
    batch = definition.get_batch(batch_parameters={"dataframe": frame})

    expectations = (
        gx.expectations.ExpectTableColumnsToMatchSet(
            column_set=[
                "run_id",
                "endpoint",
                "resource_id",
                "resource_name",
                "source_url",
                "http_status",
                "payload_json",
                "payload_sha256",
                "source_observed_at",
                "ingested_at",
                "response_bytes",
                "duration_ms",
                "attempt_count",
                "etag",
                "last_modified",
            ],
            exact_match=True,
        ),
        gx.expectations.ExpectCompoundColumnsToBeUnique(
            column_list=["endpoint", "resource_id", "payload_sha256"]
        ),
        gx.expectations.ExpectColumnValuesToNotBeNull(column="run_id"),
        gx.expectations.ExpectColumnValuesToNotBeNull(column="source_url"),
        gx.expectations.ExpectColumnValuesToMatchRegex(
            column="source_url", regex=r"^https://pokeapi\.co/api/v2/"
        ),
        gx.expectations.ExpectColumnValuesToBeInSet(column="http_status", value_set=[200]),
        gx.expectations.ExpectColumnValueLengthsToEqual(column="payload_sha256", value=64),
        gx.expectations.ExpectColumnValuesToBeBetween(
            column="attempt_count", min_value=1, max_value=10
        ),
        gx.expectations.ExpectColumnValuesToBeBetween(column="response_bytes", min_value=1),
    )

    failures: list[str] = []
    for expectation in expectations:
        result = batch.validate(expectation)
        if not result.success:
            failures.append(expectation.expectation_type)
    return failures


def test_bronze_sample_satisfies_the_data_contract() -> None:
    assert _validate(_bronze_frame()) == []


def test_bronze_contract_detects_duplicate_versions() -> None:
    frame = _bronze_frame()
    duplicated = pd.concat([frame, frame.iloc[[0]]], ignore_index=True)

    assert "expect_compound_columns_to_be_unique" in _validate(duplicated)


def test_bronze_contract_detects_invalid_source_url() -> None:
    frame = _bronze_frame()
    frame.loc[0, "source_url"] = "http://example.invalid/pokemon/1"

    assert "expect_column_values_to_match_regex" in _validate(frame)


@pytest.mark.parametrize("column", ["run_id", "source_url"])
def test_bronze_contract_detects_null_technical_fields(column: str) -> None:
    frame = _bronze_frame()
    frame.loc[0, column] = None

    assert "expect_column_values_to_not_be_null" in _validate(frame)
