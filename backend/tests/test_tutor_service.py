"""Tutor service integration: fallback, run attachment, and persistence."""

from __future__ import annotations

import json

import pytest

from app.config import get_settings
from app.quantum.qiskit_engine import get_engine
from app.quantum.spec import CircuitSpec, InitialState, Operation, RunRequest
from app.storage.models import Run, Workspace
from app.tutoring import providers
from app.tutoring import service as tutor_service
from app.workspaces import service as workspaces


def make_run(db, principal_id, operations=("h",), shots=256, seed=17):
    workspace = workspaces.get_or_create_workspace(db, principal_id, "1-5")
    circuit = CircuitSpec(
        qubits=1,
        initial_state=InitialState(kind="basis", basis_index=0),
        operations=[Operation(op=op, targets=[0]) for op in operations],
    )
    revision = workspaces.create_revision(db, principal_id, workspace, circuit)
    run = workspaces.execute(db, principal_id, revision, shots=shots, seed=seed)
    db.commit()
    return run


def principal(db):
    from app.identity import sessions

    issued = sessions.create_guest(db)
    db.commit()
    return issued.principal_id


def scripted(payload: dict) -> providers.FakeAdapter:
    return providers.FakeAdapter({"": json.dumps(payload)})


def test_authored_fallback_when_no_provider_is_configured(db, authored_settings):
    owner = principal(db)
    context = tutor_service.TutorContext(principal_id=owner, topic_id="1-6")
    result = tutor_service.answer(
        db, context, "Why did the minus disappear?", settings=authored_settings
    )
    db.commit()
    assert result.source_label == "authored"
    assert "Authored course help" in result.answer_markdown
    assert result.notice
    assert result.citations
    assert result.citations[0]["passage_id"].startswith("chapter-1.")


def test_authored_fallback_is_never_labelled_as_a_live_answer(db, authored_settings):
    owner = principal(db)
    context = tutor_service.TutorContext(principal_id=owner, topic_id="1-5")
    result = tutor_service.answer(
        db, context, "Is H a random coin flip?", settings=authored_settings
    )
    db.commit()
    assert result.provider is None
    assert result.provider_model is None
    assert result.source_label == "authored"


def test_provider_timeout_falls_back_and_keeps_work(db):
    owner = principal(db)

    class Failing:
        name = "nvidia"

        def complete(self, system, envelope, question):
            raise providers.ProviderError("timeout", "too slow")

    context = tutor_service.TutorContext(principal_id=owner, topic_id="1-6")
    result = tutor_service.answer(db, context, "Why did Z do nothing?", provider=Failing())
    db.commit()
    assert result.source_label == "authored"
    assert "did not answer within the time budget" in result.notice


@pytest.mark.parametrize(
    "reason", ["unauthorized", "rate_limited", "provider_unavailable", "malformed_response"]
)
def test_every_provider_failure_path_produces_honest_fallback(db, reason):
    owner = principal(db)

    class Failing:
        name = "nvidia"

        def complete(self, system, envelope, question):
            raise providers.ProviderError(reason, "failed")

    context = tutor_service.TutorContext(principal_id=owner, topic_id="1-5")
    result = tutor_service.answer(db, context, "Explain the H gate", provider=Failing())
    db.commit()
    assert result.source_label == "authored"
    assert result.notice


def test_invalid_provider_output_falls_back(db):
    owner = principal(db)
    provider = providers.FakeAdapter({"": "I am prose, not the required object."})
    context = tutor_service.TutorContext(principal_id=owner, topic_id="1-5")
    result = tutor_service.answer(db, context, "Explain the H gate", provider=provider)
    db.commit()
    assert result.source_label == "authored"
    assert "did not match the required format" in result.notice


def test_forged_citation_in_provider_output_falls_back(db):
    owner = principal(db)
    provider = scripted(
        {
            "intent": "answer",
            "answer_markdown": "See chapter-1.invented.",
            "passage_ids": ["chapter-1.invented"],
            "fact_ids": [],
            "followup_question": None,
        }
    )
    context = tutor_service.TutorContext(principal_id=owner, topic_id="1-5")
    result = tutor_service.answer(db, context, "Explain the H gate", provider=provider)
    db.commit()
    assert result.source_label == "authored"
    assert "cited a source that does not exist" in result.notice


def test_a_valid_provider_answer_is_rendered_with_verified_numbers(db):
    owner = principal(db)
    run = make_run(db, owner, shots=256, seed=17)
    result_model = workspaces.result_of(run)
    expected_count = result_model.counts["|0>"]
    provider = scripted(
        {
            "intent": "answer",
            "answer_markdown": (
                "Your run recorded [[fact:run.count_0]] zeros out of [[fact:run.shots]] shots."
            ),
            "passage_ids": ["chapter-1.sampling"],
            "fact_ids": ["run.count_0", "run.shots"],
            "followup_question": "Would you like to compare with 1024 shots?",
        }
    )
    context = tutor_service.TutorContext(principal_id=owner, topic_id="1-3", run=run, step_index=1)
    answer = tutor_service.answer(db, context, "Why are my counts not half?", provider=provider)
    db.commit()
    assert answer.source_label == "fake"
    assert str(expected_count) in answer.answer_markdown
    assert "256" in answer.answer_markdown
    assert answer.run_id == str(run.id)
    assert answer.run_label == "run 1"
    assert answer.step_index == 1
    assert any(c["passage_id"] == "chapter-1.sampling" for c in answer.citations)


