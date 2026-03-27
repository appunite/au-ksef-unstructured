from unittest.mock import MagicMock, patch

import pytest

from src.app.schemas.extract import PdfSettings
from src.app.services.pdf_parser import PDFParser


def _mock_page(text: str, has_tables: bool = False) -> MagicMock:
    """Create a mock pymupdf Page."""
    page = MagicMock()

    # find_tables() returns no tables by default
    tables_result = MagicMock()
    tables_result.tables = []
    page.find_tables.return_value = tables_result

    # get_text() returns plain text (used when no tables found)
    page.get_text.return_value = text

    return page


def _mock_doc(pages: list[MagicMock]) -> MagicMock:
    """Create a mock pymupdf Document."""
    doc = MagicMock()
    doc.__len__ = lambda self: len(pages)
    doc.__getitem__ = lambda self, i: pages[i]
    doc.__enter__ = lambda self: self
    doc.__exit__ = lambda self, *args: None
    return doc


@patch("src.app.services.pdf_parser.pymupdf")
def test_parse_returns_text(mock_pymupdf: MagicMock) -> None:
    page = _mock_page("Invoice #001\nTotal: $100.00")
    mock_pymupdf.open.return_value = _mock_doc([page])

    parser = PDFParser()
    result = parser.parse(b"%PDF-1.4 test", PdfSettings())

    assert result == "Invoice #001\nTotal: $100.00"
    mock_pymupdf.open.assert_called_once_with(stream=b"%PDF-1.4 test", filetype="pdf")


@patch("src.app.services.pdf_parser.pymupdf")
def test_parse_joins_multiple_pages(mock_pymupdf: MagicMock) -> None:
    mock_pymupdf.open.return_value = _mock_doc([
        _mock_page("Page 1"),
        _mock_page("Page 2"),
    ])

    parser = PDFParser()
    result = parser.parse(b"%PDF-1.4 test", PdfSettings())

    assert result == "Page 1\nPage 2"


@patch("src.app.services.pdf_parser.pymupdf")
def test_parse_empty_pdf_returns_empty_string(mock_pymupdf: MagicMock) -> None:
    mock_pymupdf.open.return_value = _mock_doc([_mock_page("")])

    parser = PDFParser()
    result = parser.parse(b"%PDF-1.4", PdfSettings())

    assert result == ""


@patch("src.app.services.pdf_parser.pymupdf")
def test_parse_formats_tables_as_markdown(mock_pymupdf: MagicMock) -> None:
    page = MagicMock()

    # Set up table detection
    tab = MagicMock()
    tab.bbox = (0, 100, 500, 200)
    tab.extract.return_value = [
        ["Item", "Qty", "Price"],
        ["Widget", "2", "10.00"],
    ]
    tables_result = MagicMock()
    tables_result.tables = [tab]
    page.find_tables.return_value = tables_result

    # Text blocks: one outside table, one inside table
    page.get_text.return_value = {
        "blocks": [
            {
                "type": 0,
                "bbox": (0, 10, 500, 30),
                "lines": [{"spans": [{"text": "Invoice #001"}]}],
            },
            {
                "type": 0,
                "bbox": (0, 110, 500, 150),  # overlaps table
                "lines": [{"spans": [{"text": "Widget"}]}],
            },
        ]
    }

    mock_pymupdf.Rect = pymupdf_rect_stub
    mock_pymupdf.open.return_value = _mock_doc([page])

    parser = PDFParser()
    result = parser.parse(b"%PDF-1.4 test", PdfSettings())

    assert "Invoice #001" in result
    assert "| Item | Qty | Price |" in result
    assert "| Widget | 2 | 10.00 |" in result


@patch("src.app.services.pdf_parser.pymupdf")
def test_parse_ocr_strategy_uses_textpage_ocr(mock_pymupdf: MagicMock) -> None:
    page = MagicMock()
    tp = MagicMock()
    page.get_textpage_ocr.return_value = tp
    page.get_text.return_value = "OCR text"

    mock_pymupdf.open.return_value = _mock_doc([page])

    settings = PdfSettings(strategy="ocr_only", languages=["eng", "pol"])

    parser = PDFParser()
    result = parser.parse(b"%PDF-1.4 test", settings)

    page.get_textpage_ocr.assert_called_once_with(language="eng+pol", full=True)
    page.get_text.assert_called_once_with(textpage=tp)
    assert result == "OCR text"


@patch("src.app.services.pdf_parser.pymupdf")
def test_parse_auto_falls_back_to_ocr_when_no_text(mock_pymupdf: MagicMock) -> None:
    # Text extraction page returns whitespace
    text_page = _mock_page("   \n  ")

    # OCR page
    ocr_page = MagicMock()
    tp = MagicMock()
    ocr_page.get_textpage_ocr.return_value = tp
    ocr_page.get_text.return_value = "OCR fallback"

    doc = MagicMock()
    doc.__enter__ = lambda self: self
    doc.__exit__ = lambda self, *args: None

    # First access for text extract uses text_page, OCR uses ocr_page
    doc.__len__ = lambda self: 1
    call_count = {"n": 0}

    def getitem(self, i):
        call_count["n"] += 1
        if call_count["n"] <= 1:
            return text_page
        return ocr_page

    doc.__getitem__ = getitem
    mock_pymupdf.open.return_value = doc

    settings = PdfSettings(strategy="auto", languages=["eng"])

    parser = PDFParser()
    result = parser.parse(b"%PDF-1.4 test", settings)

    assert result == "OCR fallback"


@patch("src.app.services.pdf_parser.pymupdf")
def test_parse_auto_skips_ocr_when_text_found(mock_pymupdf: MagicMock) -> None:
    mock_pymupdf.open.return_value = _mock_doc([_mock_page("Some text content")])

    settings = PdfSettings(strategy="auto", languages=["eng"])

    parser = PDFParser()
    result = parser.parse(b"%PDF-1.4 test", settings)

    assert result == "Some text content"


@patch("src.app.services.pdf_parser.pymupdf")
def test_parse_ocr_raises_on_missing_language(mock_pymupdf: MagicMock) -> None:
    page = MagicMock()
    page.get_textpage_ocr.side_effect = RuntimeError("Failed to load language 'jpn'")

    mock_pymupdf.open.return_value = _mock_doc([page])

    settings = PdfSettings(strategy="ocr_only", languages=["jpn"])

    parser = PDFParser()
    with pytest.raises(ValueError, match="OCR failed"):
        parser.parse(b"%PDF-1.4 test", settings)


class pymupdf_rect_stub:
    """Stub for pymupdf.Rect that supports intersects()."""

    def __init__(self, bbox):
        self.x0, self.y0, self.x1, self.y1 = bbox

    def intersects(self, other):
        return not (
            self.x1 <= other.x0
            or other.x1 <= self.x0
            or self.y1 <= other.y0
            or other.y1 <= self.y0
        )
