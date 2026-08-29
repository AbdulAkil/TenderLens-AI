from __future__ import annotations

from typing import Protocol

import httpx

from tenderlens.config import Settings


class EmbeddingProvider(Protocol):
    async def embed(self, texts: list[str]) -> list[list[float]]: ...


class EmbeddingConfigurationError(RuntimeError):
    pass


class OpenAIEmbeddingProvider:
    """Minimal provider adapter for OpenAI's `/v1/embeddings` endpoint."""

    def __init__(self, api_key: str, model: str) -> None:
        self._api_key = api_key
        self._model = model

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts or any(not text.strip() for text in texts):
            raise ValueError("Embedding input must contain non-empty text")
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                "https://api.openai.com/v1/embeddings",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={"model": self._model, "input": texts, "encoding_format": "float"},
            )
            response.raise_for_status()
        data = response.json().get("data")
        if not isinstance(data, list) or len(data) != len(texts):
            raise RuntimeError("Embedding provider returned an unexpected response")
        ordered = sorted(data, key=lambda item: item["index"])
        embeddings = [item.get("embedding") for item in ordered]
        if any(not isinstance(vector, list) for vector in embeddings):
            raise RuntimeError("Embedding provider returned an invalid embedding")
        return embeddings


def get_embedding_provider(settings: Settings) -> EmbeddingProvider | None:
    if settings.embedding_provider is None or settings.embedding_provider.strip() == "":
        return None
    if settings.embedding_provider == "openai":
        if not settings.openai_api_key:
            raise EmbeddingConfigurationError(
                "OPENAI_API_KEY is required for the OpenAI embedding provider"
            )
        return OpenAIEmbeddingProvider(settings.openai_api_key, settings.openai_embedding_model)
    raise EmbeddingConfigurationError(
        f"Unsupported embedding provider: {settings.embedding_provider}"
    )
