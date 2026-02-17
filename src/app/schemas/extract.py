from pydantic import BaseModel


class UnstructuredSettings(BaseModel):
    strategy: str = "auto"
    languages: list[str] = ["eng"]
    pdf_infer_table_structure: bool = True
    include_page_breaks: bool = False


class ErrorDetail(BaseModel):
    code: str
    message: str


class ExtractionResponse(BaseModel):
    success: bool
    data: dict | None = None
    error: ErrorDetail | None = None
