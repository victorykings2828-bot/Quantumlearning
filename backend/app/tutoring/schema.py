"""The tutor's application response contract and its validation."""

from __future__ import annotations

import json
import re
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError

Intent = Literal["answer", "hint", "clarify", "redirect"]

MAX_ANSWER_CHARACTERS = 4000

# Rendering is Markdown only. Raw HTML, scripts, and private reasoning traces
# are stripped before the answer reaches a browser.
_HTML_TAG = re.compile(r"<[^>]+>")
_THINK_BLOCK = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)
_FENCE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


class TutorResponse(BaseModel):
    """Exactly the fields the policy allows. Extra fields are rejected."""

    intent: Intent
    answer_markdown: str = Field(min_length=1, max_length=MAX_ANSWER_CHARACTERS)
    passage_ids: list[str] = Field(default_factory=list)
    fact_ids: list[str] = Field(default_factory=list)
    followup_question: str | None = None

    model_config = {"extra": "forbid"}


class ValidationOutcome(BaseModel):
    ok: bool
    response: TutorResponse | None = None
    reason_code: str = ""
    detail: str = ""


def strip_unsafe(text: str) -> str:
    without_reasoning = _THINK_BLOCK.sub("", text)
    return _HTML_TAG.sub("", without_reasoning).strip()


def extract_object(raw: str) -> dict[str, Any] | None:
    """Parse the provider's output into the response object.

    One bounded repair is allowed: a fenced or wrapped JSON object is
    extracted. Anything else is treated as invalid output.
    """
    text = _THINK_BLOCK.sub("", raw).strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        parsed = None
    if isinstance(parsed, dict):
        return parsed

    fenced = _FENCE.search(text)
    if fenced:
        try:
            candidate = json.loads(fenced.group(1))
        except json.JSONDecodeError:
            candidate = None
        if isinstance(candidate, dict):
            return candidate

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        try:
            candidate = json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return None
        if isinstance(candidate, dict):
            return candidate
    return None


def validate(
    raw: str,
    *,
    allowed_passage_ids: set[str],
    allowed_fact_ids: set[str],
    required_intent: Intent | None = None,
) -> ValidationOutcome:
    """Validate provider output against the contract and the supplied envelope."""
    payload = extract_object(raw)
    if payload is None:
        return ValidationOutcome(ok=False, reason_code="unparseable_output")

    try:
        response = TutorResponse.model_validate(payload)
    except ValidationError as error:
        return ValidationOutcome(
            ok=False, reason_code="schema_violation", detail=error.errors()[0]["msg"]
        )

    cleaned = strip_unsafe(response.answer_markdown)
    if not cleaned:
        return ValidationOutcome(ok=False, reason_code="empty_after_sanitization")
    response.answer_markdown = cleaned

    unknown_passages = [pid for pid in response.passage_ids if pid not in allowed_passage_ids]
    if unknown_passages:
        return ValidationOutcome(
            ok=False,
            reason_code="unknown_passage_id",
            detail=", ".join(unknown_passages),
        )

    unknown_facts = [fid for fid in response.fact_ids if fid not in allowed_fact_ids]
    if unknown_facts:
        return ValidationOutcome(
            ok=False, reason_code="unknown_fact_id", detail=", ".join(unknown_facts)
        )

    if required_intent is not None and response.intent != required_intent:
        return ValidationOutcome(
            ok=False,
            reason_code="intent_mismatch",
            detail=f"server decided {required_intent}, provider returned {response.intent}",
        )

    return ValidationOutcome(ok=True, response=response)
