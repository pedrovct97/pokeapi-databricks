from importlib.resources import files

from pokeapi_lakehouse.battle import BATTLE_FOUNDATION_PRODUCTS, BATTLE_PRODUCTS, MATCHUP_PRODUCT
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


def test_matchup_product_uses_partitioned_sql_contracts() -> None:
    assert MATCHUP_PRODUCT.name == "fact_pokemon_matchup"
    assert MATCHUP_PRODUCT.query_name == "pokemon_matchup"
    assert MATCHUP_PRODUCT.sources == (
        "dim_pokemon",
        "dim_game_version",
        "fact_pokemon_battle_stats",
        "bridge_pokemon_move",
        "pokemon_type",
        "type_damage_relation",
    )

    identifiers = {
        "dim_pokemon": "workspace.pokeapi_gold_dev.dim_pokemon",
        "dim_game_version": "workspace.pokeapi_gold_dev.dim_game_version",
        "fact_pokemon_battle_stats": "workspace.pokeapi_gold_dev.fact_pokemon_battle_stats",
        "bridge_pokemon_move": "workspace.pokeapi_gold_dev.bridge_pokemon_move",
        "pokemon_type": "workspace.pokeapi_silver_dev.pokemon_type",
        "type_damage_relation": "workspace.pokeapi_silver_dev.type_damage_relation",
    }
    literals = {"run_id": "test-run", "version_group_name": "scarlet-violet"}

    assert "CREATE TABLE" in sql_query(
        "create_gold_pokemon_matchup", table="workspace.pokeapi_gold_dev.fact_pokemon_matchup"
    )
    assert "TEMP VIEW" in sql_query(
        "stage_gold_pokemon_matchup_partition", identifiers=identifiers, literals=literals
    )
    assert "MERGE INTO" in sql_query(
        "merge_gold_pokemon_matchup_partition",
        table="workspace.pokeapi_gold_dev.fact_pokemon_matchup",
        literals=literals,
    )
    assert "duplicate_count" in sql_query(
        "quality_gold_pokemon_matchup_partition",
        table="workspace.pokeapi_gold_dev.fact_pokemon_matchup",
        literals=literals,
    )


def test_battle_foundation_excludes_heavy_matchup_product_by_default() -> None:
    assert [product.name for product in BATTLE_FOUNDATION_PRODUCTS] == [
        "dim_ruleset",
        "dim_type",
        "dim_ability",
        "fact_type_matchup",
        "fact_pokemon_battle_stats",
        "dim_move",
        "bridge_pokemon_move",
    ]


def test_move_pool_expands_all_ruleset_levels_and_version_groups() -> None:
    query = sql_query(
        "stage_gold_pokemon_move_pool",
        identifiers={
            "pokemon_move": "workspace.pokeapi_silver_dev.pokemon_move",
            "battle_move": "workspace.pokeapi_gold_dev.battle_move",
            "pokemon_catalog": "workspace.pokeapi_gold_dev.dim_pokemon",
            "dim_ruleset": "workspace.pokeapi_gold_dev.dim_ruleset",
        },
        literals={"run_id": "test-run"},
    )

    assert "JOIN workspace.pokeapi_gold_dev.dim_ruleset r" in query
    assert "r.version_group_name=pm.version_group_name" in query
    assert "r.level battle_level" in query
    assert "version_group_name='scarlet-violet'" not in query
    assert "'ruleset|scarlet-violet|singles|level-50|v1'" not in query


