import json
from unittest.mock import MagicMock, patch

from pydantic import BaseModel, Field

from src.app.services.llm_extractor import LLMExtractor


class _TestModel(BaseModel):
    invoice_number: str = Field(description="Invoice ID")
    total_amount: float = Field(description="Total amount")


# --- extract_with_model tests ---


@patch("src.app.services.llm_extractor.anthropic.Anthropic")
def test_extract_with_model_returns_parsed_dict(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client

    parsed_instance = _TestModel(invoice_number="INV-001", total_amount=100.0)
    mock_response = MagicMock()
    mock_response.parsed_output = parsed_instance
    mock_client.messages.parse.return_value = mock_response

    extractor = LLMExtractor(api_key="sk-test", model="claude-sonnet-4-5-20250929")
    result = extractor.extract_with_model("Invoice #INV-001\nTotal: $100.00", _TestModel)

    assert result == {"invoice_number": "INV-001", "total_amount": 100.0}


@patch("src.app.services.llm_extractor.anthropic.Anthropic")
def test_extract_with_model_passes_output_format(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client

    mock_response = MagicMock()
    mock_response.parsed_output = _TestModel(invoice_number="X", total_amount=0)
    mock_client.messages.parse.return_value = mock_response

    extractor = LLMExtractor(api_key="sk-test", model="claude-sonnet-4-5-20250929")
    extractor.extract_with_model("text", _TestModel)

    call_kwargs = mock_client.messages.parse.call_args.kwargs
    assert call_kwargs["output_format"] is _TestModel


@patch("src.app.services.llm_extractor.anthropic.Anthropic")
def test_extract_with_model_uses_model_override(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client

    mock_response = MagicMock()
    mock_response.parsed_output = _TestModel(invoice_number="X", total_amount=0)
    mock_client.messages.parse.return_value = mock_response

    extractor = LLMExtractor(api_key="sk-test", model="claude-sonnet-4-5-20250929")
    extractor.extract_with_model("text", _TestModel, model="claude-opus-4-6")

    call_kwargs = mock_client.messages.parse.call_args.kwargs
    assert call_kwargs["model"] == "claude-opus-4-6"


@patch("src.app.services.llm_extractor.anthropic.Anthropic")
def test_extract_with_model_uses_default_model(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client

    mock_response = MagicMock()
    mock_response.parsed_output = _TestModel(invoice_number="X", total_amount=0)
    mock_client.messages.parse.return_value = mock_response

    extractor = LLMExtractor(api_key="sk-test", model="claude-sonnet-4-5-20250929")
    extractor.extract_with_model("text", _TestModel)

    call_kwargs = mock_client.messages.parse.call_args.kwargs
    assert call_kwargs["model"] == "claude-sonnet-4-5-20250929"


@patch("src.app.services.llm_extractor.anthropic.Anthropic")
def test_extract_with_model_includes_document_text_in_prompt(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client

    mock_response = MagicMock()
    mock_response.parsed_output = _TestModel(invoice_number="X", total_amount=0)
    mock_client.messages.parse.return_value = mock_response

    extractor = LLMExtractor(api_key="sk-test", model="claude-sonnet-4-5-20250929")
    extractor.extract_with_model("Invoice from Acme Corp", _TestModel)

    call_kwargs = mock_client.messages.parse.call_args.kwargs
    user_message = call_kwargs["messages"][0]["content"]
    assert "Invoice from Acme Corp" in user_message


# --- extract_with_schema tests ---


@patch("src.app.services.llm_extractor.anthropic.Anthropic")
def test_extract_with_schema_returns_parsed_json(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client

    expected = {"invoice_number": "INV-001", "total_amount": 100.0}
    mock_content_block = MagicMock()
    mock_content_block.text = json.dumps(expected)
    mock_response = MagicMock()
    mock_response.content = [mock_content_block]
    mock_client.messages.create.return_value = mock_response

    extractor = LLMExtractor(api_key="sk-test", model="claude-sonnet-4-5-20250929")
    schema = {"type": "object", "properties": {"invoice_number": {"type": "string"}}}
    result = extractor.extract_with_schema("Invoice #INV-001\nTotal: $100.00", schema)

    assert result == expected


@patch("src.app.services.llm_extractor.anthropic.Anthropic")
def test_extract_with_schema_sends_schema_in_output_config(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client

    mock_content_block = MagicMock()
    mock_content_block.text = "{}"
    mock_response = MagicMock()
    mock_response.content = [mock_content_block]
    mock_client.messages.create.return_value = mock_response

    extractor = LLMExtractor(api_key="sk-test", model="claude-sonnet-4-5-20250929")
    schema = {"type": "object", "properties": {"vendor": {"type": "string"}}}
    extractor.extract_with_schema("Some text", schema)

    call_kwargs = mock_client.messages.create.call_args.kwargs
    assert call_kwargs["output_config"]["format"]["type"] == "json_schema"
    assert "schema" in call_kwargs["output_config"]["format"]


@patch("src.app.services.llm_extractor.anthropic.Anthropic")
def test_extract_with_schema_uses_model_override(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client

    mock_content_block = MagicMock()
    mock_content_block.text = "{}"
    mock_response = MagicMock()
    mock_response.content = [mock_content_block]
    mock_client.messages.create.return_value = mock_response

    extractor = LLMExtractor(api_key="sk-test", model="claude-sonnet-4-5-20250929")
    extractor.extract_with_schema(
        "text", {"type": "object", "properties": {}}, model="claude-opus-4-6"
    )

    call_kwargs = mock_client.messages.create.call_args.kwargs
    assert call_kwargs["model"] == "claude-opus-4-6"


@patch("src.app.services.llm_extractor.anthropic.Anthropic")
def test_extract_with_schema_uses_default_model(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client

    mock_content_block = MagicMock()
    mock_content_block.text = "{}"
    mock_response = MagicMock()
    mock_response.content = [mock_content_block]
    mock_client.messages.create.return_value = mock_response

    extractor = LLMExtractor(api_key="sk-test", model="claude-sonnet-4-5-20250929")
    extractor.extract_with_schema("text", {"type": "object", "properties": {}})

    call_kwargs = mock_client.messages.create.call_args.kwargs
    assert call_kwargs["model"] == "claude-sonnet-4-5-20250929"
