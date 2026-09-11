"""Provider-neutral simulation interface.

Lessons, evaluators, and the API depend only on the types in this module, so a
different engine or a future hardware backend can be substituted without
changing course content.
"""

from __future__ import annotations

from typing import Literal, Protocol

from pydantic import BaseModel, Field

from app.quantum.spec import RunRequest

ResultKind = Literal[
    "ideal_circuit_simulation",
    "sampled_simulator_outcomes",
    "analytical_prediction",
    "conceptual_walkthrough",
]
"""Truthful result labels required by the visualization rules."""


class AmplitudeView(BaseModel):
    """One basis component of a state, with the sign/phase kept visible."""

    index: int
    label: str
    re: float
    im: float
    magnitude: float
    probability: float
    phase_radians: float | None = None
    """None when the magnitude is zero: an amplitude's phase is then undefined."""


class ReducedQubitState(BaseModel):
    """Single-qubit reduced state, used for honest local-state statements."""

    qubit: int
    bloch: tuple[float, float, float]
    bloch_length: float
    purity: float
    is_mixed: bool


class StateFrame(BaseModel):
    """A computed state at one step of one branch of a run."""

    step_index: int
    """0 is the declared preparation; k is the state after operations[k-1]."""

    branch_id: str
    branch_probability: float
    kind: Literal["preparation", "unitary", "measurement"]
    operation: str | None = None
    label: str
    amplitudes: list[AmplitudeView]
    probabilities: list[float]
    measured_outcome: int | None = None
    measured_qubit: int | None = None
    reduced_states: list[ReducedQubitState] = Field(default_factory=list)


class BranchSummary(BaseModel):
    """A conditional trajectory produced by mid-circuit measurement."""

    branch_id: str
    probability: float
    outcomes: list[int]
    """Recorded mid-circuit outcomes, in order."""


class RunResult(BaseModel):
    """Everything one computed run reports.

    Exact model probabilities, recorded conditional states, and sampled counts
    are separate fields; the UI must never present one as another.
    """

    result_kind: ResultKind = "ideal_circuit_simulation"
    engine: str
    engine_version: str
    circuit_schema_version: str
    qubits: int
    frames: list[StateFrame]
    branches: list[BranchSummary]
    exact_probabilities: list[float]
    """Ensemble Z-basis distribution over the final state, averaged across branches."""

    basis_labels: list[str]
    counts: dict[str, int]
    shots: int
    seed: int | None = None
    notes: list[str] = Field(default_factory=list)


class SimulationEngine(Protocol):
    """The contract every engine implementation satisfies."""

    name: str
    version: str

    def run(self, request: RunRequest) -> RunResult:
        """Compute one run of a validated circuit."""
        ...
