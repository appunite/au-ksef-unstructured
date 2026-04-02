from pydantic import BaseModel, ConfigDict, Field


class InvoiceLineItem(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "additionalProperties": False,
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
                    "vat_rate": 0,
                },
            ],
        }
    )

    line_number: int = Field(
        description="Sequential position of this line in the invoice (1-based)"
    )
    description: str = Field(
        description="Product or service description as printed on the invoice line"
    )
    unit: str = Field(description="Unit of measure (e.g. szt., kg, godz., hrs, pcs, ea)")
    quantity: float = Field(description="Number of units for this line item")
    unit_price: float = Field(description="Unit price before tax")
    net_amount: float = Field(description="Line total before tax (quantity x unit price)")
    vat_rate: float = Field(
        description="Tax/VAT rate as a percentage (e.g. 23, 8, 5, 0). Look for labels like VAT, Tax Rate, Stawka VAT"
    )


class InvoiceSchema(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "additionalProperties": False,
            "examples": [
                {
                    "ksef_number": "1234567890-20250115-AABBCCDD-01",
                    "invoice_number": "FV/2025/01/042",
                    "issue_date": "2025-01-15",
                    "sales_date": "2025-01-15",
                    "due_date": "2025-02-14",
                    "seller_nip": "5261040828",
                    "seller_name": "AppUnite S.A.",
                    "seller_address_street": "ul. Grunwaldzka 12",
                    "seller_address_city": "Poznan",
                    "seller_address_postal_code": "60-311",
                    "seller_address_country": "PL",
                    "buyer_nip": "7811903576",
                    "buyer_name": "Klient Testowy Sp. z o.o.",
                    "buyer_address_street": "ul. Marszalkowska 1/5",
                    "buyer_address_city": "Warszawa",
                    "buyer_address_postal_code": "00-001",
                    "buyer_address_country": "PL",
                    "bank_iban": "PL61109010140000071219812874",
                    "bank_swift_bic": "WBKPPLPP",
                    "bank_name": "Santander Bank Polska S.A.",
                    "bank_routing_number": "",
                    "bank_account_number": "",
                    "bank_address": "",
                    "bank_notes": "",
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
            ],
        }
    )

    ksef_number: str = Field(description="Polish KSeF (Krajowy System e-Faktur) reference number")
    invoice_number: str = Field(
        description="Invoice identifier. Look for labels like Invoice No, Faktura nr, Invoice #, Numer faktury"
    )
    issue_date: str = Field(
        description="Invoice issue date in YYYY-MM-DD format. Look for labels like Date, Issue Date, Data wystawienia"
    )
    sales_date: str = Field(
        description="Date when the sale or service was delivered, in YYYY-MM-DD format. Look for labels like Service Date, Data sprzedazy, Delivery Date"
    )
    due_date: str = Field(
        description="Payment due date in YYYY-MM-DD format. Look for labels like Due Date, Payment Due, Termin platnosci"
    )
    seller_nip: str = Field(
        description="Seller's tax ID. EU VAT number with country prefix (e.g. PL7831812212, DE123456789) or US EIN/TIN. Include the country prefix if present"
    )
    seller_name: str = Field(
        description="Full legal name of the seller/vendor as printed on the invoice"
    )
    seller_address_street: str = Field(
        description="Seller's street name and building/apartment number (e.g. ul. Grunwaldzka 12/3, 123 Main St)"
    )
    seller_address_city: str = Field(description="Seller's city or town name")
    seller_address_postal_code: str = Field(
        description="Seller's postal or ZIP code (e.g. 60-311, 10001)"
    )
    seller_address_country: str = Field(
        description="Seller's country name or ISO 3166-1 alpha-2 code (e.g. PL, US, DE)"
    )
    buyer_nip: str = Field(
        description="Buyer's tax ID. EU VAT number with country prefix (e.g. PL7831812212, DE123456789) or US EIN/TIN"
    )
    buyer_name: str = Field(
        description="Full legal name of the buyer/customer as printed on the invoice"
    )
    buyer_address_street: str = Field(
        description="Buyer's street name and building/apartment number"
    )
    buyer_address_city: str = Field(description="Buyer's city or town name")
    buyer_address_postal_code: str = Field(description="Buyer's postal or ZIP code")
    buyer_address_country: str = Field(
        description="Buyer's country name or ISO 3166-1 alpha-2 code"
    )
    bank_iban: str = Field(description="Seller's IBAN (EU) or full bank account number")
    bank_swift_bic: str = Field(description="Seller's SWIFT/BIC code (e.g. BPKOPLPW, CITIUS33)")
    bank_name: str = Field(
        description="Name of the seller's bank (e.g. PKO Bank Polski, Citibank N.A.)"
    )
    bank_routing_number: str = Field(
        description="ABA routing number for US domestic wires (9 digits)"
    )
    bank_account_number: str = Field(
        description="Bank account number for US wires (when separate from IBAN)"
    )
    bank_address: str = Field(description="Bank branch address as printed on the invoice")
    bank_notes: str = Field(
        description="Explicit payment instructions printed on the invoice, "
        "e.g. 'Reference: INV-2025-042', 'Include invoice number in memo', "
        "'Intermediary bank: ...'"
    )
    net_amount: float = Field(
        description="Invoice total before tax. Look for labels like Net Total, Subtotal, Razem netto"
    )
    vat_amount: float = Field(
        description="Total tax amount. Look for labels like VAT, Tax, Kwota VAT"
    )
    gross_amount: float = Field(
        description="Invoice total including tax. Look for labels like Total, Amount Due, Razem brutto"
    )
    currency: str = Field(
        description="ISO 4217 currency code (e.g. PLN, EUR, USD). Infer from currency symbols ($, zl, EUR) if not explicitly stated"
    )
    line_items: list[InvoiceLineItem] = Field(
        description="Individual line items from the invoice table. Extract only product/service rows, skip subtotals and summaries"
    )
