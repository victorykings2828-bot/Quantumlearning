"""Independent verification of the reference fixtures.

Expected values here are derived from the mathematics, not read back from the
same builder that produced them.
"""

from __future__ import annotations

import math

import pytest

from app.quantum.compare import distributions_equal, states_equivalent
from app.quantum.grover import (
    GroverSettings,
    build_circuit,
    classical_average_checks,
    classical_check_and_guess,
    classical_checked_only,
    ideal_target_probability,
)
from app.quantum.qiskit_engine import get_engine
from app.quantum.spec import CircuitSpec, InitialState, Operation, RunRequest

ROOT_HALF = 1 / math.sqrt(2)
ENGINE = get_engine()


def run(operations, initial=None, qubits=1, shots=1, seed=0):
    spec = CircuitSpec(
        qubits=qubits,
        initial_state=initial or InitialState(kind="basis", basis_index=0),
        operations=[Operation(**op) for op in operations],
    )
    return ENGINE.run(RunRequest(circuit=spec, shots=shots, seed=seed))


def final_state(result):
    branch = result.branches[0].branch_id
    frames = [frame for frame in result.frames if frame.branch_id == branch]
    return [complex(view.re, view.im) for view in frames[-1].amplitudes]


X = {"op": "x", "targets": [0]}
H = {"op": "h", "targets": [0]}
Z = {"op": "z", "targets": [0]}
M = {"op": "measure_z", "targets": [0]}

KET0 = InitialState(kind="basis", basis_index=0)
KET1 = InitialState(kind="basis", basis_index=1)


@pytest.mark.parametrize("initial", [KET0, KET1])
def test_x_squared_is_identity(initial):
    start = run([], initial)
    twice = run([X, X], initial)
    assert states_equivalent(final_state(start), final_state(twice))


@pytest.mark.parametrize("initial", [KET0, KET1])
def test_h_squared_is_identity(initial):
    start = run([], initial)
    twice = run([H, H], initial)
    assert states_equivalent(final_state(start), final_state(twice))


@pytest.mark.parametrize("initial", [KET0, KET1])
def test_z_squared_is_identity(initial):
    start = run([], initial)
    twice = run([Z, Z], initial)
    assert states_equivalent(final_state(start), final_state(twice))


def test_hzh_on_ket0_is_ket1():
    assert states_equivalent(final_state(run([H, Z, H], KET0)), [0j, 1 + 0j])


def test_hzh_on_ket1_is_ket0():
    assert states_equivalent(final_state(run([H, Z, H], KET1)), [1 + 0j, 0j])


def test_hzh_on_non_basis_input():
    """HZH = X, so it must swap the amplitudes of (3/5, 4/5) too."""
    card_b = InitialState(kind="named", named="card_b")
    assert states_equivalent(final_state(run([H, Z, H], card_b)), [0.8 + 0j, 0.6 + 0j])


def test_hzzh_on_ket0_returns_ket0():
    assert states_equivalent(final_state(run([H, Z, Z, H], KET0)), [1 + 0j, 0j])


def test_z_on_card_b_flips_sign_without_changing_probabilities():
    result = run([Z], InitialState(kind="named", named="card_b"))
    assert states_equivalent(final_state(result), [0.6 + 0j, -0.8 + 0j])
    assert distributions_equal(result.exact_probabilities, [0.36, 0.64])


def test_h_on_ket0_and_ket1_share_a_distribution_but_differ_as_states():
    from_zero = final_state(run([H], KET0))
    from_one = final_state(run([H], KET1))
    assert distributions_equal([abs(v) ** 2 for v in from_zero], [0.5, 0.5])
    assert distributions_equal([abs(v) ** 2 for v in from_one], [0.5, 0.5])
    assert not states_equivalent(from_zero, from_one)


def test_plus_and_negative_plus_are_global_phase_equivalent():
    plus = [ROOT_HALF + 0j, ROOT_HALF + 0j]
    negative_plus = [-ROOT_HALF + 0j, -ROOT_HALF + 0j]
    assert states_equivalent(plus, negative_plus)


def test_measurement_between_hadamards_gives_equal_final_probabilities():
    result = run([H, M, H], KET0, shots=64, seed=3)
    assert len(result.branches) == 2
    assert all(abs(branch.probability - 0.5) < 1e-12 for branch in result.branches)
    assert distributions_equal(result.exact_probabilities, [0.5, 0.5])
    for branch in result.branches:
        frames = [frame for frame in result.frames if frame.branch_id == branch.branch_id]
        amplitudes = [complex(view.re, view.im) for view in frames[-1].amplitudes]
        assert distributions_equal([abs(v) ** 2 for v in amplitudes], [0.5, 0.5])


