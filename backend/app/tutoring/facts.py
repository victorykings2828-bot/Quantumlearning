"""Verified run facts.

A numerical claim about a learner's experiment must come from the engine
result, never from model prose. The model references a fact by ID and the
server substitutes the actual value before rendering.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from app.quantum.interface import RunResult

FACT_REFERENCE = re.compile(r"\[\[fact:([a-zA-Z0-9_.\-]+)\]\]")


@dataclass(frozen=True)
class Fact:
    id: str
    label: str
    value: str
    raw: Any

    def as_dict(self) -> dict[str, Any]:
        return {"id": self.id, "label": self.label, "value": self.value}


def _format_probability(value: float) -> str:
    return f"{value:.4f}".rstrip("0").rstrip(".") if value not in (0.0, 1.0) else f"{value:.0f}"


def build_facts(result: RunResult, *, run_label: str, step_index: int | None = None) -> list[Fact]:
    """Typed facts for one run, optionally focused on one selected step."""
    facts: list[Fact] = [
        Fact("run.label", "Run", run_label, run_label),
        Fact("run.shots", "Shot total", str(result.shots), result.shots),
        Fact(
            "run.engine",
            "Engine",
            f"{result.engine} {result.engine_version}",
            result.engine_version,
        ),
        Fact("run.result_kind", "Result label", result.result_kind, result.result_kind),
    ]
    for index, label in enumerate(result.basis_labels):
        probability = result.exact_probabilities[index]
        facts.append(
            Fact(
                f"run.exact_p{index}",
                f"Exact probability of {label}",
                _format_probability(probability),
                probability,
            )
        )
        count = result.counts.get(label, 0)
        facts.append(Fact(f"run.count_{index}", f"Measured count of {label}", str(count), count))
        if result.shots:
            frequency = count / result.shots
            facts.append(
                Fact(
                    f"run.frequency_{index}",
                    f"Observed frequency of {label}",
                    f"{frequency * 100:.2f}%",
                    frequency,
                )
            )

    if step_index is not None:
        frames = [frame for frame in result.frames if frame.step_index == step_index]
        if frames:
            frame = frames[-1]
            facts.append(Fact("step.index", "Selected step", str(step_index), step_index))
            facts.append(Fact("step.label", "Selected step label", frame.label, frame.label))
            amplitudes = ", ".join(
                f"{view.label}: {view.re:+.4f}"
                + (f"{view.im:+.4f}i" if abs(view.im) > 1e-12 else "")
                for view in frame.amplitudes
            )
            facts.append(Fact("step.amplitudes", "Amplitudes at this step", amplitudes, amplitudes))
            probabilities = ", ".join(
                f"{label}: {value:.4f}"
                for label, value in zip(result.basis_labels, frame.probabilities, strict=True)
            )
            facts.append(
                Fact(
                    "step.probabilities",
                    "Probabilities at this step",
                    probabilities,
                    probabilities,
                )
            )
            if frame.measured_outcome is not None:
                facts.append(
                    Fact(
                        "step.measured_outcome",
                        "Recorded outcome at this step",
                        str(frame.measured_outcome),
                        frame.measured_outcome,
                    )
                )
            if frame.reduced_states and result.qubits > 1:
                summary = "; ".join(
                    f"q{state.qubit} Bloch length {state.bloch_length:.4f}"
                    + (" (mixed)" if state.is_mixed else " (pure)")
                    for state in frame.reduced_states
                )
                facts.append(
                    Fact("step.reduced_states", "Reduced single-qubit states", summary, summary)
                )
    return facts


def substitute(text: str, facts: list[Fact]) -> tuple[str, list[str], list[str]]:
    """Replace [[fact:ID]] references with verified values.

    Returns the rendered text, the IDs actually used, and any invalid IDs.
    """
    lookup = {fact.id: fact for fact in facts}
    used: list[str] = []
    invalid: list[str] = []

    def replace(match: re.Match[str]) -> str:
        fact_id = match.group(1)
        fact = lookup.get(fact_id)
        if fact is None:
            invalid.append(fact_id)
            return "[unavailable value]"
        used.append(fact_id)
        return fact.value

    return FACT_REFERENCE.sub(replace, text), used, invalid