def test_matchup_uses_ruleset_level_damage_features_without_self_matchups() -> None:
    query = sql_query(
        "stage_gold_pokemon_matchup_partition",
        identifiers={
            "dim_pokemon": "workspace.pokeapi_gold_dev.dim_pokemon",
            "dim_game_version": "workspace.pokeapi_gold_dev.dim_game_version",
            "fact_pokemon_battle_stats": "workspace.pokeapi_gold_dev.fact_pokemon_battle_stats",
            "bridge_pokemon_move": "workspace.pokeapi_gold_dev.bridge_pokemon_move",
            "pokemon_type": "workspace.pokeapi_silver_dev.pokemon_type",
            "type_damage_relation": "workspace.pokeapi_silver_dev.type_damage_relation",
        },
        literals={"run_id": "test-run", "version_group_name": "scarlet-violet"},
    )

    assert "WHERE a.pokemon_id<>d.pokemon_id" not in query
    assert "d.pokemon_id<>a.pokemon_id" in query
    assert "FROM workspace.pokeapi_gold_dev.dim_game_version" in query
    assert "JOIN game_versions gv ON" in query
    assert "CONCAT_WS('|','matchup',gv.version_name,s.ruleset_id" in query
    assert "s.ruleset_key,s.ruleset_id,s.battle_level" in query
    assert "version_group_name='scarlet-violet'" in query
    assert "0.925" in query
    assert "accuracy_pct,priority,attacker_speed" in query
    assert "COALESCE(accuracy_pct,100)" in query
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


def test_matchup_partition_sql_scopes_dag_merge_and_quality() -> None:
    identifiers = {
        "dim_pokemon": "workspace.pokeapi_gold_dev.dim_pokemon",
        "dim_game_version": "workspace.pokeapi_gold_dev.dim_game_version",
        "fact_pokemon_battle_stats": "workspace.pokeapi_gold_dev.fact_pokemon_battle_stats",
        "bridge_pokemon_move": "workspace.pokeapi_gold_dev.bridge_pokemon_move",
        "pokemon_type": "workspace.pokeapi_silver_dev.pokemon_type",
        "type_damage_relation": "workspace.pokeapi_silver_dev.type_damage_relation",
    }
    literals = {
        "run_id": "test-run",
        "version_group_name": "scarlet-violet",
    }
    stage = sql_query(
        "stage_gold_pokemon_matchup_partition",
        identifiers=identifiers,
        literals=literals,
    )
    merge = sql_query(
        "merge_gold_pokemon_matchup_partition",
        table="workspace.pokeapi_gold_dev.fact_pokemon_matchup",
        literals=literals,
    )
    quality = sql_query(
        "quality_gold_pokemon_matchup_partition",
        table="workspace.pokeapi_gold_dev.fact_pokemon_matchup",
        literals=literals,
    )

    assert "mp.ruleset_key LIKE CONCAT('ruleset|','scarlet-violet'" in stage
    assert "mp.battle_level IN (50,80,100)" in stage
    assert "WHERE version_group_name='scarlet-violet'" in stage
    assert "COALESCE(accuracy_pct,100)" in stage
    assert "WHEN NOT MATCHED BY SOURCE" in merge
    assert "t.version_group_name='scarlet-violet'" in merge
    assert "t.battle_level=CAST('50' AS INT)" not in merge
    assert "WITH scoped AS" in quality
    assert "version_group_name='scarlet-violet'" in quality
    assert "battle_level=CAST('50' AS INT)" not in quality
    assert "battle_level NOT IN (50,80,100)" in quality


def test_matchup_level_partition_sql_scopes_single_battle_level() -> None:
    identifiers = {
        "dim_pokemon": "workspace.pokeapi_gold_dev.dim_pokemon",
        "dim_game_version": "workspace.pokeapi_gold_dev.dim_game_version",
        "fact_pokemon_battle_stats": "workspace.pokeapi_gold_dev.fact_pokemon_battle_stats",
        "bridge_pokemon_move": "workspace.pokeapi_gold_dev.bridge_pokemon_move",
        "pokemon_type": "workspace.pokeapi_silver_dev.pokemon_type",
        "type_damage_relation": "workspace.pokeapi_silver_dev.type_damage_relation",
    }
    literals = {
        "run_id": "test-run",
        "version_group_name": "black-white",
        "battle_level": "50",
    }
    stage = sql_query(
        "stage_gold_pokemon_matchup_partition_level",
        identifiers=identifiers,
        literals=literals,
    )
    merge = sql_query(
        "merge_gold_pokemon_matchup_partition_level",
        table="workspace.pokeapi_gold_dev.fact_pokemon_matchup",
        literals=literals,
    )
    quality = sql_query(
        "quality_gold_pokemon_matchup_partition_level",
        table="workspace.pokeapi_gold_dev.fact_pokemon_matchup",
        literals=literals,
    )

    assert "mp.ruleset_key=CONCAT_WS('|','ruleset','black-white'" in stage
    assert "mp.battle_level=CAST('50' AS INT)" in stage
    assert "WHERE version_group_name='black-white'" in stage
    assert "WHEN NOT MATCHED BY SOURCE" in merge
    assert "t.version_group_name='black-white'" in merge
    assert "t.battle_level=CAST('50' AS INT)" in merge
    assert "WITH scoped AS" in quality
    assert "version_group_name='black-white'" in quality
    assert "battle_level=CAST('50' AS INT)" in quality


