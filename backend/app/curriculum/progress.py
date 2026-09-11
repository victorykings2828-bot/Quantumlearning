"""Progress, evidence, and readiness computation.

Three records are kept apart: activity completion (possibly with help),
independent evidence (an unassisted success on a new item), and review
recommendations. Pressing Run is not understanding, and asking for a hint is
not a failure.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.curriculum import access, loader
from app.storage.models import (
    DeliveredHint,
    PreviewEncounter,
    SkillEvidence,
    TaskAttempt,
    TopicProgress,
)


def evidence_records(session: Session, principal_id: str) -> list[access.EvidenceRecord]:
    rows = session.scalars(
        select(SkillEvidence).where(SkillEvidence.principal_id == uuid.UUID(principal_id))
    )
    return [
        access.EvidenceRecord(skill_id=row.skill_id, kind=row.kind, item_family=row.item_family)
        for row in rows
    ]


def get_topic_progress(session: Session, principal_id: str, topic_id: str) -> TopicProgress:
    owner = uuid.UUID(principal_id)
    row = session.scalar(
        select(TopicProgress).where(
            TopicProgress.principal_id == owner, TopicProgress.topic_id == topic_id
        )
    )
    if row is None:
        row = TopicProgress(
            principal_id=owner,
            topic_id=topic_id,
            content_version=loader.load_chapter("chapter-1").get("version", 1),
            completed_steps={},
        )
        session.add(row)
        session.flush()
    return row


def mark_step(session: Session, principal_id: str, topic_id: str, step_id: str) -> TopicProgress:
    row = get_topic_progress(session, principal_id, topic_id)
    steps = dict(row.completed_steps or {})
    steps[step_id] = True
    row.completed_steps = steps
    if row.status == "not_started":
        row.status = "in_progress"
    session.flush()
    return row


def record_prediction(
    session: Session, principal_id: str, topic_id: str, prediction: dict[str, Any]
) -> TopicProgress:
    """A prediction is recorded for teaching feedback. A wrong one never fails a topic."""
    row = get_topic_progress(session, principal_id, topic_id)
    row.prediction = prediction
    if row.status == "not_started":
        row.status = "in_progress"
    session.flush()
    return row


def hints_used(session: Session, principal_id: str, task_id: str) -> int:
    rows = session.scalars(
        select(DeliveredHint).where(
            DeliveredHint.principal_id == uuid.UUID(principal_id),
            DeliveredHint.task_id == task_id,
        )
    )
    levels = [row.level for row in rows]
    return max(levels) if levels else 0


def record_hint(session: Session, principal_id: str, task_id: str, level: int) -> None:
    existing = session.scalar(
        select(DeliveredHint).where(
            DeliveredHint.principal_id == uuid.UUID(principal_id),
            DeliveredHint.task_id == task_id,
            DeliveredHint.level == level,
        )
    )
    if existing is None:
        session.add(
            DeliveredHint(principal_id=uuid.UUID(principal_id), task_id=task_id, level=level)
        )
        session.flush()


def record_evidence(
    session: Session,
    principal_id: str,
    *,
    skills: list[str],
    kind: str,
    item_family: str,
    source_kind: str,
    source_id: str,
    content_version: int = 1,
) -> list[SkillEvidence]:
    """Write evidence once per (skill, source). Duplicates never add mastery."""
    owner = uuid.UUID(principal_id)
    written: list[SkillEvidence] = []
    for skill_id in skills:
        existing = session.scalar(
            select(SkillEvidence).where(
                SkillEvidence.principal_id == owner,
                SkillEvidence.skill_id == skill_id,
                SkillEvidence.source_kind == source_kind,
                SkillEvidence.source_id == source_id,
            )
        )
        if existing is not None:
            continue
        row = SkillEvidence(
            principal_id=owner,
            skill_id=skill_id,
            kind=kind,
            item_family=item_family,
            source_kind=source_kind,
            source_id=source_id,
            content_version=content_version,
        )
        session.add(row)
        written.append(row)
    session.flush()
    return written


def passed_task_ids(session: Session, principal_id: str, topic_id: str) -> set[str]:
    rows = session.scalars(
        select(TaskAttempt).where(
            TaskAttempt.principal_id == uuid.UUID(principal_id),
            TaskAttempt.topic_id == topic_id,
            TaskAttempt.passed.is_(True),
        )
    )
    return {row.task_id for row in rows}


def refresh_topic_status(session: Session, principal_id: str, topic_id: str) -> TopicProgress:
    topic = loader.get_topic(topic_id)
    row = get_topic_progress(session, principal_id, topic_id)
    if topic is None:
        return row
    completion = topic.get("completion", {})
    required_steps = set(completion.get("required_step_ids", []))
    required_tasks = set(completion.get("required_task_ids", []))
    done_steps = {key for key, value in (row.completed_steps or {}).items() if value}
    done_tasks = passed_task_ids(session, principal_id, topic_id)
    if required_steps <= done_steps and required_tasks <= done_tasks:
        row.status = "complete"
    elif done_steps or done_tasks:
        row.status = "in_progress"
    session.flush()
    return row


def topic_summary(session: Session, principal_id: str, topic: dict[str, Any]) -> dict[str, Any]:
    row = get_topic_progress(session, principal_id, topic["id"])
    completion = topic.get("completion", {})
    required_steps = completion.get("required_step_ids", [])
    required_tasks = completion.get("required_task_ids", [])
    done_steps = {key for key, value in (row.completed_steps or {}).items() if value}
    done_tasks = passed_task_ids(session, principal_id, topic["id"])
    return {
        "topic_id": topic["id"],
        "number": topic["number"],
        "title": topic["title"],
        "slug": topic["slug"],
        "status": row.status,
        "steps_completed": len(done_steps & set(required_steps)),
        "steps_required": len(required_steps),
        "tasks_passed": len(done_tasks & set(required_tasks)),
        "tasks_required": len(required_tasks),
        "skills": topic.get("skills", []),
        "prerequisite_skills": topic.get("prerequisite_skills", []),
        "estimated_minutes": topic.get("estimated_minutes"),
    }


def chapter_progress(session: Session, principal_id: str) -> dict[str, Any]:
    chapter = loader.load_chapter("chapter-1")
    summaries = [topic_summary(session, principal_id, topic) for topic in chapter["topics"]]
    complete = [entry for entry in summaries if entry["status"] == "complete"]
    records = evidence_records(session, principal_id)
    demonstrated = access.demonstrated_skills(records)
    all_skills = sorted(loader.all_skills())
    return {
        "chapter_id": chapter["id"],
        "topics": summaries,
        "topics_complete": len(complete),
        "topics_total": len(summaries),
        "skills": [
            {
                "skill_id": skill,
                "demonstrated": skill in demonstrated,
                "independent_count": sum(
                    1
                    for record in records
                    if record.skill_id == skill and record.kind == "independent"
                ),
                "assisted_count": sum(
                    1
                    for record in records
                    if record.skill_id == skill and record.kind == "assisted"
                ),
                "item_families": sorted(
                    {
                        record.item_family
                        for record in records
                        if record.skill_id == skill and record.kind == "independent"
                    }
                ),
                "required_independent": access.REQUIRED_INDEPENDENT_EVIDENCE,
                "required_families": access.REQUIRED_DISTINCT_FAMILIES,
            }
            for skill in all_skills
        ],
        "next_topic_id": next(
            (entry["topic_id"] for entry in summaries if entry["status"] != "complete"), None
        ),
    }


def preview_status(session: Session, principal_id: str) -> list[dict[str, Any]]:
    rows = session.scalars(
        select(PreviewEncounter).where(PreviewEncounter.principal_id == uuid.UUID(principal_id))
    )
    return [
        {
            "algorithm_id": row.algorithm_id,
            "status": row.status,
            "run_id": str(row.run_id) if row.run_id else None,
            "parameters": row.parameters,
            "notes": row.notes,
            "reflection": row.reflection,
        }
        for row in rows
    ]


def record_preview(
    session: Session,
    principal_id: str,
    algorithm_id: str,
    *,
    run_id: uuid.UUID | None = None,
    parameters: dict[str, Any] | None = None,
    note: str | None = None,
    reflection: str | None = None,
) -> PreviewEncounter:
    owner = uuid.UUID(principal_id)
    row = session.scalar(
        select(PreviewEncounter).where(
            PreviewEncounter.principal_id == owner,
            PreviewEncounter.algorithm_id == algorithm_id,
        )
    )
    if row is None:
        row = PreviewEncounter(
            principal_id=owner, algorithm_id=algorithm_id, status="seen", notes=[]
        )
        session.add(row)
    if run_id is not None:
        row.run_id = run_id
    if parameters:
        row.parameters = parameters
    if note and note not in (row.notes or []):
        row.notes = [*(row.notes or []), note]
    if reflection is not None:
        row.reflection = reflection
    session.flush()
    return row
