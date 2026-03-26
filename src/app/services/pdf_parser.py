import io

from pdf2image import convert_from_bytes
from pdfminer.high_level import extract_text

from src.app.schemas.extract import UnstructuredSettings


class PDFParser:
    """PDF text extraction using pdfminer (text) and pdf2image + tesseract (OCR)."""

    def parse(self, pdf_content: bytes, settings: UnstructuredSettings) -> str:
        """Extract text from PDF bytes. Returns concatenated text content."""
        if settings.strategy == "ocr_only":
            return self._ocr_extract(pdf_content, settings.languages)

        text = self._text_extract(pdf_content)

        if settings.strategy == "fast" or text.strip():
            return text

        # strategy == "auto" and pdfminer returned no text — fall back to OCR
        return self._ocr_extract(pdf_content, settings.languages)

    def _text_extract(self, pdf_content: bytes) -> str:
        """Extract text using pdfminer (fast, no OCR)."""
        return extract_text(io.BytesIO(pdf_content))

    def _ocr_extract(self, pdf_content: bytes, languages: list[str]) -> str:
        """Extract text using pdf2image + tesseract OCR."""
        import pytesseract

        available = set(pytesseract.get_languages())
        valid = [lang for lang in languages if lang in available]
        if not valid:
            raise ValueError(
                f"None of the requested languages {languages} are installed. "
                f"Available: {sorted(available)}"
            )

        images = convert_from_bytes(pdf_content)
        lang = "+".join(valid)
        pages = []
        for image in images:
            pages.append(pytesseract.image_to_string(image, lang=lang))
        return "\n\n".join(pages)
