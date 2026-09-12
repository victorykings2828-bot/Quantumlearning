"""Trusted curriculum boundaries; future routing uses titles, never future lessons."""

import re

from app.curriculum import loader

ALIASES = {
    2: ("bloch", "complex number", "measurement basis", "measurement bases", "y basis", "rotation"),
    3: ("entangl", "bell state", "teleport", "tensor product", "joint probability", "mixed state"),
    4: ("reversible function", "quantum oracle"),
    5: ("deutsch", "bernstein", "vazirani"),
    6: ("grover algorithm", "full grover", "amplitude amplification"),
    7: ("simon", "hidden xor"),
    8: ("quantum fourier", "qft"),
    9: ("phase estimation", "qpe"),
    10: ("shor algorithm", "order finding"),
    11: ("error correction", "decoherence"),
    12: ("variational", "vqe", "qaoa"),
}


def chapter_number(topic_id: str | None) -> int | None:
    if topic_id and re.fullmatch(r"[1-3]-\d+", topic_id) and loader.get_topic(topic_id):
        return int(topic_id.split("-")[0])
    return None


def eligible_topics(topic_id: str | None) -> list[str]:
    ceiling = chapter_number(topic_id)
    if ceiling is None:
        return (
            []
            if topic_id
            else ["intro", "grover-preview", "shor-preview", "bridge", "platform", "lab"]
        )
    result = ["bridge", "platform"]
    for number in range(1, ceiling + 1):
        chapter = loader.load_chapter(f"chapter-{number}")
        result.extend(f"ch{topic['id']}" for topic in chapter["topics"])
    return result


def future_reply(message: str, topic_id: str | None) -> str | None:
    ceiling = chapter_number(topic_id)
    if ceiling is None:
        return None
    message = message.lower().replace("-", " ")
    matches = [
        number
        for number, aliases in ALIASES.items()
        if number > ceiling and any(alias in message for alias in aliases)
    ]
    if not matches:
        return None
    number = min(matches)
    chapter = next((c for c in loader.load_course()["chapters"] if c["number"] == number), None)
    if not chapter:
        return "That subject is beyond the material available in this chapter."
    return (
        f"This topic is discussed in Chapter {number} — {chapter['title']}. "
        f"For now, I can help you review the ideas in Chapters 1 through {ceiling}."
    )
