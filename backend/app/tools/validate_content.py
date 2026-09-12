"""Validate authored content and its references.

Run with: uv run --frozen python -m app.tools.validate_content
Exits non-zero when content is inconsistent, so CI fails on a bad edit.
"""

from __future__ import annotations

import json
import sys
from typing import Any

from app.curriculum import loader
from app.tutoring import knowledge

RUBRIC_KINDS = {
    "single_select",
    "numeric_fields",
    "matching",
    "classification",
    "compound",
    "circuit_goal",
    "run_reading",
}


def _check(problems: list[str], condition: bool, message: str) -> None:
    if not condition:
        problems.append(message)


def validate() -> list[str]:
    problems: list[str] = []
    chapter = loader.load_chapter("chapter-1")
    rubrics = loader.load_task_rubrics()
    assessment = loader.load_assessment()

    _check(problems, len(chapter["topics"]) == 8, "Chapter 1 must have eight topics")

    taught_skills: set[str] = set()
    for topic in chapter["topics"]:
        prefix = f"topic {topic['id']}"
        _check(problems, bool(topic.get("teach_markdown")), f"{prefix}: missing teaching text")
        _check(problems, len(topic.get("hints", [])) == 4, f"{prefix}: needs four hint levels")
        _check(problems, bool(topic.get("sources")), f"{prefix}: missing sources")
        step_ids = {step["id"] for step in topic.get("steps", [])}
        task_ids = {task["id"] for task in topic.get("tasks", [])}
        for step_id in topic["completion"]["required_step_ids"]:
            _check(problems, step_id in step_ids, f"{prefix}: unknown required step {step_id}")
        for task_id in topic["completion"]["required_task_ids"]:
            _check(problems, task_id in task_ids, f"{prefix}: unknown required task {task_id}")
        for skill in topic.get("prerequisite_skills", []):
            _check(
                problems,
                skill in taught_skills,
                f"{prefix}: prerequisite {skill} is not taught earlier",
            )
        taught_skills.update(topic.get("skills", []))
        for task in topic.get("tasks", []):
            rubric = rubrics.get(task["id"])
            _check(problems, rubric is not None, f"{prefix}: task {task['id']} has no rubric")
            if rubric is None:
                continue
            _check(
                problems,
                rubric["kind"] == task["kind"],
                f"{prefix}: rubric kind mismatch for {task['id']}",
            )
            _check(
                problems,
                rubric["kind"] in RUBRIC_KINDS,
                f"{prefix}: unknown rubric kind {rubric['kind']}",
            )
            _check(
                problems,
                bool(task.get("assessed_skills")),
                f"{prefix}: task {task['id']} declares no assessed skills",
            )
            _check(
                problems,
                bool(task.get("item_family")),
                f"{prefix}: task {task['id']} declares no item family",
            )

    for orphan in set(rubrics) - {
        task["id"] for topic in chapter["topics"] for task in topic["tasks"]
    }:
        problems.append(f"rubric {orphan} has no authored task")

    for form_name, form in assessment["forms"].items():
        _check(problems, len(form) == 10, f"form {form_name} must have ten items")
        for item in form:
            _check(
                problems,
                item["id"] in assessment["answer_key"],
                f"form {form_name}: item {item['id']} has no answer key",
            )
            _check(
                problems,
                bool(item.get("assessed_skills")),
                f"form {form_name}: item {item['id']} declares no assessed skills",
            )

    public = json.dumps(loader.public_assessment())
    _check(problems, "answer_key" not in public, "public assessment leaks the answer key")

    for topic in chapter["topics"]:
        rendered = json.dumps(loader.public_topic(topic))
        _check(
            problems,
            '"hints"' not in rendered,
            f"public projection of {topic['id']} leaks hints",
        )

    course = loader.load_course()
    published = [c for c in course["chapters"] if c["publication"] == "published"]
    _check(
        problems,
        {entry["id"] for entry in published} == {"chapter-1", "chapter-2", "chapter-3"},
        "the review build must publish Chapters 1, 2 and 3",
    )
    for chapter_id, expected_count in (("chapter-2", 6), ("chapter-3", 7)):
        authored = loader.load_chapter(chapter_id)
        _check(problems, bool(authored.get("recap")), f"{chapter_id}: missing beginner recall")
        _check(
            problems,
            len(authored["topics"]) == expected_count,
            f"{chapter_id}: unexpected topic count",
        )
        for topic in authored["topics"]:
            prefix = f"topic {topic['id']}"
            _check(problems, bool(topic.get("teach_markdown")), f"{prefix}: missing teaching text")
            _check(problems, bool(topic.get("sources")), f"{prefix}: missing sources")
            _check(problems, bool(topic.get("lab")), f"{prefix}: missing experiment")
    for chapter_entry in course["chapters"]:
        if chapter_entry["publication"] == "coming_soon":
            _check(
                problems,
                bool(chapter_entry.get("coming_soon_note")),
                f"chapter {chapter_entry['number']} needs an honest coming-soon note",
            )

    knowledge.reset_cache()
    passages = knowledge.load_index()
    _check(problems, len(passages) >= 20, "tutor knowledge index looks empty")
    seen: set[str] = set()
    for passage in passages:
        _check(problems, passage.id not in seen, f"duplicate passage id {passage.id}")
        seen.add(passage.id)
        _check(problems, bool(passage.text.strip()), f"passage {passage.id} is empty")

    knowledge_text = " ".join(passage.text for passage in passages)
    for key in assessment["answer_key"].values():
        rendered_key = json.dumps(key.get("key"))
        if key["kind"] != "single_select" and len(rendered_key) > 8:
            _check(
                problems,
                rendered_key not in knowledge_text,
                "tutor knowledge contains an assessment answer",
            )

    return problems


def main() -> int:
    problems = validate()
    if problems:
        print("Content validation failed:")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    documents: list[dict[str, Any]] = loader.content_versions()
    print("Content validation passed.")
    for document in documents:
        print(
            f"  {document['content_id']} v{document['version']} "
            f"({document['kind']}) {document['checksum'][:12]}"
        )
    print(f"  tutor passages: {len(knowledge.load_index())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
