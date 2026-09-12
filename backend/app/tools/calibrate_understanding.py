"""Measure held-out rubric agreement from educator-labelled JSONL; no model calls.

Each line: {family, split, human_scores:[0,1,2], model_scores:[0,1,2] or null,
           human_critical:boolean, model_sufficient:boolean, language_group:string}
Use adjudicated ratings, one development/heldout split per family. Synthetic
fixtures test this command but are not an educator-calibrated accuracy claim.
"""

import argparse
import json
from pathlib import Path


def evaluate(rows):
    development = {r["family"] for r in rows if r["split"] == "development"}
    heldout = [r for r in rows if r["split"] == "heldout"]
    if development & {r["family"] for r in heldout}:
        raise ValueError("Item-family leakage between development and heldout")
    if not heldout:
        raise ValueError("No heldout examples")
    judged = [r for r in heldout if r["model_scores"] is not None]
    for row in heldout:
        for scores in (row["human_scores"], row["model_scores"]):
            if scores is not None and (len(scores) != 3 or any(s not in (0, 1, 2) for s in scores)):
                raise ValueError("Expected three criterion scores from 0 through 2")
    agreement = sum(
        a == b for r in judged for a, b in zip(r["human_scores"], r["model_scores"], strict=True)
    )
    return {
        "heldout_responses": len(heldout),
        "rated_responses": len(judged),
        "criterion_agreement": agreement / (3 * len(judged)) if judged else None,
        "abstention_rate": 1 - len(judged) / len(heldout),
        "critical_false_passes": sum(r["human_critical"] and r["model_sufficient"] for r in judged),
        "false_rejections": sum(
            min(r["human_scores"]) > 0
            and sum(r["human_scores"]) >= 5
            and not r["human_critical"]
            and not r["model_sufficient"]
            for r in judged
        ),
        "note": "Report sample sizes. Agreement on this sample is not a guarantee of accuracy.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path)
    args = parser.parse_args()
    rows = [
        json.loads(line)
        for line in args.dataset.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    print(json.dumps(evaluate(rows), indent=2))


if __name__ == "__main__":
    main()
