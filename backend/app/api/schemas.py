"""Request and response models for the public API."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field

from app.quantum.spec import ALLOWED_SHOT_COUNTS, CircuitSpec


class GuestSessionResponse(BaseModel):
    principal_id: str
    created: bool
    expires_at: str
    csrf_token: str
    disclosure: str


class MeResponse(BaseModel):
    principal_id: str
    expires_at: str
    next_topic_id: str | None
    topics_complete: int
    topics_total: int
    disclosure: str


class ErrorDetail(BaseModel):
    code: str
    message: str


class RevisionRequest(BaseModel):
    topic_id: str
    circuit: CircuitSpec
    kind: str = "lesson"


class RevisionResponse(BaseModel):
    revision_id: str
    workspace_id: str
    ordinal: int
    circuit: dict[str, Any]
    circuit_schema_version: str


class RunRequestBody(BaseModel):
    revision_id: str
    shots: Annotated[int, Field(ge=1)] = 1
    seed: int | None = None
    label: str = "run"
    context: dict[str, Any] = Field(default_factory=dict)

    model_config = {"json_schema_extra": {"allowed_shots": list(ALLOWED_SHOT_COUNTS)}}


class RunResponse(BaseModel):
    run_id: str
    revision_id: str
    ordinal: int
    label: str
    shots: int
    seed: int | None
    engine: str
    engine_version: str
    created_at: str
    result: dict[str, Any]


class RunSummary(BaseModel):
    run_id: str
    revision_id: str
    ordinal: int
    label: str
    shots: int
    created_at: str
    result_kind: str
    exact_probabilities: list[float]
    counts: dict[str, int]


class RemeasureResponse(BaseModel):
    run_id: str
    repeatable: bool
    outcome: int | None = None
    outcome_label: str | None = None
    qubit: int | None = None
    branch_id: str | None = None
    probability: float | None = None
    explanation: str
    operation_kind: Literal["conditional_repeat_measurement"] = "conditional_repeat_measurement"


class StepCompletionRequest(BaseModel):
    step_id: str


class PredictionRequest(BaseModel):
    prediction_id: str
    selection: str


class TaskSubmission(BaseModel):
    submission: dict[str, Any] = Field(default_factory=dict)
    run_id: str | None = None
    idempotency_key: str | None = None


class TaskResult(BaseModel):
    task_id: str
    passed: bool
    reason_code: str
    message: str
    detail: dict[str, Any]
    assisted: bool
    evidence_kind: str
    hints_used: int
    duplicate: bool = False
    topic_status: str
    next_task_id: str | None = None


class HintRequest(BaseModel):
    topic_id: str
    task_id: str
    level: Annotated[int, Field(ge=1, le=4)]


class HintResponse(BaseModel):
    level: int
    text: str
    hints_available: int
    assistance_recorded: bool
    note: str


class AssessmentStartRequest(BaseModel):
    form: Literal["A", "B"]
    mode: Literal["test", "practice"] = "test"
    idempotency_key: str | None = None


class AssessmentAttemptResponse(BaseModel):
    attempt_id: str
    form: str
    mode: str
    status: str
    answers: dict[str, Any]
    items: list[dict[str, Any]]
    pass_policy: dict[str, Any]
    test_mode_help: str


class AssessmentAnswersRequest(BaseModel):
    answers: dict[str, Any]


class AssessmentSubmitRequest(BaseModel):
    idempotency_key: str | None = None


class AssessmentResultResponse(BaseModel):
    attempt_id: str
    score: float
    max_score: float
    passed: bool
    essential_items_passed: bool
    per_item: list[dict[str, Any]]
    revision_guidance: list[dict[str, str]]
    duplicate: bool = False


class GroverRunRequest(BaseModel):
    candidates: Literal[4, 8, 16] = 4
    target: Annotated[int, Field(ge=0, le=15)] = 2
    iterations: Annotated[int, Field(ge=0, le=8)] = 1
    shots: Annotated[int, Field(ge=1)] = 256
    preparation: Literal["uniform", "missing"] = "uniform"
    seed: int | None = None


class PreviewEncounterRequest(BaseModel):
    run_id: str | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)
    note: str | None = None
    reflection: str | None = None


class TutorTurnRequest(BaseModel):
    message: Annotated[str, Field(min_length=1, max_length=2000)]
    topic_id: str | None = None
    run_id: str | None = None
    step_index: int | None = None
    mode: Literal["test", "practice"] = "practice"
    client_revision_id: str | None = None


class TutorTurnResponse(BaseModel):
    intent: str
    answer_markdown: str
    citations: list[dict[str, Any]]
    fact_ids: list[str]
    facts: list[dict[str, Any]]
    followup_question: str | None
    source_label: str
    provider: str | None
    provider_model: str | None
    latency_ms: int | None
    scope_reason: str
    run_id: str | None
    run_label: str | None
    step_index: int | None
    notice: str | None
    policy_version: int
