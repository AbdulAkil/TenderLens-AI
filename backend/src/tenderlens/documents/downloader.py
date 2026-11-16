from __future__ import annotations

import asyncio
from urllib.parse import urlsplit

import httpx


class DocumentDownloadError(RuntimeError):
    pass


class DocumentDownloader:
    def __init__(self, timeout_seconds: float = 30, max_retries: int = 3) -> None:
        self._timeout_seconds = timeout_seconds
        self._max_retries = max_retries

    async def download(self, url: str) -> tuple[bytes, str | None]:
        parts = urlsplit(url)
        if (
            parts.scheme != "https"
            or parts.hostname != "ted.europa.eu"
            or parts.port not in (None, 443)
            or parts.username
            or parts.password
        ):
            raise DocumentDownloadError("Only HTTPS documents on ted.europa.eu are permitted")
        last_error: Exception | None = None
        async with httpx.AsyncClient(
            timeout=self._timeout_seconds, follow_redirects=False, trust_env=False
        ) as client:
            for attempt in range(self._max_retries + 1):
                try:
                    async with client.stream("GET", url) as response:
                        response.raise_for_status()
                        if response.is_redirect:
                            raise DocumentDownloadError(
                                "Document redirects require manual source review"
                            )
                        content = bytearray()
                        async for chunk in response.aiter_bytes():
                            content.extend(chunk)
                            if len(content) > 10 * 1024 * 1024:
                                raise DocumentDownloadError(
                                    "Document exceeds the 10 MiB processing limit"
                                )
                        return bytes(content), response.headers.get("content-type")
                except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError) as error:
                    last_error = error
                    if attempt == self._max_retries:
                        break
                    await asyncio.sleep(min(2**attempt, 16))
        raise DocumentDownloadError(f"Could not download source document: {url}") from last_error
