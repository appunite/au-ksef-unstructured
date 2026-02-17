from unittest.mock import MagicMock, patch

from src.app.schemas.extract import UnstructuredSettings
from src.app.services.pdf_parser import PDFParser


@patch("src.app.services.pdf_parser.partition_pdf")
def test_parse_concatenates_elements(mock_partition):
    el1 = MagicMock()
    el1.__str__ = lambda _: "Invoice #001"
    el2 = MagicMock()
    el2.__str__ = lambda _: "Total: $100.00"
    mock_partition.return_value = [el1, el2]

    parser = PDFParser()
    result = parser.parse(b"%PDF-1.4 test content", UnstructuredSettings())

    assert result == "Invoice #001\n\nTotal: $100.00"


@patch("src.app.services.pdf_parser.partition_pdf")
def test_parse_passes_settings(mock_partition):
    mock_partition.return_value = []

    settings = UnstructuredSettings(
        strategy="hi_res",
        languages=["pol"],
        pdf_infer_table_structure=False,
        include_page_breaks=True,
    )

    parser = PDFParser()
    parser.parse(b"%PDF-1.4 test", settings)

    call_kwargs = mock_partition.call_args.kwargs
    assert call_kwargs["strategy"] == "hi_res"
    assert call_kwargs["languages"] == ["pol"]
    assert call_kwargs["pdf_infer_table_structure"] is False
    assert call_kwargs["include_page_breaks"] is True


@patch("src.app.services.pdf_parser.partition_pdf")
def test_parse_empty_pdf_returns_empty_string(mock_partition):
    mock_partition.return_value = []

    parser = PDFParser()
    result = parser.parse(b"%PDF-1.4", UnstructuredSettings())

    assert result == ""
