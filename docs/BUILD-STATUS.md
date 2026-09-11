# Build status

Updated after the demo implementation phases. Every "run" line below records a
command that was actually executed in this environment, with its outcome. No
status is inferred from a file existing.

## Environment this was verified in

| Component | Declared for the project | Used for local verification | Note |
|---|---|---|---|
| Python | 3.12 | 3.12.11 (installed by uv) | matches |
| uv | 0.8.17+ | 0.8.17 | the build guide proposed 0.12.12; the pinned CI version is 0.12.12 and was not exercised here |
| Node | 24 (CI) | 22.22.2 | local development only; CI installs 24 |
| PostgreSQL | 17 (compose and CI) | **16.13** | Docker Hub blob downloads are blocked by this environment's network policy, so `postgres:17` could not be pulled. Compose and CI both declare 17; the local runs used the distribution's 16. |
| Qiskit | pinned range | 2.5.2 | resolved by the lockfile |

## Phase status

| Phase | Status | Evidence |
|---|---|---|
| 0. Inspect and bootstrap | Complete | Repository was empty apart from git metadata. Build kit copied in, backend and frontend created, Alembic initial migration applied to a live database, health endpoints answer. |
| 1. One working experiment | Complete | Qiskit statevector engine behind a neutral interface. 38 fixture tests derived independently from the mathematics pass, including every Grover value in the researched blueprint. |
| 2. Identity and persistence | Complete | Guest principals, hashed opaque session tokens, CSRF and origin checks, immutable revisions, owner-scoped reads. Cross-guest isolation is tested at API and browser level. |
| 3. Full learning journey | Complete | All eight topics authored and served; a test completes every topic and scores 10/10 on both assessment forms through the real API. |
| 4. Previews and revisit | Complete | Grover preview with overshoot and the missing-preparation variant; Shor storyboard with exact arithmetic; Seen status recorded and never promoted. |
| 5. Tutor | Complete except live verification | Retrieval, evaluated scope policy, NVIDIA adapter, response validation, verified run facts, authored fallback, quotas. **Live NVIDIA verification pending: no API key was supplied to this build.** |
| 6. Polish and delivery | Complete | CI workflow, container build files, README with tested commands, browser suite against the real API and database. |

## Commands actually run, and their outcomes

Backend (`cd backend`):

| Command | Outcome |
|---|---|
| `uv sync --frozen` | pass |
| `uv lock --check` | pass |
| `uv run --frozen ruff check .` | pass |
| `uv run --frozen ruff format --check .` | pass |
| `uv run --frozen alembic upgrade head` | pass, against a live PostgreSQL |
| `uv run --frozen pytest` | **220 passed** |
| `uv run --frozen python -m app.tools.validate_content` | pass |
| `uv run --frozen python export_contracts.py --check` | pass |
| `uv run --frozen python -m app.tools.tutor_smoke` | exits 2, "no live call was attempted": no key configured |

Frontend (`cd frontend`):

| Command | Outcome |
|---|---|
| `npm install` | pass |
| `npm run generate:types` | pass, `src/api/schema.d.ts` regenerated from the committed contract |
| `npm run lint` | pass (5 react-refresh warnings, no errors) |
| `npm run typecheck` | pass |
| `npm run test:unit` | **18 passed** |
| `npm run build` | pass |
| `npm run format:check` | pass |
| `npm run test:e2e` | **32 passed** in 36 s (Chromium against the real API and PostgreSQL) |

## What the browser suite covers

Playwright drives a real Chromium against the real FastAPI service and a real
PostgreSQL database. Only the tutor provider is an explicit adapter
(`TUTOR_PROVIDER=authored`), and its answers are labelled authored help in the
interface, never presented as a live model conversation.

Covered: introduction to course to topic; a changed gate changing computed
values; a stale result never presented as current; run, step, replay and rerun
identity; repeated measurement of a recorded trajectory; task and assessment
persistence across reload; an alternative circuit passing a distribution goal;
hint accounting; cross-guest isolation of runs and progress; Coming-soon
labelling; unknown routes; answer-key confinement; tutor scope, redirection and
capability refusal; keyboard-only laboratory use; phone-width layout.

## Defects found by the browser suite and fixed

1. **Tutor context update loop.** The scope setter was recreated on every
   render, so pages that set it from an effect re-rendered without end. The
   setter is now stable and a no-op when nothing changes.
2. **Pages mounted before the guest session existed.** Session-dependent
   requests raced the bootstrap and returned 401. The shell now waits for the
   bootstrap to resolve before rendering a route.
3. **Duplicate-key crash on first touch of a topic.** Two concurrent requests
   could both insert the same topic-progress row. Creation is now an upsert
   that does nothing on conflict, then re-selects.
4. **Lost step completions.** Concurrent step writes overwrote each other
   through a read-modify-write race. The merge now happens inside the database.
5. **A vanishing amplitude drew a thin negative bar.** Rounding artefacts could
   look like a small negative amplitude. Zero magnitude now draws nothing and
   is labelled 0.
6. **Topic 1.3 had no recorded measurement to repeat.** Its sampling laboratory
   now includes a real measurement, so "measure this trajectory again" acts on
   an actual recorded outcome.
7. **A missing topic rendered a bare error.** It now renders an explicit
   not-found page stating that it is not a lesson waiting to be unlocked.
8. **Submitting a task wiped the laboratory.** Refreshing progress blanked the
   page while the request was in flight, which unmounted the lesson and lost
   the learner's circuit, selected run and the verdict they had just been
   given. A refresh now keeps the current data on screen.
9. **An answer could be lost inside the save debounce.** Navigating away within
   400 ms of choosing an assessment answer dropped it. A pending save is now
   flushed with `keepalive` when the page is hidden.
10. **Single-asterisk emphasis rendered literally.** Authored italics showed
    their asterisks; the Markdown renderer now supports them.

## Known limitations

- **Live NVIDIA verification pending.** No API key was supplied, so no
  authenticated provider request has been made from this build. The adapter,
  the validation path, every failure path, and the authored fallback are
  covered by automated tests using an explicit test adapter. The live tutor
  question set in `docs/ACCEPTANCE.md` section D has **not** been run against
  the real model.
- **PostgreSQL 16 locally, 17 declared.** See the environment table above.
- **The production container build has not been executed here.** Docker Hub
  base-image layers return 403 through this environment's network policy
  (verified for both `postgres:17` and `python:3.12-slim`). What was verified:
  `docker compose config` validates the stack, and `docker build --check`
  parses both Dockerfiles and fails only at base-image download. CI builds the
  backend image, but `docker compose up --build` has not been run here.
- **No deployment.** Nothing has been deployed, and no hosting has been
  provisioned or paid for.
- **No independent educator review.** The content is researched and
  numerically checked; it has not had the expert review the research document
  asks for.
- **Scope policy is conservative, not proved.** The tutor's scope decisions are
  measured by the test suite in `backend/tests/test_tutor_policy.py`. Passing
  that finite suite does not guarantee correct classification of every future
  prompt.
- **Action pinning.** The CI workflow keeps the supplied major-version action
  tags. Full commit SHAs should be resolved and pinned before a release
  baseline; none were invented here.
