from unittest.mock import patch

from src.app.schemas.extract import UnstructuredSettings
from src.app.services.pdf_parser import PDFParser


@patch("src.app.services.pdf_parser.extract_text")
def test_parse_concatenates_text(mock_extract):
    mock_extract.return_value = "Invoice #001\nTotal: $100.00"

    parser = PDFParser()
    result = parser.parse(b"%PDF-1.4 test content", UnstructuredSettings())

    assert result == "Invoice #001\nTotal: $100.00"
    mock_extract.assert_called_once()


@patch("src.app.services.pdf_parser.extract_text")
def test_parse_fast_strategy_uses_pdfminer(mock_extract):
    mock_extract.return_value = "some text"

    settings = UnstructuredSettings(strategy="fast", languages=["pol"])

    parser = PDFParser()
    parser.parse(b"%PDF-1.4 test", settings)

    mock_extract.assert_called_once()


@patch("src.app.services.pdf_parser.extract_text")
def test_parse_empty_pdf_returns_empty_string(mock_extract):
    mock_extract.return_value = ""

    parser = PDFParser()
    result = parser.parse(b"%PDF-1.4", UnstructuredSettings())

    assert result == ""


@patch("src.app.services.pdf_parser.convert_from_bytes")
def test_parse_ocr_strategy_uses_tesseract(mock_convert):
    import pytesseract

    mock_image = type("MockImage", (), {})()
    mock_convert.return_value = [mock_image]

    settings = UnstructuredSettings(strategy="ocr_only", languages=["eng", "pol"])

    with (
        patch.object(
            pytesseract, "get_languages", return_value=["eng", "osd", "pol"]
        ),
        patch.object(pytesseract, "image_to_string", return_value="OCR text") as mock_ocr,
    ):
        parser = PDFParser()
        result = parser.parse(b"%PDF-1.4 test", settings)

    mock_convert.assert_called_once()
    mock_ocr.assert_called_once_with(mock_image, lang="eng+pol")
    assert result == "OCR text"


@patch("src.app.services.pdf_parser.extract_text")
@patch("src.app.services.pdf_parser.convert_from_bytes")
def test_parse_auto_falls_back_to_ocr_when_no_text(mock_convert, mock_extract):
    import pytesseract

    mock_extract.return_value = "   \n  "
    mock_image = type("MockImage", (), {})()
    mock_convert.return_value = [mock_image]

    settings = UnstructuredSettings(strategy="auto", languages=["eng"])

    with (
        patch.object(pytesseract, "get_languages", return_value=["eng", "osd"]),
        patch.object(pytesseract, "image_to_string", return_value="OCR fallback"),
    ):
        parser = PDFParser()
        result = parser.parse(b"%PDF-1.4 test", settings)

    mock_extract.assert_called_once()
    mock_convert.assert_called_once()
    assert result == "OCR fallback"


@patch("src.app.services.pdf_parser.convert_from_bytes")
def test_parse_ocr_rejects_unavailable_languages(mock_convert):
    import pytesseract

    settings = UnstructuredSettings(strategy="ocr_only", languages=["jpn"])

    with patch.object(pytesseract, "get_languages", return_value=["eng", "osd"]):
        parser = PDFParser()
        try:
            parser.parse(b"%PDF-1.4 test", settings)
            assert False, "Expected ValueError"
        except ValueError as exc:
            assert "jpn" in str(exc)
            assert "installed" in str(exc)
