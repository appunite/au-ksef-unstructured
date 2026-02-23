from typing import Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(description="Service health status", examples=["ok"])


class UnstructuredSettings(BaseModel):
    strategy: Literal["auto", "fast", "ocr_only", "hi_res"] = Field(
        default="auto",
        description="PDF partitioning strategy. "
        "'auto' selects heuristically; 'fast' skips OCR; "
        "'ocr_only' forces OCR; 'hi_res' uses layout detection.",
        examples=["auto"],
    )
    languages: list[str] = Field(
        default=["eng"],
        description="Tesseract language codes for OCR",
        examples=[["pol", "eng"]],
    )
    pdf_infer_table_structure: bool = Field(
        default=True,
        description="Whether to detect and extract table structure from the PDF",
    )
    include_page_breaks: bool = Field(
        default=False,
        description="Whether to include page-break markers in parsed output",
    )


class ErrorDetail(BaseModel):
    code: str = Field(
        description="Machine-readable error code",
        examples=["validation_error"],
    )
    message: str = Field(
        description="Human-readable error description",
        examples=["File must be a PDF"],
    )


class ExtractionResponse(BaseModel):
    success: bool = Field(description="Whether the extraction completed successfully")
    data: dict | None = Field(
        default=None, description="Extracted invoice data (present when success=true)"
    )
    error: ErrorDetail | None = Field(
        default=None, description="Error details (present when success=false)"
    )
