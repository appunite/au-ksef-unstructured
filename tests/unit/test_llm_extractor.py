import json
from unittest.mock import MagicMock, patch

from src.app.services.llm_extractor import LLMExtractor


@patch("src.app.services.llm_extractor.anthropic.Anthropic")
def test_extract_returns_parsed_json(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client

    expected = {"invoice_number": "INV-001", "total_amount": 100.0}
    mock_content_block = MagicMock()
    mock_content_block.text = json.dumps(expected)
    mock_response = MagicMock()
    mock_response.content = [mock_content_block]
    mock_client.messages.create.return_value = mock_response

    extractor = LLMExtractor(api_key="sk-test", model="claude-sonnet-4-5-20250929")
    schema = {
        "type": "object",
        "properties": {
            "invoice_number": {"type": "string"},
            "total_amount": {"type": "number"},
        },
    }

    result = extractor.extract("Invoice #INV-001\nTotal: $100.00", schema)

    assert result == expected


@patch("src.app.services.llm_extractor.anthropic.Anthropic")
def test_extract_passes_schema_to_output_config(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client

    mock_content_block = MagicMock()
    mock_content_block.text = "{}"
    mock_response = MagicMock()
    mock_response.content = [mock_content_block]
    mock_client.messages.create.return_value = mock_response

    extractor = LLMExtractor(api_key="sk-test", model="claude-sonnet-4-5-20250929")
    schema = {
        "type": "object",
        "properties": {
            "vendor": {"type": "string", "description": "Vendor name"},
        },
    }

    extractor.extract("Some text", schema)

    call_kwargs = mock_client.messages.create.call_args.kwargs
    assert call_kwargs["output_config"] == {
        "format": {
            "type": "json_schema",
            "schema": schema,
        }
    }


@patch("src.app.services.llm_extractor.anthropic.Anthropic")
def test_extract_uses_model_override(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client

    mock_content_block = MagicMock()
    mock_content_block.text = "{}"
    mock_response = MagicMock()
    mock_response.content = [mock_content_block]
    mock_client.messages.create.return_value = mock_response

    extractor = LLMExtractor(api_key="sk-test", model="claude-sonnet-4-5-20250929")
    extractor.extract("text", {"type": "object", "properties": {}}, model="claude-opus-4-6")

    call_kwargs = mock_client.messages.create.call_args.kwargs
    assert call_kwargs["model"] == "claude-opus-4-6"


@patch("src.app.services.llm_extractor.anthropic.Anthropic")
def test_extract_uses_default_model_when_no_override(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client

    mock_content_block = MagicMock()
    mock_content_block.text = "{}"
    mock_response = MagicMock()
    mock_response.content = [mock_content_block]
    mock_client.messages.create.return_value = mock_response

    extractor = LLMExtractor(api_key="sk-test", model="claude-sonnet-4-5-20250929")
    extractor.extract("text", {"type": "object", "properties": {}})

    call_kwargs = mock_client.messages.create.call_args.kwargs
    assert call_kwargs["model"] == "claude-sonnet-4-5-20250929"


@patch("src.app.services.llm_extractor.anthropic.Anthropic")
def test_extract_includes_document_text_in_prompt(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client

    mock_content_block = MagicMock()
    mock_content_block.text = "{}"
    mock_response = MagicMock()
    mock_response.content = [mock_content_block]
    mock_client.messages.create.return_value = mock_response

    extractor = LLMExtractor(api_key="sk-test", model="claude-sonnet-4-5-20250929")
    extractor.extract("Invoice from Acme Corp", {"type": "object", "properties": {}})

    call_kwargs = mock_client.messages.create.call_args.kwargs
    user_message = call_kwargs["messages"][0]["content"]
    assert "Invoice from Acme Corp" in user_message
