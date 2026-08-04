from __future__ import annotations

from importlib.resources import files
from pathlib import Path

import yaml

from pokeapi_lakehouse.sql_queries import sql_query
from tools.generate_data_contracts import build_contract

SQL_ROOT = Path("src/pokeapi_lakehouse/sql")
CONTRACT_ROOT = Path("src/pokeapi_lakehouse/contracts")


def _logical_contract_path(create_sql: Path) -> Path:
    expected_contract = build_contract(create_sql)
    layer = expected_contract["layer"]
    logical = create_sql.stem.removeprefix("create_")
    if logical.startswith(f"{layer}_"):
        logical = logical.removeprefix(f"{layer}_")
    if layer == "silver":
        return CONTRACT_ROOT / layer / f"{logical}.yaml"
    domain = expected_contract["domain"]
    return CONTRACT_ROOT / layer / domain / f"{logical}.yaml"


def test_sql_templates_are_grouped_in_layer_and_domain_folders() -> None:
    flat_sql_files = sorted(path.name for path in SQL_ROOT.glob("*.sql"))
    assert flat_sql_files == []

    expected_paths = [
        SQL_ROOT / "bronze" / "create" / "create_bronze_table.sql",
        SQL_ROOT / "bronze" / "merge" / "merge_ingestion_runs.sql",
        SQL_ROOT / "silver" / "stage" / "stage_silver_pokemon.sql",
        SQL_ROOT / "silver" / "merge" / "merge_silver_pokemon_move.sql",
        SQL_ROOT / "silver" / "quality" / "quality_silver_move_translation.sql",
        SQL_ROOT / "gold" / "create" / "create_gold_runs.sql",
        SQL_ROOT / "gold" / "create" / "create_gold_pokemon_catalog.sql",
        SQL_ROOT / "gold" / "stage" / "stage_gold_pokemon_matchup_partition.sql",
        SQL_ROOT / "gold" / "merge" / "merge_gold_pokemon_move_pool.sql",
    ]
    missing = [str(path) for path in expected_paths if not path.exists()]
    assert missing == []

    for layer in ("bronze", "silver", "gold"):
        assert list((SQL_ROOT / layer).glob("*.sql")) == []
        assert sorted(path.name for path in (SQL_ROOT / layer).glob("*/*.sql"))
        assert list((SQL_ROOT / layer).glob("*/*/*.sql")) == []


def test_sql_query_loads_templates_from_recursive_layout() -> None:
    assert "CREATE TABLE" in sql_query(
        "create_bronze_table", table="workspace.pokeapi_bronze_dev.pokemon"
    )
    assert "TEMP VIEW" in sql_query(
        "stage_silver_pokemon",
        identifiers={"bronze_table": "workspace.pokeapi_bronze_dev.pokemon"},
        literals={"run_id": "test-run"},
    )
    assert "MERGE INTO" in sql_query(
        "merge_gold_pokemon_matchup_partition",
        table="workspace.pokeapi_gold_dev.fact_pokemon_matchup",
        literals={"version_group_name": "scarlet-violet"},
    )


def test_package_data_includes_recursive_sql_and_yaml_contracts() -> None:
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")

    assert '"sql/**/*.sql"' in pyproject
    assert '"contracts/**/*.yaml"' in pyproject
    assert '"sql/*.sql"' not in pyproject


def test_yaml_contracts_document_quality_expectations() -> None:
    expected_files = [
        CONTRACT_ROOT / "bronze" / "entity" / "table.yaml",
        CONTRACT_ROOT / "silver" / "pokemon.yaml",
        CONTRACT_ROOT / "gold" / "fact" / "pokemon_matchup.yaml",
        CONTRACT_ROOT / "great_expectations" / "bronze_table.yaml",
    ]
    missing = [str(path) for path in expected_files if not path.exists()]
    assert missing == []

    for path in expected_files:
        contract = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert contract["version"] == 1
        assert contract["layer"] in {"bronze", "silver", "gold"}
        assert contract["owner"] == "pokeapi_lakehouse"
        assert contract.get("quality") or contract.get("quality_expectations")


def test_every_create_sql_has_a_table_yaml_contract() -> None:
    create_sql_files = sorted(SQL_ROOT.rglob("create_*.sql"))
    contract_files = sorted(
        path for path in CONTRACT_ROOT.rglob("*.yaml") if "great_expectations" not in path.parts
    )

    expected_contracts = sorted(_logical_contract_path(path) for path in create_sql_files)
    assert [str(path) for path in contract_files] == [str(path) for path in expected_contracts]

    for create_sql in create_sql_files:
        contract_path = _logical_contract_path(create_sql)
        contract = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
        assert contract["version"] == 1
        assert contract["layer"] in {"bronze", "silver", "gold"}
        assert contract["domain"] == build_contract(create_sql)["domain"]
        assert contract["owner"] == "pokeapi_lakehouse"
        assert contract["logical_name"] == contract_path.stem
        assert contract["description"]
        assert contract["grain"]
        assert "primary_key" in contract
        assert "foreign_keys" in contract
        assert "partition_by" in contract
        assert contract["columns"]
        assert contract["quality_expectations"]
        assert (
            create_sql.relative_to(Path("src/pokeapi_lakehouse")).as_posix()
            in contract["sql_templates"]
        )


def test_table_yaml_contracts_are_complete_data_dictionaries() -> None:
    for create_sql in sorted(SQL_ROOT.rglob("create_*.sql")):
        contract_path = _logical_contract_path(create_sql)
        contract = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
        expected_contract = build_contract(create_sql)

        assert contract == expected_contract
        assert contract["columns"]
        assert len(contract["columns"]) == len(expected_contract["columns"])

        for column in contract["columns"]:
            assert set(column) == {"name", "type", "nullable", "description", "semantic_role"}
            assert column["name"]
            assert column["type"]
            assert isinstance(column["nullable"], bool)
            assert column["description"]
            assert "pendente" not in column["description"].lower()
            assert column["semantic_role"] in {
                "technical_key",
                "business_key",
                "metric",
                "dimension",
                "audit",
                "lineage",
                "quality",
            }

        expectation_names = {
            expectation["name"] for expectation in contract["quality_expectations"]
        }
        assert "schema_columns_match_ddl" in expectation_names
        if contract["primary_key"]:
            assert "primary_key_not_null" in expectation_names
            assert "primary_key_unique" in expectation_names


def test_yaml_contracts_are_packaged_with_the_wheel_resources() -> None:
    contracts_root = files("pokeapi_lakehouse").joinpath("contracts")
    assert contracts_root.joinpath("bronze", "entity", "table.yaml").is_file()
    assert contracts_root.joinpath("silver", "pokemon.yaml").is_file()
    assert contracts_root.joinpath("gold", "fact", "pokemon_matchup.yaml").is_file()
