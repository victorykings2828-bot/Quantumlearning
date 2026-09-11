"""Database schema.

Identity is kept separate from evidence: a future account can claim a guest
principal without rewriting progress rows. Every learner-owned row carries a
principal_id so ownership is enforced server-side.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def _uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Principal(Base, TimestampMixin):
    """A learner identity. Guest today; an account can attach later."""

    __tablename__ = "principals"

    id: Mapped[uuid.UUID] = _uuid_pk()
    kind: Mapped[str] = mapped_column(String(16), nullable=False, default="guest")
    account_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    sessions: Mapped[list[GuestSession]] = relationship(back_populates="principal")


class GuestSession(Base, TimestampMixin):
    """Only the hash of the session token is stored."""

    __tablename__ = "guest_sessions"

    id: Mapped[uuid.UUID] = _uuid_pk()
    principal_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("principals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    csrf_token: Mapped[str] = mapped_column(String(64), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    principal: Mapped[Principal] = relationship(back_populates="sessions")


class Preference(Base, TimestampMixin):
    __tablename__ = "preferences"

    principal_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("principals.id", ondelete="CASCADE"), primary_key=True
    )
    data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)


class ContentVersion(Base, TimestampMixin):
    """Records which authored content version produced a learner record."""

    __tablename__ = "content_versions"

    id: Mapped[uuid.UUID] = _uuid_pk()
    content_id: Mapped[str] = mapped_column(String(128), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)

    __table_args__ = (UniqueConstraint("content_id", "version", name="uq_content_version"),)


class TopicProgress(Base, TimestampMixin):
    __tablename__ = "topic_progress"

    id: Mapped[uuid.UUID] = _uuid_pk()
    principal_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("principals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    topic_id: Mapped[str] = mapped_column(String(64), nullable=False)
    content_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="not_started")
    completed_steps: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    prediction: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    __table_args__ = (UniqueConstraint("principal_id", "topic_id", name="uq_topic_progress_owner"),)


class Workspace(Base, TimestampMixin):
    __tablename__ = "workspaces"

    id: Mapped[uuid.UUID] = _uuid_pk()
    principal_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("principals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    topic_id: Mapped[str] = mapped_column(String(64), nullable=False)
    kind: Mapped[str] = mapped_column(String(24), nullable=False, default="lesson")

    revisions: Mapped[list[Revision]] = relationship(back_populates="workspace")

    __table_args__ = (
        UniqueConstraint("principal_id", "topic_id", "kind", name="uq_workspace_owner_topic"),
    )


class Revision(Base, TimestampMixin):
    """An immutable circuit revision. Editing creates a new row."""

    __tablename__ = "revisions"

    id: Mapped[uuid.UUID] = _uuid_pk()
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    principal_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("principals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    circuit: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    circuit_schema_version: Mapped[str] = mapped_column(String(32), nullable=False)

    workspace: Mapped[Workspace] = relationship(back_populates="revisions")

    __table_args__ = (UniqueConstraint("workspace_id", "ordinal", name="uq_revision_ordinal"),)


class Run(Base, TimestampMixin):
    """One computed experiment, tied to exactly one revision."""

    __tablename__ = "runs"

    id: Mapped[uuid.UUID] = _uuid_pk()
    principal_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("principals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    revision_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("revisions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    label: Mapped[str] = mapped_column(String(64), nullable=False, default="run")
    shots: Mapped[int] = mapped_column(Integer, nullable=False)
    seed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    engine: Mapped[str] = mapped_column(String(48), nullable=False)
    engine_version: Mapped[str] = mapped_column(String(32), nullable=False)
    result: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    context: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)


class TaskAttempt(Base, TimestampMixin):
    """A submission against one authored topic task, with its evaluation."""

    __tablename__ = "task_attempts"

    id: Mapped[uuid.UUID] = _uuid_pk()
    principal_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("principals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    topic_id: Mapped[str] = mapped_column(String(64), nullable=False)
    task_id: Mapped[str] = mapped_column(String(96), nullable=False)
    content_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    run_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("runs.id", ondelete="SET NULL"), nullable=True
    )
    submission: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    evaluation: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    assisted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    idempotency_key: Mapped[str | None] = mapped_column(String(64), nullable=True)

    __table_args__ = (
        UniqueConstraint("principal_id", "idempotency_key", name="uq_task_attempt_idempotency"),
        Index("ix_task_attempt_owner_task", "principal_id", "task_id"),
    )


class AssessmentAttempt(Base, TimestampMixin):
    """One chapter assessment attempt in practice or test mode."""

    __tablename__ = "assessment_attempts"

    id: Mapped[uuid.UUID] = _uuid_pk()
    principal_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("principals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    assessment_id: Mapped[str] = mapped_column(String(64), nullable=False)
    form: Mapped[str] = mapped_column(String(8), nullable=False)
    mode: Mapped[str] = mapped_column(String(16), nullable=False, default="test")
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="in_progress")
    content_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    answers: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    idempotency_key: Mapped[str | None] = mapped_column(String(64), nullable=True)

    __table_args__ = (
        UniqueConstraint("principal_id", "idempotency_key", name="uq_assessment_idempotency"),
    )


class Evaluation(Base, TimestampMixin):
    """The single authoritative evaluation written for a submitted attempt."""

    __tablename__ = "evaluations"

    id: Mapped[uuid.UUID] = _uuid_pk()
    principal_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("principals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    attempt_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("assessment_attempts.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    score: Mapped[float] = mapped_column(Float, nullable=False)
    max_score: Mapped[float] = mapped_column(Float, nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    detail: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    rubric_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class SkillEvidence(Base, TimestampMixin):
    """Evidence for one skill. Assisted and independent are distinct kinds."""

    __tablename__ = "skill_evidence"

    id: Mapped[uuid.UUID] = _uuid_pk()
    principal_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("principals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    skill_id: Mapped[str] = mapped_column(String(64), nullable=False)
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    item_family: Mapped[str] = mapped_column(String(64), nullable=False)
    source_kind: Mapped[str] = mapped_column(String(24), nullable=False)
    source_id: Mapped[str] = mapped_column(String(96), nullable=False)
    content_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    __table_args__ = (
        UniqueConstraint(
            "principal_id", "skill_id", "source_kind", "source_id", name="uq_evidence_source"
        ),
        Index("ix_evidence_owner_skill", "principal_id", "skill_id"),
    )


class PreviewEncounter(Base, TimestampMixin):
    """Seen status for an algorithm preview, with the inspected run."""

    __tablename__ = "preview_encounters"

    id: Mapped[uuid.UUID] = _uuid_pk()
    principal_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("principals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    algorithm_id: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="seen")
    run_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("runs.id", ondelete="SET NULL"), nullable=True
    )
    parameters: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    notes: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    reflection: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    __table_args__ = (UniqueConstraint("principal_id", "algorithm_id", name="uq_preview_owner"),)


class Conversation(Base, TimestampMixin):
    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = _uuid_pk()
    principal_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("principals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    topic_id: Mapped[str] = mapped_column(String(64), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class TutorTurn(Base, TimestampMixin):
    __tablename__ = "tutor_turns"

    id: Mapped[uuid.UUID] = _uuid_pk()
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    principal_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("principals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    intent: Mapped[str | None] = mapped_column(String(16), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    passage_ids: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    fact_ids: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    followup_question: Mapped[str | None] = mapped_column(Text, nullable=True)
    run_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("runs.id", ondelete="SET NULL"), nullable=True
    )
    run_step: Mapped[int | None] = mapped_column(Integer, nullable=True)
    topic_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    provider: Mapped[str | None] = mapped_column(String(24), nullable=True)
    provider_model: Mapped[str | None] = mapped_column(String(96), nullable=True)
    policy_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_label: Mapped[str | None] = mapped_column(String(32), nullable=True)


class DeliveredHint(Base, TimestampMixin):
    __tablename__ = "delivered_hints"

    id: Mapped[uuid.UUID] = _uuid_pk()
    principal_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("principals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    task_id: Mapped[str] = mapped_column(String(96), nullable=False)
    level: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (
        UniqueConstraint("principal_id", "task_id", "level", name="uq_hint_owner_level"),
    )


class QuotaCounter(Base):
    """Sliding-window counters for tutor and simulation budgets."""

    __tablename__ = "quota_counters"

    id: Mapped[uuid.UUID] = _uuid_pk()
    scope: Mapped[str] = mapped_column(String(24), nullable=False)
    key: Mapped[str] = mapped_column(String(128), nullable=False)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    __table_args__ = (UniqueConstraint("scope", "key", "window_start", name="uq_quota_window"),)
