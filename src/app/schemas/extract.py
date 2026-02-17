from pydantic import BaseModel


class UnstructuredSettings(BaseModel):
    strategy: str = "auto"
    languages: list[str] = ["eng"]
    pdf_infer_table_structure: bool = True
    include_page_breaks: bool = False


class ExtractionResponse(BaseModel):
    success: bool
    data: dict | None = None
    error: str | None = None
