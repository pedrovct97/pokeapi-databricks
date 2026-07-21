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


def test_gold_catalog_has_complete_sql_contract() -> None:
    table = "workspace.pokeapi_gold_dev.dim_pokemon"

    assert "CLUSTER BY (pokemon_id)" in sql_query("create_gold_pokemon_catalog", table=table)
    assert "MERGE INTO" in sql_query("merge_gold_pokemon_catalog", table=table)
    quality = sql_query("quality_gold_pokemon_catalog", table=table)
    assert "duplicate_count" in quality
    assert "SIZE(abilities)=0" in quality
