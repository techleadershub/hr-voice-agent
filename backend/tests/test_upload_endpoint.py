"""Integration tests for /upload_resume.

These tests exercise the FastAPI route end-to-end using TestClient, with the
heavy collaborators (database + LangGraph workflow) mocked so the test stays
fast and offline. The goal is to lock down behaviour that has already broken
once or that would break silently on regression:

  * 10 MB upload cap is enforced (DoS protection)
  * PDFs are routed through pdfplumber (not naively decoded as utf-8)
  * Plain text resumes still work
  * Sync workflow runs off the event loop via asyncio.to_thread
  * Empty/scanned PDFs surface as 400, not 500
  * Multipart validation surfaces as 422
"""

import asyncio
import os
import sys
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

# Reuse the hand-built sample PDF from the parser tests.
from backend.tests.test_resume_parser import SAMPLE_PDF_BYTES  # noqa: E402


@pytest.fixture
def client():
    """Build a TestClient with database + workflow mocked.

    We patch the *names imported into backend.main*, not the source modules,
    because main.py does `from .workflow import app_workflow` — the route
    looks up the symbol on its own module.
    """
    # Import here so patch targets exist
    from backend import main as main_module

    fake_db = MagicMock()
    fake_db.create_interview.return_value = 42

    fake_workflow = MagicMock()
    fake_workflow.invoke.return_value = {
        "match_score": 88.0,
        "matched_skills": ["Python"],
        "missing_skills": ["Kubernetes"],
        "experience_gap": "1 year short",
        "questions": [{"id": "q1", "text": "Tell me about yourself.",
                       "type": "Personalized", "context": ""}],
    }

    with patch.object(main_module, "database_service", fake_db), \
         patch.object(main_module, "app_workflow", fake_workflow):
        with TestClient(main_module.app) as c:
            # Expose the mocks on the client so tests can assert against them
            c.fake_db = fake_db
            c.fake_workflow = fake_workflow
            yield c


# ---------- happy paths ----------

