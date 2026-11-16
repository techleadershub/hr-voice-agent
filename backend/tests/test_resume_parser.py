import os
import sys

import pytest

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from backend.services.resume_parser import (
    PDF_MAGIC,
    _looks_like_pdf,
    parse_resume,
)


# A minimal valid one-page PDF whose text content is "Jane Doe Python".
# Built by hand so the test has zero external fixtures.
SAMPLE_PDF_BYTES = (
    b"%PDF-1.4\n"
    b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
    b"2 0 obj << /Type /Pages /Count 1 /Kids [3 0 R] >> endobj\n"
    b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
    b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj\n"
    b"4 0 obj << /Length 44 >> stream\n"
    b"BT /F1 12 Tf 72 720 Td (Jane Doe Python) Tj ET\n"
    b"endstream endobj\n"
    b"5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n"
    b"xref\n0 6\n"
    b"0000000000 65535 f \n"
    b"0000000009 00000 n \n"
    b"0000000054 00000 n \n"
    b"0000000101 00000 n \n"
    b"0000000196 00000 n \n"
    b"0000000290 00000 n \n"
    b"trailer << /Size 6 /Root 1 0 R >>\nstartxref\n357\n%%EOF\n"
)


# ---------- _looks_like_pdf ----------

class TestLooksLikePdf:
    def test_detects_by_magic_bytes(self):
        assert _looks_like_pdf(None, None, PDF_MAGIC + b"rest") is True

    def test_detects_by_filename(self):
        assert _looks_like_pdf("resume.PDF", None, b"not pdf") is True

    def test_detects_by_content_type(self):
        assert _looks_like_pdf(None, "Application/PDF", b"not pdf") is True

    def test_plain_text_not_pdf(self):
        assert _looks_like_pdf("r.txt", "text/plain", b"hello") is False

    def test_empty_inputs_not_pdf(self):
        assert _looks_like_pdf(None, None, b"") is False


# ---------- parse_resume: PDF path ----------

class TestParseResumePdf:
    def test_extracts_text_from_real_pdf(self):
        text = parse_resume(SAMPLE_PDF_BYTES, filename="r.pdf", content_type="application/pdf")
        assert "Jane Doe" in text
        assert "Python" in text

    def test_pdf_routed_by_magic_even_with_wrong_filename(self):
        text = parse_resume(SAMPLE_PDF_BYTES, filename="r.txt", content_type="text/plain")
        assert "Jane Doe" in text

    def test_empty_pdf_raises_value_error(self):
        # PDF with no text content layer (page exists but no Tj operators)
        empty_pdf = (
            b"%PDF-1.4\n"
            b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
            b"2 0 obj << /Type /Pages /Count 1 /Kids [3 0 R] >> endobj\n"
            b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Contents 4 0 R >> endobj\n"
            b"4 0 obj << /Length 0 >> stream\nendstream endobj\n"
            b"xref\n0 5\n"
            b"0000000000 65535 f \n"
            b"0000000009 00000 n \n"
            b"0000000054 00000 n \n"
            b"0000000101 00000 n \n"
            b"0000000180 00000 n \n"
            b"trailer << /Size 5 /Root 1 0 R >>\nstartxref\n230\n%%EOF\n"
        )
        with pytest.raises(ValueError, match="Could not extract any text"):
            parse_resume(empty_pdf, filename="empty.pdf", content_type="application/pdf")

    def test_corrupt_pdf_raises(self):
        # Starts with PDF magic but is otherwise garbage — pdfplumber should raise
        # something (we only require: it does not silently return a degenerate string).
        with pytest.raises(Exception):
            parse_resume(b"%PDF-1.4\n<<garbage>>", filename="bad.pdf",
                         content_type="application/pdf")


# ---------- parse_resume: text path ----------

class TestParseResumeText:
    def test_utf8_passthrough(self):
        assert parse_resume(b"hello world", filename="r.txt") == "hello world"

    def test_utf8_with_unicode(self):
        # "Curriculum Vitæ — résumé"
        raw = "Curriculum Vitæ — résumé".encode("utf-8")
        assert parse_resume(raw, filename="r.txt") == "Curriculum Vitæ — résumé"

    def test_latin1_fallback_does_not_crash(self):
        # Bytes that are NOT valid utf-8 (lone 0xE9 = 'é' in latin-1, invalid in utf-8)
        raw = b"r\xe9sum\xe9"
        out = parse_resume(raw, filename="r.txt")
        assert "r" in out and "sum" in out
        assert isinstance(out, str)

    def test_no_filename_no_content_type_treated_as_text(self):
        assert parse_resume(b"plain text") == "plain text"
