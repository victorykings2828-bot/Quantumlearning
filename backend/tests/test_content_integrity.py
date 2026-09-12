"""Authored content validation and answer-key confinement."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from app.curriculum import access, loader

CHAPTER = loader.load_chapter("chapter-1")
RUBRICS = loader.load_task_rubrics()
ASSESSMENT = loader.load_assessment()

EXPECTED_TOPIC_IDS = [f"1-{n}" for n in range(1, 9)]


def test_chapter_has_all_eight_topics_in_order():
    assert [topic["id"] for topic in CHAPTER["topics"]] == EXPECTED_TOPIC_IDS


@pytest.mark.parametrize("topic", CHAPTER["topics"], ids=EXPECTED_TOPIC_IDS)
def test_every_topic_is_fully_authored(topic):
    assert topic["title"] and topic["objective"]
    assert len(topic["teach_markdown"]) > 400, "each topic needs real authored teaching text"
    assert topic["learning_objectives"]
    assert topic["prediction"]["prompt"] and topic["prediction"]["options"]
    assert topic["steps"], "each topic needs a stepped experiment"
    assert topic["tasks"], "each topic needs at least one graded task"
    assert len(topic["hints"]) == 4, "the hint ladder is H1 to H4"
    assert topic["sources"], "each topic cites its sources"
    assert topic["skills"]
    assert topic["completion"]["required_step_ids"]
    assert topic["completion"]["required_task_ids"]


@pytest.mark.parametrize("topic", CHAPTER["topics"], ids=EXPECTED_TOPIC_IDS)
def test_topic_completion_references_real_steps_and_tasks(topic):
    step_ids = {step["id"] for step in topic["steps"]}
    task_ids = {task["id"] for task in topic["tasks"]}
    assert set(topic["completion"]["required_step_ids"]) <= step_ids
    assert set(topic["completion"]["required_task_ids"]) <= task_ids


@pytest.mark.parametrize("topic", CHAPTER["topics"], ids=EXPECTED_TOPIC_IDS)
def test_every_topic_task_has_a_private_rubric(topic):
    for task in topic["tasks"]:
        assert task["id"] in RUBRICS
        assert task.get("assessed_skills"), task["id"]
        assert task.get("item_family"), task["id"]


def test_topics_declare_a_transfer_item():
    for topic in CHAPTER["topics"][:7]:
        ids = [task["id"] for task in topic["tasks"]]
        assert any(name.endswith("transfer") for name in ids), topic["id"]


def test_topic_prerequisites_only_reference_earlier_skills():
    seen: set[str] = set()
    for topic in CHAPTER["topics"]:
        for skill in topic["prerequisite_skills"]:
            assert skill in seen, f"{topic['id']} requires {skill} before it is taught"
        seen.update(topic["skills"])


def test_every_source_link_is_https():
    for topic in CHAPTER["topics"]:
        for source in topic["sources"]:
            assert source["url"].startswith("https://"), source


def test_public_topic_projection_hides_hints_and_keys():
    for topic in CHAPTER["topics"]:
        public = loader.public_topic(topic)
        serialized = json.dumps(public)
        assert "hints" not in public
        for rubric in RUBRICS.values():
            if rubric["task_id"].startswith(topic["id"]):
                key = json.dumps(rubric["key"]) if "key" in rubric else None
                if key and len(key) > 6:
                    assert key not in serialized


def test_public_assessment_hides_the_answer_key():
    public = json.dumps(loader.public_assessment())
    assert "answer_key" not in public
    for item_id, key in ASSESSMENT["answer_key"].items():
        assert f'"{item_id}": {json.dumps(key)}' not in public


def test_assessment_forms_cover_the_same_objectives():
    form_a = ASSESSMENT["forms"]["A"]
    form_b = ASSESSMENT["forms"]["B"]
    assert len(form_a) == len(form_b) == 10
    for item_a, item_b in zip(form_a, form_b, strict=True):
        assert item_a["number"] == item_b["number"]
        assert item_a["kind"] == item_b["kind"]
        assert item_a["assessed_skills"] == item_b["assessed_skills"]
        assert item_a["item_family"] == item_b["item_family"]


def test_every_assessment_item_has_a_key():
    for form in ASSESSMENT["forms"].values():
        for item in form:
            assert item["id"] in ASSESSMENT["answer_key"]


def test_pass_policy_matches_the_published_rule():
    policy = ASSESSMENT["pass_policy"]
    assert policy["minimum_score"] == 8
    assert policy["essential_item_numbers"] == [2, 4, 8, 9, 10]
    assert policy["requires_practice_complete"] is True
    assert "pilot policy" in policy["note"]


def test_revision_guidance_covers_every_assessed_skill():
    guidance = ASSESSMENT["revision_guidance"]
    assessed: set[str] = set()
    for form in ASSESSMENT["forms"].values():
        for item in form:
            assessed.update(item["assessed_skills"])
    assert assessed <= set(guidance)


def test_course_marks_three_published_chapters():
    course = loader.load_course()
    published = [c for c in course["chapters"] if c["publication"] == "published"]
    assert [c["number"] for c in published] == [1, 2, 3]
    for chapter in course["chapters"]:
        if chapter["publication"] == "coming_soon":
            assert chapter["coming_soon_note"]
            assert chapter["outcome"], "a coming-soon chapter still needs a true description"


def test_no_chapter_is_described_as_locked():
    course = json.dumps(loader.load_course()).lower()
    assert "locked" not in course
    assert "unlock after" not in course


def test_introduction_ends_at_the_course_overview():
    introduction = loader.load_introduction()
    assert introduction["primary_cta"]["route"] == "/course"
    assert introduction["primary_cta"]["label"] == "Explore the course"


def test_introduction_states_the_simulator_label_and_avoids_blanket_speed_claims():
    introduction = loader.load_introduction()
    text = json.dumps(introduction).lower()
    assert "simulator" in text
    assert "not measurements of a physical quantum processor" in text
    assert "quantum computers do not solve every problem faster" in text


def test_shor_preview_is_labelled_conceptual():
    previews = loader.load_previews()
    shor = next(a for a in previews["algorithms"] if a["id"] == "shor")
    assert shor["result_kind" if "result_kind" in shor else "result_label"] == (
        "conceptual_walkthrough"
    )
    assert "No Shor circuit is executed" in shor["persistent_label"]


def test_shor_storyboard_arithmetic_is_correct():
    previews = loader.load_previews()
    shor = next(a for a in previews["algorithms"] if a["id"] == "shor")
    powers = next(s for s in shor["storyboard"] if s["id"] == "powers")
    rows = powers["table"]["rows"]
    assert [row[1] for row in rows] == [pow(2, x, 15) for x in range(8)]
    factors = next(s for s in shor["storyboard"] if s["id"] == "factors")
    assert "3" in factors["body"] and "5" in factors["body"]


def test_planned_lab_entries_are_not_presented_as_working():
    previews = loader.load_previews()
    for entry in previews["planned_lab_entries"]:
        assert entry["publication"] == "coming_soon"


def test_evidence_levels_keep_mastery_separate_from_lab_mode():
    previews = loader.load_previews()
    modes = {mode["id"] for mode in previews["lab_modes"]}
    levels = {level["id"] for level in previews["evidence_levels"]}
    assert "mastered" not in modes
    assert "mastered" in levels


def test_access_policy_reasons_are_explicit():
    ready = access.decide(publication="published", required_skills=[], records=[])
    assert ready.reason_code == "open"
    blocked = access.decide(publication="published", required_skills=["gate.h_predict"], records=[])
    assert blocked.reason_code == "prerequisites_needed"
    assert "gate.h_predict" in blocked.reason
    future = access.decide(publication="coming_soon", required_skills=[], records=[])
    assert future.reason_code == "coming_soon"
    assert "not implemented yet" in future.reason


def test_a_progress_flag_cannot_make_an_unpublished_chapter_runnable():
    records = [
        access.EvidenceRecord("gate.h_predict", "independent", family) for family in ("f1", "f2")
    ]
    decision = access.decide(
        publication="coming_soon", required_skills=["gate.h_predict"], records=records
    )
    assert decision.readiness == "not_assessed"
    assert decision.publication == "coming_soon"


def test_content_versions_are_stable_checksums():
    first = loader.content_versions()
    loader.reset_cache()
    second = loader.content_versions()
    assert {v["content_id"]: v["checksum"] for v in first} == {
        v["content_id"]: v["checksum"] for v in second
    }


def test_private_content_lives_outside_the_public_directory():
    root = loader.content_root()
    public_files = {path.name for path in (root / "curriculum").glob("*.json")}
    assert "chapter-1-assessment.json" not in public_files
    assert "chapter-1-task-rubrics.json" not in public_files


def test_tutor_knowledge_contains_no_assessment_answer_key():
    knowledge_dir = loader.content_root() / "tutor" / "knowledge"
    text = " ".join(Path(path).read_text(encoding="utf-8") for path in knowledge_dir.glob("*.md"))
    for key in ASSESSMENT["answer_key"].values():
        if key["kind"] == "single_select":
            continue
        assert json.dumps(key["key"]) not in text
    assert "answer_key" not in text
    assert "essential_item_numbers" not in text


def test_scientific_corrections_from_the_ui_specification_are_applied():
    """The reference image's inaccurate wording must not be reproduced."""
    corpus = " ".join(
        [
            json.dumps(CHAPTER),
            json.dumps(loader.load_introduction()),
            json.dumps(loader.load_previews()),
            " ".join(
                Path(path).read_text(encoding="utf-8")
                for path in (loader.content_root() / "tutor" / "knowledge").glob("*.md")
            ),
        ]
    ).lower()
    assert "no state of their own" not in corpus
    assert "graded by simulator" not in corpus
    assert not re.search(r"chance\s*=\s*amplitude", corpus)
    assert "mixed" in corpus


