"""Evaluator behaviour, including the alternative-solution requirements."""

from __future__ import annotations

import pytest

from app.assessment import evaluator
from app.curriculum import loader
from app.quantum.qiskit_engine import get_engine
from app.quantum.spec import CircuitSpec, InitialState, Operation, RunRequest

ENGINE = get_engine()
RUBRICS = loader.load_task_rubrics()


def build(operations, initial_index=0, shots=1):
    circuit = CircuitSpec(
        qubits=1,
        initial_state=InitialState(kind="basis", basis_index=initial_index),
        operations=[Operation(**op) for op in operations],
    )
    return circuit, ENGINE.run(RunRequest(circuit=circuit, shots=shots, seed=0))


X = {"op": "x", "targets": [0]}
H = {"op": "h", "targets": [0]}
Z = {"op": "z", "targets": [0]}
M = {"op": "measure_z", "targets": [0]}


def test_numeric_accepts_fraction_decimal_and_percentage():
    rubric = RUBRICS["1-2.checkpoint-numeric"]
    for p0, p1 in [("0.36", "0.64"), ("9/25", "16/25"), ("36%", "64%")]:
        verdict = evaluator.evaluate(rubric, {"values": {"p0": p0, "p1": p1}})
        assert verdict.passed, (p0, p1)


def test_numeric_rejects_a_wrong_answer_and_explains():
    rubric = RUBRICS["1-2.checkpoint-numeric"]
    verdict = evaluator.evaluate(rubric, {"values": {"p0": "-0.36", "p1": "0.64"}})
    assert not verdict.passed
    assert "square" in verdict.message.lower()


def test_numeric_tolerance_is_the_authored_value():
    rubric = RUBRICS["1-2.checkpoint-numeric"]
    assert evaluator.evaluate(rubric, {"values": {"p0": "0.3605", "p1": "0.64"}}).passed
    assert not evaluator.evaluate(rubric, {"values": {"p0": "0.37", "p1": "0.64"}}).passed


def test_distribution_goal_accepts_one_or_three_x_gates():
    rubric = RUBRICS["1-4.build"]
    for operations in ([X], [X, X, X]):
        circuit, result = build(operations)
        verdict = evaluator.evaluate(rubric, {}, circuit=circuit, result=result)
        assert verdict.passed, operations


def test_distribution_goal_rejects_an_even_number_of_x_gates():
    rubric = RUBRICS["1-4.build"]
    circuit, result = build([X, X])
    verdict = evaluator.evaluate(rubric, {}, circuit=circuit, result=result)
    assert not verdict.passed
    assert verdict.reason_code == "distribution_mismatch"


def test_distribution_goal_rejects_a_circuit_over_the_gate_limit():
    rubric = RUBRICS["1-4.build"]
    circuit, result = build([X, X, X, X, X])
    verdict = evaluator.evaluate(rubric, {}, circuit=circuit, result=result)
    assert not verdict.passed
    assert verdict.reason_code == "too_many_operations"


def test_alternative_circuits_both_satisfy_the_50_50_distribution_goal():
    """H and X->H prepare different states with the same Z distribution."""
    rubric = RUBRICS["1-5.build"]
    for operations in ([H], [X, H]):
        circuit, result = build(operations)
        verdict = evaluator.evaluate(rubric, {}, circuit=circuit, result=result)
        assert verdict.passed, operations


def test_equal_distributions_do_not_pass_a_different_state_goal():
    """|+> and |-> share a Z distribution; only one satisfies the |1> state goal."""
    rubric = RUBRICS["1-7.build"]
    circuit, result = build([H, Z, H])
    assert evaluator.evaluate(rubric, {}, circuit=circuit, result=result).passed
    circuit, result = build([H, H])
    verdict = evaluator.evaluate(rubric, {}, circuit=circuit, result=result)
    assert not verdict.passed
    assert verdict.reason_code == "state_mismatch"


def test_state_goal_accepts_a_global_phase_equivalent_answer():
    """X->Z reaches -|1>, which is the same physical state as the |1> goal."""
    rubric = {**RUBRICS["1-7.build"], "constraints": {}}
    circuit, result = build([X, Z])
    final = result.frames[-1].amplitudes
    assert final[1].re == pytest.approx(-1.0)
    verdict = evaluator.evaluate(rubric, {}, circuit=circuit, result=result)
    assert verdict.passed
    assert verdict.detail["compared_using"] == "fidelity up to global phase"


