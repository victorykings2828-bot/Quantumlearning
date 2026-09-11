"""Versioned Markdown knowledge loader with stable passage IDs.

Files are split on level-2 headings. A passage ID is the file ID plus the
heading key, for example ``chapter-1.basis``. Only files on the server
allowlist are indexed; frontmatter supplied by a learner is never trusted.
Supplying these passages to a model is retrieval context, not training.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from app.curriculum.loader import content_root

# Server allowlist. A file not named here is never retrieved, whatever its
# frontmatter claims.
ALLOWED_KNOWLEDGE_FILES = ("chapter-1", "math-prerequisites", "platform")

# Per-passage topic scope, decided by the server. Frontmatter supplied inside a
# knowledge file is a convenience for authors; it never widens what a given
# topic may retrieve.
PASSAGE_TOPICS: dict[str, tuple[str, ...]] = {
    "chapter-1.basis": ("ch1-1",),
    "chapter-1.probabilities": ("ch1-2",),
    "chapter-1.measurement": ("ch1-3",),
    "chapter-1.sampling": ("ch1-3",),
    "chapter-1.x-gate": ("ch1-4",),
    "chapter-1.h-gate": ("ch1-5",),
    "chapter-1.z-gate": ("ch1-6",),
    "chapter-1.phase": ("ch1-6",),
    "chapter-1.interference": ("ch1-7",),
    "chapter-1.grover-connection": ("grover-preview", "intro", "ch1-8", "lab"),
    "chapter-1.shor-connection": ("shor-preview", "intro", "lab"),
    "chapter-1.local-states": ("lab", "intro"),
    "chapter-1.platform-help": ("platform",),
}

_FRONTMATTER = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_TOKEN = re.compile(r"[a-z0-9][a-z0-9'/_-]*")
_SOURCE_LINK = re.compile(r"\[([^\]]+)\]\((https?://[^)]+)\)")

_STOPWORD_TEXT = """
a an and are as at be but by do does for from has have how i if in into is it its
me my no not of on or so than that the their them then there these this to was what
when where which who why will with you your
"""
_STOPWORDS = frozenset(_STOPWORD_TEXT.split())


@dataclass(frozen=True)
class Passage:
    id: str
    file_id: str
    heading: str
    title: str
    text: str
    version: int
    topics: tuple[str, ...]
    sources: tuple[tuple[str, str], ...] = field(default=())

    def citation(self) -> dict[str, object]:
        return {
            "passage_id": self.id,
            "title": f"{self.title}: {self.heading}",
            "version": self.version,
            "sources": [{"title": title, "url": url} for title, url in self.sources],
        }


def _parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    match = _FRONTMATTER.match(text)
    if not match:
        return {}, text
    raw = match.group(1)
    body = text[match.end() :]
    data: dict[str, str] = {}
    for line in raw.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip()
    return data, body


def _split_topics(value: str) -> tuple[str, ...]:
    cleaned = value.strip().strip("[]")
    return tuple(item.strip() for item in cleaned.split(",") if item.strip())


def tokenize(text: str) -> list[str]:
    return [token for token in _TOKEN.findall(text.lower()) if token not in _STOPWORDS]


def document_text(passage: Passage) -> str:
    """Indexed text: the heading names the concept and is often absent from the body."""
    heading_words = passage.heading.replace("-", " ")
    return f"{passage.heading} {heading_words} {passage.text}"


def _load_file(path: Path) -> list[Passage]:
    raw = path.read_text(encoding="utf-8")
    meta, body = _parse_frontmatter(raw)
    file_id = meta.get("id", path.stem)
    version = int(meta.get("version", "1"))
    title = meta.get("title", file_id)
    topics = _split_topics(meta.get("topics", ""))

    passages: list[Passage] = []
    current_heading: str | None = None
    buffer: list[str] = []

    def flush() -> None:
        if current_heading is None:
            return
        text = "\n".join(buffer).strip()
        if not text:
            return
        sources = tuple((label, url) for label, url in _SOURCE_LINK.findall(text))
        passage_id = f"{file_id}.{current_heading}"
        passages.append(
            Passage(
                id=passage_id,
                file_id=file_id,
                heading=current_heading,
                title=title,
                text=text,
                version=version,
                topics=PASSAGE_TOPICS.get(passage_id, topics),
                sources=sources,
            )
        )

    for line in body.splitlines():
        if line.startswith("## "):
            flush()
            current_heading = line[3:].strip()
            buffer = []
        elif current_heading is not None:
            buffer.append(line)
    flush()
    return passages


@lru_cache
def load_index() -> tuple[Passage, ...]:
    directory = content_root() / "tutor" / "knowledge"
    passages: list[Passage] = []
    for file_id in ALLOWED_KNOWLEDGE_FILES:
        path = directory / f"{file_id}.md"
        if path.is_file():
            passages.extend(_load_file(path))
    return tuple(passages)


@lru_cache
def _statistics() -> tuple[dict[str, int], float, int]:
    passages = load_index()
    document_frequency: Counter[str] = Counter()
    lengths: list[int] = []
    for passage in passages:
        tokens = tokenize(document_text(passage))
        lengths.append(len(tokens))
        document_frequency.update(set(tokens))
    average = sum(lengths) / len(lengths) if lengths else 1.0
    return dict(document_frequency), average, len(passages)


def bm25_scores(query: str, *, k1: float = 1.5, b: float = 0.75) -> list[tuple[Passage, float]]:
    """Lexical BM25 retrieval. Eight topics do not need a vector service."""
    document_frequency, average_length, total = _statistics()
    query_tokens = tokenize(query)
    scored: list[tuple[Passage, float]] = []
    for passage in load_index():
        tokens = tokenize(document_text(passage))
        counts = Counter(tokens)
        length = len(tokens) or 1
        score = 0.0
        for token in query_tokens:
            frequency = counts.get(token, 0)
            if frequency == 0:
                continue
            df = document_frequency.get(token, 0)
            idf = math.log(1 + (total - df + 0.5) / (df + 0.5))
            denominator = frequency + k1 * (1 - b + b * length / average_length)
            score += idf * (frequency * (k1 + 1)) / denominator
        scored.append((passage, score))
    scored.sort(key=lambda entry: entry[1], reverse=True)
    return scored


def retrieve(
    query: str,
    *,
    topic_ids: list[str] | None = None,
    limit: int = 4,
    minimum_score: float = 0.6,
) -> list[Passage]:
    """Retrieve approved passages for the current and earlier topics."""
    allowed_topics = set(topic_ids or [])
    results: list[Passage] = []
    for passage, score in bm25_scores(query):
        if score < minimum_score:
            continue
        if allowed_topics and passage.topics and not (set(passage.topics) & allowed_topics):
            continue
        results.append(passage)
        if len(results) >= limit:
            break
    return results


def best_score(query: str) -> float:
    scores = bm25_scores(query)
    return scores[0][1] if scores else 0.0


def get_passage(passage_id: str) -> Passage | None:
    for passage in load_index():
        if passage.id == passage_id:
            return passage
    return None


def valid_passage_ids() -> set[str]:
    return {passage.id for passage in load_index()}


def reset_cache() -> None:
    load_index.cache_clear()
    _statistics.cache_clear()
