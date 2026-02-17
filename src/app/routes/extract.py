import json
import logging
from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile

from src.app.config import Settings, get_settings
from src.app.dependencies import verify_token
from src.app.schemas.extract import ErrorDetail, ExtractionResponse, UnstructuredSettings
from src.app.services.llm_extractor import LLMExtractor
from src.app.services.pdf_parser import PDFParser

logger = logging.getLogger(__name__)

router = APIRouter()

_DEFAULT_SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schemas" / "default_invoice_schema.json"


def _load_default_schema() -> dict:
    return json.loads(_DEFAULT_SCHEMA_PATH.read_text())


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
    else:
        schema_dict = _load_default_schema()

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

    try:
        parser = PDFParser()
        text = parser.parse(pdf_content, pdf_settings)

        extractor = LLMExtractor(api_key=settings.anthropic_api_key, model=resolved_model)
        data = extractor.extract(text, schema_dict, model=resolved_model)

        return ExtractionResponse(success=True, data=data)

    except Exception as e:
        logger.exception("Extraction failed")
        return ExtractionResponse(
            success=False,
            error=ErrorDetail(code="internal_error", message=str(e)),
        )
