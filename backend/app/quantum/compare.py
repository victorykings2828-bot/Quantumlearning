"""State and distribution comparison used by the authored evaluator.

State goals accept equivalence up to global phase. Distribution goals compare
probabilities only and never assert that two states are the same.
"""

from __future__ import annotations

import numpy as np

DEFAULT_STATE_TOLERANCE = 1e-6
DEFAULT_DISTRIBUTION_TOLERANCE = 1e-6


def fidelity_up_to_global_phase(left: list[complex], right: list[complex]) -> float:
    """|<a|b>|^2 for two normalized pure states; global phase cancels."""
    a = np.array(left, dtype=complex)
    b = np.array(right, dtype=complex)
    if a.shape != b.shape:
        return 0.0
    overlap = complex(np.vdot(a, b))
    return float(abs(overlap) ** 2)


def states_equivalent(
    left: list[complex], right: list[complex], tolerance: float = DEFAULT_STATE_TOLERANCE
) -> bool:
    """True when the two vectors describe the same physical pure state."""
    return abs(fidelity_up_to_global_phase(left, right) - 1.0) <= tolerance


def global_phase_offset(left: list[complex], right: list[complex]) -> float | None:
    """The phase angle relating two global-phase-equivalent states, if any."""
    if not states_equivalent(left, right):
        return None
    a = np.array(left, dtype=complex)
    b = np.array(right, dtype=complex)
    overlap = complex(np.vdot(a, b))
    if abs(overlap) < 1e-12:  # pragma: no cover - excluded by the equivalence test
        return None
    return float(np.angle(overlap))


def distributions_equal(
    left: list[float],
    right: list[float],
    tolerance: float = DEFAULT_DISTRIBUTION_TOLERANCE,
) -> bool:
    if len(left) != len(right):
        return False
    return all(abs(a - b) <= tolerance for a, b in zip(left, right, strict=True))


def total_variation_distance(left: list[float], right: list[float]) -> float:
    if len(left) != len(right):
        return 1.0
    return 0.5 * float(sum(abs(a - b) for a, b in zip(left, right, strict=True)))


def relative_phase_pattern(vector: list[complex], tolerance: float = 1e-9) -> list[float | None]:
    """Phases relative to the first populated component; None where undefined."""
    values = np.array(vector, dtype=complex)
    reference = None
    for value in values:
        if abs(value) > tolerance:
            reference = value / abs(value)
            break
    if reference is None:  # pragma: no cover - a normalized state always populates one entry
        return [None] * len(values)
    output: list[float | None] = []
    for value in values:
        if abs(value) <= tolerance:
            output.append(None)
        else:
            output.append(float(np.angle(value / reference)))
    return output
