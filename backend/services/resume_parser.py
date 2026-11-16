import io
import logging
from typing import Optional

import pdfplumber

logger = logging.getLogger(__name__)

PDF_MAGIC = b"%PDF-"


def _looks_like_pdf(filename: Optional[str], content_type: Optional[str], content: bytes) -> bool:
    if content.startswith(PDF_MAGIC):
        return True
    if filename and filename.lower().endswith(".pdf"):
        return True
    if content_type and "pdf" in content_type.lower():
        return True
    return False


def _extract_pdf_text(content: bytes) -> str:
    pages = []
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            if text.strip():
                pages.append(text)
    return "\n\n".join(pages).strip()


def parse_resume(content: bytes, filename: Optional[str] = None, content_type: Optional[str] = None) -> str:
    """Extract plain text from a resume upload (PDF or text)."""
    if _looks_like_pdf(filename, content_type, content):
        logger.info("  Resume detected as PDF, extracting with pdfplumber")
        text = _extract_pdf_text(content)
        if not text:
            raise ValueError(
                "Could not extract any text from the PDF. "
                "It may be a scanned image without an OCR layer."
            )
        logger.info(f"  Extracted {len(text)} chars from PDF")
        return text

    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        text = content.decode("latin-1", errors="replace")
    logger.info(f"  Resume decoded as text: {len(text)} chars")
    return text
