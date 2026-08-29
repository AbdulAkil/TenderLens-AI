from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Sequence
from typing import Any

import httpx

from tenderlens.config import Settings, get_settings
from tenderlens.ingestion.exceptions import (
    TedApiError,
    TedRateLimitError,
    TedResponseError,
    TedSearchTimedOutError,
)


class TedClient:
    """Transport client for TED's public v3 published-notice Search API.

    Expert-query construction stays outside this class: TED owns its field
    vocabulary and query grammar. This boundary owns retries, pagination and
    envelope validation only.
    """

    def __init__(
        self,
        settings: Settings | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._client = client or httpx.AsyncClient(
            base_url=self._settings.ted_api_base_url,
            timeout=httpx.Timeout(self._settings.ted_api_timeout_seconds),
        )
        self._owns_client = client is None

    async def __aenter__(self) -> TedClient:
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def search(
        self,
        *,
        query: str,
        fields: Sequence[str],
        limit: int = 100,
        page: int = 1,
        scope: str = "ACTIVE",
        pagination_mode: str = "PAGE_NUMBER",
        iteration_next_token: str | None = None,
        only_latest_versions: bool = True,
    ) -> dict[str, Any]:
        if not 1 <= limit <= 250:
            raise ValueError("TED Search API limit must be between 1 and 250")
        if page < 1:
            raise ValueError("TED Search API pages are one-indexed")

        payload: dict[str, Any] = {
            "query": query,
            "fields": list(fields),
            "page": page,
            "limit": limit,
            "scope": scope,
            "paginationMode": pagination_mode,
            "onlyLatestVersions": only_latest_versions,
        }
        if iteration_next_token:
            payload["iterationNextToken"] = iteration_next_token

        response = await self._post_with_retry(payload)
        try:
            data = response.json()
        except ValueError as error:
            raise TedResponseError("TED returned a non-JSON search response") from error
        if not isinstance(data, dict):
            raise TedResponseError("TED search response must be an object")
        if data.get("timedOut") is True:
            raise TedSearchTimedOutError("TED timed out before returning a complete search result")
        if not isinstance(data.get("notices", []), list):
            raise TedResponseError("TED search response notices must be a list")
        return data

    async def iterate(
        self,
        *,
        query: str,
        fields: Sequence[str],
        scope: str = "ACTIVE",
        limit: int = 250,
        only_latest_versions: bool = True,
    ) -> AsyncIterator[dict[str, Any]]:
        token: str | None = None
        while True:
            response = await self.search(
                query=query,
                fields=fields,
                scope=scope,
                limit=limit,
                pagination_mode="ITERATION",
                iteration_next_token=token,
                only_latest_versions=only_latest_versions,
            )
            yield response
            token = response.get("iterationNextToken")
            if not token or not response["notices"]:
                return

    async def _post_with_retry(self, payload: dict[str, Any]) -> httpx.Response:
        last_error: Exception | None = None
        for attempt in range(self._settings.ted_api_max_retries + 1):
            try:
                response = await self._client.post("/v3/notices/search", json=payload)
                if response.status_code == 429:
                    if attempt == self._settings.ted_api_max_retries:
                        raise TedRateLimitError("TED Search API rate limit exceeded")
                    await self._backoff(attempt, response.headers.get("Retry-After"))
                    continue
                response.raise_for_status()
                return response
            except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError) as error:
                last_error = error
                if attempt == self._settings.ted_api_max_retries:
                    break
                await self._backoff(attempt, None)
        raise TedApiError("TED Search API request failed after retries") from last_error

    @staticmethod
    async def _backoff(attempt: int, retry_after: str | None) -> None:
        try:
            delay = float(retry_after) if retry_after else min(2**attempt, 16)
        except ValueError:
            delay = min(2**attempt, 16)
        await asyncio.sleep(delay)
