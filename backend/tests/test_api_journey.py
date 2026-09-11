"""End-to-end API behaviour against a real database."""

from __future__ import annotations

import pytest

HZH = {
    "qubits": 1,
    "initial_state": {"kind": "basis", "basis_index": 0},
    "operations": [
        {"op": "h", "targets": [0]},
        {"op": "z", "targets": [0]},
        {"op": "h", "targets": [0]},
    ],
}
SINGLE_X = {
    "qubits": 1,
    "initial_state": {"kind": "basis", "basis_index": 0},
    "operations": [{"op": "x", "targets": [0]}],
}


def make_run(guest, topic_id, circuit, shots=16, seed=1):
    revision = guest.post("/api/v1/revisions", json={"topic_id": topic_id, "circuit": circuit})
    assert revision.status_code == 201, revision.text
    revision_id = revision.json()["revision_id"]
    run = guest.post(
        "/api/v1/runs",
        json={"revision_id": revision_id, "shots": shots, "seed": seed},
    )
    assert run.status_code == 201, run.text
    return revision_id, run.json()


def test_guest_session_is_created_and_reused(client):
    first = client.post("/api/v1/guest-session", headers={"origin": "http://127.0.0.1:5173"})
    assert first.status_code == 201
    assert first.json()["created"] is True
    second = client.post("/api/v1/guest-session", headers={"origin": "http://127.0.0.1:5173"})
    assert second.json()["created"] is False
    assert second.json()["principal_id"] == first.json()["principal_id"]


def test_session_cookie_is_httponly_and_the_token_is_not_returned(client):
    response = client.post("/api/v1/guest-session", headers={"origin": "http://127.0.0.1:5173"})
    cookie_header = response.headers.get("set-cookie", "")
    assert "qll_session" in cookie_header
    assert "HttpOnly" in cookie_header
    body = response.json()
    session_cookie = client.cookies.get("qll_session")
    assert session_cookie not in str(body)


def test_me_requires_a_session(client):
    assert client.get("/api/v1/me").status_code == 401


def test_mutation_without_csrf_header_is_rejected(client):
    client.post("/api/v1/guest-session", headers={"origin": "http://127.0.0.1:5173"})
    response = client.post(
        "/api/v1/revisions",
        json={"topic_id": "1-4", "circuit": SINGLE_X},
        headers={"origin": "http://127.0.0.1:5173"},
    )
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "csrf_failed"


def test_mutation_from_a_foreign_origin_is_rejected(guest):
    response = guest.client.post(
        "/api/v1/revisions",
        json={"topic_id": "1-4", "circuit": SINGLE_X},
        headers={"origin": "https://evil.example", "x-qll-csrf": guest.csrf},
    )
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "bad_origin"


def test_changed_gate_changes_computed_output(guest):
    _, without_z = make_run(guest, "1-7", {**HZH, "operations": HZH["operations"][:1] * 2})
    _, with_z = make_run(guest, "1-7", HZH)
    assert without_z["result"]["exact_probabilities"] == pytest.approx([1.0, 0.0])
    assert with_z["result"]["exact_probabilities"] == pytest.approx([0.0, 1.0])


def test_each_edit_creates_a_new_immutable_revision(guest):
    first, first_run = make_run(guest, "1-4", SINGLE_X)
    second, _ = make_run(guest, "1-4", HZH)
    assert first != second
    # The earlier revision still returns its original circuit and result.
    stored = guest.get(f"/api/v1/runs/{first_run['run_id']}").json()
    assert stored["revision_id"] == first
    assert stored["result"]["exact_probabilities"] == pytest.approx([0.0, 1.0])


def test_replay_returns_the_recorded_outcomes(guest):
    _, run = make_run(
        guest, "1-3", {**SINGLE_X, "operations": [{"op": "h", "targets": [0]}]}, shots=256, seed=7
    )
    replay = guest.get(f"/api/v1/runs/{run['run_id']}")
    assert replay.status_code == 200
    body = replay.json()
    assert body["read_kind"] == "recorded_replay"
    assert body["result"]["counts"] == run["result"]["counts"]