def test_every_skill_has_a_learner_readable_label():
    """Prerequisites are shown to learners, so raw skill ids are not enough."""
    course = loader.load_course()
    labels = course["skill_labels"]
    declared: set[str] = set()
    for chapter in course["chapters"]:
        declared.update(chapter["prerequisite_skills"])
    for topic in CHAPTER["topics"]:
        declared.update(topic["skills"])
        declared.update(topic["prerequisite_skills"])
    assert declared <= set(labels), sorted(declared - set(labels))
    for label in labels.values():
        assert label and not label.startswith(("gate.", "phase.", "amplitude."))


def test_the_test_environment_ignores_a_local_env_file(tmp_path, monkeypatch):
    """A developer's real key must never be picked up by the test suite."""
    from app.config import Settings, get_settings

    env_file = tmp_path / ".env"
    env_file.write_text("TUTOR_PROVIDER=nvidia\nNVIDIA_API_KEY=nvapi-should-not-be-read\n")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("APP_ENV", "test")
    # Clear the ambient values so the file would win if it were read at all.
    monkeypatch.delenv("TUTOR_PROVIDER", raising=False)
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)

    # The file is readable, and pointing pydantic at it explicitly does pick it up.
    assert Settings(_env_file=str(env_file)).nvidia_api_key == "nvapi-should-not-be-read"

    get_settings.cache_clear()
    try:
        settings = get_settings()
        assert settings.nvidia_api_key == ""
        assert settings.tutor_provider != "nvidia"
    finally:
        get_settings.cache_clear()
