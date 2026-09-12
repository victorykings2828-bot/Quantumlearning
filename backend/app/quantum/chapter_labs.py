"""Bounded authored experiments, backed by Qiskit. No client matrices or code."""

import math
from typing import Literal

import numpy as np
from pydantic import BaseModel, Field
from qiskit.circuit.library import XGate, ZGate
from qiskit.quantum_info import Statevector

from app.quantum.interface import RunResult, StateFrame
from app.quantum.qiskit_engine import (
    QiskitStatevectorEngine,
    _amplitude_views,
    _reduced_states,
)
from app.quantum.spec import CircuitSpec, RunRequest


class LabInput(BaseModel):
    model_config = {"extra": "forbid"}
    variant: Literal["A", "B", "C"] = "A"
    angle: float = Field(default=math.pi / 2, ge=0, le=2 * math.pi, allow_inf_nan=False)
    basis: Literal["Z", "X", "Y"] = "Z"
    correction: bool = True
    shots: Literal[1, 16, 64, 256, 1024] = 256


def op(name, target=0, control=None, angle=None):
    value = {"op": name, "targets": [target]}
    if control is not None:
        value["controls"] = [control]
    if angle is not None:
        value["angle"] = angle
    return value


def prepared(vector):
    return {
        "kind": "amplitudes",
        "amplitudes": [{"re": complex(v).real, "im": complex(v).imag} for v in vector],
    }


def circuit_for(topic: str, inputs: LabInput) -> CircuitSpec:
    v = inputs.variant
    angle = inputs.angle
    root = math.sqrt(0.5)
    initial = {"kind": "basis", "basis_index": 0}
    qubits = 1
    gates = []
    if topic == "2-1":
        initial = prepared([root, root * np.exp(1j * angle)])
        if v == "B":
            gates = [op("h")]
        elif v == "C":
            initial = prepared([1j * root, 1j * root * np.exp(1j * angle)])
    elif topic == "2-2":
        gates = [op("x"), op("h")] if v == "A" else [op("h"), op("x")]
        if v == "C":
            gates = [op("h"), op("h")]
    elif topic == "2-3":
        theta = 0 if v == "A" else math.pi / 2 if v == "B" else math.pi
        gates = [op("ry", angle=theta), op("p", angle=angle)]
    elif topic == "2-4":
        gates = [op("h"), op("p", angle=angle), op("h")]
    elif topic in {"2-5", "2-6"}:
        phase = 0 if v == "A" else math.pi if v == "B" else math.pi / 2
        initial = prepared([root, root * np.exp(1j * phase)])
    elif topic.startswith("3-"):
        qubits = 2
        if topic == "3-1":
            gates = [op("x", 0 if v == "A" else 1)]
            if v == "C":
                gates = [op("x", 0), op("x", 1)]
        elif topic == "3-2":
            gates = [op("h", 0)]
            if v == "B":
                gates += [op("h", 1)]
            if v == "C":
                initial = prepared([0.48, 0.64, 0.36, 0.48])
                gates = []
        elif topic == "3-3":
            gates = ([] if v == "A" else [op("x")]) + [op("cx", 1, 0)]
            if v == "C":
                gates = [op("h"), op("h", 1), op("cx", 1, 0)]
        elif topic in {"3-4", "3-5", "3-6"}:
            gates = [op("h"), op("cx", 1, 0)]
            if v == "C":
                gates = [op("h"), op("h", 1)]
            elif topic == "3-5" and v == "B":
                initial = prepared([0.6, 0, 0, 0.8])
                gates = []
        elif topic == "3-7":
            qubits = 3
            state = [1, 0] if v == "A" else [root, root] if v == "B" else [0.6, 0.8j]
            initial = prepared([*state, 0, 0, 0, 0, 0, 0])
            gates = [
                op("h", 1),
                op("cx", 2, 1),
                op("cx", 1, 0),
                op("h", 0),
                op("measure_z", 0),
                op("measure_z", 1),
            ]
        else:
            raise ValueError("Unknown chapter laboratory")
    else:
        raise ValueError("Unknown chapter laboratory")
    if inputs.basis != "Z" and topic != "3-7":
        for q in range(qubits):
            if inputs.basis == "Y":
                gates.append(op("sdg", q))
            gates.append(op("h", q))
    return CircuitSpec.model_validate(
        {"qubits": qubits, "initial_state": initial, "operations": gates}
    )


