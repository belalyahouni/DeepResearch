"""PDF text extraction service — downloads and parses open access PDFs."""

import tempfile

import fitz  # PyMuPDF
import httpx


async def extract_text_from_pdf(pdf_url: str | None) -> str | None:
    """Download a PDF from *pdf_url* and extract its full text.

    Returns ``None`` if the URL is missing, the download fails,
    or the PDF cannot be parsed — callers should fall back to the abstract.
    """
    if not pdf_url:
        return None

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(pdf_url)
            response.raise_for_status()
            pdf_bytes = response.content
    except (httpx.HTTPStatusError, httpx.RequestError):
        return None

    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp:
            tmp.write(pdf_bytes)
            tmp.flush()

            doc = fitz.open(tmp.name)
            pages: list[str] = []
            for page in doc:
                text = page.get_text()
                if text:
                    pages.append(text)
            doc.close()

            full_text = "\n".join(pages).strip()
            return full_text if full_text else None
    except Exception:
        return None
