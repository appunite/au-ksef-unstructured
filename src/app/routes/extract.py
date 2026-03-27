import json
import logging
import time

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from src.app.config import Settings, get_settings
from src.app.dependencies import verify_token
from src.app.schemas.extract import ErrorDetail, ExtractionResponse, PdfSettings
from src.app.schemas.invoice import InvoiceSchema
from src.app.services.llm_extractor import LLMExtractor
from src.app.services.pdf_parser import PDFParser

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Extraction"])

_ERROR_RESPONSES: dict[int | str, dict] = {
    400: {
        "description": "Invalid request (bad PDF, empty file, invalid JSON)",
        "model": ExtractionResponse,
    },
    401: {
        "description": "Missing or invalid bearer token",
        "model": ExtractionResponse,
    },
    403: {
        "description": "Token valid but not authorized",
        "model": ExtractionResponse,
    },
    422: {
        "description": "Request validation error (missing required fields)",
        "model": ExtractionResponse,
    },
    500: {
        "description": "Internal server error during extraction",
        "model": ExtractionResponse,
    },
}


@router.post(
    "/extract",
    summary="Extract structured data from a PDF invoice",
    description="Upload a PDF invoice and receive structured JSON data. "
    "The PDF is parsed with PyMuPDF, then sent to Anthropic Claude "
    "for structured extraction. Optionally provide a custom JSON Schema "
    "or override PDF parsing settings.",
    response_model=ExtractionResponse,
    responses=_ERROR_RESPONSES,
)
async def extract_invoice(
    file: UploadFile = File(description="PDF invoice file to extract data from"),
    output_schema: str | None = Form(
        None,
        description="Optional custom JSON Schema for extraction output. "
        "Must be a JSON object with a 'properties' key.",
    ),
    pdf_settings_json: str | None = Form(
        None,
        description="Optional JSON object to override PDF parsing settings "
        '(strategy: "fast"|"ocr_only"|"auto", languages: list of Tesseract codes).',
    ),
    model: str | None = Form(
        None,
        description="Anthropic model ID to use (e.g. claude-sonnet-4-5-20250929). "
        "Defaults to the server-configured model.",
    ),
    context: str | None = Form(
        None,
        description="Optional free-text context to improve extraction accuracy. "
        "Examples: 'This is a Polish VAT invoice (Faktura VAT)', "
        "'Seller is AppUnite S.A., NIP 5261040828', "
        "'Expected currency: USD'. "
        "Injected into the LLM prompt alongside the OCR text.",
    ),
    _token: str = Depends(verify_token),
    settings: Settings = Depends(get_settings),
) -> ExtractionResponse:
    if file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(status_code=400, detail="File must be a PDF")

    pdf_content = await file.read()

    if len(pdf_content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(pdf_content) > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds maximum size of {settings.max_upload_size_mb} MB",
        )

    schema_dict = None
    if output_schema is not None:
        try:
            schema_dict = json.loads(output_schema)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"Invalid output_schema JSON: {e}")
        if not isinstance(schema_dict, dict) or "properties" not in schema_dict:
            raise HTTPException(
                status_code=400,
                detail="output_schema must be a JSON Schema object with a 'properties' key",
            )

    if pdf_settings_json:
        try:
            overrides = json.loads(pdf_settings_json)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"Invalid pdf_settings JSON: {e}")
        pdf_settings = PdfSettings(
            strategy=overrides.get("strategy", settings.default_strategy),
            languages=overrides.get("languages", settings.default_languages),
        )
    else:
        pdf_settings = PdfSettings(
            strategy=settings.default_strategy,
            languages=settings.default_languages,
        )

    resolved_model = model or settings.anthropic_model
    schema_source = "custom" if output_schema is not None else "default"

    logger.info(
        "Starting extraction: file=%s size=%d bytes strategy=%s model=%s schema=%s",
        file.filename,
        len(pdf_content),
        pdf_settings.strategy,
        resolved_model,
        schema_source,
    )

    try:
        t0 = time.monotonic()
        parser = PDFParser()
        text = parser.parse(pdf_content, pdf_settings)
        t1 = time.monotonic()
        logger.info("PDF parsed: %d chars in %.1fs", len(text), t1 - t0)
        logger.debug("Extracted text:\n%s", text[:2000])

        extractor = LLMExtractor(
            api_key=settings.anthropic_api_key,
            model=resolved_model,
            timeout=settings.anthropic_timeout,
        )
        if schema_dict is not None:
            data = extractor.extract_with_schema(
                text, schema_dict, model=resolved_model, context=context
            )
        else:
            data = extractor.extract_with_model(
                text, InvoiceSchema, model=resolved_model, context=context
            )
        t2 = time.monotonic()
        logger.info("LLM extraction: %d fields in %.1fs", len(data), t2 - t1)
        logger.info("Total request time: %.1fs", t2 - t0)

        return ExtractionResponse(success=True, data=data)

    except Exception as e:
        logger.exception("Extraction failed after %.1fs: %s", time.monotonic() - t0, e)
        return ExtractionResponse(
            success=False,
            error=ErrorDetail(code="internal_error", message=str(e)),
        )
