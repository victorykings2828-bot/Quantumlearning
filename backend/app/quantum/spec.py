"""Validated circuit representation.

The engine accepts only this schema. Learner-supplied Python, arbitrary
expression strings, and unbounded resource requests are never executed.
Qubit 0 is the least significant bit and the top circuit wire, matching the
bit-ordering convention used throughout the course content.
"""

from __future__ import annotations

import math
from typing import Annotated, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

CIRCUIT_SCHEMA_VERSION = "circuit/v1"

# Application bounds. These are limits of this demo, not claims about hardware.
MAX_QUBITS = 4
MAX_OPERATIONS = 100
MAX_SHOTS = 1024
ALLOWED_SHOT_COUNTS = (1, 16, 64, 256, 1024)

# The general one/two-qubit playground palette published to learners.
PLAYGROUND_OPERATIONS = frozenset({"x", "h", "z", "cx", "cz", "measure_z"})
# Additional operation used only by authored multi-qubit presets (Grover).
PRESET_OPERATIONS = frozenset({"mcz"})
ALL_OPERATIONS = PLAYGROUND_OPERATIONS | PRESET_OPERATIONS

NORMALIZATION_TOLERANCE = 1e-9


class Complex(BaseModel):
    """A complex number carried explicitly so JSON never loses the sign."""

    re: float = 0.0
    im: float = 0.0

    @field_validator("re", "im")
    @classmethod
    def _finite(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("amplitude components must be finite")
        return value

    def as_complex(self) -> complex:
        return complex(self.re, self.im)


NamedSingleQubitState = Literal[
    "ket0",
    "ket1",
    "plus",
    "minus",
    "card_b",
    "card_c",
]
"""Authored one-qubit presets.

card_b is (3/5, 4/5) and card_c is (-3/5, 4/5) from Topic 1.2. They share a
probability distribution and differ in the sign of the first amplitude.
"""

_NAMED_STATES: dict[str, tuple[complex, complex]] = {
    "ket0": (1 + 0j, 0j),
    "ket1": (0j, 1 + 0j),
    "plus": (complex(1 / math.sqrt(2)), complex(1 / math.sqrt(2))),
    "minus": (complex(1 / math.sqrt(2)), complex(-1 / math.sqrt(2))),
    "card_b": (complex(3 / 5), complex(4 / 5)),
    "card_c": (complex(-3 / 5), complex(4 / 5)),
}


class InitialState(BaseModel):
    """The declared preparation for a run."""

    kind: Literal["basis", "named", "amplitudes"] = "basis"
    basis_index: int = 0
    named: NamedSingleQubitState | None = None
    amplitudes: list[Complex] | None = None

    model_config = {"extra": "forbid"}

    def vector(self, qubits: int) -> list[complex]:
        dimension = 2**qubits
        if self.kind == "basis":
            if not 0 <= self.basis_index < dimension:
                raise ValueError("basis_index outside the register")
            vector = [0j] * dimension
            vector[self.basis_index] = 1 + 0j
            return vector
        if self.kind == "named":
            if self.named is None:
                raise ValueError("named preparation requires a preset name")
            if qubits != 1:
                raise ValueError("named one-qubit presets require a single qubit")
            return list(_NAMED_STATES[self.named])
        if self.amplitudes is None or len(self.amplitudes) != dimension:
            raise ValueError("amplitude preparation must supply 2**qubits entries")
        return [entry.as_complex() for entry in self.amplitudes]

    def normalization_defect(self, qubits: int) -> float:
        """Return |sum of squared magnitudes - 1|; 0 for a normalized vector."""
        total = sum(abs(value) ** 2 for value in self.vector(qubits))
        return abs(total - 1.0)


class Operation(BaseModel):
    """One circuit operation in chronological order."""

    op: Literal["x", "h", "z", "s", "sdg", "p", "ry", "rx", "rz", "cx", "cz", "mcz", "measure_z"]
    targets: list[int] = Field(default_factory=list)
    controls: list[int] = Field(default_factory=list)
    angle: float | None = None

    model_config = {"extra": "forbid"}

    @model_validator(mode="after")
    def _shape(self) -> Operation:
        single = {"x", "h", "z", "s", "sdg", "p", "ry", "rx", "rz", "measure_z"}
        if self.op in {"p", "ry", "rx", "rz"}:
            if (
                self.angle is None
                or not math.isfinite(self.angle)
                or abs(self.angle) > 100 * math.pi
            ):
                raise ValueError("rotation requires a finite angle within 100 pi radians")
        elif self.angle is not None:
            raise ValueError("this operation does not accept an angle")
        if self.op in single:
            if len(self.targets) != 1 or self.controls:
                raise ValueError(f"{self.op} takes exactly one target and no control")
        elif self.op in {"cx", "cz"}:
            if len(self.targets) != 1 or len(self.controls) != 1:
                raise ValueError(f"{self.op} takes one control and one target")
        elif self.op == "mcz" and (len(self.targets) != 1 or not self.controls):
            raise ValueError("mcz takes one target and at least one control")
        wires = [*self.targets, *self.controls]
        if len(set(wires)) != len(wires):
            raise ValueError("an operation cannot reuse the same qubit as control and target")
        if any(index < 0 for index in wires):
            raise ValueError("qubit indices must be non-negative")
        return self


class CircuitSpec(BaseModel):
    """An immutable, validated circuit description."""

    schema_version: Literal["circuit/v1"] = CIRCUIT_SCHEMA_VERSION
    qubits: Annotated[int, Field(ge=1, le=MAX_QUBITS)] = 1
    initial_state: InitialState = Field(default_factory=InitialState)
    operations: list[Operation] = Field(default_factory=list)

    model_config = {"extra": "forbid"}

    @model_validator(mode="after")
    def _bounds(self) -> CircuitSpec:
        if len(self.operations) > MAX_OPERATIONS:
            raise ValueError(f"at most {MAX_OPERATIONS} operations are allowed")
        for operation in self.operations:
            for index in [*operation.targets, *operation.controls]:
                if index >= self.qubits:
                    raise ValueError(
                        f"qubit index {index} is outside the {self.qubits}-qubit register"
                    )
        defect = self.initial_state.normalization_defect(self.qubits)
        if defect > NORMALIZATION_TOLERANCE:
            raise ValueError("initial state is not normalized: squared magnitudes must sum to 1")
        return self

    def measurement_positions(self) -> list[int]:
        return [i for i, operation in enumerate(self.operations) if operation.op == "measure_z"]


class RunRequest(BaseModel):
    """A request to compute one run of a circuit."""

    circuit: CircuitSpec
    shots: Annotated[int, Field(ge=1, le=MAX_SHOTS)] = 1
    seed: int | None = None

    model_config = {"extra": "forbid"}

    @field_validator("shots")
    @classmethod
    def _allowed_shots(cls, value: int) -> int:
        if value not in ALLOWED_SHOT_COUNTS:
            raise ValueError(f"shots must be one of {list(ALLOWED_SHOT_COUNTS)}")
        return value


def basis_label(index: int, qubits: int) -> str:
    """Render a basis index as |q[n-1]...q0>."""
    bits = format(index, f"0{qubits}b")
    return f"|{bits}>"