def simulate(topic: str, inputs: LabInput) -> tuple[CircuitSpec, RunResult]:
    engine = QiskitStatevectorEngine()
    circuit = circuit_for(topic, inputs)
    result = engine.run(RunRequest(circuit=circuit, shots=inputs.shots))
    if topic in {"3-4", "3-6"} and inputs.variant == "B":
        # Classical ensemble, not a coherent sum of vectors. Evolve both pure
        # components through the same readout circuit and average density facts.
        outputs = []
        for index in (0, 3):
            component = CircuitSpec(
                qubits=2,
                initial_state={"kind": "basis", "basis_index": index},
                operations=circuit.operations[2:],
            )
            outputs.append(engine.run(RunRequest(circuit=component, shots=1)))
        frames = []
        for a, b in zip(outputs[0].frames, outputs[1].frames, strict=True):
            local = []
            for ra, rb in zip(a.reduced_states, b.reduced_states, strict=True):
                bloch = tuple((x + y) / 2 for x, y in zip(ra.bloch, rb.bloch, strict=True))
                length = float(np.linalg.norm(bloch))
                local.append(
                    ra.model_copy(
                        update={
                            "bloch": bloch,
                            "bloch_length": length,
                            "purity": (1 + length**2) / 2,
                            "is_mixed": length < 1 - 1e-9,
                        }
                    )
                )
            frames.append(
                a.model_copy(
                    update={
                        "amplitudes": [],
                        "reduced_states": local,
                        "probabilities": [
                            (x + y) / 2
                            for x, y in zip(a.probabilities, b.probabilities, strict=True)
                        ],
                        "label": "Classical 50/50 mixture: " + a.label,
                    }
                )
            )
        probs = frames[-1].probabilities
        counts = np.random.default_rng().multinomial(inputs.shots, probs)
        result = result.model_copy(
            update={
                "frames": frames,
                "exact_probabilities": probs,
                "counts": dict(zip(result.basis_labels, map(int, counts), strict=True)),
                "notes": [
                    "Density ensemble: half |00><00| and half |11><11|. "
                    "No single statevector exists."
                ],
            }
        )
    if topic == "3-7":
        final_probs = np.zeros(8)
        for branch in result.branches:
            frame = next(f for f in reversed(result.frames) if f.branch_id == branch.branch_id)
            vector = Statevector([complex(a.re, a.im) for a in frame.amplitudes])
            m0, m1 = branch.outcomes
            if inputs.correction:
                if m1:
                    vector = vector.evolve(XGate(), qargs=[2])
                if m0:
                    vector = vector.evolve(ZGate(), qargs=[2])
            result.frames.append(
                StateFrame(
                    step_index=7,
                    branch_id=branch.branch_id,
                    branch_probability=branch.probability,
                    kind="unitary",
                    operation=None,
                    label=f"m0={m0}, m1={m1}: "
                    + ("conditional X then Z" if inputs.correction else "correction omitted"),
                    amplitudes=_amplitude_views(vector.data, 3),
                    probabilities=list(vector.probabilities()),
                    reduced_states=_reduced_states(vector.data, 3),
                )
            )
            final_probs += branch.probability * vector.probabilities()
        result.exact_probabilities = list(final_probs)
        result.counts = dict(
            zip(
                result.basis_labels,
                map(int, np.random.default_rng().multinomial(inputs.shots, final_probs)),
                strict=True,
            )
        )
        result.notes = [
            "Fixed teleportation protocol. q0 input, q1 Alice, q2 Bob. "
            "m0 measures q0; m1 measures q1. "
            "Classical corrections are included as a separate protocol stage."
        ]
    result.notes.append(
        f"Readout basis {inputs.basis}. Readout gates rotate into Z; "
        "their displayed final state is after that rotation."
    )
    return circuit, result
