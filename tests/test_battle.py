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
        "fact_pokemon_matchup",
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


def test_matchup_uses_level_50_damage_features_without_self_matchups() -> None:
    query = sql_query(
        "stage_gold_pokemon_matchup",
        identifiers={
            "dim_pokemon": "workspace.pokeapi_gold_dev.dim_pokemon",
            "fact_pokemon_battle_stats": "workspace.pokeapi_gold_dev.fact_pokemon_battle_stats",
            "bridge_pokemon_move": "workspace.pokeapi_gold_dev.bridge_pokemon_move",
            "pokemon_type": "workspace.pokeapi_silver_dev.pokemon_type",
            "type_damage_relation": "workspace.pokeapi_silver_dev.type_damage_relation",
        },
        literals={"run_id": "test-run"},
    )

    assert "WHERE a.pokemon_id<>d.pokemon_id" in query
    assert "0.925" in query
    assert "1.0/(1.0+EXP(-score/15.0))" in query
    assert "CAST(ROUND(attacker_damage,2) AS DECIMAL(10,2)) attacker_expected_damage" in query
    assert "CAST(ROUND(attacker_damage_pct,2) AS DECIMAL(10,2)) attacker_damage_pct" in query
    assert "CAST(ROUND(defender_damage,2) AS DECIMAL(10,2)) defender_expected_damage" in query
    assert "CAST(ROUND(defender_damage_pct,2) AS DECIMAL(10,2)) defender_damage_pct" in query
    assert "CAST(ROUND(score,2) AS DECIMAL(10,2)) matchup_score" in query
    assert (
        "CAST(ROUND(1.0/(1.0+EXP(-score/15.0)),2) AS DECIMAL(4,2)) "
        "attacker_win_probability" in query
    )


def test_matchup_quality_accepts_zero_damage_only_for_type_immunity() -> None:
    query = "".join(
        sql_query(
            "quality_gold_pokemon_matchup",
            table="workspace.pokeapi_gold_dev.fact_pokemon_matchup",
        ).split()
    )

    assert "attacker_expected_damage<0" in query
    assert "defender_expected_damage<0" in query
    assert "attacker_expected_damage<=0" not in query
    assert "defender_expected_damage<=0" not in query
    assert (
        "attacker_expected_damage=0AND(attacker_type_multiplier<>0"
        "ORattacker_turns_to_ko<>999)" in query
    )
    assert (
        "defender_expected_damage=0AND(defender_type_multiplier<>0"
        "ORdefender_turns_to_ko<>999)" in query
    )
    assert "attacker_expected_damage>0ANDattacker_turns_to_ko=999" in query
    assert "defender_expected_damage>0ANDdefender_turns_to_ko=999" in query


def test_matchup_stage_marks_both_type_immunity_outcomes() -> None:
    query = sql_query(
        "stage_gold_pokemon_matchup",
        identifiers={
            "dim_pokemon": "workspace.pokeapi_gold_dev.dim_pokemon",
            "fact_pokemon_battle_stats": "workspace.pokeapi_gold_dev.fact_pokemon_battle_stats",
            "bridge_pokemon_move": "workspace.pokeapi_gold_dev.bridge_pokemon_move",
            "pokemon_type": "workspace.pokeapi_silver_dev.pokemon_type",
            "type_damage_relation": "workspace.pokeapi_silver_dev.type_damage_relation",
        },
        literals={"run_id": "test-run"},
    )

    assert "CASE WHEN type_multiplier=0 THEN 999" in query
    assert "attacker_cannot_damage" in query
    assert "defender_cannot_damage" in query


def test_matchup_numeric_contract_uses_decimal_scale_two() -> None:
    query = sql_query(
        "create_gold_pokemon_matchup",
        table="workspace.pokeapi_gold_dev.fact_pokemon_matchup",
    )

    assert "attacker_expected_damage DECIMAL(10,2) NOT NULL" in query
    assert "attacker_damage_pct DECIMAL(10,2) NOT NULL" in query
    assert "defender_expected_damage DECIMAL(10,2) NOT NULL" in query
    assert "defender_damage_pct DECIMAL(10,2) NOT NULL" in query
    assert "matchup_score DECIMAL(10,2) NOT NULL" in query
    assert "attacker_win_probability DECIMAL(4,2) NOT NULL" in query
