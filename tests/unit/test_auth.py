import io
import json


def test_valid_token_allows_access(client, auth_header, mock_pdf_parser, mock_llm_extractor):
    schema = json.dumps({"type": "object", "properties": {"invoice_number": {"type": "string"}}})
    response = client.post(
        "/extract",
        headers=auth_header,
        data={"output_schema": schema},
        files={"file": ("invoice.pdf", io.BytesIO(b"%PDF-1.4 test"), "application/pdf")},
    )
    assert response.status_code == 200


def test_invalid_token_returns_401(client, mock_pdf_parser, mock_llm_extractor):
    schema = json.dumps({"type": "object", "properties": {}})
    response = client.post(
        "/extract",
        headers={"Authorization": "Bearer wrong-token"},
        data={"output_schema": schema},
        files={"file": ("invoice.pdf", io.BytesIO(b"%PDF-1.4 test"), "application/pdf")},
    )
    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "authentication_error"


def test_missing_token_returns_unauthorized(client):
    schema = json.dumps({"type": "object", "properties": {}})
    response = client.post(
        "/extract",
        data={"output_schema": schema},
        files={"file": ("invoice.pdf", io.BytesIO(b"%PDF-1.4 test"), "application/pdf")},
    )
    assert response.status_code in (401, 403)
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "authentication_error"


def test_health_endpoint_no_auth_required(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
