# Read-only repository review

Reviewed 12 September 2026: [Quantumlearning](https://github.com/victorykings2828-bot/Quantumlearning), branch `claude/new-session-qdtc6d`, commit `c76df990554262b9e715c59fa253236d784bdeed`. Findings are pinned to this revision; Claude must inspect any newer working tree before implementing. No project files, GitHub issues, commits or settings were changed during this review. This is a targeted source/documentation review, not a running-site acceptance test.

## Current baseline

The latest inspected [Checks run](https://github.com/victorykings2828-bot/Quantumlearning/actions/runs/34673674927) passed. Do not repeat the earlier claim that CI has never run. The current build log records 223 backend tests, 18 frontend unit tests and 32 end-to-end tests from its development checks; these counts are reported evidence, not tests rerun for this review.

The latest section of [BUILD-STATUS.md](https://github.com/victorykings2828-bot/Quantumlearning/blob/c76df990554262b9e715c59fa253236d784bdeed/docs/BUILD-STATUS.md) records a user-reported Windows live NVIDIA smoke test: HTTP 200, model `nvidia/nemotron-3-super-120b-a12b`, response-schema success and a Chapter 1 citation. This establishes one live request, not comprehensive tutor accuracy or assessor calibration. Some older sections still say live verification is pending. Reconcile those statements using dated evidence; distinguish development-environment failures from later user-machine success. Do not infer deployment or full Docker Compose acceptance from a successful API request.

The existing product already supplies the introduction, Chapter 1, a chapter catalog, guest use, lab controls and a provider adapter. Extend that foundation. The catalog's Chapters 2 and 3 are currently described as coming soon; their research documents are not evidence that the lessons are implemented.

## Changes needed for the requested behavior

| Finding | Evidence | Required response |
|---|---|---|
| Tutor scope is hardcoded around Chapter 1 topic IDs | `TOPIC_KNOWLEDGE_SCOPE` and `knowledge_scope()` in [service.py](https://github.com/victorykings2828-bot/Quantumlearning/blob/c76df990554262b9e715c59fa253236d784bdeed/backend/app/tutoring/service.py) | Replace with server-validated cumulative chapter eligibility; full current chapter plus earlier chapters |
| A failed scoped retrieval retries without topic restrictions | `knowledge.retrieve(query, topic_ids=None, limit=3)` in the same service | Remove the unrestricted fallback before adding later chapters. This is a future-content leakage risk, not proof that currently unindexed Chapter 2 content already leaks |
| Empty topic metadata can bypass filtering | Retrieval checks `allowed_topics and passage.topics` in [knowledge.py](https://github.com/victorykings2828-bot/Quantumlearning/blob/c76df990554262b9e715c59fa253236d784bdeed/backend/app/tutoring/knowledge.py) | Fail closed on unknown metadata; distinguish an empty permitted set from unrestricted retrieval |
| Knowledge loading has a fixed file allowlist and topic map | `chapter-1`, `math-prerequisites`, `platform`; no chapter ordinal in `Passage` | Add reviewed chapter metadata and separate learner/tutor/private-assessor exports; do not simply index entire author guides |
| Retrieval source extraction expects inline links | Source extraction in the knowledge loader | Export inline source links or test an intentional parser extension for reference-style citations |
| Assessment evaluates objective and simulator tasks, with no descriptive-rubric type | Dispatch in [evaluator.py](https://github.com/victorykings2828-bot/Quantumlearning/blob/c76df990554262b9e715c59fa253236d784bdeed/backend/app/assessment/evaluator.py) | Preserve deterministic grading; add a separate AI-assisted explanation assessor and server-owned evidence policy |
| Pure-state goals reject multiple branches | `_final_state()` requires one branch in the evaluator | Add appropriate density/reduced-state and all-branch checks for mixture comparisons and teleportation |
| Circuit input lacks angle and classical-condition fields | [spec.py](https://github.com/victorykings2828-bot/Quantumlearning/blob/c76df990554262b9e715c59fa253236d784bdeed/backend/app/quantum/spec.py) | Extend operations for required chapter experiments and a bounded teleportation protocol; validate input and retain backward compatibility |

## Capabilities to preserve

The circuit schema already supports finite complex amplitudes and up to four qubits. Do not rebuild complex serialization or raise the qubit cap just to support the three-qubit teleportation lab. The inspected operation set includes X, H, Z, CX, CZ and Z measurement, with MCZ for presets. It does not yet expose the angle gates, mixture preparation or classical conditional operations needed by the proposed lessons. This observation concerns the public input schema, not a claim that no density-matrix calculation exists anywhere internally.

Keep the existing shot options `(1, 16, 64, 256, 1024)` and existing resource bounds unless a documented need justifies changing them. Existing grading correctly uses probabilities rather than treating sampled counts as exact; retain that distinction. Ordinary tutoring currently does not write grades: preserve that separation while implementing the newly requested, separately scoped assessor.

## Implementation priorities

1. Context metadata, future-topic routing and tests for leakage/fallback/history.
2. Reusable chapter entry/recall UI and the separate Chapter 2/3 lessons.
3. Simulator/schema changes, numerical fixtures and the two animations.
4. Descriptive evidence workflow, reviewed rubrics, pending/review states and progress policy.
5. Educator calibration, live-provider acceptance and truthful status documentation.

No local website, API, containers or project tests were executed during this review. Passing the current CI run does not cover the new requirements. The accompanying Claude prompt defines the implementation and verification work still required.