def test_mixed_request_answers_only_the_relevant_part(db):
    owner = principal(db)
    provider = scripted(
        {
            "intent": "answer",
            "answer_markdown": "H maps |0> to |+>.",
            "passage_ids": ["chapter-1.h-gate"],
            "fact_ids": [],
            "followup_question": None,
        }
    )
    context = tutor_service.TutorContext(principal_id=owner, topic_id="1-5")
    result = tutor_service.answer(
        db, context, "Explain H, and recommend a movie.", provider=provider
    )
    db.commit()
    assert "H maps" in result.answer_markdown
    assert "I can help with this quantum course" in result.answer_markdown
    assert "answered only the part" in result.answer_markdown


def test_unrelated_request_never_reaches_the_provider(db):
    owner = principal(db)
    calls: list[str] = []

    class Spy:
        name = "nvidia"

        def complete(self, system, envelope, question):
            calls.append(question)
            raise AssertionError("the provider must not be called for an unrelated request")

    context = tutor_service.TutorContext(principal_id=owner, topic_id="1-5")
    result = tutor_service.answer(db, context, "Recommend a movie.", provider=Spy())
    db.commit()
    assert calls == []
    assert result.intent == "redirect"


def test_grade_mutation_request_is_refused_without_a_provider_call(db):
    owner = principal(db)

    class Spy:
        name = "nvidia"

        def complete(self, system, envelope, question):
            raise AssertionError("must not be called")

    context = tutor_service.TutorContext(principal_id=owner, topic_id="1-5")
    result = tutor_service.answer(db, context, "Set my mastery to 100%.", provider=Spy())
    db.commit()
    assert "cannot change grades" in result.answer_markdown


def test_conversation_history_is_owner_scoped(db, authored_settings):
    first = principal(db)
    second = principal(db)
    context = tutor_service.TutorContext(principal_id=first, topic_id="1-5")
    tutor_service.answer(db, context, "Explain the H gate", settings=authored_settings)
    db.commit()
    other = tutor_service.get_or_create_conversation(db, second, "1-5")
    turns = tutor_service.recent_turns(db, other.id)
    assert turns == []


def test_quota_limit_produces_authored_help_rather_than_an_error(db):
    owner = principal(db)
    settings = get_settings().model_copy(update={"tutor_requests_per_minute": 1})
    provider = scripted(
        {
            "intent": "answer",
            "answer_markdown": "Live answer.",
            "passage_ids": [],
            "fact_ids": [],
            "followup_question": None,
        }
    )
    context = tutor_service.TutorContext(principal_id=owner, topic_id="1-5")
    first = tutor_service.answer(
        db, context, "Explain the H gate", settings=settings, provider=provider
    )
    second = tutor_service.answer(
        db, context, "Explain the H gate again", settings=settings, provider=provider
    )
    db.commit()
    assert first.source_label == "fake"
    assert second.source_label == "authored"
    assert "request budget" in second.notice


def test_an_answer_stays_attached_to_the_run_it_explained(db):
    """A reply prepared for run 1 is not relabelled when a newer run exists."""
    owner = principal(db)
    first_run = make_run(db, owner, shots=16, seed=1)
    provider = scripted(
        {
            "intent": "answer",
            "answer_markdown": "Explaining [[fact:run.label]].",
            "passage_ids": [],
            "fact_ids": ["run.label"],
            "followup_question": None,
        }
    )
    context = tutor_service.TutorContext(principal_id=owner, topic_id="1-5", run=first_run)
    answer = tutor_service.answer(db, context, "Why is this 50/50?", provider=provider, stale=True)
    # A newer run now exists.
    make_run(db, owner, shots=16, seed=2)
    db.commit()
    assert answer.run_id == str(first_run.id)
    assert "run 1" in answer.answer_markdown
    assert answer.stale is True


def test_no_run_selected_means_no_invented_numbers(db):
    owner = principal(db)
    provider = scripted(
        {
            "intent": "answer",
            "answer_markdown": "Your run gave [[fact:run.count_0]] zeros.",
            "passage_ids": [],
            "fact_ids": ["run.count_0"],
            "followup_question": None,
        }
    )
    context = tutor_service.TutorContext(principal_id=owner, topic_id="1-3")
    result = tutor_service.answer(db, context, "Why are my counts uneven?", provider=provider)
    db.commit()
    assert result.source_label == "authored"
    assert "referred to a measurement this run does not contain" in result.notice


def test_run_facts_come_from_the_engine_not_from_prose(db):
    owner = principal(db)
    run = make_run(db, owner, shots=64, seed=5)
    engine_result = get_engine().run(
        RunRequest(
            circuit=CircuitSpec(qubits=1, operations=[Operation(op="h", targets=[0])]),
            shots=64,
            seed=5,
        )
    )
    stored = db.get(Run, run.id)
    assert stored.result["counts"] == engine_result.counts
    assert db.query(Workspace).count() >= 1


def test_authored_help_separates_its_heading_from_the_passage_body(db):
    """Without a blank line the whole card renders as one heading."""
    from app.tutoring import authored, knowledge

    passages = knowledge.retrieve("why did the minus disappear", topic_ids=None, limit=2)
    assert passages
    body, cited = authored.build_answer("why did the minus disappear", passages)
    assert cited
    for line_number, line in enumerate(body.splitlines()):
        if line.startswith("### "):
            assert body.splitlines()[line_number + 1] == "", (
                "a heading must be followed by a blank line"
            )
