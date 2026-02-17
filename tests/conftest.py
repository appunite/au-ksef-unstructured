import os
from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Set env vars before importing app modules
os.environ.setdefault("API_TOKEN", "test-token")
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-test")

from src.app.config import get_settings
from src.app.main import create_app


@pytest.fixture
def app():
    a = create_app()
    # Clear cached settings so tests get fresh config
    get_settings.cache_clear()
    return a


@pytest.fixture
def client(app) -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_header() -> dict[str, str]:
    return {"Authorization": "Bearer test-token"}


@pytest.fixture
def mock_pdf_parser():
    with patch("src.app.routes.extract.PDFParser") as mock_cls:
        instance = MagicMock()
        instance.parse.return_value = "Invoice #INV-001\nTotal: $100.00\nVendor: Acme Corp"
        mock_cls.return_value = instance
        yield instance


@pytest.fixture
def mock_llm_extractor():
    with patch("src.app.routes.extract.LLMExtractor") as mock_cls:
        instance = MagicMock()
        return_data = {
            "invoice_number": "INV-001",
            "total_amount": 100.00,
        }
        instance.extract_with_model.return_value = return_data
        instance.extract_with_schema.return_value = return_data
        mock_cls.return_value = instance
        yield instance
