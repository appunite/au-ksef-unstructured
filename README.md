# au-ksef-unstructured

Extract structured invoice data from PDF files using PyMuPDF for text extraction and Anthropic Claude for structured data extraction.

## Architecture

```
PDF file ──► PyMuPDF (text extraction) ──► Anthropic Claude (structured output) ──► JSON
```

The service accepts a **PDF file** containing an invoice and returns structured JSON using Anthropic's Structured Output feature.

By default it extracts Polish KSeF invoice fields (invoice number, NIP, dates, amounts, bank details, line items, etc.). You can also provide a custom **JSON Schema** to extract any fields you need.

## Setup

### Prerequisites

- Python 3.11.7
- [uv](https://docs.astral.sh/uv/) package manager

### Install

```bash
make install
```

### Configure

```bash
cp .env.example .env
# Edit .env with your API keys
```

Required environment variables:
- `API_TOKEN` — Bearer token for API authentication
- `ANTHROPIC_API_KEY` — Your Anthropic API key

Optional:
- `ANTHROPIC_MODEL` — Default model (default: `claude-sonnet-4-5-20250929`)
- `LOG_LEVEL` — Logging level (default: `INFO`)
- `DEFAULT_STRATEGY` — PDF parsing strategy: `fast`, `ocr_only`, or `auto` (default: `fast`)
- `DEFAULT_LANGUAGES` — OCR languages as JSON array (default: `["eng", "pol"]`)
- `MAX_UPLOAD_SIZE_MB` — Maximum PDF upload size (default: `10`)
- `ANTHROPIC_TIMEOUT` — API request timeout in seconds (default: `120`)

## Usage

### Run locally

```bash
make dev
```

### API

#### `POST /extract`

Extract structured data from a PDF invoice.

**Headers:**
- `Authorization: Bearer <API_TOKEN>`

**Form fields:**
- `file` — PDF file (required)
- `output_schema` — JSON Schema string describing desired output (optional; uses built-in KSeF invoice schema when omitted)
- `pdf_settings_json` — JSON string with PDF parsing overrides: `strategy`, `languages` (optional)
- `model` — Anthropic model override (optional)
- `context` — Free-text context to improve extraction accuracy (optional)

**Default extraction** (Polish KSeF invoice fields):

```bash
curl -X POST http://localhost:8000/extract \
  -H "Authorization: Bearer $API_TOKEN" \
  -F "file=@invoice.pdf"
```

**Custom schema** (all fields must be `required`; use `anyOf` with `null` for nullable fields):

```bash
curl -X POST http://localhost:8000/extract \
  -H "Authorization: Bearer $API_TOKEN" \
  -F "file=@invoice.pdf" \
  -F 'output_schema={
    "type": "object",
    "properties": {
      "invoice_number": {
        "type": "string",
        "description": "Unique invoice identifier (e.g. INV-2025-001)"
      },
      "total_amount": {
        "anyOf": [{"type": "number"}, {"type": "null"}],
        "description": "Total invoice amount including tax"
      },
      "vendor_name": {
        "type": "string",
        "description": "Name of the company that issued the invoice"
      }
    },
    "required": ["invoice_number", "total_amount", "vendor_name"],
    "additionalProperties": false
  }'
```

**Response:**

```json
{
  "success": true,
  "data": {
    "invoice_number": "INV-2025-001",
    "total_amount": 1234.56,
    "vendor_name": "Acme Corp"
  }
}
```

#### `GET /health`

Health check endpoint (no auth required).

```bash
curl http://localhost:8000/health
```

## Development

```bash
make test        # Run tests
make lint        # Run linter
make format      # Format code
make typecheck   # Type checking
```

### Updating the default schema

The file `src/app/schemas/default_invoice_schema.json` is auto-generated from the Pydantic `InvoiceSchema` model. After modifying `src/app/schemas/invoice.py`, regenerate it:

```bash
uv run python -m scripts.generate_schema
```

A test (`test_default_schema_json_matches_pydantic_model`) will fail if the JSON file is out of sync.

## Docker

```bash
make docker       # Build and run
make docker-build # Build only
make docker-run   # Run only
```

## License

Proprietary
