# Separate reviewer test copy

This checkout is independent of the original Quantumlearning installation. It began at `c76df990554262b9e715c59fa253236d784bdeed` and uses branch `codex/reviewer-test`. The user authorized publishing this review branch on GitHub on 2026-09-12. The original default branch is `claude/new-session-qdtc6d`; it must remain unchanged until the user approves a merge. Publishing the branch does not deploy a public website.

The original revision is preserved in `../outputs/quantumlearning-original-c76df99.zip`. A verified Git bundle beside it preserves the original complete history. Keep both until you approve a replacement.

## Open the current test

The native preview on this computer is **http://127.0.0.1:5189/** while its local servers are running. It uses its own PostgreSQL cluster on port 55439, database `quantum_demo`, backend port 8019 and separate `qll_review_session` / `qll_review_csrf` cookies. PostgreSQL test cases use a different database, `quantum_test`.

For a reusable Docker-based test instance, run `./Start-Test.ps1` from this checkout after installing Docker Desktop. It uses project name `quantumlearning-reviewer-test`, an independent volume, separate cookies and **http://127.0.0.1:8089**. `./Start-Test.ps1 -Stop` stops only that named stack and preserves its volume. This Docker launcher was authored and syntax-checked here, but Docker is unavailable in this environment, so its container launch is not claimed tested.

Do not copy the local `.env` into the original project. The test `.env` has no NVIDIA key. Add a key only to this test checkout's ignored `backend/.env` if you want to evaluate live AI, and set `TUTOR_PROVIDER=nvidia`. The normal provider adapter and configured model are retained. These credentials are excluded from Git, the delivery archive and Docker build context.

## Implemented in this test version

- Separate Chapter 2 and Chapter 3 content, all 13 topic routes, readable explanations, citations, beginner recall and open navigation.
- Bounded Qiskit experiments with changeable preparations, phase and readout basis where relevant; prediction capture, stepping, playback, saved runs and restored experiments.
- Phase/interference and Bell preparation amplitude animations with pause, replay, speed and motion-off controls. These illustrate mathematical states, not physical particle paths.
- Actual density-ensemble comparison for the classical mixture; no fake amplitude vector for a mixed state.
- Fixed three-qubit teleportation protocol with each measurement branch and conditional correction. Numerical tests cover basis, plus and complex-phase input states.
- Cumulative tutor eligibility, future chapter-name redirects, removal of unrestricted retrieval fallback, unknown-topic rejection, run/topic validation and clearing stale chapter conversations from the drawer.
- Separate explanation assessment route with private rubrics, MCQs, two changed-condition question variants for each new topic, response persistence, assisted/repeated-attempt labels and pending/provisional/review states. Chapter 1 has an initial explanation check linked from its existing objective quiz.
- A separate NVIDIA assessor request with structured criterion ratings and exact evidence-quote validation. It cannot directly award chapter completion.
- Local educator review and calibration commands. Reviewer events append to the evidence history instead of replacing the original learner answer.
- Existing Chapter 1, introduction, previews and playground remain working.

## What approval should not assume

This is a functioning first test implementation, not a claim that every detail of the longer authoring package or the production roadmap is finished.

**AI:** No live NVIDIA request was made from this test copy. The earlier repository smoke-test report belongs to the original baseline. Explanation scores here remain pending without a key, and provisional with a model until educator calibration. No accuracy percentage has been established.

**Understanding:** The server requires two distinct independent reviewed question families for each topic and blocks unresolved critical misconceptions. Provisional AI ratings cannot complete this rule; reviewed evidence is shown separately from reading/quiz completion. Fully automated calibrated scoring, simulator-graded practical transfer tasks, delayed recall scheduling and expanded Chapter 1 explanation coverage remain work before a production learning claim. Existing Chapter 1 quiz results are retained and explicitly labelled as objective/practice evidence.

**Teaching depth:** New topics currently use concise lessons and bounded experiment presets. The full authoring guides propose richer derivations, task ladders, diagnostics and additional variations. Review the learning experience before deciding which of those to expand. A clicked reading-complete button records reading, never understanding.

**Tutor:** Future routing includes tested aliases and output screening; it is not a proof against every paraphrase or adversarial model reply. The future-topic directory is metadata-only. Some mixed current/future requests conservatively defer the request rather than teaching the permitted clause separately.

**Deployment:** Native PostgreSQL/API/frontend operation was tested. Container builds, deployment and a live AI assessment suite were not executed. The local preview must remain running to use its URL.

## Reviewer walkthrough

1. Introduction → Course → Chapter 2. Read the recall panel and open Topic 2.4.
2. Predict the result for phase π. Run, step through H/P/H and observe the final 0 probability falling to zero. Reload and confirm the experiment is restored.
3. Ask the Chapter 2 tutor about H; then ask how to create a Bell state. The second request names Chapter 3.
4. In Chapter 3 Topic 3.6, compare Bell and classical mixture under Z then X. The mixture has no single amplitude vector. Try motion off.
5. In Topic 3.7, inspect all four correction branches and then omit the corrections. Compare Bob's reduced Bloch coordinates for the complex input.
6. Open an understanding check. Give a correct MCQ but an incorrect explanation. A correct MCQ must not award understanding. With no key the answer is saved pending evaluation, not graded by a fake model.
7. Return to Chapter 1 and check that the tutor drawer does not retain later responses as current context.

## Verification record

The full backend suite passed with 248 tests at the first regression checkpoint, including 25 new tests. Four additional rubric/calibration/policy tests were then added; the targeted final suite is recorded in BUILD-STATUS.md. The frontend's 18 unit tests passed. All 36 browser tests passed with explicit desktop/mobile projects against the real API and isolated PostgreSQL database. No live model was used by these tests.

TypeScript checking, ESLint, Ruff, formatting and the production frontend build were exercised. OpenAPI was regenerated and checked. Dependency versions and lockfiles were preserved. On this Windows sandbox, native esbuild cannot list the profile ancestor despite a granted read request; a process-local Q: mapping plus `preserveSymlinks` allowed build/testing inside the authorized checkout. The product's normal Vite architecture was retained.

## Educator tools

`python -m app.tools.review_understanding ATTEMPT_UUID rating.json --reviewer NAME` appends a trusted local review. The JSON follows `Rating` in `routes_learning.py`: three unique claim/mechanism/transfer criteria, 0–2 scores, literal supporting quotes, feedback, critical-misconception flag and disposition. A local command is used because the demo has no authenticated educator role; no public grade-override endpoint was introduced.

`python -m app.tools.calibrate_understanding labelled.jsonl` measures criterion agreement, critical false passes, false rejections and abstention on adjudicated held-out answers. Its module docstring specifies the input. It rejects shared item families across development and held-out sets. Synthetic tests verify the calculation only; they are not educator calibration evidence.

## Before using this in the main project

Review this test copy first. Preserve the backup and the main database. Compare the branch changes, complete the remaining learning/AI acceptance items you require, then explicitly approve integration. Nothing in this test run automatically replaces the main files or data.