def test_a_new_run_is_a_distinct_record(guest):
    revision = guest.post(
        "/api/v1/revisions",
        json={
            "topic_id": "1-3",
            "circuit": {**SINGLE_X, "operations": [{"op": "h", "targets": [0]}]},
        },
    ).json()["revision_id"]
    first = guest.post(
        "/api/v1/runs", json={"revision_id": revision, "shots": 16, "seed": 1}
    ).json()
    second = guest.post(
        "/api/v1/runs", json={"revision_id": revision, "shots": 16, "seed": 2}
    ).json()
    assert first["run_id"] != second["run_id"]
    assert second["ordinal"] == first["ordinal"] + 1


def test_repeat_measurement_is_distinct_from_a_fresh_shot(guest):
    circuit = {
        "qubits": 1,
        "initial_state": {"kind": "named", "named": "plus"},
        "operations": [{"op": "measure_z", "targets": [0]}],
    }
    _, run = make_run(guest, "1-3", circuit, shots=1, seed=5)
    repeat = guest.post(f"/api/v1/runs/{run['run_id']}/repeat-measurement")
    assert repeat.status_code == 200
    body = repeat.json()
    assert body["repeatable"] is True
    assert body["probability"] == 1.0
    assert body["operation_kind"] == "conditional_repeat_measurement"
    assert body["outcome"] in (0, 1)
    # Repeating it again gives the same recorded outcome.
    again = guest.post(f"/api/v1/runs/{run['run_id']}/repeat-measurement").json()
    assert again["outcome"] == body["outcome"]


def test_a_second_guest_cannot_read_the_first_guests_run(guest, second_guest):
    _, run = make_run(guest, "1-4", SINGLE_X)
    response = second_guest.get(f"/api/v1/runs/{run['run_id']}")
    assert response.status_code == 404


def test_a_second_guest_cannot_run_the_first_guests_revision(guest, second_guest):
    revision_id, _ = make_run(guest, "1-4", SINGLE_X)
    response = second_guest.post("/api/v1/runs", json={"revision_id": revision_id, "shots": 16})
    assert response.status_code == 404


def test_a_second_guest_sees_separate_progress(guest, second_guest):
    guest.post("/api/v1/topics/1-1/steps", json={"step_id": "s1"})
    mine = guest.get("/api/v1/topics/1-1").json()
    theirs = second_guest.get("/api/v1/topics/1-1").json()
    assert mine["completed_steps"] == {"s1": True}
    assert theirs["completed_steps"] == {}


def test_disallowed_shot_count_is_rejected(guest):
    revision_id, _ = make_run(guest, "1-4", SINGLE_X)
    response = guest.post("/api/v1/runs", json={"revision_id": revision_id, "shots": 7})
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "shots_not_allowed"


def test_unnormalized_circuit_is_rejected_by_the_api(guest):
    response = guest.post(
        "/api/v1/revisions",
        json={
            "topic_id": "1-2",
            "circuit": {
                "qubits": 1,
                "initial_state": {
                    "kind": "amplitudes",
                    "amplitudes": [{"re": 0.5, "im": 0.0}, {"re": 0.5, "im": 0.0}],
                },
                "operations": [],
            },
        },
    )
    assert response.status_code == 422


def test_unsupported_operation_is_rejected(guest):
    response = guest.post(
        "/api/v1/revisions",
        json={
            "topic_id": "1-4",
            "circuit": {
                "qubits": 1,
                "initial_state": {"kind": "basis", "basis_index": 0},
                "operations": [{"op": "toffoli", "targets": [0]}],
            },
        },
    )
    assert response.status_code == 422


