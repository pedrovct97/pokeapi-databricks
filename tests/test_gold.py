from types import SimpleNamespace

from pokeapi_lakehouse.gold import (
    GAME_CONTEXT_PRODUCTS,
    MATCHUP_SERVING_MART_PRODUCTS,
    SERVING_MART_PRODUCTS,
    ensure_gold_table_schema,
)
from pokeapi_lakehouse.sql_queries import sql_query


def test_gold_stage_uses_pipe_delimited_deterministic_key() -> None:
    identifiers = {
        name: f"workspace.pokeapi_silver_dev.{name}"
        for name in (
            "pokemon",
            "pokemon_species",
            "pokemon_species_translation",
            "pokemon_type",
            "type_translation",
            "pokemon_stat",
            "pokemon_ability",
            "ability_translation",
            "pokemon_media",
        )
    }
    query = sql_query(
        "stage_gold_pokemon_catalog",
        identifiers=identifiers,
        literals={"run_id": "test-run"},
    )

    assert "CONCAT_WS('|','pokemon',CAST(p.pokemon_id AS STRING))" in query
    assert "language_code='en'" in query
    assert "CROSS JOIN" not in query
    assert "WHERE la.abilities IS NOT NULL" in query
    assert "official_artwork_url" in query


def test_gold_catalog_has_complete_sql_contract() -> None:
    table = "workspace.pokeapi_gold_dev.dim_pokemon"

    assert "CLUSTER BY (pokemon_id)" in sql_query("create_gold_pokemon_catalog", table=table)
    assert "MERGE INTO" in sql_query("merge_gold_pokemon_catalog", table=table)
    quality = sql_query("quality_gold_pokemon_catalog", table=table)
    assert "duplicate_count" in quality
    assert "SIZE(abilities)=0" in quality


def test_gold_game_context_products_have_complete_sql_contracts() -> None:
    assert [product.name for product in GAME_CONTEXT_PRODUCTS] == [
        "dim_version_group",
        "dim_game_version",
    ]
    for product in GAME_CONTEXT_PRODUCTS:
        table = f"workspace.pokeapi_gold_dev.{product.name}"
        identifiers = {
            source: f"workspace.pokeapi_bronze_dev.{source}" for source in product.sources
        }
        assert "CREATE TABLE" in sql_query(f"create_gold_{product.query_name}", table=table)
        assert "TEMP VIEW" in sql_query(
            f"stage_gold_{product.query_name}",
            identifiers=identifiers,
            literals={"run_id": "test-run"},
        )
        assert "MERGE INTO" in sql_query(f"merge_gold_{product.query_name}", table=table)
        assert "duplicate_count" in sql_query(f"quality_gold_{product.query_name}", table=table)


def test_gold_serving_mart_products_have_complete_sql_contracts() -> None:
    assert [product.name for product in SERVING_MART_PRODUCTS] == ["mart_game_pokemon_options"]
    assert [product.name for product in MATCHUP_SERVING_MART_PRODUCTS] == ["mart_matchup_explorer"]


def test_gold_game_pokemon_options_mart_has_complete_sql_contract() -> None:
    product = SERVING_MART_PRODUCTS[0]
    table = f"workspace.pokeapi_gold_dev.{product.name}"
    identifiers = {source: f"workspace.pokeapi_gold_dev.{source}" for source in product.sources}

    create = sql_query(f"create_gold_{product.query_name}", table=table)
    stage = sql_query(
        f"stage_gold_{product.query_name}",
        identifiers=identifiers,
        literals={"run_id": "test-run"},
    )
    merge = sql_query(f"merge_gold_{product.query_name}", table=table)
    quality = sql_query(f"quality_gold_{product.query_name}", table=table)

    assert "CREATE TABLE" in create
    assert "CLUSTER BY (version_name,battle_level)" in create
    assert "PARTITIONED BY" not in create
    assert "TEMP VIEW" in stage
    assert "FROM workspace.pokeapi_gold_dev.fact_pokemon_battle_stats" in stage
    assert "JOIN workspace.pokeapi_gold_dev.dim_game_version" in stage
    assert "JOIN workspace.pokeapi_gold_dev.dim_pokemon" in stage
    assert "fact_pokemon_matchup" not in stage
    assert "MERGE INTO" in merge
    assert "duplicate_count" in quality


