from __future__ import annotations

from types import SimpleNamespace

from pokeapi_lakehouse.endpoints import ENDPOINTS
from pokeapi_lakehouse.uc_metadata import (
    TableComment,
    load_table_comments,
    render_comment_statements,
    sync_uc_comments,
)


def test_load_table_comments_expands_bronze_endpoint_contract() -> None:
    comments = load_table_comments(layers={"bronze"}, domains={"entity"})

    assert len(comments) == len(ENDPOINTS)
    assert {comment.table_name for comment in comments} == {
        endpoint.table_name for endpoint in ENDPOINTS
    }
    pokemon = next(comment for comment in comments if comment.table_name == "pokemon")
    assert pokemon.description.startswith("Payloads JSON imutáveis")
    assert {column.name for column in pokemon.columns} >= {"endpoint", "payload_json", "run_id"}


def test_render_comment_statements_quotes_identifiers_and_escapes_text() -> None:
    comment = TableComment(
        layer="silver",
        domain="table",
        logical_name="pokemon",
        table_name="pokemon",
        description="Tabela d'água",
        columns=(
            SimpleNamespace(name="pokemon_id", description="ID d'origem"),
            SimpleNamespace(name="missing_col", description="Não deve renderizar"),
        ),
    )

    statements = render_comment_statements(
        comment,
        catalog="workspace",
        bronze_schema="pokeapi_bronze_dev",
        silver_schema="pokeapi_silver_dev",
        gold_schema="pokeapi_gold_dev",
        existing_columns={"pokemon_id"},
    )

    assert statements == (
        "COMMENT ON TABLE `workspace`.`pokeapi_silver_dev`.`pokemon` IS 'Tabela d''água'",
        "ALTER TABLE `workspace`.`pokeapi_silver_dev`.`pokemon` ALTER COLUMN `pokemon_id` "
        "COMMENT 'ID d''origem'",
    )


def test_sync_uc_comments_dry_run_skips_missing_tables_and_columns() -> None:
    class FakeCatalog:
        def tableExists(self, table: str) -> bool:  # noqa: N802 - Spark API shape
            return table == "workspace.pokeapi_silver_dev.pokemon"

    class FakeSpark:
        catalog = FakeCatalog()

        def __init__(self) -> None:
            self.executed: list[str] = []

        def table(self, _table: str) -> SimpleNamespace:
            return SimpleNamespace(
                schema=SimpleNamespace(
                    fields=[
                        SimpleNamespace(name="pokemon_id"),
                        SimpleNamespace(name="pokemon_name"),
                    ]
                )
            )

        def sql(self, statement: str) -> None:
            self.executed.append(statement)

    spark = FakeSpark()

    result = sync_uc_comments(
        spark,
        catalog="workspace",
        bronze_schema="pokeapi_bronze_dev",
        silver_schema="pokeapi_silver_dev",
        gold_schema="pokeapi_gold_dev",
        layers={"silver"},
        domains={"table"},
        dry_run=True,
        skip_missing=True,
    )

    assert spark.executed == []
    assert result.applied_count == 0
    assert any(table.endswith(".ability") for table in result.skipped_tables)
    assert "workspace.pokeapi_silver_dev.pokemon.base_experience" in result.skipped_columns
    assert result.statements == (
        "COMMENT ON TABLE `workspace`.`pokeapi_silver_dev`.`pokemon` IS "
        "'Cadastro atual tipado de Pokémon derivado exclusivamente da Bronze'",
        "ALTER TABLE `workspace`.`pokeapi_silver_dev`.`pokemon` ALTER COLUMN `pokemon_id` "
        "COMMENT 'Identificador da PokéAPI; chave lógica'",
        "ALTER TABLE `workspace`.`pokeapi_silver_dev`.`pokemon` ALTER COLUMN `pokemon_name` "
        "COMMENT 'Nome canônico do Pokémon'",
    )
