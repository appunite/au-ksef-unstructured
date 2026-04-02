import json
from pathlib import Path

from src.app.schemas.invoice import InvoiceLineItem, InvoiceSchema


class TestInvoiceLineItem:
    def test_all_fields_required(self) -> None:
        item = InvoiceLineItem(
            line_number=1,
            description="Monitor Dell P2720DC",
            unit="szt.",
            quantity=1.0,
            unit_price=120.0,
            net_amount=120.0,
            vat_rate=23.0,
        )
        data = item.model_dump()
        assert data["line_number"] == 1
        assert data["description"] == "Monitor Dell P2720DC"
        assert data["unit"] == "szt."
        assert data["vat_rate"] == 23.0

    def test_missing_values_use_defaults(self) -> None:
        """When LLM can't find a value, it returns empty string / 0."""
        item = InvoiceLineItem(
            line_number=1,
            description="Service",
            unit="",
            quantity=0,
            unit_price=0,
            net_amount=0,
            vat_rate=0,
        )
        data = item.model_dump()
        assert data["unit"] == ""
        assert data["quantity"] == 0
        assert data["vat_rate"] == 0


class TestInvoiceSchema:
    def test_flat_structure(self) -> None:
        """All address and bank fields are flat, no nesting."""
        invoice = InvoiceSchema(
            ksef_number="",
            invoice_number="FV/2025/01/001",
            issue_date="2025-01-15",
            sales_date="2025-01-15",
            due_date="2025-02-14",
            seller_nip="5261040828",
            seller_name="AppUnite S.A.",
            seller_address_street="ul. Grunwaldzka 12",
            seller_address_city="Poznan",
            seller_address_postal_code="60-311",
            seller_address_country="PL",
            buyer_nip="7811903576",
            buyer_name="Klient Testowy Sp. z o.o.",
            buyer_address_street="ul. Marszalkowska 1/5",
            buyer_address_city="Warszawa",
            buyer_address_postal_code="00-001",
            buyer_address_country="PL",
            bank_iban="PL61109010140000071219812874",
            bank_swift_bic="WBKPPLPP",
            bank_name="Santander Bank Polska S.A.",
            bank_routing_number="",
            bank_account_number="",
            bank_address="",
            bank_notes="",
            net_amount=30000.0,
            vat_amount=6900.0,
            gross_amount=36900.0,
            currency="PLN",
            line_items=[
                InvoiceLineItem(
                    line_number=1,
                    description="Uslugi doradcze IT",
                    unit="godz.",
                    quantity=120.0,
                    unit_price=250.0,
                    net_amount=30000.0,
                    vat_rate=23,
                )
            ],
        )
        data = invoice.model_dump()
        assert data["seller_address_street"] == "ul. Grunwaldzka 12"
        assert data["bank_iban"] == "PL61109010140000071219812874"
        assert data["bank_routing_number"] == ""

    def test_missing_values_use_empty_defaults(self) -> None:
        """Fields not found on invoice get empty string / 0."""
        invoice = InvoiceSchema(
            ksef_number="",
            invoice_number="INV-001",
            issue_date="2025-01-15",
            sales_date="",
            due_date="",
            seller_nip="5261040828",
            seller_name="Acme Corp",
            seller_address_street="",
            seller_address_city="",
            seller_address_postal_code="",
            seller_address_country="",
            buyer_nip="",
            buyer_name="",
            buyer_address_street="",
            buyer_address_city="",
            buyer_address_postal_code="",
            buyer_address_country="",
            bank_iban="",
            bank_swift_bic="",
            bank_name="",
            bank_routing_number="",
            bank_account_number="",
            bank_address="",
            bank_notes="",
            net_amount=0,
            vat_amount=0,
            gross_amount=0,
            currency="PLN",
            line_items=[],
        )
        assert invoice.buyer_name == ""
        assert invoice.net_amount == 0

    def test_from_dict(self) -> None:
        """Simulates what the LLM returns — raw dict."""
        invoice = InvoiceSchema.model_validate(
            {
                "ksef_number": "",
                "invoice_number": "INV-001",
                "issue_date": "2025-01-15",
                "sales_date": "",
                "due_date": "",
                "seller_nip": "5261040828",
                "seller_name": "Acme Corp",
                "seller_address_street": "123 Main St",
                "seller_address_city": "New York",
                "seller_address_postal_code": "10001",
                "seller_address_country": "US",
                "buyer_nip": "",
                "buyer_name": "Client Inc.",
                "buyer_address_street": "",
                "buyer_address_city": "",
                "buyer_address_postal_code": "",
                "buyer_address_country": "",
                "bank_iban": "",
                "bank_swift_bic": "CITIUS33",
                "bank_name": "Citibank N.A.",
                "bank_routing_number": "021000089",
                "bank_account_number": "12345678",
                "bank_address": "388 Greenwich St, New York",
                "bank_notes": "Reference: INV-2025-042",
                "net_amount": 1000.0,
                "vat_amount": 0,
                "gross_amount": 1000.0,
                "currency": "USD",
                "line_items": [
                    {
                        "line_number": 1,
                        "description": "Consulting",
                        "unit": "hrs",
                        "quantity": 10,
                        "unit_price": 100,
                        "net_amount": 1000,
                        "vat_rate": 0,
                    }
                ],
            }
        )
        assert invoice.seller_address_city == "New York"
        assert invoice.bank_routing_number == "021000089"

    def test_no_optional_fields_in_schema(self) -> None:
        """All fields must be required — no optionals that bloat structured output."""
        schema = InvoiceSchema.model_json_schema()
        properties = set(schema["properties"].keys())
        required = set(schema["required"])
        assert properties == required, (
            f"Optional fields found: {properties - required}. "
            "All fields must be required for structured output compatibility."
        )

    def test_no_nested_objects_in_top_level(self) -> None:
        """No nested object types at top level — only flat fields and line_items array."""
        schema = InvoiceSchema.model_json_schema()
        assert schema.get("additionalProperties") is False
        for name, prop in schema["properties"].items():
            if name == "line_items":
                assert prop["type"] == "array"
            else:
                assert prop["type"] in ("string", "number", "integer"), (
                    f"Field '{name}' has type '{prop.get('type')}' — "
                    "top-level fields must be flat (string/number/integer)"
                )

    def test_line_item_schema_constraints(self) -> None:
        """InvoiceLineItem must also be all-required with additionalProperties: false."""
        schema = InvoiceLineItem.model_json_schema()
        properties = set(schema["properties"].keys())
        required = set(schema["required"])
        assert properties == required, (
            f"Optional line item fields: {properties - required}"
        )
        assert schema.get("additionalProperties") is False


def test_default_schema_json_matches_pydantic_model() -> None:
    """Ensure default_invoice_schema.json stays in sync with InvoiceSchema.

    If this fails, run: uv run python -m scripts.generate_schema
    """
    from scripts.generate_schema import generate

    schema_path = Path("src/app/schemas/default_invoice_schema.json")
    on_disk = json.loads(schema_path.read_text())
    expected = generate()
    assert on_disk == expected, (
        "default_invoice_schema.json is out of sync with InvoiceSchema. "
        "Run: uv run python -m scripts.generate_schema"
    )
