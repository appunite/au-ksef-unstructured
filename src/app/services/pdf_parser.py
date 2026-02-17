import tempfile

from unstructured.partition.pdf import partition_pdf

from src.app.schemas.extract import UnstructuredSettings


class PDFParser:
    """Abstraction over unstructured library for PDF text extraction."""

    def parse(self, pdf_content: bytes, settings: UnstructuredSettings) -> str:
        """Extract text from PDF bytes. Returns concatenated text content."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=True) as tmp:
            tmp.write(pdf_content)
            tmp.flush()

            elements = partition_pdf(
                filename=tmp.name,
                strategy=settings.strategy,
                languages=settings.languages,
                pdf_infer_table_structure=settings.pdf_infer_table_structure,
                include_page_breaks=settings.include_page_breaks,
            )

        return "\n\n".join(str(el) for el in elements)
