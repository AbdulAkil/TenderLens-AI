import pytest

from tenderlens.ai.embeddings import EmbeddingConfigurationError, get_embedding_provider
from tenderlens.config import Settings


def test_embedding_provider_is_optional_by_default() -> None:
    assert get_embedding_provider(Settings()) is None


def test_openai_embedding_provider_requires_api_key() -> None:
    with pytest.raises(EmbeddingConfigurationError, match="OPENAI_API_KEY"):
        get_embedding_provider(Settings(embedding_provider="openai"))
