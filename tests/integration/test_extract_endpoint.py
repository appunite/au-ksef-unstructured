import io
import json
from typing import Any


def test_extract_full_pipeline(client, auth_header, mock_pdf_parser, mock_llm_extractor):
    schema = json.dumps(
        {
            "type": "object",
            "properties": {
                "invoice_number": {"type": "string", "description": "Invoice ID"},
                "total_amount": {"type": "number", "description": "Total amount"},
            },
            "required": ["invoice_number", "total_amount"],
        }
    )

    response = client.post(
        "/extract",
        headers=auth_header,
        data={"output_schema": schema},
        files={"file": ("invoice.pdf", io.BytesIO(b"%PDF-1.4 test"), "application/pdf")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["invoice_number"] == "INV-001"
    assert body["data"]["total_amount"] == 100.0

    mock_pdf_parser.parse.assert_called_once()
    mock_llm_extractor.extract_with_schema.assert_called_once()


def test_extract_uses_default_schema_when_not_provided(
    client, auth_header, mock_pdf_parser, mock_llm_extractor
):
    response = client.post(
        "/extract",
        headers=auth_header,
        files={"file": ("invoice.pdf", io.BytesIO(b"%PDF-1.4 test"), "application/pdf")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True

    mock_llm_extractor.extract_with_model.assert_called_once()
    call_args = mock_llm_extractor.extract_with_model.call_args
    from src.app.schemas.invoice import InvoiceSchema

    assert call_args[0][1] is InvoiceSchema


def test_extract_rejects_empty_file(client, auth_header):
    response = client.post(
        "/extract",
        headers=auth_header,
        files={"file": ("invoice.pdf", io.BytesIO(b""), "application/pdf")},
    )

    assert response.status_code == 400
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "validation_error"
    assert "empty" in body["error"]["message"].lower()


def test_extract_rejects_file_exceeding_size_limit(client, auth_header):
    # Default limit is 10 MB; send just over
    oversized = b"%" * (10 * 1024 * 1024 + 1)
    response = client.post(
        "/extract",
        headers=auth_header,
        files={"file": ("invoice.pdf", io.BytesIO(oversized), "application/pdf")},
    )

    assert response.status_code == 400
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "validation_error"
    assert "size" in body["error"]["message"].lower()


def test_extract_rejects_schema_without_properties(client, auth_header):
    response = client.post(
        "/extract",
        headers=auth_header,
        data={"output_schema": json.dumps({"type": "string"})},
        files={"file": ("invoice.pdf", io.BytesIO(b"%PDF-1.4 test"), "application/pdf")},
    )

    assert response.status_code == 400
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "validation_error"
    assert "properties" in body["error"]["message"]


def test_extract_rejects_non_pdf(client, auth_header):
    schema = json.dumps({"type": "object", "properties": {}})

    response = client.post(
        "/extract",
        headers=auth_header,
        data={"output_schema": schema},
        files={"file": ("doc.txt", io.BytesIO(b"not a pdf"), "text/plain")},
    )

    assert response.status_code == 400
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "validation_error"
    assert "PDF" in body["error"]["message"]


def test_extract_rejects_invalid_schema_json(client, auth_header):
    response = client.post(
        "/extract",
        headers=auth_header,
        data={"output_schema": "not valid json{"},
        files={"file": ("invoice.pdf", io.BytesIO(b"%PDF-1.4 test"), "application/pdf")},
    )

    assert response.status_code == 400
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "validation_error"
    assert "output_schema" in body["error"]["message"]


def test_extract_rejects_invalid_pdf_settings(client, auth_header):
    schema = json.dumps({"type": "object", "properties": {}})

    response = client.post(
        "/extract",
        headers=auth_header,
        data={"output_schema": schema, "pdf_settings_json": "bad json{"},
        files={"file": ("invoice.pdf", io.BytesIO(b"%PDF-1.4 test"), "application/pdf")},
    )

    assert response.status_code == 400
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "validation_error"
    assert "pdf_settings" in body["error"]["message"]


def test_extract_with_custom_pdf_settings(
    client: Any, auth_header: dict[str, str], mock_pdf_parser: Any, mock_llm_extractor: Any
) -> None:
    schema = json.dumps({"type": "object", "properties": {}})
    us_settings = json.dumps({"strategy": "ocr_only", "languages": ["pol"]})

    response = client.post(
        "/extract",
        headers=auth_header,
        data={"output_schema": schema, "pdf_settings_json": us_settings},
        files={"file": ("invoice.pdf", io.BytesIO(b"%PDF-1.4 test"), "application/pdf")},
    )

    assert response.status_code == 200
    call_args = mock_pdf_parser.parse.call_args
    settings = call_args[0][1]
    assert settings.strategy == "ocr_only"
    assert settings.languages == ["pol"]


def test_extract_with_model_override(client, auth_header, mock_pdf_parser, mock_llm_extractor):
    schema = json.dumps({"type": "object", "properties": {}})

    response = client.post(
        "/extract",
        headers=auth_header,
        data={"output_schema": schema, "model": "claude-opus-4-6"},
        files={"file": ("invoice.pdf", io.BytesIO(b"%PDF-1.4 test"), "application/pdf")},
    )

    assert response.status_code == 200
    call_kwargs = mock_llm_extractor.extract_with_schema.call_args
    assert call_kwargs[1]["model"] == "claude-opus-4-6" or call_kwargs[0][2] == "claude-opus-4-6"
