"""Tests for the PDF text extraction service."""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.services.pdf_parser import extract_text_from_pdf


@pytest.fixture
def _sample_pdf_bytes() -> bytes:
    """Create a minimal valid PDF in memory using PyMuPDF."""
    import fitz

    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Hello from the PDF parser test.")
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


@pytest.mark.asyncio
async def test_extract_text_none_url():
    """None URL returns None without making any requests."""
    result = await extract_text_from_pdf(None)
    assert result is None


@pytest.mark.asyncio
async def test_extract_text_empty_url():
    """Empty string URL returns None."""
    result = await extract_text_from_pdf("")
    assert result is None


@pytest.mark.asyncio
async def test_extract_text_download_failure():
    """HTTP error during download returns None."""
    with patch("app.services.pdf_parser.httpx.AsyncClient") as mock_cls:
        mock_instance = MagicMock()

        async def mock_aenter(_self):
            return mock_instance

        async def mock_aexit(_self, *args):
            pass

        mock_cls.return_value.__aenter__ = mock_aenter
        mock_cls.return_value.__aexit__ = mock_aexit

        mock_instance.get = MagicMock(
            side_effect=httpx.RequestError("Connection failed")
        )

        result = await extract_text_from_pdf("https://example.com/paper.pdf")
        assert result is None


@pytest.mark.asyncio
async def test_extract_text_corrupt_pdf():
    """Corrupt/unparseable PDF returns None."""
    with patch("app.services.pdf_parser.httpx.AsyncClient") as mock_cls:
        mock_response = MagicMock()
        mock_response.content = b"this is not a PDF"
        mock_response.raise_for_status = MagicMock()

        mock_instance = MagicMock()

        async def mock_aenter(_self):
            return mock_instance

        async def mock_aexit(_self, *args):
            pass

        mock_cls.return_value.__aenter__ = mock_aenter
        mock_cls.return_value.__aexit__ = mock_aexit

        async def mock_get(url):
            return mock_response

        mock_instance.get = mock_get

        result = await extract_text_from_pdf("https://example.com/paper.pdf")
        assert result is None


@pytest.mark.asyncio
async def test_extract_text_successful_parse(_sample_pdf_bytes: bytes):
    """Valid PDF download + parse returns extracted text."""
    with patch("app.services.pdf_parser.httpx.AsyncClient") as mock_cls:
        mock_response = MagicMock()
        mock_response.content = _sample_pdf_bytes
        mock_response.raise_for_status = MagicMock()

        mock_instance = MagicMock()

        async def mock_aenter(_self):
            return mock_instance

        async def mock_aexit(_self, *args):
            pass

        mock_cls.return_value.__aenter__ = mock_aenter
        mock_cls.return_value.__aexit__ = mock_aexit

        async def mock_get(url):
            return mock_response

        mock_instance.get = mock_get

        result = await extract_text_from_pdf("https://example.com/paper.pdf")
        assert result is not None
        assert "Hello from the PDF parser test" in result
