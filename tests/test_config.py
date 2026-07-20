import pytest

from pokeapi_lakehouse.config import LakehouseConfig


def test_returns_qualified_schema_for_each_layer() -> None:
    config = LakehouseConfig("workspace", "bronze_dev", "silver_dev", "gold_dev")

    assert config.qualified_schema("bronze") == "workspace.bronze_dev"
    assert config.qualified_schema("SILVER") == "workspace.silver_dev"
    assert config.qualified_schema("gold") == "workspace.gold_dev"


@pytest.mark.parametrize("value", ["", "has-hyphen", "has space", "schema.name"])
def test_rejects_unsafe_unity_catalog_identifier(value: str) -> None:
    with pytest.raises(ValueError, match="apenas letras"):
        LakehouseConfig("workspace", value, "silver_dev", "gold_dev")


def test_rejects_unknown_layer() -> None:
    config = LakehouseConfig("workspace", "bronze_dev", "silver_dev", "gold_dev")

    with pytest.raises(ValueError, match="camada desconhecida"):
        config.qualified_schema("platinum")
