from __future__ import annotations

import asyncio

import httpx


class DocumentDownloadError(RuntimeError):
    pass


class DocumentDownloader:
    def __init__(self, timeout_seconds: float = 30, max_retries: int = 3) -> None:
        self._timeout_seconds = timeout_seconds
        self._max_retries = max_retries

    async def download(self, url: str) -> tuple[bytes, str | None]:
        last_error: Exception | None = None
        async with httpx.AsyncClient(
            timeout=self._timeout_seconds, follow_redirects=True
        ) as client:
            for attempt in range(self._max_retries + 1):
                try:
                    response = await client.get(url)
                    response.raise_for_status()
                    return response.content, response.headers.get("content-type")
                except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError) as error:
                    last_error = error
                    if attempt == self._max_retries:
                        break
                    await asyncio.sleep(min(2**attempt, 16))
        raise DocumentDownloadError(f"Could not download source document: {url}") from last_error
