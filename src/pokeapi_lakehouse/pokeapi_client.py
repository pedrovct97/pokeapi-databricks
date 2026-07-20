"""Small, dependency-free PokéAPI client with bounded retries and concurrency."""

from __future__ import annotations

import json
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

BASE_URL = "https://pokeapi.co/api/v2"


@dataclass(frozen=True)
class FetchedResource:
    endpoint: str
    source_url: str
    http_status: int
    payload_json: str
    source_observed_at: datetime


@dataclass(frozen=True)
class FetchFailure:
    endpoint: str
    source_url: str
    error_type: str
    error_message: str
    attempted_at: datetime


class PokeApiClient:
    """Discover and fetch REST resources while respecting PokéAPI fair use."""

    def __init__(
        self,
        timeout_seconds: float = 30.0,
        max_retries: int = 3,
        max_workers: int = 8,
        page_size: int = 100,
    ) -> None:
        if timeout_seconds <= 0 or max_retries < 0 or max_workers <= 0 or page_size <= 0:
            raise ValueError("parâmetros do cliente devem ser positivos")
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.max_workers = max_workers
        self.page_size = page_size

    def _get(self, url: str) -> tuple[int, str, datetime]:
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.hostname != "pokeapi.co":
            raise ValueError(f"URL fora do domínio permitido: {url}")

        request = Request(url, headers={"User-Agent": "pokeapi-lakehouse/0.1"})
        for attempt in range(self.max_retries + 1):
            try:
                with urlopen(request, timeout=self.timeout_seconds) as response:  # noqa: S310
                    body = response.read().decode("utf-8")
                    json.loads(body)
                    return response.status, body, datetime.now(UTC)
            except (HTTPError, URLError, TimeoutError, UnicodeDecodeError, json.JSONDecodeError):
                if attempt == self.max_retries:
                    raise
                time.sleep(min(2**attempt + random.random(), 10.0))
        raise AssertionError("retry loop terminou sem retorno")

    def discover_urls(self, endpoint: str) -> list[str]:
        """Walk every list page and return the canonical detail URLs."""
        next_url: str | None = f"{BASE_URL}/{endpoint}/?limit={self.page_size}&offset=0"
        urls: list[str] = []
        while next_url:
            _, body, _ = self._get(next_url)
            page: dict[str, Any] = json.loads(body)
            results = page.get("results")
            if not isinstance(results, list):
                raise ValueError(f"lista inválida retornada por {endpoint}")
            for result in results:
                if not isinstance(result, dict) or not isinstance(result.get("url"), str):
                    raise ValueError(f"recurso inválido retornado por {endpoint}")
                urls.append(result["url"])
            raw_next = page.get("next")
            if raw_next is not None and not isinstance(raw_next, str):
                raise ValueError(f"paginação inválida retornada por {endpoint}")
            next_url = raw_next
        return list(dict.fromkeys(urls))

    def fetch_endpoint(
        self, endpoint: str
    ) -> tuple[list[FetchedResource], list[FetchFailure], int]:
        urls = self.discover_urls(endpoint)
        resources: list[FetchedResource] = []
        failures: list[FetchFailure] = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self._get, url): url for url in urls}
            for future in as_completed(futures):
                url = futures[future]
                try:
                    status, body, observed_at = future.result()
                    resources.append(FetchedResource(endpoint, url, status, body, observed_at))
                except Exception as exc:  # failure is persisted by the orchestration boundary
                    failures.append(
                        FetchFailure(
                            endpoint=endpoint,
                            source_url=url,
                            error_type=type(exc).__name__,
                            error_message=str(exc)[:1000],
                            attempted_at=datetime.now(UTC),
                        )
                    )
        resources.sort(key=lambda resource: resource.source_url)
        failures.sort(key=lambda failure: failure.source_url)
        return resources, failures, len(urls)