def test_state_goal_enforces_the_fixed_prefix_and_suffix():
    rubric = RUBRICS["1-7.build"]
    circuit, result = build([X])
    verdict = evaluator.evaluate(rubric, {}, circuit=circuit, result=result)
    assert not verdict.passed
    assert verdict.reason_code in {"operation_not_allowed", "fixed_prefix_missing"}


def test_measurement_is_rejected_where_the_task_forbids_it():
    rubric = RUBRICS["1-5.build"]
    circuit, result = build([H, M])
    verdict = evaluator.evaluate(rubric, {}, circuit=circuit, result=result)
    assert not verdict.passed
    assert verdict.reason_code == "measurement_not_allowed"


def test_random_counts_never_decide_an_exact_probability_goal():
    """A 50/50 goal passes on the exact probabilities whatever the sample shows."""
    rubric = RUBRICS["1-5.build"]
    for seed in range(8):
        circuit = CircuitSpec(qubits=1, operations=[Operation(**H)])
        result = ENGINE.run(RunRequest(circuit=circuit, shots=16, seed=seed))
        verdict = evaluator.evaluate(rubric, {}, circuit=circuit, result=result)
        assert verdict.passed
        assert verdict.detail["compared_using"].startswith("exact model probabilities")


def test_classification_requires_every_item():
    rubric = RUBRICS["1-6.checkpoint-classify"]
    assert evaluator.evaluate(
        rubric, {"assignments": {"pair1": "relative", "pair2": "global"}}
    ).passed
    assert not evaluator.evaluate(
        rubric, {"assignments": {"pair1": "relative", "pair2": "relative"}}
    ).passed


def test_matching_requires_every_pair():
    rubric = RUBRICS["1-1.checkpoint"]
    assert evaluator.evaluate(
        rubric,
        {"matches": {"vec01": "ket1", "bars10": "ket0", "outcome": "classical"}},
    ).passed
    assert not evaluator.evaluate(rubric, {"matches": {"vec01": "ket1", "bars10": "ket0"}}).passed


def test_run_reading_uses_the_learners_actual_run():
    rubric = RUBRICS["1-8.capstone-c"]
    circuit = CircuitSpec(qubits=1, operations=[Operation(**H)])
    result = ENGINE.run(RunRequest(circuit=circuit, shots=256, seed=11))
    zero_count = result.counts["|0>"]
    verdict = evaluator.evaluate(
        rubric,
        {
            "values": {"exact_p0": "0.5", "count_0": str(zero_count), "shots": "256"},
            "selection": "a",
        },
        result=result,
    )
    assert verdict.passed
    wrong = evaluator.evaluate(
        rubric,
        {
            "values": {"exact_p0": "0.5", "count_0": str(zero_count + 1), "shots": "256"},
            "selection": "a",
        },
        result=result,
    )
    assert not wrong.passed


def test_run_reading_without_a_run_asks_for_one():
    rubric = RUBRICS["1-8.capstone-c"]
    verdict = evaluator.evaluate(rubric, {"values": {}, "selection": "a"}, result=None)
    assert not verdict.passed
    assert verdict.reason_code == "no_run_selected"


def test_state_goal_on_a_branching_circuit_is_refused_not_guessed():
    from app.quantum.errors import CircuitRejected

    rubric = {**RUBRICS["1-7.build"], "constraints": {}}
    circuit, result = build([H, M, H])
    with pytest.raises(CircuitRejected):
        evaluator.evaluate(rubric, {}, circuit=circuit, result=result)


def test_every_authored_task_has_a_rubric_of_a_known_kind():
    known = {
        "single_select",
        "numeric_fields",
        "matching",
        "classification",
        "compound",
        "circuit_goal",
        "run_reading",
    }
    for topic in loader.load_chapter("chapter-1")["topics"]:
        for task in topic["tasks"]:
            rubric = RUBRICS[task["id"]]
            assert rubric["kind"] in known
            assert rubric["kind"] == task["kind"]
            assert rubric["feedback"]["correct"]
            assert rubric["feedback"]["incorrect"]
