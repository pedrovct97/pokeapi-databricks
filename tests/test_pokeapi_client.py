import json
from datetime import UTC, datetime

import pytest

from pokeapi_lakehouse.pokeapi_client import PokeApiClient


def test_discovers_all_pages_and_removes_duplicate_urls(monkeypatch: pytest.MonkeyPatch) -> None:
    client = PokeApiClient(page_size=2)
    pages = {
        "https://pokeapi.co/api/v2/pokemon/?limit=2&offset=0": {
            "results": [
                {"name": "bulbasaur", "url": "https://pokeapi.co/api/v2/pokemon/1/"},
                {"name": "ivysaur", "url": "https://pokeapi.co/api/v2/pokemon/2/"},
            ],
            "next": "https://pokeapi.co/api/v2/pokemon/?limit=2&offset=2",
        },
        "https://pokeapi.co/api/v2/pokemon/?limit=2&offset=2": {
            "results": [{"name": "ivysaur", "url": "https://pokeapi.co/api/v2/pokemon/2/"}],
            "next": None,
        },
    }

    def fake_get(url: str) -> tuple[int, str, datetime]:
        return 200, json.dumps(pages[url]), datetime.now(UTC)

    monkeypatch.setattr(client, "_get", fake_get)

    assert client.discover_urls("pokemon") == [
        "https://pokeapi.co/api/v2/pokemon/1/",
        "https://pokeapi.co/api/v2/pokemon/2/",
    ]


def test_rejects_urls_outside_official_domain() -> None:
    client = PokeApiClient(max_retries=0)

    with pytest.raises(ValueError, match="domínio permitido"):
        client._get("https://example.com/api/v2/pokemon/1/")
