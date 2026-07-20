import pytest

from pokeapi_lakehouse.sql_queries import sql_query


def test_loads_parameterized_create_table_query() -> None:
    query = sql_query("create_bronze_table", table="workspace.pokeapi_bronze_dev.pokemon")

    assert "CREATE TABLE IF NOT EXISTS workspace.pokeapi_bronze_dev.pokemon" in query
    assert "payload_json STRING NOT NULL" in query
    assert "response_bytes BIGINT NOT NULL" in query
    assert "{{table}}" not in query


@pytest.mark.parametrize(
    "table",
    ["workspace.schema", "workspace.schema.table; DROP TABLE x", "workspace.schema.bad-name"],
)
def test_rejects_unsafe_table_identifier(table: str) -> None:
    with pytest.raises(ValueError, match="identificador SQL inválido"):
        sql_query("merge_bronze_table", table=table)


def test_binds_multiple_identifiers_and_literal() -> None:
    query = sql_query(
        "stage_silver_pokemon",
        identifiers={"bronze_table": "workspace.pokeapi_bronze_dev.pokemon"},
        literals={"run_id": "run-'safe"},
    )

    assert "FROM workspace.pokeapi_bronze_dev.pokemon" in query
    assert "'run-''safe' AS silver_run_id" in query
    assert "{{" not in query
