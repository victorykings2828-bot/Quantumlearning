"""Session, health, and published content routes."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import delete, select, text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.curriculum import access, loader, progress
from app.identity import sessions
from app.identity.dependencies import (
    Principal,
    clear_session_cookies,
    optional_principal,
    require_principal,
    set_session_cookies,
)
from app.storage.database import db_session
from app.storage.models import (
    AssessmentAttempt,
    Conversation,
    DeliveredHint,
    Evaluation,
    PreviewEncounter,
    Revision,
    Run,
    SkillEvidence,
    TaskAttempt,
    TopicProgress,
    TutorTurn,
    Workspace,
)
from app.tutoring import providers

router = APIRouter()

GUEST_DISCLOSURE = (
    "Your progress is saved against a private guest session held in this browser. "
    "Clearing site data, using private browsing, or switching device will not carry it "
    "across, and an anonymous session cannot be recovered once its cookie is gone."
)


@router.get("/health/live", tags=["health"])
def health_live() -> dict[str, str]:
    return {"status": "live"}


@router.get("/health/ready", tags=["health"])
def health_ready(session: Session = Depends(db_session)) -> dict[str, Any]:
    checks: dict[str, Any] = {}
    try:
        session.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:  # pragma: no cover - surfaced as a 503 in deployment
        checks["database"] = "unavailable"
    try:
        loader.load_chapter("chapter-1")
        checks["content"] = "ok"
    except Exception:  # pragma: no cover
        checks["content"] = "unavailable"
    ready = all(value == "ok" for value in checks.values())
    if not ready:
        raise HTTPException(status_code=503, detail={"code": "not_ready", "checks": checks})
    # The tutor entry is a mode name only and never echoes a credential.
    checks["tutor_provider"] = providers.diagnostics(get_settings())["provider"]
    return {"status": "ready", "checks": checks}


@router.post("/guest-session", tags=["identity"], status_code=status.HTTP_201_CREATED)
def create_guest_session(
    request: Request, response: Response, session: Session = Depends(db_session)
) -> dict[str, Any]:
    """The only bootstrap endpoint. A still-valid session is reused, not replaced."""
    token = request.cookies.get(sessions.SESSION_COOKIE_NAME)
    existing = sessions.resolve(session, token)
    if existing is not None:
        session.commit()
        return {
            "principal_id": existing.principal_id,
            "created": False,
            "expires_at": existing.expires_at.isoformat(),
            "csrf_token": existing.csrf_token,
            "disclosure": GUEST_DISCLOSURE,
        }
    issued = sessions.create_guest(session)
    session.commit()
    set_session_cookies(response, issued)
    return {
        "principal_id": issued.principal_id,
        "created": True,
        "expires_at": issued.expires_at.isoformat(),
        "csrf_token": issued.csrf_token,
        "disclosure": GUEST_DISCLOSURE,
    }


@router.get("/me", tags=["identity"])
def read_me(
    request: Request,
    principal: Principal | None = Depends(optional_principal),
    session: Session = Depends(db_session),
) -> dict[str, Any]:
    if principal is None:
        raise HTTPException(
            status_code=401,
            detail={
                "code": "no_guest_session",
                "message": "No active guest session. Start one to save progress.",
            },
        )
    resolved = sessions.resolve(session, request.cookies.get(sessions.SESSION_COOKIE_NAME))
    chapter = progress.chapter_progress(session, principal.id)
    session.commit()
    return {
        "principal_id": principal.id,
        "expires_at": resolved.expires_at.isoformat() if resolved else "",
        "next_topic_id": chapter["next_topic_id"],
        "topics_complete": chapter["topics_complete"],
        "topics_total": chapter["topics_total"],
        "disclosure": GUEST_DISCLOSURE,
    }


@router.post("/reset-progress", tags=["identity"])
def reset_progress(
    principal: Principal = Depends(require_principal),
    session: Session = Depends(db_session),
) -> dict[str, Any]:
    """Delete this guest's records. Scoped to this principal and nobody else."""
    owner = uuid.UUID(principal.id)
    # Evaluations hang off attempts, so remove them first.
    attempt_ids = [
        row.id
        for row in session.scalars(
            select(AssessmentAttempt).where(AssessmentAttempt.principal_id == owner)
        )
    ]
    if attempt_ids:
        session.execute(delete(Evaluation).where(Evaluation.attempt_id.in_(attempt_ids)))
    for model in (
        TutorTurn,
        Conversation,
        DeliveredHint,
        TaskAttempt,
        AssessmentAttempt,
        SkillEvidence,
        PreviewEncounter,
        TopicProgress,
        Run,
        Revision,
        Workspace,
    ):
        session.execute(delete(model).where(model.principal_id == owner))
    session.commit()
    return {"reset": True, "principal_id": principal.id}


