from tenderlens.ai.llm import OpenAIResponsesProvider


def test_openai_response_parser_reads_text_and_usage() -> None:
    result = OpenAIResponsesProvider("test", "test-model")._result_from_response(
        {
            "model": "test-model",
            "usage": {"input_tokens": 12, "output_tokens": 8},
            "output": [
                {"type": "message", "content": [{"type": "output_text", "text": "Evidence"}]}
            ],
        }
    )

    assert result.text == "Evidence"
    assert result.input_tokens == 12
    assert result.output_tokens == 8
