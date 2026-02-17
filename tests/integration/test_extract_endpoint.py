import io
import json


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
    mock_llm_extractor.extract.assert_called_once()


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

    call_args = mock_llm_extractor.extract.call_args
    schema_arg = call_args[0][1]
    assert schema_arg["required"] == ["invoice_number", "issue_date", "seller_nip", "seller_name"]
    assert "line_items" in schema_arg["properties"]


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


def test_extract_rejects_invalid_unstructured_settings(client, auth_header):
    schema = json.dumps({"type": "object", "properties": {}})

    response = client.post(
        "/extract",
        headers=auth_header,
        data={"output_schema": schema, "unstructured_settings": "bad json{"},
        files={"file": ("invoice.pdf", io.BytesIO(b"%PDF-1.4 test"), "application/pdf")},
    )

    assert response.status_code == 400
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "validation_error"
    assert "unstructured_settings" in body["error"]["message"]


def test_extract_with_custom_unstructured_settings(
    client, auth_header, mock_pdf_parser, mock_llm_extractor
):
    schema = json.dumps({"type": "object", "properties": {}})
    us_settings = json.dumps({"strategy": "hi_res", "languages": ["pol"]})

    response = client.post(
        "/extract",
        headers=auth_header,
        data={"output_schema": schema, "unstructured_settings": us_settings},
        files={"file": ("invoice.pdf", io.BytesIO(b"%PDF-1.4 test"), "application/pdf")},
    )

    assert response.status_code == 200
    call_args = mock_pdf_parser.parse.call_args
    settings = call_args[0][1]
    assert settings.strategy == "hi_res"
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
    call_kwargs = mock_llm_extractor.extract.call_args
    assert call_kwargs[1]["model"] == "claude-opus-4-6" or call_kwargs[0][2] == "claude-opus-4-6"
