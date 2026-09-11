"""Bounded Grover preset builder and the analytical comparison model.

The builder emits an ordinary validated circuit, so preview runs are computed
by the same engine as every other experiment. The analytical helpers are
separate and are always labelled as formula evaluations, never as measurements.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from app.quantum.errors import CircuitRejected
from app.quantum.spec import CircuitSpec, InitialState, Operation

ALLOWED_CANDIDATE_COUNTS = (4, 8, 16)
MAX_ITERATIONS = 8

PREPARATION_UNIFORM = "uniform"
PREPARATION_MISSING = "missing"
ALLOWED_PREPARATIONS = (PREPARATION_UNIFORM, PREPARATION_MISSING)


@dataclass(frozen=True)
class GroverSettings:
    candidates: int
    target: int
    iterations: int
    preparation: str = PREPARATION_UNIFORM

    def qubits(self) -> int:
        return int(math.log2(self.candidates))


def validate(settings: GroverSettings) -> GroverSettings:
    if settings.candidates not in ALLOWED_CANDIDATE_COUNTS:
        raise CircuitRejected(
            "unsupported_search_space",
            f"the preview supports N in {list(ALLOWED_CANDIDATE_COUNTS)}",
        )
    if not 0 <= settings.target < settings.candidates:
        raise CircuitRejected("invalid_target", "the target must name an existing candidate")
    if not 0 <= settings.iterations <= MAX_ITERATIONS:
        raise CircuitRejected(
            "iteration_limit", f"the preview allows 0 to {MAX_ITERATIONS} iterations"
        )
    if settings.preparation not in ALLOWED_PREPARATIONS:
        raise CircuitRejected("invalid_preparation", "unknown preparation option")
    return settings


def _all_qubits(qubits: int) -> list[int]:
    return list(range(qubits))


def _phase_flip_on(target: int, qubits: int) -> list[Operation]:
    """Flip the phase of one basis state using X conjugation plus a controlled Z."""
    zeros = [q for q in range(qubits) if not (target >> q) & 1]
    operations = [Operation(op="x", targets=[q]) for q in zeros]
    controls = list(range(qubits - 1))
    if controls:
        operations.append(Operation(op="mcz", controls=controls, targets=[qubits - 1]))
    else:  # pragma: no cover - N >= 4 always has at least two qubits
        operations.append(Operation(op="z", targets=[0]))
    operations.extend(Operation(op="x", targets=[q]) for q in zeros)
    return operations


def oracle_operations(settings: GroverSettings) -> list[Operation]:
    return _phase_flip_on(settings.target, settings.qubits())


def diffusion_operations(qubits: int) -> list[Operation]:
    """Reflection about the uniform superposition."""
    operations = [Operation(op="h", targets=[q]) for q in _all_qubits(qubits)]
    operations.extend(_phase_flip_on(0, qubits))
    operations.extend(Operation(op="h", targets=[q]) for q in _all_qubits(qubits))
    return operations


def build_circuit(settings: GroverSettings) -> CircuitSpec:
    settings = validate(settings)
    qubits = settings.qubits()
    operations: list[Operation] = []
    if settings.preparation == PREPARATION_UNIFORM:
        operations.extend(Operation(op="h", targets=[q]) for q in _all_qubits(qubits))
    for _ in range(settings.iterations):
        operations.extend(oracle_operations(settings))
        operations.extend(diffusion_operations(qubits))
    return CircuitSpec(
        qubits=qubits,
        initial_state=InitialState(kind="basis", basis_index=0),
        operations=operations,
    )


def stage_boundaries(settings: GroverSettings) -> list[dict[str, int | str]]:
    """Step indices that separate preparation, oracle, and diffusion blocks."""
    qubits = settings.qubits()
    stages: list[dict[str, int | str]] = []
    cursor = 0
    if settings.preparation == PREPARATION_UNIFORM:
        cursor += qubits
        stages.append({"name": "Prepare uniform superposition", "end_step": cursor})
    else:
        stages.append({"name": "No preparation (starts in |0...0>)", "end_step": 0})
    oracle_length = len(oracle_operations(settings))
    diffusion_length = len(diffusion_operations(qubits))
    for iteration in range(1, settings.iterations + 1):
        cursor += oracle_length
        stages.append({"name": f"Oracle {iteration}", "end_step": cursor})
        cursor += diffusion_length
        stages.append({"name": f"Diffusion {iteration}", "end_step": cursor})
    return stages


def ideal_target_probability(candidates: int, iterations: int) -> float:
    """P(target) = sin^2((2k+1)theta), theta = arcsin(1/sqrt(N)).

    Valid only for the standard uniform preparation with exactly one marked
    candidate and the standard diffusion operator.
    """
    theta = math.asin(1.0 / math.sqrt(candidates))
    return math.sin((2 * iterations + 1) * theta) ** 2


def best_iteration_count(candidates: int) -> int:
    """The integer iteration count nearest the first probability peak."""
    theta = math.asin(1.0 / math.sqrt(candidates))
    ideal = math.pi / (4 * theta) - 0.5
    candidates_to_test = {max(0, math.floor(ideal)), max(0, math.ceil(ideal))}
    return max(candidates_to_test, key=lambda k: ideal_target_probability(candidates, k))


def classical_check_and_guess(candidates: int, queries: int) -> float:
    """Success probability of checking q distinct labels then guessing one more.

    (q+1)/N for a uniformly located target, capped at 1.
    """
    if queries >= candidates - 1:
        return 1.0
    return (queries + 1) / candidates


def classical_checked_only(candidates: int, queries: int) -> float:
    """Success probability when only a confirmed check counts: q/N."""
    return min(queries, candidates) / candidates


def sequential_search_trace(candidates: int, target: int) -> list[dict[str, object]]:
    """The actual classical checks performed when scanning in increasing order."""
    trace: list[dict[str, object]] = []
    for index in range(candidates):
        found = index == target
        trace.append({"query": index + 1, "candidate": index, "matches": found})
        if found:
            break
    return trace


def classical_average_checks(candidates: int) -> dict[str, float]:
    """Two clearly separated stopping rules for sequential search."""
    return {
        "checks_every_candidate_mean": (candidates + 1) / 2,
        "checks_every_candidate_worst": float(candidates),
        "uses_promise_mean": (sum(range(1, candidates)) + (candidates - 1)) / candidates,
        "uses_promise_worst": float(candidates - 1),
    }
