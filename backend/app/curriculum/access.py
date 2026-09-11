"""Server-side access policy.

Publication and readiness are separate. Publication says whether the content
exists; readiness says whether this learner has the evidence an assessed
activity requires. A future unpublished chapter can never become runnable
through a progress flag, and browsing is never gated.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Literal, Protocol

Publication = Literal["published", "coming_soon"]
Readiness = Literal["ready", "prerequisites_needed", "not_assessed"]

# Proposed pilot rule from the researched blueprint: two unassisted successes
# from distinct item families for each required skill.
REQUIRED_INDEPENDENT_EVIDENCE = 2
REQUIRED_DISTINCT_FAMILIES = 2


@dataclass(frozen=True)
class EvidenceRecord:
    skill_id: str
    kind: Literal["independent", "assisted"]
    item_family: str


@dataclass(frozen=True)
class AccessDecision:
    publication: Publication
    readiness: Readiness
    reason_code: str
    reason: str
    missing_skills: list[str]

    def as_dict(self) -> dict[str, object]:
        return {
            "publication": self.publication,
            "readiness": self.readiness,
            "reason_code": self.reason_code,
            "reason": self.reason,
            "missing_skills": self.missing_skills,
        }


class EvidenceSource(Protocol):
    """Anything that can list a principal's skill evidence."""

    def evidence_for(self, principal_id: str) -> list[EvidenceRecord]: ...


def skill_is_demonstrated(records: list[EvidenceRecord], skill_id: str) -> bool:
    independent = [
        record for record in records if record.skill_id == skill_id and record.kind == "independent"
    ]
    families = {record.item_family for record in independent}
    return (
        len(independent) >= REQUIRED_INDEPENDENT_EVIDENCE
        and len(families) >= REQUIRED_DISTINCT_FAMILIES
    )


def demonstrated_skills(records: list[EvidenceRecord]) -> set[str]:
    grouped: dict[str, list[EvidenceRecord]] = defaultdict(list)
    for record in records:
        grouped[record.skill_id].append(record)
    return {
        skill_id
        for skill_id, skill_records in grouped.items()
        if skill_is_demonstrated(skill_records, skill_id)
    }


def decide(
    *,
    publication: Publication,
    required_skills: list[str],
    records: list[EvidenceRecord],
    assessed: bool = True,
) -> AccessDecision:
    """Decide access for one activity."""
    if publication == "coming_soon":
        return AccessDecision(
            publication="coming_soon",
            readiness="not_assessed",
            reason_code="coming_soon",
            reason=(
                "This chapter is not implemented yet. Its description is accurate and "
                "there is no lesson behind it waiting to be unlocked."
            ),
            missing_skills=[],
        )
    if not assessed or not required_skills:
        return AccessDecision(
            publication="published",
            readiness="ready",
            reason_code="open",
            reason="Open to everyone. No prior evidence is required.",
            missing_skills=[],
        )
    have = demonstrated_skills(records)
    missing = [skill for skill in required_skills if skill not in have]
    if missing:
        return AccessDecision(
            publication="published",
            readiness="prerequisites_needed",
            reason_code="prerequisites_needed",
            reason=(
                "Graded work here needs demonstrated evidence for: "
                + ", ".join(missing)
                + ". Two unassisted successes from different item families count as "
                "evidence for a skill, and an equivalent diagnostic can substitute."
            ),
            missing_skills=missing,
        )
    return AccessDecision(
        publication="published",
        readiness="ready",
        reason_code="prerequisites_met",
        reason="You have demonstrated the prerequisite skills for this activity.",
        missing_skills=[],
    )


def browsing_always_allowed() -> str:
    return (
        "Chapter descriptions, topic previews, and algorithm previews are readable by "
        "everyone. Readiness applies only to assessed work."
    )
