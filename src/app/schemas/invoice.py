from pydantic import BaseModel, ConfigDict, Field


class InvoiceLineItem(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "line_number": 1,
                    "description": "Uslugi doradcze IT - styczen 2025",
                    "unit": "godz.",
                    "quantity": 120.0,
                    "unit_price": 250.00,
                    "net_amount": 30000.00,
                    "vat_rate": 23,
                }
            ]
        }
    )

    line_number: int = Field(description="Sequential line number (NrWierszaFa)")
    description: str = Field(description="Product or service description (FA(3) field P_7)")
    unit: str | None = Field(description="Unit of measure, e.g. szt., kg, godz. (FA(3) field P_8A)")
    quantity: float | None = Field(description="Quantity of items (FA(3) field P_8B)")
    unit_price: float | None = Field(description="Price per unit net of VAT (FA(3) field P_9A)")
    net_amount: float | None = Field(description="Line net amount (FA(3) field P_11)")
    vat_rate: float | None = Field(
        description="VAT rate as percentage, e.g. 23, 8, 5, 0 (FA(3) field P_12)"
    )


class InvoiceSchema(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "ksef_number": "1234567890-20250115-AABBCCDD-01",
                    "invoice_number": "FV/2025/01/042",
                    "issue_date": "2025-01-15",
                    "sales_date": "2025-01-15",
                    "due_date": "2025-02-14",
                    "seller_nip": "5261040828",
                    "seller_name": "AppUnite S.A.",
                    "buyer_nip": "7811903576",
                    "buyer_name": "Klient Testowy Sp. z o.o.",
                    "iban": "PL61109010140000071219812874",
                    "net_amount": 30000.00,
                    "vat_amount": 6900.00,
                    "gross_amount": 36900.00,
                    "currency": "PLN",
                    "line_items": [
                        {
                            "line_number": 1,
                            "description": "Uslugi doradcze IT - styczen 2025",
                            "unit": "godz.",
                            "quantity": 120.0,
                            "unit_price": 250.00,
                            "net_amount": 30000.00,
                            "vat_rate": 23,
                        }
                    ],
                }
            ]
        }
    )

    ksef_number: str | None = Field(
        description="KSeF reference number assigned by the National e-Invoice System (e.g. 1234567890-20250115-AABBCCDD-01)"
    )
    invoice_number: str = Field(
        description="Sequential invoice identifier (FA(3) field P_2, e.g. FV/2025/01/001)"
    )
    issue_date: str = Field(description="Invoice issue date in YYYY-MM-DD format (FA(3) field P_1)")
    sales_date: str | None = Field(
        description="Date of sale/service delivery in YYYY-MM-DD format (FA(3) field P_6)"
    )
    due_date: str | None = Field(
        description="Payment due date in YYYY-MM-DD format (FA(3) field TerminPlatnosci)"
    )
    seller_nip: str = Field(
        description="Seller's 10-digit Polish tax identification number (NIP, digits only)"
    )
    seller_name: str = Field(description="Full name of the selling company or person")
    buyer_nip: str | None = Field(
        description="Buyer's 10-digit Polish tax identification number (NIP, digits only)"
    )
    buyer_name: str | None = Field(description="Full name of the buying company or person")
    iban: str | None = Field(
        description="Seller's bank account number in IBAN format (FA(3) field NrRachunkuBankowego)"
    )
    net_amount: float | None = Field(
        description="Total net amount excluding VAT (FA(3) field P_13_1)"
    )
    vat_amount: float | None = Field(description="Total VAT amount (FA(3) field P_14_1)")
    gross_amount: float | None = Field(
        description="Total gross amount including VAT (FA(3) field P_15)"
    )
    currency: str = Field(
        description="ISO 4217 currency code (e.g. PLN, EUR, USD). Defaults to PLN if not specified on invoice."
    )
    line_items: list[InvoiceLineItem] = Field(description="Individual invoice line items")
