"""Assessment submission, scoring, evidence, and answer-key confinement."""

from __future__ import annotations

import pytest

CORRECT_A = {
    "A1": "b",
    "A2": {"p1": "0.64"},
    "A3": "a",
    "A4": "a",
    "A5": "a",
    "A6": {
        "qubits": 1,
        "initial_state": {"kind": "basis", "basis_index": 1},
        "operations": [{"op": "x", "targets": [0]}],
    },
    "A7": "a",
    "A8": {"i1": "global", "i2": "relative"},
    "A9": "a",
    "A10": {"choice": "z", "reason": "a"},
}

CORRECT_B = {
    "B1": "a",
    "B2": {"p1": "0.36"},
    "B3": "a",
    "B4": "a",
    "B5": "a",
    "B6": {
        "qubits": 1,
        "initial_state": {"kind": "basis", "basis_index": 0},
        "operations": [
            {"op": "x", "targets": [0]},
            {"op": "x", "targets": [0]},
            {"op": "x", "targets": [0]},
        ],
    },
    "B7": "a",
    "B8": {"i1": "global", "i2": "relative"},
    "B9": "a",
    "B10": {"choice": "z", "reason": "a"},
}


def complete_all_topics(guest):
    """Complete the required steps and tasks so the practice rule is satisfied."""
    from app.curriculum import loader

    correct = {
        "1-1.checkpoint": {"matches": {"vec01": "ket1", "bars10": "ket0", "outcome": "classical"}},
        "1-1.transfer": {"selection": "b"},
        "1-2.checkpoint-numeric": {"values": {"p0": "0.36", "p1": "0.64"}},
        "1-2.checkpoint-compare": {"selection": "a"},
        "1-2.checkpoint-normalization": {"selection": "a"},
        "1-2.transfer": {"values": {"p0": "0.64", "p1": "0.36"}},
        "1-3.checkpoint-counts": {"selection": "a"},
        "1-3.checkpoint-action": {"selection": "a"},
        "1-3.checkpoint-remeasure": {"selection": "a"},
        "1-3.transfer": {"selection": "a"},
        "1-4.checkpoint": {"selection": "a"},
        "1-4.transfer": {"values": {"p0": "0.64"}},
        "1-5.checkpoint-deterministic": {"selection": "a"},
        "1-5.checkpoint-signs": {"selection": "a"},
        "1-5.transfer": {"selection": "a"},
        "1-6.checkpoint-classify": {"assignments": {"pair1": "relative", "pair2": "global"}},
        "1-6.checkpoint-probabilities": {"selection": "a"},
        "1-6.transfer": {"selection": "a"},
        "1-7.checkpoint-divergence": {"selection": "a"},
        "1-7.checkpoint-measurement": {"selection": "a"},
        "1-7.transfer": {"selection": "a"},
        "1-8.capstone-a-role": {"selection": "a"},
        "1-8.capstone-b": {"selection": "a"},
        "1-8.revisit-grover": {"selection": "a"},
    }
    circuits = {
        "1-4.build": [{"op": "x", "targets": [0]}],
        "1-5.build": [{"op": "h", "targets": [0]}],
        "1-7.build": [
            {"op": "h", "targets": [0]},
            {"op": "z", "targets": [0]},
            {"op": "h", "targets": [0]},
        ],
        "1-8.capstone-a-zero": [{"op": "h", "targets": [0]}, {"op": "h", "targets": [0]}],
        "1-8.capstone-a-one": [
            {"op": "h", "targets": [0]},
            {"op": "z", "targets": [0]},
            {"op": "h", "targets": [0]},
        ],
    }

    for topic in loader.load_chapter("chapter-1")["topics"]:
        for step in topic["completion"]["required_step_ids"]:
            guest.post(f"/api/v1/topics/{topic['id']}/steps", json={"step_id": step})
        for task_id in topic["completion"]["required_task_ids"]:
            if task_id in correct:
                response = guest.post(
                    f"/api/v1/tasks/{task_id}/attempts", json={"submission": correct[task_id]}
                )
                assert response.json()["passed"] is True, (task_id, response.json())
            elif task_id in circuits:
                revision = guest.post(
                    "/api/v1/revisions",
                    json={
                        "topic_id": topic["id"],
                        "circuit": {
                            "qubits": 1,
                            "initial_state": {"kind": "basis", "basis_index": 0},
                            "operations": circuits[task_id],
                        },
                    },
                ).json()["revision_id"]
                run = guest.post(
                    "/api/v1/runs", json={"revision_id": revision, "shots": 16, "seed": 2}
                ).json()
                response = guest.post(
                    f"/api/v1/tasks/{task_id}/attempts",
                    json={"submission": {}, "run_id": run["run_id"]},
                )
                assert response.json()["passed"] is True, (task_id, response.json())
            elif task_id == "1-8.capstone-c":
                revision = guest.post(
                    "/api/v1/revisions",
                    json={
                        "topic_id": "1-8",
                        "circuit": {
                            "qubits": 1,
                            "initial_state": {"kind": "basis", "basis_index": 0},
                            "operations": [{"op": "h", "targets": [0]}],
                        },
                    },
                ).json()["revision_id"]
                run = guest.post(
                    "/api/v1/runs", json={"revision_id": revision, "shots": 256, "seed": 13}
                ).json()
                counts = run["result"]["counts"]["|0>"]
                response = guest.post(
                    "/api/v1/tasks/1-8.capstone-c/attempts",
                    json={
                        "submission": {
                            "values": {
                                "exact_p0": "0.5",
                                "count_0": str(counts),
                                "shots": "256",
                            },
                            "selection": "a",
                        },
                        "run_id": run["run_id"],
                    },
                )
                assert response.json()["passed"] is True, response.json()
            else:  # pragma: no cover - every required task is covered above
                raise AssertionError(f"no answer prepared for {task_id}")