def test_unnormalized_initial_state_is_rejected():
    with pytest.raises(ValueError, match="not normalized"):
        CircuitSpec(
            qubits=1,
            initial_state=InitialState(kind="amplitudes", amplitudes=[{"re": 0.5}, {"re": 0.5}]),
        )


def test_zero_amplitude_has_undefined_phase():
    result = run([], KET0)
    views = result.frames[-1].amplitudes
    assert views[0].phase_radians is not None
    assert views[1].phase_radians is None


def test_operation_limit_enforced():
    with pytest.raises(ValueError, match="at most 100 operations"):
        CircuitSpec(qubits=1, operations=[Operation(**X) for _ in range(101)])


def test_shot_limit_enforced():
    with pytest.raises(ValueError):
        RunRequest(circuit=CircuitSpec(qubits=1), shots=2048)


def test_qubit_index_outside_register_rejected():
    with pytest.raises(ValueError, match="outside"):
        CircuitSpec(qubits=1, operations=[Operation(op="x", targets=[3])])


def test_duplicate_control_and_target_rejected():
    with pytest.raises(ValueError, match="cannot reuse"):
        Operation(op="cx", controls=[0], targets=[0])


def test_bit_ordering_q0_is_least_significant():
    """X on q0 of a two-qubit register must move |00> to |01>."""
    result = run([{"op": "x", "targets": [0]}], qubits=2)
    assert result.basis_labels == ["|00>", "|01>", "|10>", "|11>"]
    assert result.exact_probabilities[1] == pytest.approx(1.0)


@pytest.mark.parametrize(
    ("candidates", "iterations", "expected"),
    [
        (4, 0, 0.25),
        (4, 1, 1.0),
        (4, 2, 0.25),
        (8, 0, 0.125),
        (8, 1, 0.78125),
        (8, 2, 121 / 128),
        (8, 3, 169 / 512),
    ],
)
def test_grover_matches_independently_derived_values(candidates, iterations, expected):
    """Independently derived fixtures from the researched blueprint."""
    for target in range(candidates):
        settings = GroverSettings(candidates=candidates, target=target, iterations=iterations)
        result = ENGINE.run(RunRequest(circuit=build_circuit(settings), shots=1, seed=0))
        assert result.exact_probabilities[target] == pytest.approx(expected, abs=1e-12)


def test_grover_n16_three_iterations():
    settings = GroverSettings(candidates=16, target=9, iterations=3)
    result = ENGINE.run(RunRequest(circuit=build_circuit(settings), shots=1, seed=0))
    assert result.exact_probabilities[9] == pytest.approx(0.961319, abs=1e-6)


def test_grover_simulation_agrees_with_the_analytical_formula():
    for candidates in (4, 8, 16):
        for iterations in range(5):
            settings = GroverSettings(candidates=candidates, target=1, iterations=iterations)
            result = ENGINE.run(RunRequest(circuit=build_circuit(settings), shots=1, seed=0))
            assert result.exact_probabilities[1] == pytest.approx(
                ideal_target_probability(candidates, iterations), abs=1e-12
            )


def test_grover_oracle_changes_a_sign_before_any_probability_changes():
    settings = GroverSettings(candidates=4, target=2, iterations=1)
    result = ENGINE.run(RunRequest(circuit=build_circuit(settings), shots=1, seed=0))
    # Two H gates prepare the uniform state; the oracle block follows.
    after_preparation = result.frames[2]
    after_oracle = next(frame for frame in result.frames if frame.step_index == 2 + 3)
    assert distributions_equal(after_preparation.probabilities, [0.25] * 4)
    assert distributions_equal(after_oracle.probabilities, [0.25] * 4)
    assert after_preparation.amplitudes[2].re == pytest.approx(0.5)
    assert after_oracle.amplitudes[2].re == pytest.approx(-0.5)


def test_grover_overshoot_is_visible():
    assert ideal_target_probability(8, 3) < ideal_target_probability(8, 2)


def test_missing_preparation_variant_is_outside_the_formula():
    settings = GroverSettings(candidates=4, target=2, iterations=1, preparation="missing")
    result = ENGINE.run(RunRequest(circuit=build_circuit(settings), shots=1, seed=0))
    assert result.exact_probabilities[2] != pytest.approx(ideal_target_probability(4, 1), abs=1e-9)


