"""Qiskit implementation of the neutral simulation interface.

Every number this module returns is computed by Qiskit's statevector
simulation of the exact circuit supplied. Nothing is estimated, cached from
authored text, or generated.
"""

from __future__ import annotations

import cmath
from collections import Counter

import numpy as np
import qiskit
from qiskit.circuit.library import CXGate, CZGate, HGate, XGate, ZGate
from qiskit.quantum_info import Statevector

from app.quantum.errors import CircuitRejected
from app.quantum.interface import (
    AmplitudeView,
    BranchSummary,
    ReducedQubitState,
    RunResult,
    StateFrame,
)
from app.quantum.spec import (
    CIRCUIT_SCHEMA_VERSION,
    CircuitSpec,
    Operation,
    RunRequest,
    basis_label,
)

_ZERO_MAGNITUDE = 1e-12
_BRANCH_CUTOFF = 1e-12

_OPERATION_LABELS = {
    "x": "X gate",
    "h": "Hadamard",
    "z": "Z gate",
    "cx": "Controlled-NOT",
    "cz": "Controlled-Z",
    "mcz": "Multi-controlled Z",
    "measure_z": "Measure in the Z basis",
}


def _gate(operation: Operation):
    if operation.op == "x":
        return XGate(), list(operation.targets)
    if operation.op == "h":
        return HGate(), list(operation.targets)
    if operation.op == "z":
        return ZGate(), list(operation.targets)
    if operation.op == "cx":
        return CXGate(), [operation.controls[0], operation.targets[0]]
    if operation.op == "cz":
        return CZGate(), [operation.controls[0], operation.targets[0]]
    if operation.op == "mcz":
        return ZGate().control(len(operation.controls)), [
            *operation.controls,
            operation.targets[0],
        ]
    raise CircuitRejected("unsupported_operation", f"operation {operation.op} is not supported")


def _describe(operation: Operation) -> str:
    base = _OPERATION_LABELS[operation.op]
    wires = ", ".join(f"q{index}" for index in operation.targets)
    if operation.controls:
        controls = ", ".join(f"q{index}" for index in operation.controls)
        return f"{base}: control {controls}, target {wires}"
    return f"{base} on {wires}"


def _amplitude_views(vector: np.ndarray, qubits: int) -> list[AmplitudeView]:
    views: list[AmplitudeView] = []
    for index, value in enumerate(vector):
        magnitude = float(abs(value))
        phase = None if magnitude <= _ZERO_MAGNITUDE else float(cmath.phase(complex(value)))
        views.append(
            AmplitudeView(
                index=index,
                label=basis_label(index, qubits),
                re=float(np.real(value)),
                im=float(np.imag(value)),
                magnitude=magnitude,
                probability=magnitude**2,
                phase_radians=phase,
            )
        )
    return views


def _reduced_states(vector: np.ndarray, qubits: int) -> list[ReducedQubitState]:
    """Single-qubit reduced density matrices, computed from the joint state."""
    if qubits < 2:
        # A single-qubit pure state needs no partial trace; report it anyway so
        # the display code has one uniform shape.
        rho = np.outer(vector, vector.conj())
        return [_bloch(rho, 0)]
    tensor = vector.reshape([2] * qubits)
    results: list[ReducedQubitState] = []
    for qubit in range(qubits):
        # Qubit 0 is the least significant bit, i.e. the last tensor axis.
        axis = qubits - 1 - qubit
        moved = np.moveaxis(tensor, axis, 0).reshape(2, -1)
        rho = moved @ moved.conj().T
        results.append(_bloch(rho, qubit))
    return results


def _bloch(rho: np.ndarray, qubit: int) -> ReducedQubitState:
    x = float(np.real(rho[0, 1] + rho[1, 0]))
    y = float(np.real(1j * (rho[0, 1] - rho[1, 0])))
    z = float(np.real(rho[0, 0] - rho[1, 1]))
    length = float(np.sqrt(x * x + y * y + z * z))
    purity = float(np.real(np.trace(rho @ rho)))
    return ReducedQubitState(
        qubit=qubit,
        bloch=(x, y, z),
        bloch_length=length,
        purity=purity,
        is_mixed=purity < 1.0 - 1e-9,
    )


def _marginal(vector: np.ndarray, qubits: int, qubit: int) -> tuple[float, float]:
    probabilities = np.abs(vector) ** 2
    mask = 1 << qubit
    p1 = float(sum(p for index, p in enumerate(probabilities) if index & mask))
    return 1.0 - p1, p1


def _project(vector: np.ndarray, qubit: int, outcome: int) -> tuple[np.ndarray, float]:
    mask = 1 << qubit
    projected = np.array(
        [value if bool(index & mask) == bool(outcome) else 0j for index, value in enumerate(vector)]
    )
    norm = float(np.linalg.norm(projected))
    if norm <= _BRANCH_CUTOFF:
        return projected, 0.0
    return projected / norm, norm**2


