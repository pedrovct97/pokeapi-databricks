import pytest

from pokeapi_lakehouse.sql_queries import sql_query


def test_loads_parameterized_create_table_query() -> None:
    query = sql_query("create_bronze_table", table="workspace.pokeapi_bronze_dev.pokemon")

    assert "CREATE TABLE IF NOT EXISTS workspace.pokeapi_bronze_dev.pokemon" in query
    assert "payload_json STRING NOT NULL" in query
    assert "{{table}}" not in query


@pytest.mark.parametrize(
    "table",
    ["workspace.schema", "workspace.schema.table; DROP TABLE x", "workspace.schema.bad-name"],
)
def test_rejects_unsafe_table_identifier(table: str) -> None:
    with pytest.raises(ValueError, match="tabela inválida"):
        sql_query("merge_bronze_table", table=table)