def test_matchup_quality_accepts_zero_damage_only_for_type_immunity() -> None:
    query = "".join(
        sql_query(
            "quality_gold_pokemon_matchup_partition",
            table="workspace.pokeapi_gold_dev.fact_pokemon_matchup",
            literals={"version_group_name": "scarlet-violet"},
        ).split()
    )

    assert "attacker_expected_damage<0" in query
    assert "defender_expected_damage<0" in query
    assert "game_version_key<>CONCAT_WS('|','game_version',CAST(version_idASSTRING))" in query
    assert "battle_levelNOTIN(50,80,100)" in query
    assert (
        "ruleset_id<>CONCAT_WS('|',version_group_name,'singles',"
        "CONCAT('level-',CAST(battle_levelASSTRING)),'v1')" in query
    )
    assert (
        "ruleset_key<>CONCAT_WS('|','ruleset',version_group_name,'singles',"
        "CONCAT('level-',CAST(battle_levelASSTRING)),'v1')" in query
    )
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
        "stage_gold_pokemon_matchup_partition",
        identifiers={
            "dim_pokemon": "workspace.pokeapi_gold_dev.dim_pokemon",
            "dim_game_version": "workspace.pokeapi_gold_dev.dim_game_version",
            "fact_pokemon_battle_stats": "workspace.pokeapi_gold_dev.fact_pokemon_battle_stats",
            "bridge_pokemon_move": "workspace.pokeapi_gold_dev.bridge_pokemon_move",
            "pokemon_type": "workspace.pokeapi_silver_dev.pokemon_type",
            "type_damage_relation": "workspace.pokeapi_silver_dev.type_damage_relation",
        },
        literals={"run_id": "test-run", "version_group_name": "scarlet-violet"},
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
    assert "ruleset_id STRING NOT NULL" in query
    assert "battle_level INT NOT NULL" in query
    assert "game_version_key STRING NOT NULL" in query
    assert "version_id BIGINT NOT NULL" in query
    assert "version_name STRING NOT NULL" in query
    assert "game_version_display_name STRING NOT NULL" in query
    assert "version_group_key STRING NOT NULL" in query
    assert "version_group_name STRING NOT NULL" in query
    assert "attacker_damage_pct DECIMAL(10,2) NOT NULL" in query
    assert "defender_expected_damage DECIMAL(10,2) NOT NULL" in query
    assert "defender_damage_pct DECIMAL(10,2) NOT NULL" in query
    assert "matchup_score DECIMAL(10,2) NOT NULL" in query
    assert "attacker_win_probability DECIMAL(4,2) NOT NULL" in query
    assert "PARTITIONED BY (version_name,battle_level)" in query
    assert "CLUSTER BY" not in query


def test_gold_create_sql_columns_are_documented() -> None:
    sql_dir = files("pokeapi_lakehouse").joinpath("sql")
    data_types = (
        " STRING",
        " BIGINT",
        " DOUBLE",
        " DECIMAL",
        " INT",
        " BOOLEAN",
        " ARRAY",
        " TIMESTAMP",
    )
    offenders: list[str] = []

    for sql_file in sql_dir.iterdir():
        if not sql_file.name.startswith("create_gold_") or sql_file.suffix != ".sql":
            continue
        for line_number, line in enumerate(sql_file.read_text().splitlines(), start=1):
            stripped = line.strip()
            if (
                any(data_type in stripped for data_type in data_types)
                and not stripped.startswith(("CREATE ", "USING ", "COMMENT ", ")"))
                and " COMMENT " not in stripped
            ):
                offenders.append(f"{sql_file.name}:{line_number}: {stripped}")

    assert offenders == []


