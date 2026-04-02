from pydantic import BaseModel, ConfigDict, Field


class BankInfo(BaseModel):
    iban: str | None = Field(default=None, description="IBAN (EU) or full account number")
    swift_bic: str | None = Field(
        default=None, description="SWIFT/BIC code (e.g. BPKOPLPW, CITIUS33)"
    )
    bank_name: str | None = Field(
        default=None, description="Name of the bank (e.g. PKO Bank Polski, Citibank N.A.)"
    )
    bank_address: str | None = Field(
        default=None, description="Bank branch address as printed on the invoice"
    )
    routing_number: str | None = Field(
        default=None, description="ABA routing number for US domestic wires (9 digits)"
    )
    account_number: str | None = Field(
        default=None, description="Bank account number for US wires (when separate from IBAN)"
    )
    notes: str | None = Field(
        default=None,
        description="Explicit payment instructions printed on the invoice, "
        "e.g. 'Reference: INV-2025-042', 'Include invoice number in memo', "
        "'Intermediary bank: ...'. Null if no such instructions are present",
    )


class Address(BaseModel):
    street: str | None = Field(
        default=None,
        description="Street name and building/apartment number (e.g. ul. Grunwaldzka 12/3, 123 Main St)",
    )
    city: str | None = Field(default=None, description="City or town name")
    postal_code: str | None = Field(
        default=None, description="Postal or ZIP code (e.g. 60-311, 10001, SW1A 1AA)"
    )
    country: str | None = Field(
        default=None, description="Country name or ISO 3166-1 alpha-2 code (e.g. PL, US, DE)"
    )


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
                },
                {
                    "line_number": 1,
                    "description": "Software Development Services - January 2025",
                    "unit": "hrs",
                    "quantity": 80.0,
                    "unit_price": 150.00,
                    "net_amount": 12000.00,
                    "vat_rate": None,
                },
            ]
        }
    )

    line_number: int = Field(
        description="Sequential position of this line in the invoice (1-based)"
    )
    description: str = Field(
        description="Product or service description as printed on the invoice line"
    )
    unit: str | None = Field(
        default=None, description="Unit of measure (e.g. szt., kg, godz., hrs, pcs, ea)"
    )
    quantity: float | None = Field(default=None, description="Number of units for this line item")
    unit_price: float | None = Field(default=None, description="Unit price before tax")
    net_amount: float | None = Field(
        default=None, description="Line total before tax (quantity x unit price)"
    )
    vat_rate: float | None = Field(
        default=None,
        description="Tax/VAT rate as a percentage (e.g. 23, 8, 5, 0). Look for labels like VAT, Tax Rate, Stawka VAT",
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
                    "seller_address": {
                        "street": "ul. Grunwaldzka 12",
                        "city": "Poznan",
                        "postal_code": "60-311",
                        "country": "PL",
                    },
                    "buyer_nip": "7811903576",
                    "buyer_name": "Klient Testowy Sp. z o.o.",
                    "buyer_address": {
                        "street": "ul. Marszalkowska 1/5",
                        "city": "Warszawa",
                        "postal_code": "00-001",
                        "country": "PL",
                    },
                    "bank_details": {
                        "iban": "PL61109010140000071219812874",
                        "swift_bic": "WBKPPLPP",
                        "bank_name": "Santander Bank Polska S.A.",
                    },
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
        default=None,
        description="Polish KSeF (Krajowy System e-Faktur) reference number, if present. Null for non-Polish invoices",
    )
    invoice_number: str = Field(
        description="Invoice identifier. Look for labels like Invoice No, Faktura nr, Invoice #, Numer faktury"
    )
    issue_date: str = Field(
        description="Invoice issue date in YYYY-MM-DD format. Look for labels like Date, Issue Date, Data wystawienia"
    )
    sales_date: str | None = Field(
        default=None,
        description="Date when the sale or service was delivered, in YYYY-MM-DD format. Look for labels like Service Date, Data sprzedazy, Delivery Date",
    )
    due_date: str | None = Field(
        default=None,
        description="Payment due date in YYYY-MM-DD format. Look for labels like Due Date, Payment Due, Termin platnosci",
    )
    seller_nip: str = Field(
        description="Seller's tax ID. EU VAT number with country prefix (e.g. PL7831812212, DE123456789) or US EIN/TIN. Include the country prefix if present"
    )
    seller_name: str = Field(
        description="Full legal name of the seller/vendor as printed on the invoice"
    )
    seller_address: Address | None = Field(
        default=None,
        description="Seller's address. Look for labels like Address, Adres, Siedziba",
    )
    buyer_nip: str | None = Field(
        default=None,
        description="Buyer's tax ID. EU VAT number with country prefix (e.g. PL7831812212, DE123456789) or US EIN/TIN. Include the country prefix if present",
    )
    buyer_name: str | None = Field(
        default=None,
        description="Full legal name of the buyer/customer as printed on the invoice",
    )
    buyer_address: Address | None = Field(
        default=None,
        description="Buyer's address. Look for labels like Address, Adres, Bill To, Nabywca",
    )
    bank_details: BankInfo | None = Field(
        default=None,
        description="Seller's bank and payment details: IBAN, SWIFT/BIC, bank name, routing/account numbers, and any wire transfer instructions",
    )
    net_amount: float | None = Field(
        default=None,
        description="Invoice total before tax. Look for labels like Net Total, Subtotal, Razem netto, Amount Due before tax",
    )
    vat_amount: float | None = Field(
        default=None,
        description="Total tax amount. Look for labels like VAT, Tax, Kwota VAT, Sales Tax",
    )
    gross_amount: float | None = Field(
        default=None,
        description="Invoice total including tax. Look for labels like Total, Amount Due, Razem brutto, Balance Due",
    )
    currency: str = Field(
        description="ISO 4217 currency code (e.g. PLN, EUR, USD). Infer from currency symbols ($, zl, EUR) if not explicitly stated"
    )
    line_items: list[InvoiceLineItem] = Field(
        description="Individual line items from the invoice table. Extract only product/service rows, skip subtotals and summaries"
    )