@router.post("/end-session", tags=["identity"])
def end_session(
    response: Response,
    principal: Principal = Depends(require_principal),
    session: Session = Depends(db_session),
) -> dict[str, bool]:
    sessions.revoke(session, principal.session_id)
    session.commit()
    clear_session_cookies(response)
    return {"ended": True}


@router.get("/introduction", tags=["content"])
def read_introduction() -> dict[str, Any]:
    return loader.load_introduction()


@router.get("/beginner-bridge", tags=["content"])
def read_bridge() -> dict[str, Any]:
    return loader.load_bridge()


@router.get("/previews", tags=["content"])
def read_previews() -> dict[str, Any]:
    return loader.load_previews()


@router.get("/course", tags=["content"])
def read_course(
    principal: Principal | None = Depends(optional_principal),
    session: Session = Depends(db_session),
) -> dict[str, Any]:
    """The chapter map with real progress and explicit availability reasons."""
    course = dict(loader.load_course())
    records = progress.evidence_records(session, principal.id) if principal is not None else []
    chapter_progress = (
        progress.chapter_progress(session, principal.id) if principal is not None else None
    )

    chapters: list[dict[str, Any]] = []
    for chapter in course["chapters"]:
        decision = access.decide(
            publication=chapter["publication"],
            required_skills=chapter.get("prerequisite_skills", []),
            records=records,
            assessed=bool(chapter.get("prerequisite_skills")),
        )
        entry = dict(chapter)
        entry["access"] = decision.as_dict()
        if chapter["id"] == "chapter-1" and chapter_progress is not None:
            entry["progress"] = {
                "topics_complete": chapter_progress["topics_complete"],
                "topics_total": chapter_progress["topics_total"],
                "next_topic_id": chapter_progress["next_topic_id"],
            }
            entry["topics"] = chapter_progress["topics"]
        elif chapter["id"] == "chapter-1":
            published = loader.load_chapter("chapter-1")
            entry["topics"] = [
                {
                    "topic_id": topic["id"],
                    "number": topic["number"],
                    "title": topic["title"],
                    "slug": topic["slug"],
                    "status": "not_started",
                    "steps_completed": 0,
                    "steps_required": len(topic["completion"]["required_step_ids"]),
                    "tasks_passed": 0,
                    "tasks_required": len(topic["completion"]["required_task_ids"]),
                    "skills": topic["skills"],
                    "prerequisite_skills": topic["prerequisite_skills"],
                    "estimated_minutes": topic.get("estimated_minutes"),
                }
                for topic in published["topics"]
            ]
        chapters.append(entry)

    course["chapters"] = chapters
    course["browsing_note"] = access.browsing_always_allowed()
    if principal is not None:
        session.commit()
    return course


@router.get("/course/{chapter_id}", tags=["content"])
def read_chapter(
    chapter_id: str,
    principal: Principal | None = Depends(optional_principal),
    session: Session = Depends(db_session),
) -> dict[str, Any]:
    try:
        chapter = loader.load_chapter(chapter_id)
    except KeyError as error:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "chapter_not_published",
                "message": (
                    "That chapter is not implemented yet. Its description on the course "
                    "page is accurate; there is no lesson behind it."
                ),
            },
        ) from error
    payload = {key: value for key, value in chapter.items() if key != "topics"}
    payload["topics"] = [
        loader.public_topic(topic, include_body=False) for topic in chapter["topics"]
    ]
    if principal is not None:
        payload["progress"] = progress.chapter_progress(session, principal.id)
        session.commit()
    return payload