def test_battle_foundation_create_sql_matches_stage_contracts() -> None:
    type_matchup = sql_query(
        "create_gold_type_matchup_matrix",
        table="workspace.pokeapi_gold_dev.fact_type_matchup",
    )
    assert "matchup_key STRING NOT NULL" in type_matchup
    assert "ruleset_key STRING NOT NULL" in type_matchup
    assert "ruleset_id STRING NOT NULL" in type_matchup
    assert "battle_level INT NOT NULL" in type_matchup
    assert "type_matchup_key" not in type_matchup

    type_matchup_stage = sql_query(
        "stage_gold_type_matchup_matrix",
        identifiers={
            "type": "workspace.pokeapi_silver_dev.type",
            "type_damage_relation": "workspace.pokeapi_silver_dev.type_damage_relation",
            "dim_ruleset": "workspace.pokeapi_gold_dev.dim_ruleset",
        },
        literals={"run_id": "test-run"},
    )
    assert "FROM workspace.pokeapi_gold_dev.dim_ruleset r CROSS JOIN" in type_matchup_stage
    assert "'ruleset|scarlet-violet|singles|level-50|v1'" not in type_matchup_stage

    battle_profile = sql_query(
        "create_gold_pokemon_battle_profile",
        table="workspace.pokeapi_gold_dev.fact_pokemon_battle_stats",
    )
    assert "primary_offense STRING NOT NULL" in battle_profile
    assert "ruleset_id STRING NOT NULL" in battle_profile
    assert "battle_level INT NOT NULL" in battle_profile
    assert "primary_type STRING" not in battle_profile
    assert "secondary_type STRING" not in battle_profile

    battle_profile_stage = sql_query(
        "stage_gold_pokemon_battle_profile",
        identifiers={
            "pokemon_catalog": "workspace.pokeapi_gold_dev.dim_pokemon",
            "type": "workspace.pokeapi_silver_dev.type",
            "pokemon_type": "workspace.pokeapi_silver_dev.pokemon_type",
            "type_damage_relation": "workspace.pokeapi_silver_dev.type_damage_relation",
            "pokemon_stat": "workspace.pokeapi_silver_dev.pokemon_stat",
            "dim_ruleset": "workspace.pokeapi_gold_dev.dim_ruleset",
        },
        literals={"run_id": "test-run"},
    )
    assert "CROSS JOIN workspace.pokeapi_gold_dev.dim_ruleset r" in battle_profile_stage
    assert "CONCAT_WS('|','battle-stats',r.ruleset_id" in battle_profile_stage
    assert "'ruleset|scarlet-violet|singles|level-50|v1'" not in battle_profile_stage

    move_pool = sql_query(
        "create_gold_pokemon_move_pool",
        table="workspace.pokeapi_gold_dev.bridge_pokemon_move",
    )
    assert "ruleset_key STRING NOT NULL" in move_pool
    assert "ruleset_id STRING NOT NULL" in move_pool
    assert "battle_level INT NOT NULL" in move_pool


def test_ruleset_stage_expands_all_version_groups_and_requested_levels() -> None:
    query = sql_query(
        "stage_gold_ruleset",
        identifiers={"dim_version_group": "workspace.pokeapi_gold_dev.dim_version_group"},
        literals={"run_id": "test-run"},
    )
    quality = sql_query("quality_gold_ruleset", table="workspace.pokeapi_gold_dev.dim_ruleset")

    assert "FROM workspace.pokeapi_gold_dev.dim_version_group vg CROSS JOIN levels l" in query
    assert "SELECT 50 level UNION ALL SELECT 80 level UNION ALL SELECT 100 level" in query
    assert "CONCAT_WS('|','ruleset',vg.version_group_name,'singles'" in query
    assert "level NOT IN (50,80,100)" in quality
