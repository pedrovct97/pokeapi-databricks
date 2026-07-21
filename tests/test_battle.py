from pokeapi_lakehouse.battle import BATTLE_PRODUCTS
from pokeapi_lakehouse.sql_queries import sql_query


def test_battle_products_have_complete_sql_contracts() -> None:
    assert [product.name for product in BATTLE_PRODUCTS] == [
        "dim_ruleset",
        "dim_type",
        "dim_ability",
        "fact_type_matchup",
        "fact_pokemon_battle_stats",
        "dim_move",
        "bridge_pokemon_move",
    ]
    for product in BATTLE_PRODUCTS:
        table = f"workspace.pokeapi_gold_dev.{product.name}"
        identifiers = {
            source: f"workspace.pokeapi_silver_dev.{source}" for source in product.sources
        }
        assert "CREATE TABLE" in sql_query(f"create_gold_{product.query_name}", table=table)
        assert "TEMP VIEW" in sql_query(
            f"stage_gold_{product.query_name}",
            identifiers=identifiers,
            literals={"run_id": "test-run"},
        )
        assert "MERGE INTO" in sql_query(f"merge_gold_{product.query_name}", table=table)
        assert "duplicate_count" in sql_query(f"quality_gold_{product.query_name}", table=table)


def test_move_pool_is_pinned_to_approved_ruleset() -> None:
    query = sql_query(
        "stage_gold_pokemon_move_pool",
        identifiers={
            "pokemon_move": "workspace.pokeapi_silver_dev.pokemon_move",
            "battle_move": "workspace.pokeapi_gold_dev.battle_move",
            "pokemon_catalog": "workspace.pokeapi_gold_dev.dim_pokemon",
        },
        literals={"run_id": "test-run"},
    )

    assert "version_group_name='scarlet-violet'" in query
    assert "scarlet-violet|singles|level-50|v1" in query
