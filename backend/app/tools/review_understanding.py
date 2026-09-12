"""Local educator review. Append a review event; never overwrite a learner answer.

Usage: python -m app.tools.review_understanding ATTEMPT_UUID rating.json --reviewer NAME
The rating JSON uses routes_learning.Rating. No public unprotected grading endpoint.
"""

import argparse
import json
import uuid
from pathlib import Path

from app.api.routes_learning import validate_rating
from app.storage.database import get_session_factory
from app.storage.models import TaskAttempt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("attempt_id", type=uuid.UUID)
    parser.add_argument("rating_file", type=Path)
    parser.add_argument("--reviewer", required=True)
    args = parser.parse_args()
    with get_session_factory()() as session:
        original = session.get(TaskAttempt, args.attempt_id)
        if original is None or not original.task_id.startswith("understanding:"):
            raise SystemExit("No understanding attempt with that ID")
        rating = validate_rating(
            args.rating_file.read_text(encoding="utf-8"), original.submission["explanation"]
        )
        passed = (
            rating.disposition == "sufficient"
            and not original.assisted
            and original.evaluation.get("mcq_correct", False)
        )
        review = TaskAttempt(
            principal_id=original.principal_id,
            topic_id=original.topic_id,
            task_id=original.task_id,
            content_version=original.content_version,
            submission=dict(original.submission),
            assisted=original.assisted,
            passed=passed,
            evaluation={
                **original.evaluation,
                "status": "reviewed",
                "rating": rating.model_dump(),
                "reviewer": args.reviewer,
                "supersedes": str(original.id),
                "demonstrated": False,
            },
        )
        session.add(review)
        session.commit()
        print(
            json.dumps(
                {
                    "review_event_id": str(review.id),
                    "item_evidence_sufficient": passed,
                    "chapter_completion": "Separate multi-family policy; no automatic award",
                }
            )
        )


if __name__ == "__main__":
    main()
