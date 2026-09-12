import json
import math
import uuid

import numpy as np
import pytest

from app.api.routes_learning import validate_rating
from app.quantum.chapter_labs import LabInput, simulate
from app.tutoring.chapter_scope import eligible_topics, future_reply
from app.tutoring.knowledge import retrieve


@pytest.mark.parametrize("topic", [f"2-{i}" for i in range(1, 7)] + [f"3-{i}" for i in range(1, 8)])
def test_all_labs_are_normalized(topic):
    for variant in ("A", "B", "C"):
        _, result = simulate(topic, LabInput(variant=variant))
        assert sum(result.exact_probabilities) == pytest.approx(1)
        assert sum(result.counts.values()) == 256
        for frame in result.frames:
            assert sum(frame.probabilities) == pytest.approx(1)


@pytest.mark.parametrize("phase,p0", [(0, 1), (math.pi / 2, 0.5), (math.pi, 0)])
def test_phase_interference(phase, p0):
    _, result = simulate("2-4", LabInput(angle=phase))
    assert result.frames[2].probabilities == pytest.approx([0.5, 0.5])
    assert result.exact_probabilities[0] == pytest.approx(p0)


def test_bell_and_mixture_are_different_in_x():
    _, bell_z = simulate("3-6", LabInput())
    _, mix_z = simulate("3-6", LabInput(variant="B"))
    assert bell_z.exact_probabilities == pytest.approx(mix_z.exact_probabilities)
    _, bell_x = simulate("3-6", LabInput(basis="X"))
    _, mix_x = simulate("3-6", LabInput(variant="B", basis="X"))
    assert bell_x.exact_probabilities == pytest.approx([0.5, 0, 0, 0.5])
    assert mix_x.exact_probabilities == pytest.approx([0.25] * 4)
    assert mix_x.frames[-1].amplitudes == []
    assert all(s.is_mixed for s in mix_x.frames[-1].reduced_states)


def test_y_readout():
    _, result = simulate("2-5", LabInput(variant="C", basis="Y"))
    assert result.exact_probabilities == pytest.approx([1, 0])


@pytest.mark.parametrize(
    "variant,expected", [("A", [0, 0, 1]), ("B", [1, 0, 0]), ("C", [0, 0.96, -0.28])]
)
def test_teleportation_every_branch(variant, expected):
    _, result = simulate("3-7", LabInput(variant=variant))
    assert len(result.branches) == 4
    for frame in result.frames[-4:]:
        assert frame.reduced_states[2].bloch == pytest.approx(expected)
        assert frame.branch_probability == pytest.approx(0.25)
    _, omitted = simulate("3-7", LabInput(variant=variant, correction=False))
    average = np.mean([f.reduced_states[2].bloch for f in omitted.frames[-4:]], axis=0)
    assert average == pytest.approx([0, 0, 0], abs=1e-9)


def test_boundary_and_empty_scope():
    assert "ch2-6" in eligible_topics("2-1")
    assert "ch3-1" not in eligible_topics("2-6")
    assert "ch2-1" not in eligible_topics("1-8")
    assert eligible_topics("99-1") == []
    assert retrieve("amplitude", topic_ids=[]) == []
    assert "Chapter 3" in future_reply("Bell state", "2-4")
    assert "Chapter 2" in future_reply("Bloch sphere", "1-8")
    assert future_reply("Hadamard", "2-4") is None


def test_assessor_requires_real_evidence():
    raw = {
        "criteria": [
            {"id": c, "score": 2, "quote": "invented", "feedback": "ok"}
            for c in ("claim", "mechanism", "transfer")
        ],
        "critical_misconception": False,
        "disposition": "sufficient",
    }
    with pytest.raises(ValueError):
        validate_rating(json.dumps(raw), "my actual answer")


def test_assessor_rejects_critical_false_pass():
    raw = {
        "criteria": [
            {"id": c, "score": 2, "quote": "same odds", "feedback": "ok"}
            for c in ("claim", "mechanism", "transfer")
        ],
        "critical_misconception": True,
        "disposition": "sufficient",
    }
    with pytest.raises(ValueError):
        validate_rating(json.dumps(raw), "same odds")


def test_only_reviewed_distinct_evidence_counts():
    from types import SimpleNamespace

    from app.api.routes_learning import evidence_summary

    def row(family, status="reviewed", critical=False):
        return SimpleNamespace(
            topic_id="2-1",
            task_id=family,
            assisted=False,
            passed=True,
            evaluation={"status": status, "rating": {"critical_misconception": critical}},
        )

    assert not evidence_summary(["2-1"], [row("a"), row("a")])["demonstrated"]
    assert not evidence_summary(["2-1"], [row("a"), row("b", "provisional")])["demonstrated"]
    assert evidence_summary(["2-1"], [row("a"), row("b")])["demonstrated"]
    assert not evidence_summary(["2-1"], [row("a"), row("b", critical=True)])["demonstrated"]


def test_calibration_rejects_family_leakage():
    from app.tools.calibrate_understanding import evaluate

    rows = [{"family": "same", "split": split} for split in ("development", "heldout")]
    with pytest.raises(ValueError, match="leakage"):
        evaluate(rows)


def test_calibration_reports_false_passes_and_abstention():
    from app.tools.calibrate_understanding import evaluate

    rows = [
        {
            "family": "a",
            "split": "heldout",
            "human_scores": [0, 0, 0],
            "model_scores": [2, 2, 2],
            "human_critical": True,
            "model_sufficient": True,
        },
        {
            "family": "b",
            "split": "heldout",
            "human_scores": [2, 2, 2],
            "model_scores": None,
            "human_critical": False,
            "model_sufficient": False,
        },
    ]
    result = evaluate(rows)
    assert result["critical_false_passes"] == 1
    assert result["abstention_rate"] == 0.5


def test_new_content_and_pending_evidence(guest):
    chapter = guest.get("/api/v1/course/chapter-2")
    assert chapter.status_code == 200
    assert len(chapter.json()["topics"]) == 6
    payload = guest.get("/api/v1/understanding/chapter-2").json()
    assert "key" not in payload["items"][0]
    item = payload["items"][0]
    body = {
        "item_id": item["id"],
        "selection": 0,
        "explanation": "I need to review this.",
        "idempotency_key": str(uuid.uuid4()),
    }
    result = guest.post("/api/v1/understanding/chapter-2", json=body)
    assert result.status_code == 200
    assert result.json()["evaluation"]["status"] == "awaiting_evaluation"
    assert result.json()["evaluation"]["demonstrated"] is False
    assert (
        guest.post("/api/v1/understanding/chapter-2", json=body).json()["id"] == result.json()["id"]
    )
    assert (
        guest.post(
            "/api/v1/understanding/chapter-1", json={**body, "idempotency_key": str(uuid.uuid4())}
        ).status_code
        == 422
    )


def test_new_labs_save_run_and_respect_tutor_topic(guest):
    response = guest.post("/api/v1/chapter-labs/3-6", json={"variant": "B", "basis": "X"})
    assert response.status_code == 200
    run = response.json()
    assert guest.get(f"/api/v1/runs/{run['run_id']}").status_code == 200
    leaked = guest.post(
        "/api/v1/tutor/turns",
        json={"topic_id": "1-1", "message": "explain this", "run_id": run["run_id"]},
    )
    assert leaked.status_code == 422
