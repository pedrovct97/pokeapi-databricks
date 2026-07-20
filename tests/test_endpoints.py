import pytest

from pokeapi_lakehouse.endpoints import ENDPOINTS, select_endpoints


def test_registry_has_unique_api_and_table_names() -> None:
    names = [endpoint.name for endpoint in ENDPOINTS]
    tables = [endpoint.table_name for endpoint in ENDPOINTS]

    assert len(names) == 48
    assert len(names) == len(set(names))
    assert len(tables) == len(set(tables))


def test_selects_valid_subset_in_registry_order() -> None:
    selected = select_endpoints("type,pokemon")

    assert [endpoint.name for endpoint in selected] == ["pokemon", "type"]


def test_rejects_unknown_endpoint() -> None:
    with pytest.raises(ValueError, match="desconhecidos"):
        select_endpoints("digimon")
