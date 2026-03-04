from pydantic import BaseModel, ConfigDict, Field


class Address(BaseModel):
    street: str | None = Field(
        description="Street name and building/apartment number (e.g. ul. Grunwaldzka 12/3, 123 Main St)"
    )
    city: str | None = Field(description="City or town name")
    postal_code: str | None = Field(
        description="Postal or ZIP code (e.g. 60-311, 10001, SW1A 1AA)"
    )
    country: str | None = Field(
        description="Country name or ISO 3166-1 alpha-2 code (e.g. PL, US, DE)"
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

    line_number: int = Field(description="Sequential position of this line in the invoice (1-based)")
    description: str = Field(description="Product or service description as printed on the invoice line")
    unit: str | None = Field(description="Unit of measure (e.g. szt., kg, godz., hrs, pcs, ea)")
    quantity: float | None = Field(description="Number of units for this line item")
    unit_price: float | None = Field(description="Unit price before tax")
    net_amount: float | None = Field(description="Line total before tax (quantity x unit price)")
    vat_rate: float | None = Field(
        description="Tax/VAT rate as a percentage (e.g. 23, 8, 5, 0). Look for labels like VAT, Tax Rate, Stawka VAT"
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
        description="Polish KSeF (Krajowy System e-Faktur) reference number, if present. Null for non-Polish invoices"
    )
    invoice_number: str = Field(
        description="Invoice identifier. Look for labels like Invoice No, Faktura nr, Invoice #, Numer faktury"
    )
    issue_date: str = Field(
        description="Invoice issue date in YYYY-MM-DD format. Look for labels like Date, Issue Date, Data wystawienia"
    )
    sales_date: str | None = Field(
        description="Date when the sale or service was delivered, in YYYY-MM-DD format. Look for labels like Service Date, Data sprzedazy, Delivery Date"
    )
    due_date: str | None = Field(
        description="Payment due date in YYYY-MM-DD format. Look for labels like Due Date, Payment Due, Termin platnosci"
    )
    seller_nip: str = Field(
        description="Seller's tax ID. EU VAT number with country prefix (e.g. PL7831812212, DE123456789) or US EIN/TIN. Include the country prefix if present"
    )
    seller_name: str = Field(
        description="Full legal name of the seller/vendor as printed on the invoice"
    )
    seller_address: Address | None = Field(
        description="Seller's address. Look for labels like Address, Adres, Siedziba"
    )
    buyer_nip: str | None = Field(
        description="Buyer's tax ID. EU VAT number with country prefix (e.g. PL7831812212, DE123456789) or US EIN/TIN. Include the country prefix if present"
    )
    buyer_name: str | None = Field(
        description="Full legal name of the buyer/customer as printed on the invoice"
    )
    buyer_address: Address | None = Field(
        description="Buyer's address. Look for labels like Address, Adres, Bill To, Nabywca"
    )
    iban: str | None = Field(
        description="Seller's bank account number. IBAN format for EU invoices, routing+account for US"
    )
    net_amount: float | None = Field(
        description="Invoice total before tax. Look for labels like Net Total, Subtotal, Razem netto, Amount Due before tax"
    )
    vat_amount: float | None = Field(
        description="Total tax amount. Look for labels like VAT, Tax, Kwota VAT, Sales Tax"
    )
    gross_amount: float | None = Field(
        description="Invoice total including tax. Look for labels like Total, Amount Due, Razem brutto, Balance Due"
    )
    currency: str = Field(
        description="ISO 4217 currency code (e.g. PLN, EUR, USD). Infer from currency symbols ($, zl, EUR) if not explicitly stated"
    )
    line_items: list[InvoiceLineItem] = Field(
        description="Individual line items from the invoice table. Extract only product/service rows, skip subtotals and summaries"
    )
