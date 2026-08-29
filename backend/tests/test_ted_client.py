import httpx
import pytest

from tenderlens.config import Settings
from tenderlens.ingestion.exceptions import TedSearchTimedOutError
from tenderlens.ingestion.ted_client import TedClient


@pytest.mark.asyncio
async def test_ted_client_posts_documented_search_shape() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["json"] = request.content
        return httpx.Response(200, json={"notices": []})

    client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler), base_url="https://api.ted.europa.eu"
    )
    ted = TedClient(Settings(ted_api_base_url="https://api.ted.europa.eu"), client)
    result = await ted.search(
        query="publication-date>=20260101", fields=["publication-number"], limit=25
    )

    assert result == {"notices": []}
    assert captured["url"] == "https://api.ted.europa.eu/v3/notices/search"
    assert b'"scope":"ACTIVE"' in captured["json"]
    await client.aclose()


@pytest.mark.asyncio
async def test_ted_client_rejects_partial_search_results() -> None:
    client = httpx.AsyncClient(
        transport=httpx.MockTransport(lambda _: httpx.Response(200, json={"timedOut": True})),
        base_url="https://api.ted.europa.eu",
    )
    ted = TedClient(Settings(ted_api_base_url="https://api.ted.europa.eu"), client)

    with pytest.raises(TedSearchTimedOutError):
        await ted.search(query="PD = 20260812", fields=["publication-number"])
    await client.aclose()
