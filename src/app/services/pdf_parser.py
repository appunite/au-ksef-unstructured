import pymupdf

from src.app.schemas.extract import PdfSettings

# Suppress "Consider using pymupdf_layout" message printed by find_tables().
# This warning is hardcoded in pymupdf.table and bypasses both set_messages()
# and Python logging — monkey-patching the internal callable is the only option.
pymupdf._warn_layout_once = lambda: None  # type: ignore[attr-defined]


class PDFParser:
    """PDF text extraction using PyMuPDF with table-aware formatting."""

    def parse(self, pdf_content: bytes, settings: PdfSettings) -> str:
        """Extract text from PDF bytes. Returns concatenated text content."""
        with pymupdf.open(stream=pdf_content, filetype="pdf") as doc:
            if settings.strategy == "ocr_only":
                return self._ocr_extract(doc, settings.languages)

            text = self._text_extract(doc)

            if settings.strategy == "fast" or text.strip():
                return text

            # strategy == "auto" and text extraction returned nothing — fall back to OCR
            return self._ocr_extract(doc, settings.languages)

    def _text_extract(self, doc: pymupdf.Document) -> str:
        """Extract text with tables formatted as markdown."""
        pages = []
        for i in range(len(doc)):
            pages.append(self._extract_page(doc[i]))
        return "\n".join(pages)

    def _extract_page(self, page: pymupdf.Page) -> str:
        """Extract a single page, replacing table regions with markdown tables."""
        tables = page.find_tables()
        if not tables.tables:
            return str(page.get_text())

        # Collect table bounding boxes and their markdown representations
        table_rects = []
        for tab in tables.tables:
            table_rects.append((tab.bbox, _table_to_markdown(tab.extract())))

        # Get text blocks and replace table regions with markdown
        parts: list[str] = []
        used_tables: set[int] = set()

        for block in page.get_text("dict")["blocks"]:
            if block["type"] != 0:  # skip image blocks
                continue

            block_rect = pymupdf.Rect(block["bbox"])

            # Check if this text block overlaps a table
            table_idx = _find_overlapping_table(block_rect, table_rects)
            if table_idx is not None:
                if table_idx not in used_tables:
                    used_tables.add(table_idx)
                    parts.append(table_rects[table_idx][1])
                continue

            # Regular text block — extract lines
            for line in block["lines"]:
                text = " ".join(span["text"] for span in line["spans"]).strip()
                if text:
                    parts.append(text)

        return "\n".join(parts)

    def _ocr_extract(self, doc: pymupdf.Document, languages: list[str]) -> str:
        """Extract text using PyMuPDF's built-in Tesseract OCR."""
        lang = "+".join(languages)
        pages = []
        for i in range(len(doc)):
            page = doc[i]
            try:
                tp = page.get_textpage_ocr(language=lang, full=True)
            except RuntimeError as e:
                raise ValueError(
                    f"OCR failed for language '{lang}'. "
                    f"Ensure the required tesseract language packs are installed: {e}"
                ) from e
            pages.append(page.get_text(textpage=tp))
        return "\n".join(pages)


def _find_overlapping_table(
    block_rect: pymupdf.Rect, table_rects: list[tuple[tuple, str]]
) -> int | None:
    """Return index of the table whose bbox contains the block, or None."""
    for i, (bbox, _) in enumerate(table_rects):
        table_rect = pymupdf.Rect(bbox)
        if block_rect.intersects(table_rect):
            return i
    return None


def _table_to_markdown(rows: list[list]) -> str:
    """Convert extracted table rows to a markdown table string."""
    if not rows:
        return ""

    def clean(cell: object) -> str:
        return str(cell).replace("\n", " ").replace("|", "\\|").strip() if cell else ""

    header = [clean(c) for c in rows[0]]
    if not any(header):
        return ""
    md = "| " + " | ".join(header) + " |"
    md += "\n| " + " | ".join("---" for _ in header) + " |"

    for row in rows[1:]:
        cells = [clean(c) for c in row]
        # Normalize to exactly the same column count as header
        while len(cells) < len(header):
            cells.append("")
        cells = cells[: len(header)]
        md += "\n| " + " | ".join(cells) + " |"

    return md
