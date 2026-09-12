"""Tutor conversation routes."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api import schemas
from app.config import get_settings
from app.curriculum import loader, progress
from app.identity.dependencies import Principal, require_principal
from app.storage.database import db_session
from app.storage.models import TutorTurn
from app.tutoring import knowledge
from app.tutoring import service as tutor_service
from app.workspaces import service as workspaces

router = APIRouter()


@router.post("/tutor/turns", tags=["tutor"])
def create_turn(
    body: schemas.TutorTurnRequest,
    principal: Principal = Depends(require_principal),
    session: Session = Depends(db_session),
) -> dict[str, Any]:
    """One tutor turn. Scope is re-decided here on every request."""
    settings = get_settings()
    if len(body.message) > settings.tutor_max_input_characters:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "message_too_long",
                "message": (
                    f"Questions are limited to {settings.tutor_max_input_characters} characters."
                ),
            },
        )

    if body.topic_id and loader.get_topic(body.topic_id) is None:
        raise HTTPException(status_code=422, detail="Unknown topic")
    run = None
    if body.run_id:
        try:
            run = workspaces.load_run(session, principal.id, body.run_id)
        except workspaces.OwnershipError as error:
            raise HTTPException(
                status_code=404,
                detail={"code": "not_found", "message": "No such run for this guest."},
            ) from error

    if run is not None and body.topic_id:
        from app.storage.models import Revision, Workspace

        revision = session.get(Revision, run.revision_id)
        workspace = session.get(Workspace, revision.workspace_id) if revision else None
        if workspace is None or workspace.topic_id != body.topic_id:
            raise HTTPException(status_code=422, detail="Run does not belong to the selected topic")

    max_hint_level = 0
    if body.topic_id:
        hints = loader.get_hints(body.topic_id)
        # An unassisted test permits no substantive hint disclosure at all.
        max_hint_level = 0 if body.mode == "test" else len(hints)

    context = tutor_service.TutorContext(
        principal_id=principal.id,
        topic_id=body.topic_id,
        mode=body.mode,
        run=run,
        step_index=body.step_index,
    )
    answer = tutor_service.answer(
        session, context, body.message, settings=settings, max_hint_level=max_hint_level
    )
    session.commit()
    return answer.as_dict()


@router.get("/tutor/conversations/{topic_key}", tags=["tutor"])
def read_conversation(
    topic_key: str,
    principal: Principal = Depends(require_principal),
    session: Session = Depends(db_session),
) -> dict[str, Any]:
    """Owner-scoped history. A guessed conversation key returns nothing else's data."""
    conversation = tutor_service.get_or_create_conversation(
        session, principal.id, None if topic_key == "general" else topic_key
    )
    rows = session.scalars(
        select(TutorTurn)
        .where(
            TutorTurn.conversation_id == conversation.id,
            TutorTurn.principal_id == uuid.UUID(principal.id),
        )
        .order_by(TutorTurn.created_at)
        .limit(50)
    )
    turns = [
        {
            "id": str(row.id),
            "role": row.role,
            "intent": row.intent,
            "content": row.content,
            "passage_ids": row.passage_ids,
            "fact_ids": row.fact_ids,
            "followup_question": row.followup_question,
            "run_id": str(row.run_id) if row.run_id else None,
            "run_step": row.run_step,
            "source_label": row.source_label,
            "provider_model": row.provider_model,
            "created_at": row.created_at.isoformat(),
        }
        for row in rows
    ]
    session.commit()
    return {"topic_key": topic_key, "turns": turns}


@router.get("/tutor/passages/{passage_id}", tags=["tutor"])
def read_passage(passage_id: str) -> dict[str, Any]:
    """Open a cited passage without discarding the learner's work."""
    passage = knowledge.get_passage(passage_id)
    if passage is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "not_found", "message": "No such course passage."},
        )
    return {
        "passage_id": passage.id,
        "title": passage.title,
        "heading": passage.heading,
        "version": passage.version,
        "text": passage.text,
        "sources": [{"title": title, "url": url} for title, url in passage.sources],
    }


@router.get("/tutor/hint-availability/{topic_id}", tags=["tutor"])
def hint_availability(
    topic_id: str,
    task_id: str,
    principal: Principal = Depends(require_principal),
    session: Session = Depends(db_session),
) -> dict[str, Any]:
    hints = loader.get_hints(topic_id)
    used = progress.hints_used(session, principal.id, task_id)
    session.commit()
    return {
        "topic_id": topic_id,
        "task_id": task_id,
        "levels_available": len(hints),
        "highest_level_delivered": used,
        "next_level": min(used + 1, len(hints)) if hints else 0,
    }
