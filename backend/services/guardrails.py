"""Guardrails for the HR voice agent.

Defends against:
  * Oversized / malformed user input (cost blow-up, prompt-context flooding)
  * Prompt injection from candidate-controlled text (resume, voice answers)
  * Discriminatory / illegal interview questions in generator output
  * LLM-coerced evaluations that break the schema or contradict themselves
"""

import logging
import re
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

# --- input length caps ---
MAX_CANDIDATE_NAME = 200
MAX_JOB_DESCRIPTION = 50_000     # typical JD < 5K chars
MAX_RESUME_TEXT = 100_000        # typical resume < 10K chars
MAX_ANSWER_TEXT = 10_000         # one Whisper transcription

# Strip:
#   * C0/C1 control chars (except \t, \n, \r)
#   * Unicode bidi-override / zero-width / BOM characters. These are
#     invisible to a human reviewer but visible to the LLM — a documented
#     prompt-injection vector for documents that pass through human review.
#       U+200B-200F  zero-width space, ZWNJ, ZWJ, LRM, RLM
#       U+202A-202E  bidi embedding / override (incl. U+202E RLO)
#       U+2060       word joiner
#       U+FEFF       BOM / zero-width no-break space
_CONTROL_CHAR_RE = re.compile(
    "["
    "\x00-\x08\x0B\x0C\x0E-\x1F\x7F"
    "​-‏"
    "‪-‮"
    "⁠"
    "﻿"
    "]"
)


class GuardrailError(ValueError):
    """Raised when input or output violates a hard guardrail."""


def sanitize_user_text(
    text: Optional[str],
    max_len: int,
    *,
    field: str = "input",
    min_len: int = 1,
) -> str:
    """Strip control + bidi/zero-width chars, trim, enforce length bounds.
    Raises GuardrailError on violation."""
    if text is None or not isinstance(text, str):
        raise GuardrailError(f"{field} must be a string")
    cleaned = _CONTROL_CHAR_RE.sub("", text).strip()
    if len(cleaned) < min_len:
        raise GuardrailError(f"{field} is empty or too short")
    if len(cleaned) > max_len:
        raise GuardrailError(
            f"{field} exceeds {max_len} character limit ({len(cleaned)} chars)"
        )
    return cleaned


def wrap_untrusted(label: str, content: str) -> str:
    """Wrap user content in clearly-delimited tags so the LLM can distinguish
    instructions from data. Neutralises any inner occurrence of the closing
    tag so a malicious input cannot 'close out' early and inject instructions.
    """
    closing = f"</{label}>"
    safe = content.replace(closing, f"</ {label}>")
    return f"<{label}>\n{safe}\n</{label}>"


# --- bias / illegal-question screening on generated questions ---
#
# Conservative regexes: only flag questions that ask the *candidate* about a
# protected attribute. We deliberately do not flag general topical mentions
# (e.g. "design a UX for elderly users" mentions age but is not asking the
# candidate's age).
_BIAS_PATTERNS: List[Tuple[str, re.Pattern]] = [
    ("age", re.compile(
        r"\b(how old are you|what(?:'s| is) your age|your age|"
        r"date of birth|when were you born)\b", re.I)),
    ("marital", re.compile(
        r"\b(are you (married|single|divorced|engaged)|"
        r"marital status|your (spouse|husband|wife))\b", re.I)),
    ("pregnancy", re.compile(
        r"\b(are you pregnant|"
        r"(planning|plan) (to have|on having) (a baby|children|kids)|"
        r"pregnan(t|cy))\b", re.I)),
    ("religion", re.compile(
        r"\b(what(?:'s| is) your religion|"
        r"are you (religious|christian|muslim|jewish|hindu|buddhist|atheist)|"
        r"religious belief|which (church|mosque|temple|synagogue))\b", re.I)),
    ("race_origin", re.compile(
        r"\b(what(?:'s| is) your (race|ethnicity)|"
        r"where are you (really )?from|"
        r"your nationality|country of origin)\b", re.I)),
    ("disability", re.compile(
        r"\b(do you have (a |any )?disabilit(y|ies)|"
        r"are you disabled|"
        r"any (medical condition|chronic illness))\b", re.I)),
    ("orientation", re.compile(
        r"\b(what(?:'s| is) your sexual orientation|"
        r"are you (gay|straight|lesbian|bisexual|homosexual))\b", re.I)),
    ("citizenship", re.compile(
        r"\b(are you a (us |u\.s\. )?citizen|"
        r"citizenship status|"
        r"do you have a green card)\b", re.I)),
]


def screen_question_for_bias(text: str) -> Optional[str]:
    """Return the violated category (e.g. 'age') if the question is biased,
    else None."""
    if not text:
        return None
    for label, pat in _BIAS_PATTERNS:
        if pat.search(text):
            return label
    return None


def filter_biased_questions(questions: list) -> Tuple[list, List[Tuple[str, str]]]:
    """Return (kept, dropped). `dropped` is a list of (question_text, reason)."""
    kept: list = []
    dropped: List[Tuple[str, str]] = []
    for q in questions:
        text = q.text if hasattr(q, "text") else (q.get("text", "") if isinstance(q, dict) else "")
        reason = screen_question_for_bias(text)
        if reason:
            dropped.append((text, reason))
            logger.warning(f"Guardrail dropped biased question ({reason}): {text!r}")
        else:
            kept.append(q)
    return kept, dropped


# --- evaluation output validation ---

ALLOWED_RECOMMENDATIONS = {"Hire", "No Hire", "Strong Hire"}
_SCORE_FIELDS = (
    "technical_score",
    "communication_score",
    "cultural_fit_score",
    "overall_score",
)
_RECOMMENDATION_CANONICAL = {
    "hire": "Hire",
    "no hire": "No Hire",
    "strong hire": "Strong Hire",
}


def normalize_recommendation(value) -> Optional[str]:
    """Map a model-emitted recommendation to its canonical form, ignoring
    case and surrounding/inner whitespace. Returns None if unrecognised.

    Accepts e.g. "STRONG HIRE", "  strong  hire  ", "No  Hire" → "Strong Hire" / "No Hire".
    """
    if not isinstance(value, str):
        return None
    norm = " ".join(value.split()).lower()
    return _RECOMMENDATION_CANONICAL.get(norm)


def validate_evaluation(eval_obj) -> None:
    """Hard-fail on out-of-range scores or unknown recommendation; warn on
    contradictions that suggest prompt injection. Mutates `eval_obj` to
    canonicalise the recommendation field (e.g. 'STRONG HIRE' → 'Strong Hire')
    so downstream code can rely on the canonical form."""
    for field in _SCORE_FIELDS:
        v = getattr(eval_obj, field, None)
        if v is None or not isinstance(v, (int, float)) or not (0 <= v <= 100):
            raise GuardrailError(f"evaluation.{field} out of range: {v!r}")

    canonical = normalize_recommendation(eval_obj.recommendation)
    if canonical is None:
        raise GuardrailError(
            f"evaluation.recommendation not allowed: {eval_obj.recommendation!r}"
        )
    eval_obj.recommendation = canonical

    if canonical == "Strong Hire" and eval_obj.overall_score < 50:
        logger.warning(
            "Evaluation contradicts itself: overall_score=%s but "
            "recommendation=Strong Hire — possible prompt injection",
            eval_obj.overall_score,
        )
