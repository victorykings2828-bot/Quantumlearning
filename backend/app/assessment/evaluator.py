"""The authored evaluator.

It reads a private rubric and the authoritative engine result, and returns a
verdict. Nothing here consults a language model, and a random sample frequency
never decides whether an exact probability target was met.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any

from app.quantum.compare import distributions_equal, states_equivalent
from app.quantum.errors import CircuitRejected
from app.quantum.interface import RunResult
from app.quantum.spec import CircuitSpec

DEFAULT_NUMERIC_TOLERANCE = 0.001


@dataclass
class Verdict:
    passed: bool
    reason_code: str
    message: str
    detail: dict[str, Any] = field(default_factory=dict)
    assessed_skills: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "reason_code": self.reason_code,
            "message": self.message,
            "detail": self.detail,
            "assessed_skills": self.assessed_skills,
        }


def parse_number(raw: Any) -> float | None:
    """Accept a decimal, a fraction such as 16/25, or a percentage."""
    if isinstance(raw, int | float):
        return float(raw)
    if not isinstance(raw, str):
        return None
    text = raw.strip().replace(" ", "")
    if not text:
        return None
    percent = text.endswith("%")
    if percent:
        text = text[:-1]
    try:
        value = float(Fraction(text))
    except (ValueError, ZeroDivisionError):
        return None
    return value / 100.0 if percent else value


def _numeric_fields(submission: dict[str, Any], rubric: dict[str, Any]) -> Verdict:
    key: dict[str, float] = rubric["key"]
    tolerance = float(rubric.get("tolerance", DEFAULT_NUMERIC_TOLERANCE))
    answers = submission.get("values", {}) or {}
    per_field: dict[str, Any] = {}
    passed = True
    for field_id, expected in key.items():
        supplied = parse_number(answers.get(field_id))
        if supplied is None:
            per_field[field_id] = {"ok": False, "reason": "unreadable_number"}
            passed = False
            continue
        ok = abs(supplied - float(expected)) <= tolerance
        per_field[field_id] = {"ok": ok, "supplied": supplied}
        passed = passed and ok
    return Verdict(
        passed=passed,
        reason_code="numeric_match" if passed else "numeric_mismatch",
        message="",
        detail={"fields": per_field, "tolerance": tolerance},
    )


def _single_select(submission: dict[str, Any], rubric: dict[str, Any]) -> Verdict:
    chosen = submission.get("selection")
    passed = chosen == rubric["key"]
    return Verdict(
        passed=passed,
        reason_code="selection_match" if passed else "selection_mismatch",
        message="",
        detail={"selection": chosen},
    )


def _mapping(submission: dict[str, Any], rubric: dict[str, Any], field_name: str) -> Verdict:
    key: dict[str, str] = rubric["key"]
    supplied = submission.get(field_name, {}) or {}
    per_item = {
        item: {"ok": supplied.get(item) == expected, "supplied": supplied.get(item)}
        for item, expected in key.items()
    }
    passed = all(entry["ok"] for entry in per_item.values())
    return Verdict(
        passed=passed,
        reason_code="mapping_match" if passed else "mapping_mismatch",
        message="",
        detail={"items": per_item, "all_required": True},
    )


def _compound(submission: dict[str, Any], rubric: dict[str, Any]) -> Verdict:
    key: dict[str, str] = rubric["key"]
    supplied = submission.get("parts", {}) or {}
    per_part = {
        part: {"ok": supplied.get(part) == expected, "supplied": supplied.get(part)}
        for part, expected in key.items()
    }
    passed = all(entry["ok"] for entry in per_part.values())
    return Verdict(
        passed=passed,
        reason_code="compound_match" if passed else "compound_mismatch",
        message="",
        detail={"parts": per_part, "all_required": True},
    )


def check_constraints(circuit: CircuitSpec, constraints: dict[str, Any]) -> str | None:
    """Return a reason code when the circuit breaks a published constraint."""
    allowed = constraints.get("allowed_operations")
    operations = [operation.op for operation in circuit.operations]
    gate_operations = [op for op in operations if op != "measure_z"]

    if constraints.get("forbid_measurement") and "measure_z" in operations:
        return "measurement_not_allowed"
    if allowed is not None:
        for op in gate_operations:
            if op not in allowed:
                return "operation_not_allowed"
    maximum = constraints.get("max_operations")
    if maximum is not None and len(gate_operations) > int(maximum):
        return "too_many_operations"
    minimum = constraints.get("min_operations")
    if minimum is not None and len(gate_operations) < int(minimum):
        return "too_few_operations"

    expected_initial = constraints.get("initial_state")
    if expected_initial is not None:
        actual = circuit.initial_state
        if expected_initial == "ket0":
            ok = actual.kind == "basis" and actual.basis_index == 0
        elif expected_initial == "ket1":
            ok = (actual.kind == "basis" and actual.basis_index == 1) or (
                actual.kind == "named" and actual.named == "ket1"
            )
        else:
            ok = actual.kind == "named" and actual.named == expected_initial
        if not ok:
            return "wrong_initial_state"

    prefix = constraints.get("fixed_prefix")
    if prefix and gate_operations[: len(prefix)] != list(prefix):
        return "fixed_prefix_missing"
    suffix = constraints.get("fixed_suffix")
    if suffix and gate_operations[-len(suffix) :] != list(suffix):
        return "fixed_suffix_missing"
    return None


def _final_state(result: RunResult) -> list[complex]:
    """The final statevector of the single deterministic branch."""
    if len(result.branches) != 1:
        raise CircuitRejected(
            "branching_state_goal",
            "a state goal cannot be evaluated on a circuit containing a measurement",
        )
    branch_id = result.branches[0].branch_id
    final = [frame for frame in result.frames if frame.branch_id == branch_id]
    frame = final[-1]
    return [complex(view.re, view.im) for view in frame.amplitudes]


def _circuit_goal(circuit: CircuitSpec, result: RunResult, rubric: dict[str, Any]) -> Verdict:
    constraints = rubric.get("constraints", {})
    violation = check_constraints(circuit, constraints)
    if violation is not None:
        return Verdict(
            passed=False,
            reason_code=violation,
            message="",
            detail={"constraints": constraints},
        )

    goal_kind = rubric.get("goal_kind", "distribution")
    if goal_kind == "distribution":
        target = [float(value) for value in rubric["key"]["distribution"]]
        observed = result.exact_probabilities
        passed = distributions_equal(observed, target)
        return Verdict(
            passed=passed,
            reason_code="distribution_match" if passed else "distribution_mismatch",
            message="",
            detail={
                "goal_kind": "distribution",
                "target_distribution": target,
                "exact_probabilities": observed,
                "compared_using": "exact model probabilities, not sampled counts",
            },
        )

    target_state = [complex(entry[0], entry[1]) for entry in rubric["key"]["state"]]
    observed_state = _final_state(result)
    passed = states_equivalent(observed_state, target_state)
    return Verdict(
        passed=passed,
        reason_code="state_match" if passed else "state_mismatch",
        message="",
        detail={
            "goal_kind": "state",
            "compared_using": "fidelity up to global phase",
            "final_amplitudes": [[value.real, value.imag] for value in observed_state],
        },
    )


def _run_reading(
    submission: dict[str, Any], rubric: dict[str, Any], result: RunResult | None
) -> Verdict:
    if result is None:
        return Verdict(
            passed=False,
            reason_code="no_run_selected",
            message="Select one of your own runs before answering this task.",
            detail={},
        )
    tolerance = float(rubric.get("tolerance", DEFAULT_NUMERIC_TOLERANCE))
    values = submission.get("values", {}) or {}
    zero_label = result.basis_labels[0]
    expected = {
        "exact_p0": result.exact_probabilities[0],
        "count_0": float(result.counts.get(zero_label, 0)),
        "shots": float(result.shots),
    }
    per_field: dict[str, Any] = {}
    passed = True
    for field_id, expected_value in expected.items():
        supplied = parse_number(values.get(field_id))
        if supplied is None:
            per_field[field_id] = {"ok": False, "reason": "unreadable_number"}
            passed = False
            continue
        ok = abs(supplied - expected_value) <= (tolerance if field_id == "exact_p0" else 0.0)
        per_field[field_id] = {"ok": ok, "supplied": supplied, "expected": expected_value}
        passed = passed and ok
    selection_ok = submission.get("selection") == rubric["key"]["selection"]
    per_field["selection"] = {"ok": selection_ok, "supplied": submission.get("selection")}
    passed = passed and selection_ok
    return Verdict(
        passed=passed,
        reason_code="run_reading_match" if passed else "run_reading_mismatch",
        message="",
        detail={"fields": per_field, "read_from_run": True},
    )


def evaluate(
    rubric: dict[str, Any],
    submission: dict[str, Any],
    *,
    circuit: CircuitSpec | None = None,
    result: RunResult | None = None,
    assessed_skills: list[str] | None = None,
) -> Verdict:
    """Evaluate one submission against its private rubric."""
    kind = rubric["kind"]
    if kind == "single_select":
        verdict = _single_select(submission, rubric)
    elif kind == "numeric_fields":
        verdict = _numeric_fields(submission, rubric)
    elif kind == "matching":
        verdict = _mapping(submission, rubric, "matches")
    elif kind == "classification":
        verdict = _mapping(submission, rubric, "assignments")
    elif kind == "compound":
        verdict = _compound(submission, rubric)
    elif kind == "run_reading":
        verdict = _run_reading(submission, rubric, result)
    elif kind == "circuit_goal":
        if circuit is None or result is None:
            verdict = Verdict(
                passed=False,
                reason_code="no_circuit_submitted",
                message="Build and run a circuit before submitting this task.",
                detail={},
            )
        else:
            verdict = _circuit_goal(circuit, result, rubric)
    else:  # pragma: no cover - guarded by content validation
        raise ValueError(f"unknown rubric kind: {kind}")

    feedback = rubric.get("feedback", {})
    verdict.message = feedback.get("correct" if verdict.passed else "incorrect", "")
    verdict.assessed_skills = list(assessed_skills or [])
    return verdict
