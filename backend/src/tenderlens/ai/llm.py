from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

import httpx
from pydantic import BaseModel

from tenderlens.config import Settings


class LLMConfigurationError(RuntimeError):
    pass


@dataclass(frozen=True)
class LLMResult:
    text: str
    model: str
    input_tokens: int | None
    output_tokens: int | None


class LLMProvider(Protocol):
    async def answer(self, *, instructions: str, input_text: str) -> LLMResult: ...

    async def structured(
        self, *, instructions: str, input_text: str, schema: type[BaseModel]
    ) -> tuple[BaseModel, LLMResult]: ...


class OpenAIResponsesProvider:
    """Small Responses API adapter; application data stays in TenderLens PostgreSQL."""

    def __init__(self, api_key: str, model: str) -> None:
        self._api_key = api_key
        self._model = model

    async def answer(self, *, instructions: str, input_text: str) -> LLMResult:
        response = await self._create({"instructions": instructions, "input": input_text})
        return self._result_from_response(response)

    async def structured(
        self, *, instructions: str, input_text: str, schema: type[BaseModel]
    ) -> tuple[BaseModel, LLMResult]:
        response = await self._create(
            {
                "instructions": instructions,
                "input": input_text,
                "text": {
                    "format": {
                        "type": "json_schema",
                        "name": schema.__name__.lower(),
                        "strict": True,
                        "schema": schema.model_json_schema(),
                    }
                },
            }
        )
        result = self._result_from_response(response)
        try:
            return schema.model_validate_json(result.text), result
        except ValueError as exc:
            raise RuntimeError(
                "LLM returned data that does not match the requested schema"
            ) from exc

    async def _create(self, payload: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                "https://api.openai.com/v1/responses",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={"model": self._model, "store": False, **payload},
            )
            response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            raise RuntimeError("LLM provider returned an unexpected response")
        return data

    def _result_from_response(self, response: dict[str, Any]) -> LLMResult:
        output = response.get("output")
        if not isinstance(output, list):
            raise RuntimeError("LLM provider did not return output")
        texts = [
            content.get("text")
            for item in output
            if item.get("type") == "message"
            for content in item.get("content", [])
            if content.get("type") == "output_text" and isinstance(content.get("text"), str)
        ]
        if not texts:
            raise RuntimeError("LLM provider returned no text output")
        usage = response.get("usage") if isinstance(response.get("usage"), dict) else {}
        return LLMResult(
            text="\n".join(texts),
            model=str(response.get("model", self._model)),
            input_tokens=usage.get("input_tokens")
            if isinstance(usage.get("input_tokens"), int)
            else None,
            output_tokens=usage.get("output_tokens")
            if isinstance(usage.get("output_tokens"), int)
            else None,
        )


def get_llm_provider(settings: Settings) -> LLMProvider | None:
    if not settings.llm_enabled:
        return None
    if settings.llm_provider == "openai":
        if not settings.openai_api_key:
            raise LLMConfigurationError("OPENAI_API_KEY is required for the OpenAI LLM provider")
        return OpenAIResponsesProvider(settings.openai_api_key, settings.openai_llm_model)
    if not settings.llm_provider:
        raise LLMConfigurationError("LLM_PROVIDER is required when LLM_ENABLED=true")
    raise LLMConfigurationError(f"Unsupported LLM provider: {settings.llm_provider}")
