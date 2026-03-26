from typing import Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(description="Service health status", examples=["ok"])


class UnstructuredSettings(BaseModel):
    strategy: Literal["auto", "fast", "ocr_only"] = Field(
        default="fast",
        description="PDF text extraction strategy. "
        "'fast' uses pdfminer for direct text extraction (fastest); "
        "'ocr_only' forces OCR via tesseract; "
        "'auto' tries pdfminer first, falls back to OCR if no text found.",
        examples=["fast"],
    )
    languages: list[str] = Field(
        default=["eng"],
        description="Tesseract language codes for OCR",
        examples=[["pol", "eng"]],
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