def test_assessment_payload_never_contains_the_answer_key(guest):
    body = guest.get("/api/v1/assessments/chapter-1").json()
    serialized = str(body)
    assert "answer_key" not in serialized
    assert "revision_guidance" not in serialized
    assert len(body["forms"]["A"]) == 10
    assert len(body["forms"]["B"]) == 10


def test_full_journey_completes_every_topic(guest):
    complete_all_topics(guest)
    progress = guest.get("/api/v1/progress").json()
    assert progress["chapter"]["topics_complete"] == 8
    assert progress["chapter"]["next_topic_id"] is None


@pytest.mark.parametrize(("form", "answers"), [("A", CORRECT_A), ("B", CORRECT_B)])
def test_both_forms_score_ten_out_of_ten_for_correct_answers(guest, form, answers):
    complete_all_topics(guest)
    attempt = guest.post(
        "/api/v1/assessments/chapter-1/attempts", json={"form": form, "mode": "test"}
    ).json()
    guest.patch(f"/api/v1/assessments/attempts/{attempt['attempt_id']}", json={"answers": answers})
    result = guest.post(
        f"/api/v1/assessments/attempts/{attempt['attempt_id']}/submit", json={}
    ).json()
    assert result["score"] == 10.0
    assert result["passed"] is True
    assert result["essential_items_passed"] is True


def test_answers_survive_a_reload_before_submission(guest):
    attempt = guest.post(
        "/api/v1/assessments/chapter-1/attempts", json={"form": "A", "mode": "practice"}
    ).json()
    guest.patch(
        f"/api/v1/assessments/attempts/{attempt['attempt_id']}", json={"answers": {"A1": "b"}}
    )
    reopened = guest.post(
        "/api/v1/assessments/chapter-1/attempts", json={"form": "A", "mode": "practice"}
    ).json()
    assert reopened["attempt_id"] == attempt["attempt_id"]
    assert reopened["answers"] == {"A1": "b"}


def test_failing_essential_items_fails_despite_a_high_score(guest):
    complete_all_topics(guest)
    answers = {**CORRECT_A, "A8": {"i1": "relative", "i2": "relative"}, "A9": "b"}
    attempt = guest.post(
        "/api/v1/assessments/chapter-1/attempts", json={"form": "A", "mode": "test"}
    ).json()
    guest.patch(f"/api/v1/assessments/attempts/{attempt['attempt_id']}", json={"answers": answers})
    result = guest.post(
        f"/api/v1/assessments/attempts/{attempt['attempt_id']}/submit", json={}
    ).json()
    assert result["score"] == 8.0
    assert result["essential_items_passed"] is False
    assert result["passed"] is False
    assert any(
        entry["skill_id"] == "interference.phase_to_probability"
        for entry in result["revision_guidance"]
    )


def test_alternative_circuit_answer_passes_the_construction_item(guest):
    attempt = guest.post(
        "/api/v1/assessments/chapter-1/attempts", json={"form": "B", "mode": "practice"}
    ).json()
    one_gate = {
        **CORRECT_B,
        "B6": {
            "qubits": 1,
            "initial_state": {"kind": "basis", "basis_index": 0},
            "operations": [{"op": "x", "targets": [0]}],
        },
    }
    guest.patch(f"/api/v1/assessments/attempts/{attempt['attempt_id']}", json={"answers": one_gate})
    result = guest.post(
        f"/api/v1/assessments/attempts/{attempt['attempt_id']}/submit", json={}
    ).json()
    item = next(entry for entry in result["per_item"] if entry["item_id"] == "B6")
    assert item["passed"] is True


