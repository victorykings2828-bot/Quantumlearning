"""Workspace, revision, and run operations.

An edit creates a new immutable revision. A run references exactly one
revision. Replay reads a saved run; it never recomputes and never resamples.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.config import get_settings
from app.quantum.errors import CircuitRejected
from app.quantum.interface import RunResult
from app.quantum.qiskit_engine import get_engine
from app.quantum.spec import CircuitSpec, RunRequest
from app.storage.models import Revision, Run, Workspace


class OwnershipError(PermissionError):
    """The requested resource does not belong to this principal."""


def _as_uuid(value: str) -> uuid.UUID | None:
    try:
        return uuid.UUID(str(value))
    except (ValueError, AttributeError, TypeError):
        return None


def get_or_create_workspace(
    session: Session, principal_id: str, topic_id: str, kind: str = "lesson"
) -> Workspace:
    owner = uuid.UUID(principal_id)
    workspace = session.scalar(
        select(Workspace).where(
            Workspace.principal_id == owner,
            Workspace.topic_id == topic_id,
            Workspace.kind == kind,
        )
    )
    if workspace is not None:
        return workspace
    # Same race as topic progress: insert, ignore a conflict, then re-select.
    session.execute(
        pg_insert(Workspace)
        .values(id=uuid.uuid4(), principal_id=owner, topic_id=topic_id, kind=kind)
        .on_conflict_do_nothing(constraint="uq_workspace_owner_topic")
    )
    session.flush()
    return session.scalar(
        select(Workspace).where(
            Workspace.principal_id == owner,
            Workspace.topic_id == topic_id,
            Workspace.kind == kind,
        )
    )


def load_workspace(session: Session, principal_id: str, workspace_id: str) -> Workspace:
    key = _as_uuid(workspace_id)
    workspace = session.get(Workspace, key) if key else None
    if workspace is None or str(workspace.principal_id) != principal_id:
        raise OwnershipError("workspace not found for this guest")
    return workspace


def create_revision(
    session: Session, principal_id: str, workspace: Workspace, circuit: CircuitSpec
) -> Revision:
    """Every committed edit becomes a new immutable revision."""
    highest = session.scalar(
        select(func.max(Revision.ordinal)).where(Revision.workspace_id == workspace.id)
    )
    revision = Revision(
        workspace_id=workspace.id,
        principal_id=uuid.UUID(principal_id),
        ordinal=(highest or 0) + 1,
        circuit=circuit.model_dump(mode="json"),
        circuit_schema_version=circuit.schema_version,
    )
    session.add(revision)
    session.flush()
    return revision


def load_revision(session: Session, principal_id: str, revision_id: str) -> Revision:
    key = _as_uuid(revision_id)
    revision = session.get(Revision, key) if key else None
    if revision is None or str(revision.principal_id) != principal_id:
        raise OwnershipError("revision not found for this guest")
    return revision


def load_run(session: Session, principal_id: str, run_id: str) -> Run:
    key = _as_uuid(run_id)
    run = session.get(Run, key) if key else None
    if run is None or str(run.principal_id) != principal_id:
        raise OwnershipError("run not found for this guest")
    return run


def execute(
    session: Session,
    principal_id: str,
    revision: Revision,
    shots: int,
    seed: int | None = None,
    label: str = "run",
    context: dict[str, Any] | None = None,
) -> Run:
    """Compute a new run. Each shot restarts the declared preparation."""
    settings = get_settings()
    circuit = CircuitSpec.model_validate(revision.circuit)
    if shots > settings.simulation_max_shots:
        raise CircuitRejected("shot_limit", f"at most {settings.simulation_max_shots} shots")
    if len(circuit.operations) > settings.simulation_max_operations:
        raise CircuitRejected(
            "operation_limit", f"at most {settings.simulation_max_operations} operations"
        )

    result = get_engine().run(RunRequest(circuit=circuit, shots=shots, seed=seed))
    highest = session.scalar(select(func.max(Run.ordinal)).where(Run.revision_id == revision.id))
    run = Run(
        principal_id=uuid.UUID(principal_id),
        revision_id=revision.id,
        ordinal=(highest or 0) + 1,
        label=label,
        shots=shots,
        seed=seed,
        engine=result.engine,
        engine_version=result.engine_version,
        result=result.model_dump(mode="json"),
        context=context or {},
    )
    session.add(run)
    session.flush()
    return run


def result_of(run: Run) -> RunResult:
    return RunResult.model_validate(run.result)


def remeasure_recorded_trajectory(run: Run, branch_id: str | None = None) -> dict[str, Any]:
    """Read the recorded conditional outcome again.

    This is not a new shot. An ideal same-basis measurement of an already
    measured trajectory repeats its recorded outcome with probability 1.
    """
    result = result_of(run)
    frames = [frame for frame in result.frames if frame.measured_outcome is not None]
    if branch_id is not None:
        frames = [frame for frame in frames if frame.branch_id == branch_id]
    if not frames:
        final = result.exact_probabilities
        definite = [index for index, value in enumerate(final) if abs(value - 1.0) < 1e-9]
        if not definite:
            return {
                "repeatable": False,
                "explanation": (
                    "This run has no recorded measurement outcome to repeat. Run a shot "
                    "first, then repeat the measurement of that trajectory."
                ),
            }
        return {
            "repeatable": True,
            "outcome_label": result.basis_labels[definite[0]],
            "probability": 1.0,
            "explanation": (
                "The final state is already a basis state, so an ideal Z measurement "
                "returns this outcome with probability 1."
            ),
        }
    frame = frames[-1]
    return {
        "repeatable": True,
        "outcome": frame.measured_outcome,
        "qubit": frame.measured_qubit,
        "branch_id": frame.branch_id,
        "probability": 1.0,
        "explanation": (
            "The recorded measurement left the qubit in that basis state. With no gate "
            "in between, repeating the same measurement returns the same outcome with "
            "probability 1. This is a different operation from a fresh shot."
        ),
    }


def list_runs(session: Session, principal_id: str, topic_id: str, limit: int = 20) -> list[Run]:
    owner = uuid.UUID(principal_id)
    statement = (
        select(Run)
        .join(Revision, Run.revision_id == Revision.id)
        .join(Workspace, Revision.workspace_id == Workspace.id)
        .where(Run.principal_id == owner, Workspace.topic_id == topic_id)
        .order_by(Run.created_at.desc())
        .limit(limit)
    )
    return list(session.scalars(statement))
