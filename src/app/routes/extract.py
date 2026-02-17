import json
import logging
import time

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile

from src.app.config import Settings, get_settings
from src.app.dependencies import verify_token
from src.app.schemas.extract import ErrorDetail, ExtractionResponse, UnstructuredSettings
from src.app.schemas.invoice import InvoiceSchema
from src.app.services.llm_extractor import LLMExtractor
from src.app.services.pdf_parser import PDFParser

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/extract", response_model=ExtractionResponse)
async def extract_invoice(
    file: UploadFile,
    output_schema: str | None = Form(None),
    unstructured_settings: str | None = Form(None),
    model: str | None = Form(None),
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

    if unstructured_settings:
        try:
            overrides = json.loads(unstructured_settings)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"Invalid unstructured_settings JSON: {e}")
        pdf_settings = UnstructuredSettings(
            strategy=overrides.get("strategy", settings.default_strategy),
            languages=overrides.get("languages", settings.default_languages),
            pdf_infer_table_structure=overrides.get(
                "pdf_infer_table_structure",
                settings.default_pdf_infer_table_structure,
            ),
            include_page_breaks=overrides.get("include_page_breaks", False),
        )
    else:
        pdf_settings = UnstructuredSettings(
            strategy=settings.default_strategy,
            languages=settings.default_languages,
            pdf_infer_table_structure=settings.default_pdf_infer_table_structure,
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
            data = extractor.extract_with_schema(text, schema_dict, model=resolved_model)
        else:
            data = extractor.extract_with_model(text, InvoiceSchema, model=resolved_model)
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
