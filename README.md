# au-ksef-unstructured

Extract structured invoice data from PDF files using `unstructured` for text extraction and Anthropic Claude for structured data extraction.

## Architecture

```
PDF file ──► unstructured (text extraction) ──► Anthropic Claude (structured output) ──► JSON
```

The service accepts:
1. A **PDF file** containing an invoice
2. A **JSON Schema** describing the desired output format (field names, types, descriptions)

It returns structured JSON guaranteed to conform to the provided schema, using Anthropic's Structured Output feature.

## Setup

### Prerequisites

- Python 3.11.7
- [uv](https://docs.astral.sh/uv/) package manager
- System dependencies for PDF processing: `poppler-utils`, `tesseract-ocr`, `libmagic`

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
- `DEFAULT_STRATEGY` — Unstructured parsing strategy (default: `auto`)
- `DEFAULT_LANGUAGES` — OCR languages as JSON array (default: `["eng"]`)
- `DEFAULT_PDF_INFER_TABLE_STRUCTURE` — Infer tables (default: `true`)

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
- `output_schema` — JSON Schema string describing desired output (required)
- `unstructured_settings` — JSON string with unstructured overrides (optional)
- `model` — Anthropic model override (optional)

**Example:**

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
        "type": "number",
        "description": "Total invoice amount including tax"
      },
      "vendor_name": {
        "type": "string",
        "description": "Name of the company that issued the invoice"
      }
    },
    "required": ["invoice_number", "total_amount"]
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

## Docker

```bash
make docker-build
make docker-run
```

## License

Proprietary