def test_classical_baselines():
    assert classical_check_and_guess(8, 2) == pytest.approx(3 / 8)
    assert classical_checked_only(8, 2) == pytest.approx(2 / 8)
    rules = classical_average_checks(8)
    assert rules["checks_every_candidate_mean"] == pytest.approx(4.5)
    assert rules["uses_promise_mean"] == pytest.approx(4.375)
    assert rules["uses_promise_worst"] == pytest.approx(7.0)


def test_shots_restart_the_preparation():
    """Every shot of |+> is an independent trial, so counts vary across seeds."""
    counts = {
        ENGINE.run(
            RunRequest(
                circuit=CircuitSpec(
                    qubits=1, initial_state=InitialState(kind="named", named="plus")
                ),
                shots=16,
                seed=seed,
            )
        ).counts["|0>"]
        for seed in range(12)
    }
    assert len(counts) > 1
    assert all(0 <= value <= 16 for value in counts)


def test_seeded_run_is_reproducible():
    first = ENGINE.run(
        RunRequest(
            circuit=CircuitSpec(qubits=1, initial_state=InitialState(kind="named", named="plus")),
            shots=256,
            seed=99,
        )
    )
    second = ENGINE.run(
        RunRequest(
            circuit=CircuitSpec(qubits=1, initial_state=InitialState(kind="named", named="plus")),
            shots=256,
            seed=99,
        )
    )
    assert first.counts == second.counts
    assert sum(first.counts.values()) == 256


def test_bell_state_reduced_states_are_maximally_mixed():
    """For a verified pure joint state, a mixed reduced state shows entanglement."""
    result = run(
        [{"op": "h", "targets": [0]}, {"op": "cx", "controls": [0], "targets": [1]}],
        qubits=2,
    )
    final = result.frames[-1]
    assert distributions_equal(final.probabilities, [0.5, 0.0, 0.0, 0.5])
    for reduced in final.reduced_states:
        assert reduced.bloch_length == pytest.approx(0.0, abs=1e-12)
        assert reduced.purity == pytest.approx(0.5, abs=1e-12)
        assert reduced.is_mixed


def test_product_state_reduced_states_are_pure():
    result = run([{"op": "h", "targets": [0]}], qubits=2)
    for reduced in result.frames[-1].reduced_states:
        assert reduced.bloch_length == pytest.approx(1.0, abs=1e-12)
        assert not reduced.is_mixed


def test_two_qubit_playground_operations_are_supported():
    """The published playground allows X, H, Z, CNOT and CZ on two qubits."""
    operations = [
        {"op": "h", "targets": [0]},
        {"op": "x", "targets": [1]},
        {"op": "z", "targets": [0]},
        {"op": "cx", "controls": [0], "targets": [1]},
        {"op": "cz", "controls": [1], "targets": [0]},
    ]
    result = run(operations, qubits=2, shots=16, seed=4)
    assert result.qubits == 2
    assert sum(result.exact_probabilities) == pytest.approx(1.0)
    assert sum(result.counts.values()) == 16


def test_bell_state_is_reached_by_h_then_cnot():
    result = run(
        [{"op": "h", "targets": [0]}, {"op": "cx", "controls": [0], "targets": [1]}],
        qubits=2,
    )
    final = final_state(result)
    expected = [ROOT_HALF + 0j, 0j, 0j, ROOT_HALF + 0j]
    assert states_equivalent(final, expected)


def test_equal_marginals_alone_do_not_establish_entanglement():
    """A product state can give each qubit an even 50/50 marginal too."""
    product = run(
        [{"op": "h", "targets": [0]}, {"op": "h", "targets": [1]}],
        qubits=2,
    )
    bell = run(
        [{"op": "h", "targets": [0]}, {"op": "cx", "controls": [0], "targets": [1]}],
        qubits=2,
    )
    for frame in (product.frames[-1], bell.frames[-1]):
        marginal_one = frame.probabilities[1] + frame.probabilities[3]
        assert marginal_one == pytest.approx(0.5)
    # The reduced states are what separate them, not the marginals.
    assert all(not state.is_mixed for state in product.frames[-1].reduced_states)
    assert all(state.is_mixed for state in bell.frames[-1].reduced_states)


def test_three_qubit_register_rejects_playground_bounds_violation():
    with pytest.raises(ValueError):
        CircuitSpec(qubits=5, operations=[])
