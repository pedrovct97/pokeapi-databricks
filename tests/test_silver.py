import pytest

from pokeapi_lakehouse.silver import select_silver_entities
from pokeapi_lakehouse.sql_queries import sql_query


def test_selects_pilot_entities_in_stable_order() -> None:
    selected = select_silver_entities("move,pokemon")

    assert [entity.name for entity in selected] == ["pokemon", "move"]


def test_all_selects_battle_domain_scope() -> None:
    assert [entity.name for entity in select_silver_entities("all")] == [
        "pokemon",
        "move",
        "type",
        "stat",
        "ability",
        "pokemon_species",
        "pokemon_type",
        "pokemon_stat",
        "pokemon_ability",
        "pokemon_move",
        "pokemon_media",
        "type_damage_relation",
        "language",
        "pokemon_species_translation",
        "move_translation",
        "ability_translation",
        "type_translation",
    ]


def test_rejects_entity_outside_pilot() -> None:
    with pytest.raises(ValueError, match="desconhecidas"):
        select_silver_entities("berry")


def test_every_silver_entity_has_complete_sql_contract() -> None:
    for entity in select_silver_entities("all"):
        target = f"workspace.pokeapi_silver_dev.{entity.name}"
        bronze = f"workspace.pokeapi_bronze_dev.{entity.bronze_name}"
        assert "CREATE TABLE" in sql_query(f"create_silver_{entity.name}", table=target)
        assert "TEMP VIEW" in sql_query(
            f"stage_silver_{entity.name}",
            identifiers={"bronze_table": bronze},
            literals={"run_id": "test-run"},
        )
        assert "MERGE INTO" in sql_query(f"merge_silver_{entity.name}", table=target)
        assert "duplicate_count" in sql_query(f"quality_silver_{entity.name}", table=target)


def test_relationship_stages_expose_lineage_contract() -> None:
    for entity_name in (
        "pokemon_type",
        "pokemon_stat",
        "pokemon_ability",
        "pokemon_move",
    ):
        query = sql_query(
            f"stage_silver_{entity_name}",
            identifiers={"bronze_table": "workspace.pokeapi_bronze_dev.pokemon"},
            literals={"run_id": "test-run"},
        )
        assert "source_payload_sha256" in query


def test_translation_stages_use_null_safe_array_access() -> None:
    for entity_name, bronze_name in (
        ("pokemon_species_translation", "pokemon_species"),
        ("move_translation", "move"),
        ("ability_translation", "ability"),
    ):
        query = sql_query(
            f"stage_silver_{entity_name}",
            identifiers={"bronze_table": f"workspace.pokeapi_bronze_dev.{bronze_name}"},
            literals={"run_id": "test-run"},
        )
        assert "GET(FILTER(" in query
        assert "ELEMENT_AT(FILTER(" not in query