def test_gold_matchup_explorer_mart_has_complete_sql_contract() -> None:
    product = MATCHUP_SERVING_MART_PRODUCTS[0]
    assert product.name == "mart_matchup_explorer"
    table = f"workspace.pokeapi_gold_dev.{product.name}"
    identifiers = {source: f"workspace.pokeapi_gold_dev.{source}" for source in product.sources}

    create = sql_query(f"create_gold_{product.query_name}", table=table)
    stage = sql_query(
        f"stage_gold_{product.query_name}",
        identifiers=identifiers,
        literals={"run_id": "test-run"},
    )
    merge = sql_query(f"merge_gold_{product.query_name}", table=table)
    quality = sql_query(f"quality_gold_{product.query_name}", table=table)

    assert "CREATE TABLE" in create
    assert "PARTITIONED BY (version_name,battle_level)" in create
    assert "CLUSTER BY" not in create
    assert "TEMP VIEW" in stage
    assert "FROM workspace.pokeapi_gold_dev.fact_pokemon_matchup" in stage
    assert stage.count("JOIN workspace.pokeapi_gold_dev.dim_pokemon") == 2
    assert "attacker_display_name" in stage
    assert "defender_display_name" in stage
    assert "SELECT *" not in stage.upper()
    assert "MERGE INTO" in merge
    assert "WHEN NOT MATCHED BY SOURCE THEN DELETE" in merge
    assert "duplicate_count" in quality


def test_gold_game_version_stage_uses_game_as_primary_dashboard_context() -> None:
    query = sql_query(
        "stage_gold_game_version",
        identifiers={
            "version": "workspace.pokeapi_bronze_dev.version",
            "version_group": "workspace.pokeapi_bronze_dev.version_group",
            "generation": "workspace.pokeapi_bronze_dev.generation",
        },
        literals={"run_id": "test-run"},
    )

    assert "game_version_key" in query
    assert "version_group_key" in query
    assert "Pokémon Emerald" in query
    assert "main_region" in query
    assert "workspace.pokeapi_bronze_dev.version" in query
    assert "workspace.pokeapi_bronze_dev.version_group" in query


def test_gold_game_context_create_sql_documents_columns() -> None:
    version_group = sql_query(
        "create_gold_version_group", table="workspace.pokeapi_gold_dev.dim_version_group"
    )
    game_version = sql_query(
        "create_gold_game_version", table="workspace.pokeapi_gold_dev.dim_game_version"
    )

    assert "version_group_key STRING NOT NULL COMMENT" in version_group
    assert "game_version_key STRING NOT NULL COMMENT" in game_version
    assert "display_name STRING NOT NULL COMMENT" in game_version
    assert "region_name STRING COMMENT" in game_version


def test_gold_schema_evolution_adds_missing_columns_as_nullable_with_comments() -> None:
    class FakeSpark:
        def __init__(self) -> None:
            self.commands: list[str] = []

        def table(self, _table: str) -> SimpleNamespace:
            return SimpleNamespace(
                schema=SimpleNamespace(
                    fields=[
                        SimpleNamespace(name="matchup_key"),
                        SimpleNamespace(name="ruleset_key"),
                    ]
                )
            )

        def sql(self, command: str) -> None:
            self.commands.append(command)

    spark = FakeSpark()

    ensure_gold_table_schema(
        spark, "workspace.pokeapi_gold_dev.fact_pokemon_matchup", "pokemon_matchup"
    )

    joined = "\n".join(spark.commands)
    assert "ADD COLUMNS (battle_level INT COMMENT" in joined
    assert "ADD COLUMNS (game_version_key STRING COMMENT" in joined
    assert "ADD COLUMNS (ruleset_key" not in joined
    assert "NOT NULL" not in joined
