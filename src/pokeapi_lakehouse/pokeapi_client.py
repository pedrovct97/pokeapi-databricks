"""Dependency-free PokéAPI client with bounded retries and observability metadata."""

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
class HttpResponse:
    http_status: int
    body: str
    observed_at: datetime
    response_bytes: int
    duration_ms: int
    attempt_count: int
    etag: str | None
    last_modified: str | None


@dataclass(frozen=True)
class FetchedResource:
    endpoint: str
    source_url: str
    http_status: int
    payload_json: str
    source_observed_at: datetime
    response_bytes: int = 0
    duration_ms: int = 0
    attempt_count: int = 1
    etag: str | None = None
    last_modified: str | None = None


@dataclass(frozen=True)
class FetchFailure:
    endpoint: str
    source_url: str
    error_type: str
    error_message: str
    attempted_at: datetime
    http_status: int | None = None
    attempt_count: int = 1
    duration_ms: int = 0
    is_retriable: bool = False


@dataclass(frozen=True)
class EndpointFetchResult:
    resources: list[FetchedResource]
    failures: list[FetchFailure]
    discovered_count: int
    list_count: int
    page_count: int


class RequestFailedError(Exception):
    def __init__(
        self,
        cause: Exception,
        *,
        http_status: int | None,
        attempt_count: int,
        duration_ms: int,
        is_retriable: bool,
    ) -> None:
        super().__init__(str(cause))
        self.cause = cause
        self.http_status = http_status
        self.attempt_count = attempt_count
        self.duration_ms = duration_ms
        self.is_retriable = is_retriable


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

    def _get(self, url: str) -> HttpResponse:
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.hostname != "pokeapi.co":
            raise ValueError(f"URL fora do domínio permitido: {url}")

        request = Request(url, headers={"User-Agent": "pokeapi-lakehouse/0.2"})
        started = time.perf_counter()
        for attempt in range(self.max_retries + 1):
            try:
                with urlopen(request, timeout=self.timeout_seconds) as response:  # noqa: S310
                    raw_body = response.read()
                    body = raw_body.decode("utf-8")
                    json.loads(body)
                    return HttpResponse(
                        http_status=response.status,
                        body=body,
                        observed_at=datetime.now(UTC),
                        response_bytes=len(raw_body),
                        duration_ms=round((time.perf_counter() - started) * 1000),
                        attempt_count=attempt + 1,
                        etag=response.headers.get("ETag"),
                        last_modified=response.headers.get("Last-Modified"),
                    )
            except (
                HTTPError,
                URLError,
                TimeoutError,
                UnicodeDecodeError,
                json.JSONDecodeError,
            ) as exc:
                status = exc.code if isinstance(exc, HTTPError) else None
                retriable = (
                    status == 429 or (status is not None and status >= 500) or status is None
                )
                if attempt == self.max_retries or not retriable:
                    raise RequestFailedError(
                        exc,
                        http_status=status,
                        attempt_count=attempt + 1,
                        duration_ms=round((time.perf_counter() - started) * 1000),
                        is_retriable=retriable,
                    ) from exc
                time.sleep(min(2**attempt + random.random(), 10.0))
        raise AssertionError("retry loop terminou sem retorno")

    def discover_urls(self, endpoint: str) -> tuple[list[str], int, int]:
        """Walk every list page and return URLs, advertised count, and page count."""
        next_url: str | None = f"{BASE_URL}/{endpoint}/?limit={self.page_size}&offset=0"
        urls: list[str] = []
        list_count: int | None = None
        page_count = 0
        while next_url:
            response = self._get(next_url)
            page: dict[str, Any] = json.loads(response.body)
            page_count += 1
            raw_count = page.get("count")
            if not isinstance(raw_count, int):
                raise ValueError(f"count inválido retornado por {endpoint}")
            list_count = raw_count if list_count is None else list_count
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
        return list(dict.fromkeys(urls)), list_count or 0, page_count

    def fetch_endpoint(self, endpoint: str) -> EndpointFetchResult:
        urls, list_count, page_count = self.discover_urls(endpoint)
        resources: list[FetchedResource] = []
        failures: list[FetchFailure] = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self._get, url): url for url in urls}
            for future in as_completed(futures):
                url = futures[future]
                try:
                    response = future.result()
                    resources.append(
                        FetchedResource(
                            endpoint=endpoint,
                            source_url=url,
                            http_status=response.http_status,
                            payload_json=response.body,
                            source_observed_at=response.observed_at,
                            response_bytes=response.response_bytes,
                            duration_ms=response.duration_ms,
                            attempt_count=response.attempt_count,
                            etag=response.etag,
                            last_modified=response.last_modified,
                        )
                    )
                except RequestFailedError as exc:
                    failures.append(
                        FetchFailure(
                            endpoint=endpoint,
                            source_url=url,
                            error_type=type(exc.cause).__name__,
                            error_message=str(exc)[:1000],
                            attempted_at=datetime.now(UTC),
                            http_status=exc.http_status,
                            attempt_count=exc.attempt_count,
                            duration_ms=exc.duration_ms,
                            is_retriable=exc.is_retriable,
                        )
                    )
        resources.sort(key=lambda resource: resource.source_url)
        failures.sort(key=lambda failure: failure.source_url)
        return EndpointFetchResult(resources, failures, len(urls), list_count, page_count)
