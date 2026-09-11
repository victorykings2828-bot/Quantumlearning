"""Chapter assessment routes.

Submission is transactional: validate ownership, freeze the answers, evaluate,
write exactly one evaluation plus its evidence, update completion, commit.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api import schemas
from app.assessment import evaluator
from app.curriculum import loader, progress
from app.identity.dependencies import Principal, require_principal
from app.quantum.qiskit_engine import get_engine
from app.quantum.spec import CircuitSpec, RunRequest
from app.storage.database import db_session
from app.storage.models import AssessmentAttempt, Evaluation

router = APIRouter()

ASSESSMENT_ID = "chapter-1-assessment"


def _load_attempt(session: Session, principal_id: str, attempt_id: str) -> AssessmentAttempt:
    try:
        key = uuid.UUID(attempt_id)
    except ValueError as error:
        raise HTTPException(
            status_code=404, detail={"code": "not_found", "message": "No such attempt."}
        ) from error
    attempt = session.get(AssessmentAttempt, key)
    if attempt is None or str(attempt.principal_id) != principal_id:
        raise HTTPException(
            status_code=404, detail={"code": "not_found", "message": "No such attempt."}
        )
    return attempt


@router.get("/assessments/chapter-1", tags=["assessment"])
def read_assessment(
    principal: Principal = Depends(require_principal),
    session: Session = Depends(db_session),
) -> dict[str, Any]:
    """The learner-safe assessment. The answer key never leaves the server."""
    document = loader.public_assessment()
    chapter = progress.chapter_progress(session, principal.id)
    practice_complete = chapter["topics_complete"] == chapter["topics_total"]
    attempts = session.scalars(
        select(AssessmentAttempt).where(
            AssessmentAttempt.principal_id == uuid.UUID(principal.id),
            AssessmentAttempt.assessment_id == ASSESSMENT_ID,
        )
    )
    history = [
        {
            "attempt_id": str(row.id),
            "form": row.form,
            "mode": row.mode,
            "status": row.status,
            "submitted_at": row.submitted_at.isoformat() if row.submitted_at else None,
        }
        for row in attempts
    ]
    session.commit()
    return {
        **document,
        "practice_complete": practice_complete,
        "practice_note": (
            "The published pass policy asks for the required practice activities to be "
            "complete. You can still open a practice attempt at any time."
        ),
        "attempts": history,
    }


@router.post("/assessments/chapter-1/attempts", tags=["assessment"], status_code=201)
def start_attempt(
    body: schemas.AssessmentStartRequest,
    principal: Principal = Depends(require_principal),
    session: Session = Depends(db_session),
) -> dict[str, Any]:
    owner = uuid.UUID(principal.id)
    if body.idempotency_key:
        existing = session.scalar(
            select(AssessmentAttempt).where(
                AssessmentAttempt.principal_id == owner,
                AssessmentAttempt.idempotency_key == body.idempotency_key,
            )
        )
        if existing is not None:
            return _attempt_payload(existing, duplicate=True)

    open_attempt = session.scalar(
        select(AssessmentAttempt).where(
            AssessmentAttempt.principal_id == owner,
            AssessmentAttempt.assessment_id == ASSESSMENT_ID,
            AssessmentAttempt.form == body.form,
            AssessmentAttempt.status == "in_progress",
        )
    )
    if open_attempt is not None:
        return _attempt_payload(open_attempt, duplicate=False)

    attempt = AssessmentAttempt(
        principal_id=owner,
        assessment_id=ASSESSMENT_ID,
        form=body.form,
        mode=body.mode,
        status="in_progress",
        content_version=loader.load_assessment().get("version", 1),
        answers={},
        idempotency_key=body.idempotency_key,
    )
    session.add(attempt)
    session.commit()
    return _attempt_payload(attempt, duplicate=False)


def _attempt_payload(attempt: AssessmentAttempt, *, duplicate: bool) -> dict[str, Any]:
    document = loader.public_assessment(form=attempt.form)
    return {
        "attempt_id": str(attempt.id),
        "form": attempt.form,
        "mode": attempt.mode,
        "status": attempt.status,
        "answers": attempt.answers,
        "items": document["forms"][attempt.form],
        "pass_policy": document["pass_policy"],
        "test_mode_help": document["test_mode_help"],
        "duplicate": duplicate,
    }


@router.patch("/assessments/attempts/{attempt_id}", tags=["assessment"])
def save_answers(
    attempt_id: str,
    body: schemas.AssessmentAnswersRequest,
    principal: Principal = Depends(require_principal),
    session: Session = Depends(db_session),
) -> dict[str, Any]:
    """Answers are saved server-side so a reload or a crash does not lose them."""
    attempt = _load_attempt(session, principal.id, attempt_id)
    if attempt.status != "in_progress":
        raise HTTPException(
            status_code=409,
            detail={
                "code": "attempt_closed",
                "message": "This attempt has been submitted and can no longer be changed.",
            },
        )
    merged = dict(attempt.answers or {})
    merged.update(body.answers)
    attempt.answers = merged
    session.commit()
    return {"attempt_id": attempt_id, "saved": True, "answers": attempt.answers}


@router.post("/assessments/attempts/{attempt_id}/convert-to-practice", tags=["assessment"])
def convert_to_practice(
    attempt_id: str,
    principal: Principal = Depends(require_principal),
    session: Session = Depends(db_session),
) -> dict[str, Any]:
    """The platform performs this transition and records the assistance, not the tutor."""
    attempt = _load_attempt(session, principal.id, attempt_id)
    if attempt.status != "in_progress":
        raise HTTPException(
            status_code=409,
            detail={"code": "attempt_closed", "message": "This attempt is already submitted."},
        )
    attempt.mode = "practice"
    session.commit()
    return {
        "attempt_id": attempt_id,
        "mode": attempt.mode,
        "note": (
            "This attempt is now a practice attempt. Substantive help is available, and "
            "its results record assisted rather than independent evidence."
        ),
    }


def _evaluate_item(item: dict[str, Any], key: dict[str, Any], answer: Any) -> evaluator.Verdict:
    kind = key["kind"]
    submission: dict[str, Any]
    if kind == "single_select":
        submission = {"selection": answer}
    elif kind == "numeric_fields":
        submission = {"values": answer or {}}
    elif kind == "classification":
        submission = {"assignments": answer or {}}
    elif kind == "compound":
        submission = {"parts": answer or {}}
    elif kind == "circuit_goal":
        circuit = None
        result = None
        if answer:
            try:
                circuit = CircuitSpec.model_validate(answer)
                result = get_engine().run(RunRequest(circuit=circuit, shots=1, seed=0))
            except Exception:  # an invalid circuit is simply a wrong answer
                circuit = None
                result = None
        return evaluator.evaluate(
            key,
            {},
            circuit=circuit,
            result=result,
            assessed_skills=item.get("assessed_skills", []),
        )
    else:  # pragma: no cover - content validation prevents this
        raise ValueError(f"unknown assessment item kind: {kind}")
    return evaluator.evaluate(key, submission, assessed_skills=item.get("assessed_skills", []))


@router.post("/assessments/attempts/{attempt_id}/submit", tags=["assessment"])
def submit_attempt(
    attempt_id: str,
    body: schemas.AssessmentSubmitRequest,
    principal: Principal = Depends(require_principal),
    session: Session = Depends(db_session),
) -> dict[str, Any]:
    attempt = _load_attempt(session, principal.id, attempt_id)
    existing = session.scalar(select(Evaluation).where(Evaluation.attempt_id == attempt.id))
    if existing is not None:
        # A duplicate submission returns the original outcome and adds no evidence.
        return {**existing.detail, "duplicate": True}

    document = loader.load_assessment()
    items = document["forms"][attempt.form]
    answer_key = document["answer_key"]
    policy = document["pass_policy"]
    answers = attempt.answers or {}

    per_item: list[dict[str, Any]] = []
    score = 0.0
    for item in items:
        key = answer_key[item["id"]]
        verdict = _evaluate_item(item, key, answers.get(item["id"]))
        if verdict.passed:
            score += document["points_per_item"]
        per_item.append(
            {
                "item_id": item["id"],
                "number": item["number"],
                "passed": verdict.passed,
                "reason_code": verdict.reason_code,
                "assessed_skills": item.get("assessed_skills", []),
                "item_family": item.get("item_family"),
            }
        )

    essential = set(policy["essential_item_numbers"])
    essential_passed = all(entry["passed"] for entry in per_item if entry["number"] in essential)
    chapter = progress.chapter_progress(session, principal.id)
    practice_complete = chapter["topics_complete"] == chapter["topics_total"]
    passed = (
        score >= policy["minimum_score"]
        and essential_passed
        and (practice_complete or not policy.get("requires_practice_complete", True))
    )

    guidance = document.get("revision_guidance", {})
    weak_skills: list[str] = []
    for entry in per_item:
        if not entry["passed"]:
            weak_skills.extend(entry["assessed_skills"])
    revision_guidance = [
        {"skill_id": skill, "advice": guidance[skill]}
        for skill in dict.fromkeys(weak_skills)
        if skill in guidance
    ]

    detail = {
        "attempt_id": str(attempt.id),
        "form": attempt.form,
        "mode": attempt.mode,
        "score": score,
        "max_score": float(len(items) * document["points_per_item"]),
        "passed": passed,
        "essential_items_passed": essential_passed,
        "practice_complete": practice_complete,
        "per_item": per_item,
        "revision_guidance": revision_guidance,
        "pass_policy": policy,
    }

    attempt.status = "submitted"
    attempt.submitted_at = datetime.now(UTC)
    session.add(
        Evaluation(
            principal_id=uuid.UUID(principal.id),
            attempt_id=attempt.id,
            score=score,
            max_score=detail["max_score"],
            passed=passed,
            detail=detail,
            rubric_version=document.get("version", 1),
        )
    )

    # Evidence comes only from items the rubric actually evaluated, and an
    # unassisted test attempt is what produces independent evidence.
    evidence_kind = "independent" if attempt.mode == "test" else "assisted"
    for entry in per_item:
        if entry["passed"]:
            progress.record_evidence(
                session,
                principal.id,
                skills=entry["assessed_skills"],
                kind=evidence_kind,
                item_family=entry["item_family"] or entry["item_id"],
                source_kind="assessment_item",
                source_id=f"{attempt.id}:{entry['item_id']}",
            )
    session.commit()
    return {**detail, "duplicate": False}