def test_topic_payload_never_contains_hints_or_answers(guest):
    body = guest.get("/api/v1/topics/1-2").json()
    assert "hints" not in body
    assert body["hint_levels"] == 4
    serialized = str(body)
    assert '"key"' not in serialized
    for task in body["tasks"]:
        assert "answer" not in task
        assert "key" not in task


def test_hints_are_served_on_request_and_recorded(guest):
    response = guest.post(
        "/api/v1/hints", json={"topic_id": "1-2", "task_id": "1-2.transfer", "level": 1}
    )
    assert response.status_code == 200
    assert response.json()["assistance_recorded"] is True
    availability = guest.get("/api/v1/tutor/hint-availability/1-2?task_id=1-2.transfer").json()
    assert availability["highest_level_delivered"] == 1


def test_task_submission_evaluates_and_records_evidence(guest):
    response = guest.post(
        "/api/v1/tasks/1-2.checkpoint-numeric/attempts",
        json={"submission": {"values": {"p0": "0.36", "p1": "0.64"}}},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["passed"] is True
    assert body["evidence_kind"] == "independent"
    progress = guest.get("/api/v1/progress").json()
    born = next(
        entry
        for entry in progress["chapter"]["skills"]
        if entry["skill_id"] == "amplitude.born_rule"
    )
    assert born["independent_count"] == 1


def test_heavy_hint_use_records_assisted_rather_than_independent(guest):
    for level in (1, 2, 3):
        guest.post(
            "/api/v1/hints",
            json={"topic_id": "1-2", "task_id": "1-2.transfer", "level": level},
        )
    body = guest.post(
        "/api/v1/tasks/1-2.transfer/attempts",
        json={"submission": {"values": {"p0": "0.64", "p1": "0.36"}}},
    ).json()
    assert body["passed"] is True
    assert body["assisted"] is True
    assert body["evidence_kind"] == "assisted"


def test_duplicate_submission_does_not_duplicate_evidence(guest):
    payload = {
        "submission": {"values": {"p0": "0.36", "p1": "0.64"}},
        "idempotency_key": "key-1",
    }
    first = guest.post("/api/v1/tasks/1-2.checkpoint-numeric/attempts", json=payload).json()
    second = guest.post("/api/v1/tasks/1-2.checkpoint-numeric/attempts", json=payload).json()
    assert first["duplicate"] is False
    assert second["duplicate"] is True
    progress = guest.get("/api/v1/progress").json()
    born = next(
        entry
        for entry in progress["chapter"]["skills"]
        if entry["skill_id"] == "amplitude.born_rule"
    )
    assert born["independent_count"] == 1


def test_idempotency_key_reuse_with_different_data_is_rejected(guest):
    guest.post(
        "/api/v1/tasks/1-2.checkpoint-numeric/attempts",
        json={"submission": {"values": {"p0": "0.36", "p1": "0.64"}}, "idempotency_key": "k"},
    )
    response = guest.post(
        "/api/v1/tasks/1-2.checkpoint-compare/attempts",
        json={"submission": {"selection": "a"}, "idempotency_key": "k"},
    )
    assert response.status_code == 409


def test_failed_attempt_does_not_reduce_existing_evidence(guest):
    guest.post(
        "/api/v1/tasks/1-2.checkpoint-numeric/attempts",
        json={"submission": {"values": {"p0": "0.36", "p1": "0.64"}}},
    )
    guest.post(
        "/api/v1/tasks/1-2.transfer/attempts",
        json={"submission": {"values": {"p0": "0.1", "p1": "0.9"}}},
    )
    progress = guest.get("/api/v1/progress").json()
    born = next(
        entry
        for entry in progress["chapter"]["skills"]
        if entry["skill_id"] == "amplitude.born_rule"
    )
    assert born["independent_count"] == 1


def test_incorrect_prediction_never_blocks_a_topic(guest):
    response = guest.post(
        "/api/v1/topics/1-3/prediction",
        json={"prediction_id": "1-3.predict", "selection": "a"},
    )
    assert response.status_code == 200
    assert "does not affect completion" in response.json()["note"]
    topic = guest.get("/api/v1/topics/1-3").json()
    assert topic["progress"]["status"] in {"in_progress", "not_started"}


def test_course_marks_later_chapters_coming_soon(guest):
    body = guest.get("/api/v1/course").json()
    published = [c for c in body["chapters"] if c["publication"] == "published"]
    coming = [c for c in body["chapters"] if c["publication"] == "coming_soon"]
    assert [c["number"] for c in published] == [1]
    assert len(coming) == 12
    for chapter in coming:
        assert chapter["access"]["readiness"] == "not_assessed"
        assert chapter["access"]["reason_code"] == "coming_soon"


def test_unpublished_chapter_route_does_not_serve_fake_content(guest):
    response = guest.get("/api/v1/course/chapter-6")
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "chapter_not_published"


def test_unknown_topic_is_not_invented(guest):
    assert guest.get("/api/v1/topics/9-9").status_code == 404


def test_grover_preview_run_and_seen_status(guest):
    response = guest.post(
        "/api/v1/grover/runs",
        json={"candidates": 4, "target": 2, "iterations": 1, "shots": 256, "seed": 4},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["result"]["exact_probabilities"][2] == pytest.approx(1.0)
    assert body["analytical_target_probability"] == pytest.approx(1.0)
    assert body["oracle_query_count"] == 256
    progress = guest.get("/api/v1/progress").json()
    grover = next(p for p in progress["previews"] if p["algorithm_id"] == "grover")
    assert grover["status"] == "seen"


def test_grover_overshoot_visible_through_the_api(guest):
    two = guest.post(
        "/api/v1/grover/runs",
        json={"candidates": 8, "target": 5, "iterations": 2, "shots": 1, "seed": 1},
    ).json()
    three = guest.post(
        "/api/v1/grover/runs",
        json={"candidates": 8, "target": 5, "iterations": 3, "shots": 1, "seed": 1},
    ).json()
    assert two["result"]["exact_probabilities"][5] == pytest.approx(121 / 128)
    assert three["result"]["exact_probabilities"][5] == pytest.approx(169 / 512)
    assert three["result"]["exact_probabilities"][5] < two["result"]["exact_probabilities"][5]


def test_missing_preparation_variant_is_labelled_outside_the_formula(guest):
    body = guest.post(
        "/api/v1/grover/runs",
        json={
            "candidates": 4,
            "target": 2,
            "iterations": 1,
            "shots": 1,
            "preparation": "missing",
        },
    ).json()
    assert body["formula_applies"] is False
    assert body["analytical_target_probability"] is None
    assert "does not apply" in body["formula_note"]


def test_analysis_endpoint_is_labelled_analytical(guest):
    body = guest.get("/api/v1/grover/analysis?candidates=8").json()
    assert body["result_kind"] == "analytical_prediction"
    assert body["best_iterations"] == 2
    row = next(r for r in body["rows"] if r["iterations"] == 2)
    assert row["ideal_target_probability"] == pytest.approx(121 / 128)
    assert row["classical_check_and_guess"] == pytest.approx(3 / 8)


def test_reset_progress_clears_only_this_guest(guest, second_guest):
    guest.post("/api/v1/topics/1-1/steps", json={"step_id": "s1"})
    second_guest.post("/api/v1/topics/1-1/steps", json={"step_id": "s1"})
    guest.post("/api/v1/reset-progress")
    assert guest.get("/api/v1/topics/1-1").json()["completed_steps"] == {}
    assert second_guest.get("/api/v1/topics/1-1").json()["completed_steps"] == {"s1": True}


def test_health_endpoints(client):
    assert client.get("/api/v1/health/live").json()["status"] == "live"
    ready = client.get("/api/v1/health/ready")
    assert ready.status_code == 200
    assert ready.json()["checks"]["database"] == "ok"
    assert "nvidia_api_key" not in ready.text.lower()
