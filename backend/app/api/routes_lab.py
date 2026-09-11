"""Workspace, revision, run, task, hint, and preview routes."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api import schemas
from app.assessment import evaluator
from app.curriculum import loader, progress
from app.identity.dependencies import Principal, optional_principal, require_principal
from app.quantum import grover
from app.quantum.errors import CircuitRejected
from app.quantum.spec import ALLOWED_SHOT_COUNTS, CircuitSpec
from app.storage.database import db_session
from app.storage.models import TaskAttempt
from app.workspaces import service as workspaces

router = APIRouter()


def _reject(error: CircuitRejected) -> HTTPException:
    return HTTPException(
        status_code=422, detail={"code": error.reason_code, "message": error.message}
    )


def _not_found(message: str) -> HTTPException:
    # Ownership failures return 404 so a guessed identifier reveals nothing.
    return HTTPException(status_code=404, detail={"code": "not_found", "message": message})


@router.post("/revisions", tags=["lab"], status_code=201)
def create_revision(
    body: schemas.RevisionRequest,
    principal: Principal = Depends(require_principal),
    session: Session = Depends(db_session),
) -> dict[str, Any]:
    """Commit an edit. Every committed edit becomes a new immutable revision."""
    workspace = workspaces.get_or_create_workspace(session, principal.id, body.topic_id, body.kind)
    revision = workspaces.create_revision(session, principal.id, workspace, body.circuit)
    session.commit()
    return {
        "revision_id": str(revision.id),
        "workspace_id": str(workspace.id),
        "ordinal": revision.ordinal,
        "circuit": revision.circuit,
        "circuit_schema_version": revision.circuit_schema_version,
    }


@router.post("/runs", tags=["lab"], status_code=201)
def create_run(
    body: schemas.RunRequestBody,
    principal: Principal = Depends(require_principal),
    session: Session = Depends(db_session),
) -> dict[str, Any]:
    """Compute a new run. Each shot restarts the declared preparation."""
    if body.shots not in ALLOWED_SHOT_COUNTS:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "shots_not_allowed",
                "message": f"shots must be one of {list(ALLOWED_SHOT_COUNTS)}",
            },
        )
    try:
        revision = workspaces.load_revision(session, principal.id, body.revision_id)
    except workspaces.OwnershipError as error:
        raise _not_found(str(error)) from error
    try:
        run = workspaces.execute(
            session,
            principal.id,
            revision,
            shots=body.shots,
            seed=body.seed,
            label=body.label,
            context=body.context,
        )
    except CircuitRejected as error:
        raise _reject(error) from error
    session.commit()
    return _run_payload(run)


def _run_payload(run: Any) -> dict[str, Any]:
    return {
        "run_id": str(run.id),
        "revision_id": str(run.revision_id),
        "ordinal": run.ordinal,
        "label": run.label,
        "shots": run.shots,
        "seed": run.seed,
        "engine": run.engine,
        "engine_version": run.engine_version,
        "created_at": run.created_at.isoformat(),
        "result": run.result,
        "context": run.context,
    }


@router.get("/runs/{run_id}", tags=["lab"])
def read_run(
    run_id: str,
    principal: Principal = Depends(require_principal),
    session: Session = Depends(db_session),
) -> dict[str, Any]:
    """Replay reads a saved run, including the outcomes it actually recorded."""
    try:
        run = workspaces.load_run(session, principal.id, run_id)
    except workspaces.OwnershipError as error:
        raise _not_found(str(error)) from error
    session.commit()
    payload = _run_payload(run)
    payload["read_kind"] = "recorded_replay"
    payload["replay_note"] = (
        "These are the recorded results of a saved run. Replay is not a new "
        "measurement and does not reverse one."
    )
    return payload


@router.post("/runs/{run_id}/repeat-measurement", tags=["lab"])
def repeat_measurement(
    run_id: str,
    principal: Principal = Depends(require_principal),
    session: Session = Depends(db_session),
) -> dict[str, Any]:
    """Re-read the recorded conditional trajectory. Not a fresh shot."""
    try:
        run = workspaces.load_run(session, principal.id, run_id)
    except workspaces.OwnershipError as error:
        raise _not_found(str(error)) from error
    payload = workspaces.remeasure_recorded_trajectory(run)
    session.commit()
    return {"run_id": run_id, "operation_kind": "conditional_repeat_measurement", **payload}


@router.get("/topics/{topic_id}/runs", tags=["lab"])
def list_topic_runs(
    topic_id: str,
    limit: int = Query(default=10, ge=1, le=50),
    principal: Principal = Depends(require_principal),
    session: Session = Depends(db_session),
) -> dict[str, Any]:
    runs = workspaces.list_runs(session, principal.id, topic_id, limit=limit)
    session.commit()
    return {
        "runs": [
            {
                "run_id": str(run.id),
                "revision_id": str(run.revision_id),
                "ordinal": run.ordinal,
                "label": run.label,
                "shots": run.shots,
                "created_at": run.created_at.isoformat(),
                "result_kind": run.result.get("result_kind"),
                "exact_probabilities": run.result.get("exact_probabilities"),
                "counts": run.result.get("counts"),
            }
            for run in runs
        ]
    }


@router.post("/topics/{topic_id}/steps", tags=["progress"])
def complete_step(
    topic_id: str,
    body: schemas.StepCompletionRequest,
    principal: Principal = Depends(require_principal),
    session: Session = Depends(db_session),
) -> dict[str, Any]:
    topic = loader.get_topic(topic_id)
    if topic is None:
        raise _not_found("No such topic.")
    valid = {step["id"] for step in topic.get("steps", [])}
    if body.step_id not in valid:
        raise HTTPException(
            status_code=422,
            detail={"code": "unknown_step", "message": "That step is not part of this topic."},
        )
    progress.mark_step(session, principal.id, topic_id, body.step_id)
    row = progress.refresh_topic_status(session, principal.id, topic_id)
    session.commit()
    return {"topic_id": topic_id, "status": row.status, "completed_steps": row.completed_steps}


@router.post("/topics/{topic_id}/prediction", tags=["progress"])
def submit_prediction(
    topic_id: str,
    body: schemas.PredictionRequest,
    principal: Principal = Depends(require_principal),
    session: Session = Depends(db_session),
) -> dict[str, Any]:
    """A prediction is recorded for teaching feedback. A wrong one never fails a topic."""
    topic = loader.get_topic(topic_id)
    if topic is None:
        raise _not_found("No such topic.")
    progress.record_prediction(
        session,
        principal.id,
        topic_id,
        {"prediction_id": body.prediction_id, "selection": body.selection},
    )
    session.commit()
    return {
        "recorded": True,
        "topic_id": topic_id,
        "note": (
            "Your prediction is saved so the lesson can compare it with what you "
            "observe. An incorrect prediction does not affect completion or evidence."
        ),
    }


@router.post("/hints", tags=["hints"])
def request_hint(
    body: schemas.HintRequest,
    principal: Principal = Depends(require_principal),
    session: Session = Depends(db_session),
) -> dict[str, Any]:
    """Authored hints. Delivery is recorded so assisted success stays distinguishable."""
    hints = loader.get_hints(body.topic_id)
    if not hints:
        raise _not_found("No hints are authored for that topic.")
    match = next((hint for hint in hints if hint["level"] == body.level), None)
    if match is None:
        raise HTTPException(
            status_code=422,
            detail={"code": "unknown_hint_level", "message": "That hint level does not exist."},
        )
    progress.record_hint(session, principal.id, body.task_id, body.level)
    session.commit()
    note = (
        "This hint is recorded as assistance. Assisted success completes the practice "
        "activity; independent evidence comes from an unassisted item."
    )
    if body.level >= 4:
        note = (
            "This is the worked solution, recorded as assistance. Complete an equivalent "
            "new-input task to record independent evidence for this skill."
        )
    return {
        "level": match["level"],
        "text": match["text"],
        "hints_available": len(hints),
        "assistance_recorded": True,
        "note": note,
    }


@router.post("/tasks/{task_id}/attempts", tags=["tasks"])
def submit_task(
    task_id: str,
    body: schemas.TaskSubmission,
    principal: Principal = Depends(require_principal),
    session: Session = Depends(db_session),
) -> dict[str, Any]:
    """Evaluate one topic task deterministically and write evidence once."""
    found = loader.get_task(task_id)
    if found is None:
        raise _not_found("No such task.")
    topic, task = found
    rubrics = loader.load_task_rubrics()
    rubric = rubrics.get(task_id)
    if rubric is None:  # pragma: no cover - content validation prevents this
        raise _not_found("No rubric is authored for that task.")

    if body.idempotency_key:
        existing = session.scalar(
            select(TaskAttempt).where(
                TaskAttempt.principal_id == uuid.UUID(principal.id),
                TaskAttempt.idempotency_key == body.idempotency_key,
            )
        )
        if existing is not None:
            if existing.task_id != task_id:
                raise HTTPException(
                    status_code=409,
                    detail={
                        "code": "idempotency_key_reused",
                        "message": "That idempotency key was used for a different task.",
                    },
                )
            row = progress.refresh_topic_status(session, principal.id, topic["id"])
            session.commit()
            return {
                "task_id": task_id,
                "duplicate": True,
                "topic_status": row.status,
                **existing.evaluation,
            }

    circuit = None
    result = None
    run = None
    if body.run_id:
        try:
            run = workspaces.load_run(session, principal.id, body.run_id)
        except workspaces.OwnershipError as error:
            raise _not_found(str(error)) from error
        result = workspaces.result_of(run)
        stored = workspaces.load_revision(session, principal.id, str(run.revision_id))
        circuit = CircuitSpec.model_validate(stored.circuit)

    try:
        verdict = evaluator.evaluate(
            rubric,
            body.submission,
            circuit=circuit,
            result=result,
            assessed_skills=task.get("assessed_skills", []),
        )
    except CircuitRejected as error:
        raise _reject(error) from error

    hints_used = progress.hints_used(session, principal.id, task_id)
    assisted = hints_used >= 3
    evidence_kind = "independent" if (verdict.passed and not assisted) else "assisted"

    evaluation = verdict.as_dict()
    evaluation["hints_used"] = hints_used
    evaluation["assisted"] = assisted
    evaluation["evidence_kind"] = evidence_kind

    attempt = TaskAttempt(
        principal_id=uuid.UUID(principal.id),
        topic_id=topic["id"],
        task_id=task_id,
        content_version=loader.load_chapter("chapter-1").get("version", 1),
        run_id=run.id if run else None,
        submission=body.submission,
        evaluation=evaluation,
        passed=verdict.passed,
        assisted=assisted,
        idempotency_key=body.idempotency_key,
    )
    session.add(attempt)
    session.flush()

    if verdict.passed:
        progress.record_evidence(
            session,
            principal.id,
            skills=task.get("assessed_skills", []),
            kind=evidence_kind,
            item_family=task.get("item_family", task_id),
            source_kind="task",
            source_id=task_id,
        )
        records = task.get("records") or rubric.get("records")
        if records:
            progress.record_preview(
                session,
                principal.id,
                records["algorithm_id"],
                note=records.get("note"),
            )

    row = progress.refresh_topic_status(session, principal.id, topic["id"])
    required = topic["completion"]["required_task_ids"]
    passed_ids = progress.passed_task_ids(session, principal.id, topic["id"])
    next_task = next((item for item in required if item not in passed_ids), None)
    session.commit()

    return {
        "task_id": task_id,
        "duplicate": False,
        "topic_status": row.status,
        "next_task_id": next_task,
        **evaluation,
    }


@router.get("/grover/analysis", tags=["previews"])
def grover_analysis(candidates: int = Query(default=4)) -> dict[str, Any]:
    """Analytical prediction curve. Labelled as a formula evaluation, not a run."""
    if candidates not in grover.ALLOWED_CANDIDATE_COUNTS:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "unsupported_search_space",
                "message": f"N must be one of {list(grover.ALLOWED_CANDIDATE_COUNTS)}",
            },
        )
    rows = [
        {
            "iterations": k,
            "ideal_target_probability": grover.ideal_target_probability(candidates, k),
            "classical_check_and_guess": grover.classical_check_and_guess(candidates, k),
            "classical_checked_only": grover.classical_checked_only(candidates, k),
        }
        for k in range(grover.MAX_ITERATIONS + 1)
    ]
    return {
        "result_kind": "analytical_prediction",
        "candidates": candidates,
        "best_iterations": grover.best_iteration_count(candidates),
        "rows": rows,
        "classical_stopping_rules": grover.classical_average_checks(candidates),
        "assumptions": [
            "Ideal noiseless model.",
            "Exactly one marked candidate.",
            "Standard uniform initial preparation.",
            "The specified phase oracle and the usual diffusion operation.",
        ],
        "formula": "P(target) = sin^2((2k+1) * arcsin(1/sqrt(N)))",
        "note": (
            "These values come from the formula, not from a simulated circuit. They do "
            "not apply to a non-uniform initial preparation."
        ),
    }


@router.get("/grover/classical-trace", tags=["previews"])
def grover_classical_trace(
    candidates: int = Query(default=8), target: int = Query(default=5)
) -> dict[str, Any]:
    if candidates not in grover.ALLOWED_CANDIDATE_COUNTS or not 0 <= target < candidates:
        raise HTTPException(
            status_code=422,
            detail={"code": "invalid_parameters", "message": "Check N and the target."},
        )
    trace = grover.sequential_search_trace(candidates, target)
    return {
        "result_kind": "analytical_prediction",
        "candidates": candidates,
        "target": target,
        "trace": trace,
        "queries_used": len(trace),
        "stopping_rules": grover.classical_average_checks(candidates),
        "note": (
            "Each row is one use of the yes/no test, scanning in increasing order. The "
            "mean and worst case depend on which stopping rule is in use, so both are "
            "reported."
        ),
    }


@router.post("/grover/runs", tags=["previews"], status_code=201)
def grover_run(
    body: schemas.GroverRunRequest,
    principal: Principal = Depends(require_principal),
    session: Session = Depends(db_session),
) -> dict[str, Any]:
    """Run the bounded Grover preset through the ordinary engine."""
    settings_shots = body.shots
    if settings_shots not in ALLOWED_SHOT_COUNTS:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "shots_not_allowed",
                "message": f"shots must be one of {list(ALLOWED_SHOT_COUNTS)}",
            },
        )
    settings = grover.GroverSettings(
        candidates=body.candidates,
        target=body.target,
        iterations=body.iterations,
        preparation=body.preparation,
    )
    try:
        circuit = grover.build_circuit(settings)
    except CircuitRejected as error:
        raise _reject(error) from error

    workspace = workspaces.get_or_create_workspace(
        session, principal.id, "preview-grover", kind="preview"
    )
    revision = workspaces.create_revision(session, principal.id, workspace, circuit)
    run = workspaces.execute(
        session,
        principal.id,
        revision,
        shots=body.shots,
        seed=body.seed,
        label=f"Grover N={body.candidates} k={body.iterations}",
        context={
            "preview": "grover",
            "candidates": body.candidates,
            "target": body.target,
            "iterations": body.iterations,
            "preparation": body.preparation,
        },
    )
    progress.record_preview(
        session,
        principal.id,
        "grover",
        run_id=run.id,
        parameters={
            "candidates": body.candidates,
            "target": body.target,
            "iterations": body.iterations,
            "preparation": body.preparation,
            "shots": body.shots,
        },
    )
    session.commit()

    payload = _run_payload(run)
    payload["stages"] = grover.stage_boundaries(settings)
    payload["target"] = body.target
    payload["candidates"] = body.candidates
    if body.preparation == grover.PREPARATION_UNIFORM:
        payload["analytical_target_probability"] = grover.ideal_target_probability(
            body.candidates, body.iterations
        )
        payload["formula_applies"] = True
    else:
        payload["analytical_target_probability"] = None
        payload["formula_applies"] = False
        payload["formula_note"] = (
            "This run starts in |0...0> with no preparation, so the uniform-start "
            "success formula does not apply to it. The result below is the actual "
            "computed circuit, and it is not general amplitude amplification."
        )
    payload["oracle_query_count"] = body.iterations * body.shots
    payload["cost_note"] = (
        f"This histogram represents {body.shots} complete preparations and "
        f"{body.iterations * body.shots} phase-oracle uses, before any optional "
        f"candidate verification. It is not a single {body.iterations}-query search."
    )
    return payload


@router.post("/previews/{algorithm_id}/encounters", tags=["previews"])
def record_encounter(
    algorithm_id: str,
    body: schemas.PreviewEncounterRequest,
    principal: Principal = Depends(require_principal),
    session: Session = Depends(db_session),
) -> dict[str, Any]:
    """Record Seen for a preview. Seeing a preview never grants a higher level."""
    known = {entry["id"] for entry in loader.load_previews()["algorithms"]}
    if algorithm_id not in known:
        raise _not_found("No such preview.")
    run_uuid = None
    if body.run_id:
        try:
            run = workspaces.load_run(session, principal.id, body.run_id)
        except workspaces.OwnershipError as error:
            raise _not_found(str(error)) from error
        run_uuid = run.id
    row = progress.record_preview(
        session,
        principal.id,
        algorithm_id,
        run_id=run_uuid,
        parameters=body.parameters,
        note=body.note,
        reflection=body.reflection,
    )
    session.commit()
    return {
        "algorithm_id": algorithm_id,
        "status": row.status,
        "run_id": str(row.run_id) if row.run_id else None,
        "notes": row.notes,
        "note": (
            "Seen means you opened the preview and reached its main result. Can Explain "
            "and Mastered require the algorithm's own objectives, taught later."
        ),
    }


@router.get("/lab/catalog", tags=["previews"])
def lab_catalog(
    principal: Principal | None = Depends(optional_principal),
    session: Session = Depends(db_session),
) -> dict[str, Any]:
    previews = loader.load_previews()
    encounters = (
        {entry["algorithm_id"]: entry for entry in progress.preview_status(session, principal.id)}
        if principal is not None
        else {}
    )
    if principal is not None:
        session.commit()
    entries = []
    for algorithm in previews["algorithms"]:
        entries.append(
            {
                "id": algorithm["id"],
                "title": algorithm["title"],
                "kind": algorithm["kind"],
                "publication": algorithm["publication"],
                "summary": algorithm["summary"],
                "result_label": algorithm["result_label"],
                "status": encounters.get(algorithm["id"], {}).get("status"),
            }
        )
    for planned in previews["planned_lab_entries"]:
        entries.append({**planned, "status": None, "result_label": None})
    return {
        "entries": entries,
        "modes": previews["lab_modes"],
        "evidence_levels": previews["evidence_levels"],
        "evidence_note": previews["evidence_note"],
    }
