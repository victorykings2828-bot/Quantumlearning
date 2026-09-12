"""Versioned content loader.

Public content and private assessment data live in separate directories and are
loaded by separate functions. The public projection strips hints and any field
that could disclose an answer, so a learner endpoint physically cannot leak one.
"""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.config import get_settings

PUBLIC_DIR = "curriculum"
PRIVATE_DIR = "assessments"

# Fields removed from every public topic/task projection.
PRIVATE_TASK_FIELDS = frozenset({"answer", "key", "correct"})
PRIVATE_TOPIC_FIELDS = frozenset({"hints"})


def content_root() -> Path:
    settings = get_settings()
    if settings.content_root:
        return Path(settings.content_root)
    return Path(__file__).resolve().parents[3] / "content"


def _read(directory: str, name: str) -> dict[str, Any]:
    path = content_root() / directory / f"{name}.json"
    if not path.is_file():
        raise FileNotFoundError(f"content file missing: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def checksum(document: dict[str, Any]) -> str:
    payload = json.dumps(document, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@lru_cache
def load_course() -> dict[str, Any]:
    return _read(PUBLIC_DIR, "course")


@lru_cache
def load_introduction() -> dict[str, Any]:
    return _read(PUBLIC_DIR, "introduction")


@lru_cache
def load_previews() -> dict[str, Any]:
    return _read(PUBLIC_DIR, "previews")


@lru_cache
def load_bridge() -> dict[str, Any]:
    return _read(PUBLIC_DIR, "beginner-bridge")


@lru_cache
def load_playground() -> dict[str, Any]:
    return _read(PUBLIC_DIR, "playground")


@lru_cache
def load_chapter(chapter_id: str) -> dict[str, Any]:
    if chapter_id not in {"chapter-1", "chapter-2", "chapter-3"}:
        raise KeyError(chapter_id)
    return _read(PUBLIC_DIR, chapter_id)


@lru_cache
def load_task_rubrics() -> dict[str, dict[str, Any]]:
    """Private. Never return this from a learner endpoint."""
    document = _read(PRIVATE_DIR, "chapter-1-task-rubrics")
    return {rubric["task_id"]: rubric for rubric in document["rubrics"]}


@lru_cache
def load_assessment() -> dict[str, Any]:
    """Private in part: the answer_key block must never reach a learner."""
    return _read(PRIVATE_DIR, "chapter-1-assessment")


def public_assessment(form: str | None = None) -> dict[str, Any]:
    """The learner-safe projection of the assessment."""
    document = deepcopy(load_assessment())
    document.pop("answer_key", None)
    document.pop("warning", None)
    document.pop("revision_guidance", None)
    if form is not None:
        forms = document.get("forms", {})
        document["forms"] = {form: forms.get(form, [])}
    return document


def _public_task(task: dict[str, Any]) -> dict[str, Any]:
    projection = {
        key: deepcopy(value) for key, value in task.items() if key not in PRIVATE_TASK_FIELDS
    }
    return projection


def public_topic(topic: dict[str, Any], *, include_body: bool = True) -> dict[str, Any]:
    projection = {
        key: deepcopy(value) for key, value in topic.items() if key not in PRIVATE_TOPIC_FIELDS
    }
    projection["tasks"] = [_public_task(task) for task in topic.get("tasks", [])]
    projection["hint_levels"] = len(topic.get("hints", []))
    if not include_body:
        projection.pop("teach_markdown", None)
        projection.pop("steps", None)
        projection.pop("tasks", None)
    return projection


def get_topic(topic_id: str) -> dict[str, Any] | None:
    for topic in all_topics():
        if topic["id"] == topic_id:
            return topic
    return None


def get_task(task_id: str) -> tuple[dict[str, Any], dict[str, Any]] | None:
    """Return (topic, task) for an authored topic task."""
    for topic in all_topics():
        for task in topic.get("tasks", []):
            if task["id"] == task_id:
                return topic, task
    return None


def get_hints(topic_id: str) -> list[dict[str, Any]]:
    topic = get_topic(topic_id)
    return list(topic.get("hints", [])) if topic else []


def all_skills() -> set[str]:
    skills: set[str] = set()
    for topic in all_topics():
        skills.update(topic.get("skills", []))
    return skills


def content_versions() -> list[dict[str, Any]]:
    """Every loaded document with its version and checksum, for provenance."""
    documents = {
        "course-root": (load_course(), "course"),
        "introduction": (load_introduction(), "introduction"),
        "previews": (load_previews(), "previews"),
        "beginner-bridge": (load_bridge(), "bridge"),
        "playground": (load_playground(), "playground"),
        "chapter-1": (load_chapter("chapter-1"), "chapter"),
        "chapter-2": (load_chapter("chapter-2"), "chapter"),
        "chapter-3": (load_chapter("chapter-3"), "chapter"),
        "chapter-1-assessment": (load_assessment(), "assessment"),
        "understanding": (_read(PRIVATE_DIR, "understanding"), "assessment"),
    }
    return [
        {
            "content_id": content_id,
            "version": document.get("version", 1),
            "kind": kind,
            "checksum": checksum(document),
        }
        for content_id, (document, kind) in documents.items()
    ]


def reset_cache() -> None:
    for cached in (
        load_course,
        load_introduction,
        load_previews,
        load_bridge,
        load_playground,
        load_chapter,
        load_task_rubrics,
        load_assessment,
    ):
        cached.cache_clear()


def all_topics():
    for chapter_id in ("chapter-1", "chapter-2", "chapter-3"):
        path = content_root() / PUBLIC_DIR / f"{chapter_id}.json"
        if path.is_file():
            yield from load_chapter(chapter_id)["topics"]