@router.get("/topics/{topic_id}", tags=["content"])
def read_topic(
    topic_id: str,
    principal: Principal | None = Depends(optional_principal),
    session: Session = Depends(db_session),
) -> dict[str, Any]:
    topic = loader.get_topic(topic_id)
    if topic is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "topic_not_found", "message": "No such topic in this chapter."},
        )
    payload = loader.public_topic(topic)
    chapter = loader.load_chapter("chapter-1")
    topics = chapter["topics"]
    index = next(i for i, item in enumerate(topics) if item["id"] == topic_id)
    payload["previous_topic_id"] = topics[index - 1]["id"] if index > 0 else None
    payload["next_topic_id"] = topics[index + 1]["id"] if index + 1 < len(topics) else None
    payload["notation_contract"] = chapter["notation_contract"]
    payload["content_version"] = chapter.get("version", 1)

    if principal is not None:
        records = progress.evidence_records(session, principal.id)
        decision = access.decide(
            publication="published",
            required_skills=topic.get("prerequisite_skills", []),
            records=records,
            assessed=False,
        )
        payload["access"] = decision.as_dict()
        payload["progress"] = progress.topic_summary(session, principal.id, topic)
        row = progress.get_topic_progress(session, principal.id, topic_id)
        payload["completed_steps"] = row.completed_steps or {}
        payload["recorded_prediction"] = row.prediction
        payload["passed_task_ids"] = sorted(
            progress.passed_task_ids(session, principal.id, topic_id)
        )
        session.commit()
    else:
        payload["access"] = access.decide(
            publication="published", required_skills=[], records=[], assessed=False
        ).as_dict()
    return payload


@router.get("/progress", tags=["progress"])
def read_progress(
    principal: Principal = Depends(require_principal),
    session: Session = Depends(db_session),
) -> dict[str, Any]:
    chapter = progress.chapter_progress(session, principal.id)
    previews = progress.preview_status(session, principal.id)
    records = progress.evidence_records(session, principal.id)
    assessment_rows = session.scalars(
        select(AssessmentAttempt).where(AssessmentAttempt.principal_id == uuid.UUID(principal.id))
    )
    attempts = []
    for attempt in assessment_rows:
        evaluation = session.scalar(select(Evaluation).where(Evaluation.attempt_id == attempt.id))
        attempts.append(
            {
                "attempt_id": str(attempt.id),
                "form": attempt.form,
                "mode": attempt.mode,
                "status": attempt.status,
                "submitted_at": attempt.submitted_at.isoformat() if attempt.submitted_at else None,
                "score": evaluation.score if evaluation else None,
                "max_score": evaluation.max_score if evaluation else None,
                "passed": evaluation.passed if evaluation else None,
            }
        )
    session.commit()
    return {
        "chapter": chapter,
        "previews": previews,
        "assessment_attempts": attempts,
        "evidence_rule": {
            "required_independent": access.REQUIRED_INDEPENDENT_EVIDENCE,
            "required_distinct_families": access.REQUIRED_DISTINCT_FAMILIES,
            "note": (
                "Activity completion, independent evidence, and review recommendations "
                "are separate records. Asking for a hint is not a failure, and a "
                "review recommendation does not erase past achievement."
            ),
        },
        "demonstrated_skills": sorted(access.demonstrated_skills(records)),
        "disclosure": GUEST_DISCLOSURE,
    }


@router.get("/tutor/diagnostics", tags=["tutor"])
def tutor_diagnostics() -> dict[str, Any]:
    return providers.diagnostics(get_settings())


@router.get("/content-versions", tags=["content"])
def content_versions() -> dict[str, Any]:
    return {"documents": loader.content_versions()}