def test_duplicate_submission_returns_the_original_and_adds_no_evidence(guest):
    attempt = guest.post(
        "/api/v1/assessments/chapter-1/attempts", json={"form": "A", "mode": "test"}
    ).json()
    guest.patch(
        f"/api/v1/assessments/attempts/{attempt['attempt_id']}", json={"answers": CORRECT_A}
    )
    first = guest.post(
        f"/api/v1/assessments/attempts/{attempt['attempt_id']}/submit", json={}
    ).json()
    second = guest.post(
        f"/api/v1/assessments/attempts/{attempt['attempt_id']}/submit", json={}
    ).json()
    assert first["duplicate"] is False
    assert second["duplicate"] is True
    assert second["score"] == first["score"]
    progress = guest.get("/api/v1/progress").json()
    basis = next(
        entry
        for entry in progress["chapter"]["skills"]
        if entry["skill_id"] == "basis.read_single_qubit"
    )
    assert basis["independent_count"] == 1


def test_evidence_only_records_skills_the_rubric_evaluated(guest):
    attempt = guest.post(
        "/api/v1/assessments/chapter-1/attempts", json={"form": "A", "mode": "test"}
    ).json()
    only_first = {"A1": "b"}
    guest.patch(
        f"/api/v1/assessments/attempts/{attempt['attempt_id']}", json={"answers": only_first}
    )
    guest.post(f"/api/v1/assessments/attempts/{attempt['attempt_id']}/submit", json={})
    progress = guest.get("/api/v1/progress").json()
    by_skill = {entry["skill_id"]: entry for entry in progress["chapter"]["skills"]}
    assert by_skill["basis.read_single_qubit"]["independent_count"] == 1
    assert by_skill["interference.phase_to_probability"]["independent_count"] == 0


def test_a_submitted_attempt_cannot_be_edited(guest):
    attempt = guest.post(
        "/api/v1/assessments/chapter-1/attempts", json={"form": "A", "mode": "test"}
    ).json()
    guest.post(f"/api/v1/assessments/attempts/{attempt['attempt_id']}/submit", json={})
    response = guest.patch(
        f"/api/v1/assessments/attempts/{attempt['attempt_id']}", json={"answers": CORRECT_A}
    )
    assert response.status_code == 409


def test_another_guest_cannot_read_or_submit_an_attempt(guest, second_guest):
    attempt = guest.post(
        "/api/v1/assessments/chapter-1/attempts", json={"form": "A", "mode": "test"}
    ).json()
    assert (
        second_guest.patch(
            f"/api/v1/assessments/attempts/{attempt['attempt_id']}",
            json={"answers": CORRECT_A},
        ).status_code
        == 404
    )
    assert (
        second_guest.post(
            f"/api/v1/assessments/attempts/{attempt['attempt_id']}/submit", json={}
        ).status_code
        == 404
    )


def test_converting_a_test_attempt_to_practice_is_a_platform_action(guest):
    attempt = guest.post(
        "/api/v1/assessments/chapter-1/attempts", json={"form": "A", "mode": "test"}
    ).json()
    response = guest.post(
        f"/api/v1/assessments/attempts/{attempt['attempt_id']}/convert-to-practice"
    )
    assert response.status_code == 200
    assert response.json()["mode"] == "practice"


def test_demonstrated_skills_require_two_distinct_item_families(guest):
    """One correct test item is evidence; it is not yet a demonstrated skill."""
    attempt = guest.post(
        "/api/v1/assessments/chapter-1/attempts", json={"form": "A", "mode": "test"}
    ).json()
    guest.patch(
        f"/api/v1/assessments/attempts/{attempt['attempt_id']}", json={"answers": {"A1": "b"}}
    )
    guest.post(f"/api/v1/assessments/attempts/{attempt['attempt_id']}/submit", json={})
    progress = guest.get("/api/v1/progress").json()
    assert "basis.read_single_qubit" not in progress["demonstrated_skills"]
    guest.post("/api/v1/tasks/1-1.transfer/attempts", json={"submission": {"selection": "b"}})
    progress = guest.get("/api/v1/progress").json()
    assert "basis.read_single_qubit" in progress["demonstrated_skills"]