class TestUploadHappyPath:
    def test_pdf_upload_routes_through_pdfplumber(self, client):
        resp = client.post(
            "/upload_resume",
            data={"candidate_name": "Jane", "job_description": "Python role"},
            files={"file": ("resume.pdf", SAMPLE_PDF_BYTES, "application/pdf")},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["interview_id"] == 42
        assert body["status"] == "preparation_complete"
        assert body["match_score"] == 88.0

        # The DB must have received the *parsed* PDF text, not the raw bytes.
        args, _ = client.fake_db.create_interview.call_args
        candidate_name, resume_text, jd = args
        assert candidate_name == "Jane"
        assert jd == "Python role"
        assert "Jane Doe" in resume_text  # extracted from PDF
        assert "%PDF" not in resume_text  # raw bytes did NOT leak through

    def test_text_upload_passes_through(self, client):
        resp = client.post(
            "/upload_resume",
            data={"candidate_name": "Bob", "job_description": "JD"},
            files={"file": ("resume.txt", b"Bob Smith\nPython, FastAPI", "text/plain")},
        )
        assert resp.status_code == 200, resp.text

        _, resume_text, _ = client.fake_db.create_interview.call_args.args
        assert resume_text == "Bob Smith\nPython, FastAPI"

    def test_workflow_state_includes_parsed_resume(self, client):
        client.post(
            "/upload_resume",
            data={"candidate_name": "Jane", "job_description": "JD"},
            files={"file": ("r.pdf", SAMPLE_PDF_BYTES, "application/pdf")},
        )
        state = client.fake_workflow.invoke.call_args.args[0]
        assert state["interview_id"] == "42"
        assert state["job_description"] == "JD"
        assert "Jane Doe" in state["resume_text"]


# ---------- size cap ----------

class TestUploadSizeCap:
    def test_oversize_upload_rejected_with_413(self, client):
        from backend.main import MAX_RESUME_BYTES
        big = b"A" * (MAX_RESUME_BYTES + 1)
        resp = client.post(
            "/upload_resume",
            data={"candidate_name": "X", "job_description": "Y"},
            files={"file": ("big.pdf", big, "application/pdf")},
        )
        assert resp.status_code == 413
        assert "10 MB" in resp.json()["detail"]
        # Workflow must never have been touched
        client.fake_workflow.invoke.assert_not_called()
        client.fake_db.create_interview.assert_not_called()

    def test_at_cap_is_accepted(self, client):
        # Build a payload that is *exactly* the cap (use a real PDF + padding
        # would exceed it; instead test by patching the cap down for one call).
        from backend import main as main_module
        small_cap = len(SAMPLE_PDF_BYTES)
        with patch.object(main_module, "MAX_RESUME_BYTES", small_cap):
            resp = client.post(
                "/upload_resume",
                data={"candidate_name": "Jane", "job_description": "JD"},
                files={"file": ("r.pdf", SAMPLE_PDF_BYTES, "application/pdf")},
            )
        assert resp.status_code == 200, resp.text


# ---------- error surfaces ----------

class TestUploadErrors:
    def test_scanned_pdf_returns_400_not_500(self, client):
        # A PDF that pdfplumber can open but yields no text.
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
        resp = client.post(
            "/upload_resume",
            data={"candidate_name": "Jane", "job_description": "JD"},
            files={"file": ("scan.pdf", empty_pdf, "application/pdf")},
        )
        assert resp.status_code == 400
        assert "scanned image" in resp.json()["detail"].lower() \
            or "could not extract" in resp.json()["detail"].lower()

    def test_missing_file_returns_422(self, client):
        resp = client.post(
            "/upload_resume",
            data={"candidate_name": "Jane", "job_description": "JD"},
        )
        assert resp.status_code == 422

    def test_missing_candidate_name_returns_422(self, client):
        resp = client.post(
            "/upload_resume",
            data={"job_description": "JD"},
            files={"file": ("r.txt", b"hi", "text/plain")},
        )
        assert resp.status_code == 422


class TestUploadGuardrails:
    """Hard input-validation regressions. If any of these stop returning 400,
    the guardrail wiring in upload_resume has been removed."""

    def test_blank_candidate_name_returns_400(self, client):
        resp = client.post(
            "/upload_resume",
            data={"candidate_name": "   ", "job_description": "JD"},
            files={"file": ("r.txt", b"hi", "text/plain")},
        )
        assert resp.status_code == 400
        assert "candidate_name" in resp.json()["detail"]
        client.fake_workflow.invoke.assert_not_called()

    def test_oversized_jd_returns_400(self, client):
        from backend.services.guardrails import MAX_JOB_DESCRIPTION
        resp = client.post(
            "/upload_resume",
            data={"candidate_name": "Jane",
                  "job_description": "x" * (MAX_JOB_DESCRIPTION + 1)},
            files={"file": ("r.txt", b"hi", "text/plain")},
        )
        assert resp.status_code == 400
        assert "job_description" in resp.json()["detail"]
        client.fake_workflow.invoke.assert_not_called()

    def test_control_chars_stripped_from_jd(self, client):
        resp = client.post(
            "/upload_resume",
            data={"candidate_name": "Jane", "job_description": "Python\x00\x07role"},
            files={"file": ("r.txt", b"hi", "text/plain")},
        )
        assert resp.status_code == 200
        _, _, jd = client.fake_db.create_interview.call_args.args
        assert "\x00" not in jd and "\x07" not in jd
        assert jd == "Pythonrole"

    def test_oversized_parsed_resume_returns_400(self, client):
        # Build a text resume that is over the parsed-text cap
        from backend.services.guardrails import MAX_RESUME_TEXT
        big = ("a" * (MAX_RESUME_TEXT + 1)).encode("utf-8")
        # Below the byte cap (10 MB) but over the text cap
        assert len(big) < 10 * 1024 * 1024
        resp = client.post(
            "/upload_resume",
            data={"candidate_name": "Jane", "job_description": "JD"},
            files={"file": ("r.txt", big, "text/plain")},
        )
        assert resp.status_code == 400
        assert "resume_text" in resp.json()["detail"]
        client.fake_workflow.invoke.assert_not_called()


# ---------- non-blocking workflow execution ----------

class TestNonBlockingExecution:
    """Regression: the synchronous LangGraph workflow and pdfplumber parser
    must run in a thread, not on the event loop. Otherwise one upload freezes
    every other request (including health checks and active WebSockets).
    """

    def test_workflow_dispatched_via_to_thread(self, client):
        with patch("backend.main.asyncio.to_thread",
                   wraps=asyncio.to_thread) as spy:
            resp = client.post(
                "/upload_resume",
                data={"candidate_name": "Jane", "job_description": "JD"},
                files={"file": ("r.txt", b"hello", "text/plain")},
            )
            assert resp.status_code == 200, resp.text

        called_fns = [c.args[0] for c in spy.call_args_list]
        # parse_resume + app_workflow.invoke both go through to_thread
        from backend.services.resume_parser import parse_resume
        assert parse_resume in called_fns
        assert client.fake_workflow.invoke in called_fns
