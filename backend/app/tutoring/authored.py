"""Authored course help.

Used when no provider is configured, when a provider call fails, and when
validation rejects a provider answer. It is assembled from approved course
passages and always labelled as authored help, never as a live AI answer.
"""

from __future__ import annotations

from app.tutoring.knowledge import Passage

AUTHORED_LABEL = "authored"

NO_PASSAGE_HELP = (
    "I do not have an approved course passage that covers that. I can help with the "
    "material in this chapter, the arithmetic it relies on, the introduction and "
    "previews, and how to use this laboratory. Could you point me at the panel, gate, "
    "or number you are asking about?"
)

NO_RUN_HELP = (
    "I do not have a computed run selected, so I cannot describe your numbers. Press "
    "Run, or select one of your saved runs, and ask again. I can give a general "
    "explanation in the meantime."
)


def build_answer(question: str, passages: list[Passage]) -> tuple[str, list[str]]:
    """Assemble an authored help card from retrieved passages."""
    if not passages:
        return NO_PASSAGE_HELP, []

    lines = [
        "**Authored course help.** The AI tutor is not answering right now, so here is "
        "the relevant course material.",
        "",
    ]
    for passage in passages[:2]:
        # The blank line matters: without it the heading and the passage body
        # become one Markdown block and the whole answer renders as a heading.
        lines.append(f"### {passage.title}: {passage.heading}")
        lines.append("")
        lines.append(passage.text.strip())
        lines.append("")
    lines.append(
        "If this does not answer your question, try the topic's hints, which are "
        "written for exactly this task."
    )
    return "\n".join(lines).strip(), [passage.id for passage in passages[:2]]


def failure_note(reason_code: str) -> str:
    notes = {
        "missing_credentials": (
            "No AI provider is configured for this installation, so the tutor is "
            "running in authored-help mode."
        ),
        "unauthorized": (
            "The configured AI credentials were rejected, so authored help is shown "
            "instead. Your work is saved and unaffected."
        ),
        "rate_limited": (
            "The AI provider reported a rate or quota limit, so authored help is shown "
            "instead. Your work is saved and unaffected."
        ),
        "timeout": (
            "The AI provider did not answer within the time budget, so authored help is "
            "shown instead. Your work is saved and unaffected."
        ),
        "proxy_blocked": (
            "This installation's network blocked the connection to the AI provider, so "
            "authored help is shown instead. Your work is saved and unaffected."
        ),
        "connect_error": (
            "The AI provider could not be reached over the network, so authored help is "
            "shown instead. Your work is saved and unaffected."
        ),
        "provider_unavailable": (
            "The AI provider is temporarily unavailable, so authored help is shown "
            "instead. Your work is saved and unaffected."
        ),
        "unparseable_output": (
            "The AI response did not match the required format and was rejected, so "
            "authored help is shown instead."
        ),
        "schema_violation": (
            "The AI response did not match the required format and was rejected, so "
            "authored help is shown instead."
        ),
        "unknown_passage_id": (
            "The AI answer cited a source that does not exist, so it was rejected and "
            "authored help is shown instead."
        ),
        "unknown_fact_id": (
            "The AI answer referred to a measurement this run does not contain, so it "
            "was rejected and authored help is shown instead."
        ),
        "intent_mismatch": (
            "The AI answer did not respect the server's scope decision, so it was "
            "rejected and authored help is shown instead."
        ),
        "quota_exceeded": (
            "You have reached this installation's tutor request budget for the moment. "
            "Authored help is shown instead; try the AI tutor again shortly."
        ),
        "concurrent_request": (
            "One tutor request is already in progress for this session. Authored help is "
            "shown instead."
        ),
    }
    return notes.get(
        reason_code,
        "The AI tutor could not answer, so authored help is shown instead. Your work is "
        "saved and unaffected.",
    )