class QiskitStatevectorEngine:
    """Bounded statevector engine backed by ``qiskit.quantum_info``."""

    name = "qiskit-statevector"
    version = qiskit.__version__

    def run(self, request: RunRequest) -> RunResult:
        circuit = request.circuit
        qubits = circuit.qubits
        labels = [basis_label(index, qubits) for index in range(2**qubits)]

        try:
            start = np.array(circuit.initial_state.vector(qubits), dtype=complex)
        except ValueError as error:  # pragma: no cover - spec validation covers this
            raise CircuitRejected("invalid_initial_state", str(error)) from error

        frames: list[StateFrame] = [
            StateFrame(
                step_index=0,
                branch_id="root",
                branch_probability=1.0,
                kind="preparation",
                operation=None,
                label="Preparation",
                amplitudes=_amplitude_views(start, qubits),
                probabilities=[float(abs(value) ** 2) for value in start],
                reduced_states=_reduced_states(start, qubits),
            )
        ]

        # (branch_id, statevector, branch probability, recorded outcomes)
        active: list[tuple[str, np.ndarray, float, list[int]]] = [("root", start, 1.0, [])]

        for step, operation in enumerate(circuit.operations, start=1):
            next_active: list[tuple[str, np.ndarray, float, list[int]]] = []
            for branch_id, vector, weight, outcomes in active:
                if operation.op == "measure_z":
                    qubit = operation.targets[0]
                    p0, p1 = _marginal(vector, qubits, qubit)
                    for outcome, probability in ((0, p0), (1, p1)):
                        if probability <= _BRANCH_CUTOFF:
                            continue
                        projected, _ = _project(vector, qubit, outcome)
                        child = f"{branch_id}|m{step}q{qubit}={outcome}"
                        child_weight = weight * probability
                        frames.append(
                            StateFrame(
                                step_index=step,
                                branch_id=child,
                                branch_probability=child_weight,
                                kind="measurement",
                                operation=operation.op,
                                label=f"{_describe(operation)} - recorded outcome {outcome}",
                                amplitudes=_amplitude_views(projected, qubits),
                                probabilities=[float(abs(v) ** 2) for v in projected],
                                measured_outcome=outcome,
                                measured_qubit=qubit,
                                reduced_states=_reduced_states(projected, qubits),
                            )
                        )
                        next_active.append((child, projected, child_weight, [*outcomes, outcome]))
                else:
                    gate, wires = _gate(operation)
                    evolved = np.asarray(
                        Statevector(vector).evolve(gate, qargs=wires).data, dtype=complex
                    )
                    frames.append(
                        StateFrame(
                            step_index=step,
                            branch_id=branch_id,
                            branch_probability=weight,
                            kind="unitary",
                            operation=operation.op,
                            label=_describe(operation),
                            amplitudes=_amplitude_views(evolved, qubits),
                            probabilities=[float(abs(v) ** 2) for v in evolved],
                            reduced_states=_reduced_states(evolved, qubits),
                        )
                    )
                    next_active.append((branch_id, evolved, weight, outcomes))
            active = next_active

        branches = [
            BranchSummary(branch_id=branch_id, probability=weight, outcomes=outcomes)
            for branch_id, _, weight, outcomes in active
        ]

        exact = np.zeros(2**qubits)
        for _, vector, weight, _ in active:
            exact += weight * (np.abs(vector) ** 2)
        exact_probabilities = [float(value) for value in exact]

        counts = self._sample(circuit, request.shots, request.seed, qubits, labels)

        notes: list[str] = []
        if circuit.measurement_positions():
            notes.append(
                "This circuit contains a mid-circuit measurement, so the result is "
                "reported as separate conditional branches plus an ensemble summary."
            )

        return RunResult(
            result_kind="ideal_circuit_simulation",
            engine=self.name,
            engine_version=self.version,
            circuit_schema_version=CIRCUIT_SCHEMA_VERSION,
            qubits=qubits,
            frames=frames,
            branches=branches,
            exact_probabilities=exact_probabilities,
            basis_labels=labels,
            counts=counts,
            shots=request.shots,
            seed=request.seed,
            notes=notes,
        )

    def _sample(
        self,
        circuit: CircuitSpec,
        shots: int,
        seed: int | None,
        qubits: int,
        labels: list[str],
    ) -> dict[str, int]:
        """Sample complete trajectories: each shot restarts the preparation."""
        rng = np.random.default_rng(seed)
        start = np.array(circuit.initial_state.vector(qubits), dtype=complex)
        tally: Counter[str] = Counter()
        for _ in range(shots):
            vector = start
            for operation in circuit.operations:
                if operation.op == "measure_z":
                    qubit = operation.targets[0]
                    _, p1 = _marginal(vector, qubits, qubit)
                    outcome = 1 if rng.random() < p1 else 0
                    vector, _ = _project(vector, qubit, outcome)
                else:
                    gate, wires = _gate(operation)
                    vector = np.asarray(
                        Statevector(vector).evolve(gate, qargs=wires).data, dtype=complex
                    )
            probabilities = np.abs(vector) ** 2
            total = probabilities.sum()
            probabilities = probabilities / total if total > 0 else probabilities
            index = int(rng.choice(len(probabilities), p=probabilities))
            tally[labels[index]] += 1
        return {label: tally.get(label, 0) for label in labels}


def get_engine() -> QiskitStatevectorEngine:
    return QiskitStatevectorEngine()
