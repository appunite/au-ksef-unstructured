from src.app.schemas.invoice import Address, BankInfo, InvoiceLineItem, InvoiceSchema


class TestBankInfo:
    def test_all_fields_populated(self) -> None:
        info = BankInfo(
            iban="PL61109010140000071219812874",
            swift_bic="WBKPPLPP",
            bank_name="Santander Bank Polska S.A.",
            bank_address="ul. Grunwaldzka 182, Poznan",
            routing_number=None,
            account_number=None,
            notes=None,
        )
        data = info.model_dump()
        assert data["iban"] == "PL61109010140000071219812874"
        assert data["swift_bic"] == "WBKPPLPP"
        assert data["bank_name"] == "Santander Bank Polska S.A."
        assert data["bank_address"] == "ul. Grunwaldzka 182, Poznan"

    def test_all_none_is_valid(self) -> None:
        info = BankInfo(
            iban=None,
            swift_bic=None,
            bank_name=None,
            bank_address=None,
            routing_number=None,
            account_number=None,
            notes=None,
        )
        assert all(v is None for v in info.model_dump().values())

    def test_us_wire_fields(self) -> None:
        info = BankInfo(
            iban=None,
            swift_bic="CITIUS33",
            bank_name="Citibank N.A.",
            bank_address=None,
            routing_number="021000089",
            account_number="12345678",
            notes="Reference: INV-2025-042",
        )
        data = info.model_dump()
        assert data["routing_number"] == "021000089"
        assert data["account_number"] == "12345678"
        assert data["swift_bic"] == "CITIUS33"
        assert data["notes"] == "Reference: INV-2025-042"

    def test_round_trip_json(self) -> None:
        info = BankInfo(
            iban="DE89370400440532013000",
            swift_bic="COBADEFFXXX",
            bank_name=None,
            bank_address=None,
            routing_number=None,
            account_number=None,
            notes=None,
        )
        rebuilt = BankInfo.model_validate_json(info.model_dump_json())
        assert rebuilt == info


class TestAddress:
    def test_full_address(self) -> None:
        addr = Address(
            street="ul. Grunwaldzka 12/3",
            city="Poznan",
            postal_code="60-311",
            country="PL",
        )
        assert addr.model_dump() == {
            "street": "ul. Grunwaldzka 12/3",
            "city": "Poznan",
            "postal_code": "60-311",
            "country": "PL",
        }

    def test_all_none_is_valid(self) -> None:
        addr = Address(street=None, city=None, postal_code=None, country=None)
        assert all(v is None for v in addr.model_dump().values())


class TestInvoiceSchema:
    def test_bank_details_nested(self) -> None:
        invoice = InvoiceSchema(
            ksef_number=None,
            invoice_number="FV/2025/01/001",
            issue_date="2025-01-15",
            sales_date=None,
            due_date=None,
            seller_nip="5261040828",
            seller_name="AppUnite S.A.",
            seller_address=None,
            buyer_nip=None,
            buyer_name=None,
            buyer_address=None,
            bank_details=BankInfo(
                iban="PL61109010140000071219812874",
                swift_bic="WBKPPLPP",
                bank_name=None,
                bank_address=None,
                routing_number=None,
                account_number=None,
                notes=None,
            ),
            net_amount=100.0,
            vat_amount=23.0,
            gross_amount=123.0,
            currency="PLN",
            line_items=[
                InvoiceLineItem(
                    line_number=1,
                    description="Service",
                    unit=None,
                    quantity=1.0,
                    unit_price=100.0,
                    net_amount=100.0,
                    vat_rate=23.0,
                )
            ],
        )
        data = invoice.model_dump()
        assert data["bank_details"]["iban"] == "PL61109010140000071219812874"
        assert data["bank_details"]["swift_bic"] == "WBKPPLPP"

    def test_bank_details_null_is_valid(self) -> None:
        invoice = InvoiceSchema(
            ksef_number=None,
            invoice_number="FV/2025/01/001",
            issue_date="2025-01-15",
            sales_date=None,
            due_date=None,
            seller_nip="5261040828",
            seller_name="AppUnite S.A.",
            seller_address=None,
            buyer_nip=None,
            buyer_name=None,
            buyer_address=None,
            bank_details=None,
            net_amount=None,
            vat_amount=None,
            gross_amount=None,
            currency="PLN",
            line_items=[],
        )
        assert invoice.bank_details is None

    def test_bank_details_from_dict(self) -> None:
        """Simulates what the LLM returns — raw dict, not BankInfo instance."""
        invoice = InvoiceSchema.model_validate(
            {
                "ksef_number": None,
                "invoice_number": "INV-001",
                "issue_date": "2025-01-15",
                "seller_nip": "5261040828",
                "seller_name": "Acme Corp",
                "bank_details": {
                    "iban": "PL61109010140000071219812874",
                    "routing_number": "021000089",
                },
                "currency": "PLN",
                "line_items": [],
            }
        )
        assert invoice.bank_details is not None
        assert isinstance(invoice.bank_details, BankInfo)
        assert invoice.bank_details.iban == "PL61109010140000071219812874"
        assert invoice.bank_details.routing_number == "021000089"
        assert invoice.bank_details.swift_bic is None
