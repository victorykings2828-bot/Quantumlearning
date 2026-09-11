"""Evaluated scope policy for the course tutor.

Scope is decided on the server before any provider call, and re-decided on
every turn. The decision combines four independent signals rather than a
keyword list: retrieval grounding against approved course passages, approved
concept metadata, discourse context (a follow-up such as "why did that
happen?" is in scope because of the current topic and run), and task-intent
detection for requests whose actual task is unrelated regardless of the words
it contains.

This is a conservative, testable policy. It is not a proof that every future
prompt will be classified correctly; measured behaviour is reported in the
acceptance evidence rather than guaranteed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

from app.tutoring import knowledge

Decision = Literal["answer", "mixed", "clarify", "redirect", "capability_refusal"]

GROUNDING_THRESHOLD = 1.2
STRONG_GROUNDING = 4.0

# Course vocabulary treated as approved concept metadata. Presence is one
# signal among several, never sufficient on its own.
_CONCEPT_VOCABULARY = """
qubit qubits amplitude amplitudes probability probabilities normalization normalized
measurement measure measured shot shots gate gates circuit circuits superposition
phase relative global interference oracle grover shor basis ket hadamard bloch
entangled entanglement statevector born diffusion iteration iterations candidate
candidates eigenphase qft qpe teleportation simulator replay rerun trajectory branch
histogram counts frequency chapter topic lesson tutor hint assessment
"""
CONCEPT_TERMS = frozenset(_CONCEPT_VOCABULARY.split())

GATE_TOKENS = frozenset({"h", "x", "z", "cnot", "cz", "hzh", "hh"})

# Deictic follow-ups. In scope only when the server supplied a topic or run.
_FOLLOWUP = re.compile(
    r"\b(why|how|what)\b.{0,40}\b(that|this|it|these|those|here|mine|my (run|circuit|result))\b",
    re.IGNORECASE,
)
_SHORT_FOLLOWUP = re.compile(
    r"^\s*(why|how come|what happened|explain that|explain this|and why|but why)\b",
    re.IGNORECASE,
)

# Task-intent patterns. These describe the task being requested, so appending a
# course keyword to an unrelated request does not make its task relevant.
_UNRELATED_TASK_INTENTS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "recommendation",
        re.compile(
            r"\b(recommend|suggest|best)\b.{0,30}"
            r"\b(movie|film|show|series|book|restaurant|hotel|song|album|game|"
            r"holiday|vacation)\b",
            re.I,
        ),
    ),
    (
        "recommendation",
        re.compile(r"\bwhat should i (watch|read for fun|eat|buy|wear)\b", re.I),
    ),
    (
        "copywriting",
        re.compile(
            r"\b(write|draft|compose|generate)\b.{0,40}"
            r"(sales|marketing|promotional|cold|outreach|advertising)?\s*"
            r"\b(email|e-mail|newsletter|advert|ad copy|blog post|tweet|"
            r"linkedin post|press release)\b",
            re.I,
        ),
    ),
    (
        "shopping",
        re.compile(
            r"\b(where (can|do) i buy|cheapest|discount code|price of|"
            r"how much does .* cost)\b",
            re.I,
        ),
    ),
    (
        "politics",
        re.compile(
            r"\b(who should i vote|political|election|president|prime minister)\b"
            r".{0,40}\b(opinion|think|better|debate|argue)\b",
            re.I,
        ),
    ),
    (
        "unrelated_coding",
        re.compile(
            r"\b(write|fix|debug|refactor)\b.{0,30}\b(my|a|an)\b.{0,20}"
            r"\b(react|django|flask|node|android|ios|wordpress|excel|vba|website|app)\b",
            re.I,
        ),
    ),
    (
        "roleplay",
        re.compile(
            r"\b(pretend|role[- ]?play|act as|you are now)\b.{0,40}"
            r"\b(?!a (quantum|course|physics) (tutor|teacher))",
            re.I,
        ),
    ),
    (
        "instruction_override",
        re.compile(
            r"\b(ignore|disregard|forget)\b.{0,30}\b(your |the |all )?"
            r"(previous |prior |above )?"
            r"(instructions?|rules?|policy|system prompt|guidelines?)\b",
            re.I,
        ),
    ),
    (
        "instruction_override",
        re.compile(
            r"\b(reveal|show|print|repeat)\b.{0,30}\b(your |the )?"
            r"(system prompt|hidden instructions?|api key|secret|credentials?)\b",
            re.I,
        ),
    ),
    (
        "general_assistant",
        re.compile(r"\bact as a general (purpose )?assistant\b", re.I),
    ),
)

_CAPABILITY_REQUESTS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "grade_mutation",
        re.compile(
            r"\b(set|change|update|give|mark|make)\b.{0,30}\b(my |the )?"
            r"(mastery|grade|score|progress|completion)\b",
            re.I,
        ),
    ),
    (
        "grade_mutation",
        re.compile(
            r"\b(unlock|complete|pass)\b.{0,20}\b(this |the |my )?"
            r"(chapter|topic|assessment|test)\b",
            re.I,
        ),
    ),
    (
        "other_learner_data",
        re.compile(
            r"\b(another|other|someone else'?s?|a different)\b.{0,20}"
            r"\b(student|learner|user|guest)'?s?\b",
            re.I,
        ),
    ),
)

# Asking for the solution outright. What this means depends on the attempt mode
# the server supplied: during an unassisted test it is refused; in practice it
# is an ordinary request for the next hint level.
_ANSWER_REQUEST = re.compile(
    r"\b(give|tell|show)\s+me\b.{0,30}\banswers?\b"
    r"|\bwhat('?s| is)\b.{0,30}\b(the )?(correct )?answers?\b"
    r"|\bjust tell me\b"
    r"|\b(solve|do) (this|it) for me\b",
    re.I,
)

_CLAUSE_SPLIT = re.compile(r"(?:[.?!;]+\s+|\s+,?\s*(?:and|also|then|plus)\s+|\n+)")


@dataclass
class ScopeResult:
    decision: Decision
    reason_code: str
    in_scope_text: str
    out_of_scope_text: str = ""
    capability_kind: str | None = None
    signals: dict[str, object] = field(default_factory=dict)
    clauses: list[dict[str, object]] = field(default_factory=list)


def _clauses(message: str) -> list[str]:
    parts = [part.strip(" ,") for part in _CLAUSE_SPLIT.split(message.strip()) if part.strip(" ,")]
    return parts or [message.strip()]


def _task_intent(text: str) -> str | None:
    for label, pattern in _UNRELATED_TASK_INTENTS:
        if pattern.search(text):
            return label
    return None


def _capability_intent(text: str) -> str | None:
    for label, pattern in _CAPABILITY_REQUESTS:
        if pattern.search(text):
            return label
    return None


def _concept_signal(text: str) -> bool:
    tokens = set(re.findall(r"[a-z0-9|+-]+", text.lower()))
    if tokens & CONCEPT_TERMS:
        return True
    return bool(tokens & GATE_TOKENS)


def _discourse_signal(text: str, has_context: bool) -> bool:
    if not has_context:
        return False
    return bool(_FOLLOWUP.search(text) or _SHORT_FOLLOWUP.search(text))


def classify(
    message: str,
    *,
    topic_id: str | None = None,
    has_run_context: bool = False,
    recent_turns: int = 0,
    mode: str = "practice",
) -> ScopeResult:
    """Classify one learner turn. Previous in-scope turns do not carry over."""
    text = message.strip()
    if not text:
        return ScopeResult(
            decision="clarify",
            reason_code="empty_message",
            in_scope_text="",
            signals={},
        )

    capability = _capability_intent(text)
    if capability is not None:
        return ScopeResult(
            decision="capability_refusal",
            reason_code=f"capability_{capability}",
            in_scope_text=text,
            capability_kind=capability,
            signals={"capability": capability},
        )

    if _ANSWER_REQUEST.search(text):
        if mode == "test":
            return ScopeResult(
                decision="capability_refusal",
                reason_code="capability_test_answer",
                in_scope_text=text,
                capability_kind="test_answer",
                signals={"mode": mode},
            )
        return ScopeResult(
            decision="answer",
            reason_code="hint_request",
            in_scope_text=text,
            signals={"mode": mode, "wants_solution": True},
        )

    has_context = bool(topic_id) or has_run_context or recent_turns > 0
    clause_reports: list[dict[str, object]] = []
    in_scope: list[str] = []
    out_of_scope: list[str] = []
    uncertain: list[str] = []

    for clause in _clauses(text):
        intent = _task_intent(clause)
        grounding = knowledge.best_score(clause)
        concept = _concept_signal(clause)
        discourse = _discourse_signal(clause, has_context)

        if intent is not None:
            verdict = "unrelated"
        elif grounding >= GROUNDING_THRESHOLD or concept or discourse:
            verdict = "related"
        else:
            verdict = "uncertain"

        clause_reports.append(
            {
                "text": clause,
                "verdict": verdict,
                "task_intent": intent,
                "grounding": round(grounding, 3),
                "concept_signal": concept,
                "discourse_signal": discourse,
            }
        )
        if verdict == "related":
            in_scope.append(clause)
        elif verdict == "unrelated":
            out_of_scope.append(clause)
        else:
            uncertain.append(clause)

    signals = {
        "clause_count": len(clause_reports),
        "best_grounding": max((report["grounding"] for report in clause_reports), default=0.0),
        "has_context": has_context,
    }

    if in_scope and out_of_scope:
        return ScopeResult(
            decision="mixed",
            reason_code="mixed_request",
            in_scope_text=" ".join(in_scope),
            out_of_scope_text=" ".join(out_of_scope),
            signals=signals,
            clauses=clause_reports,
        )
    if out_of_scope and not in_scope:
        return ScopeResult(
            decision="redirect",
            reason_code="unrelated_request",
            in_scope_text="",
            out_of_scope_text=" ".join(out_of_scope),
            signals=signals,
            clauses=clause_reports,
        )
    if in_scope:
        return ScopeResult(
            decision="answer",
            reason_code="course_related",
            in_scope_text=" ".join(in_scope) if not uncertain else text,
            signals=signals,
            clauses=clause_reports,
        )
    return ScopeResult(
        decision="clarify",
        reason_code="insufficient_grounding",
        in_scope_text=text,
        signals=signals,
        clauses=clause_reports,
    )


def redirect_message(topic_title: str | None) -> str:
    target = topic_title or "this quantum course"
    return (
        f"I can help with this quantum course and its experiments. "
        f"Would you like to continue with {target}?"
    )


def capability_message(kind: str, topic_title: str | None) -> str:
    target = topic_title or "the current topic"
    if kind == "grade_mutation":
        return (
            "I cannot change grades, mastery records, completion, or unlocks. Those come "
            "from the authored evaluator on the server, which runs without me. What I can "
            f"do is work through the item with you so the evidence is real. Shall we take "
            f"the next step in {target}?"
        )
    if kind == "other_learner_data":
        return (
            "I can only see your own work. Another learner's answers, runs, and progress "
            "are not reachable from this conversation, and the server refuses those "
            "requests regardless of what I do. I can help with your own attempt instead."
        )
    if kind == "test_answer":
        return (
            "I will not give a test answer during an unassisted attempt. If you would like "
            "worked help, you can switch this attempt to practice from the assessment page. "
            "The platform performs that switch and records that assistance; I cannot do it "
            "for you. I can still help with navigation or the wording of a question."
        )
    return redirect_message(topic_title)
