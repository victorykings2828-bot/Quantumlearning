# Build status

Updated after the demo implementation phases. Every "run" line below records a
command that was actually executed in this environment, with its outcome. No
status is inferred from a file existing.

## Environment this was verified in

| Component | Declared for the project | Used for local verification | Note |
|---|---|---|---|
| Python | 3.12 | 3.12.11 (installed by uv) | matches |
| uv | 0.8.17+ | 0.8.17 for development, **and 0.12.12 verified** | the lockfile, `uv lock --check`, `uv sync --frozen` and the full test run were all confirmed under 0.12.12, the version the workflow pins |
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
| `uv run --frozen pytest` | **223 passed**, under both the default settings and CI's `TUTOR_PROVIDER=fake` |
| `uv run --frozen python -m app.tools.validate_content` | pass |
| `uv run --frozen python export_contracts.py --check` | pass |
| `uv run --frozen python -m app.tools.tutor_smoke` | **ran with a real key supplied by the user**; the request could not leave this sandbox. The build environment's proxy denies outbound CONNECT to `integrate.api.nvidia.com` with 403, as it does for any host outside its allowlist. The smoke test reports `proxy_blocked` and states that this is a network failure, not a rejected credential |

Frontend (`cd frontend`):

| Command | Outcome |
|---|---|
| `npm install` | pass |
| `npm run generate:types` | pass, `src/api/schema.d.ts` regenerated from the committed contract |
| `npm run lint` | pass, **no errors and no warnings** |
| `npm run typecheck` | pass |
| `npm run test:unit` | **18 passed** |
| `npm run build` | pass |
| `npm run format:check` | pass |
| `npm run test:e2e` | **32 passed** in 38 s (Chromium against the real API and PostgreSQL). This sandbox's preinstalled Chromium is an older build than the one the pinned Playwright expects, so the run needs `PW_CHROMIUM_PATH=/opt/pw-browsers/chromium-1194/chrome-linux/chrome`. On an ordinary machine `npx playwright install chromium` makes the variable unnecessary; CI installs the matching browser and does not set it |

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
11. **CI could not run the backend tests.** The test tools sat in an optional
    extra, which `uv sync --frozen` does not install, so `pytest` was missing
    on the runner. They are now a uv dependency group, which a plain
    `uv sync --frozen` installs. Verified from a clean environment with
    uv 0.12.12, the version the workflow pins.
12. **Authored help rendered as one giant heading.** A missing blank line made
    the card's heading and its body a single Markdown block.
13. **The tutor drawer covered the experiment it was explaining.** On a wide
    screen it now takes its own column, and the floating launcher hides while
    it is open instead of sitting on top of a result panel.
14. **Closing the drawer with Escape lost focus.** The launcher was focused
    while still hidden, which silently does nothing; focus is now restored
    after the render that unhides it.
15. **Two tutor tests read the ambient provider setting.** They described
    behaviour with no provider configured but did not pin it, so they passed
    locally and failed in CI, where the workflow sets the fake adapter. They
    now pin authored-only settings themselves.
16. **The test suite read a developer's `.env`.** Someone with a real provider
    key in `backend/.env` would have had the suite make live calls with it.
    Under `APP_ENV=test` the local `.env` is now ignored, with a test proving
    it.
17. **A blocked connection was reported as a generic transport error.** The
    adapter now distinguishes a proxy refusal and a connection failure from a
    rejected credential, and says which it is.

## Lint cleanliness (react-refresh)

ESLint's `react-refresh/only-export-components` rule fired on six files that
exported a React component *and* a hook or context object from the same module.
The rule is not cosmetic: a mixed module breaks fast refresh, so an edit during
development remounts the tree and silently discards component state.

The fix separates the concerns rather than disabling the rule. Contexts and
hooks now live in their own modules and the component files import them:

| New module | What it holds |
|---|---|
| `src/app/sessionContext.ts` | the guest-session context object |
| `src/app/useSession.ts` | the `useSession` hook |
| `src/features/tutor/context.ts` | the tutor context object and its types |
| `src/features/tutor/useTutor.ts` | the `useTutor` hook |
| `src/features/lesson/circuit.ts` | circuit helpers shared by the editor and its tests |

`npm run lint` now reports no errors and no warnings, and the full browser
suite passes unchanged after the move, which is what establishes that the
refactor is behaviour-preserving.

## Known limitations

- **Live NVIDIA verification is still pending, and cannot be completed from
  this build environment.** A real key was supplied and configured correctly:
  the application read it, reported `provider: nvidia` and
  `live_answers_available: true`, and attempted the call. The request never
  left the sandbox, because this environment's network policy denies outbound
  CONNECT to `integrate.api.nvidia.com` with HTTP 403 (`pypi.org` and
  `api.github.com` are reachable; `integrate.api.nvidia.com` and
  `www.google.com` are not). So the credential has **not** been exercised
  against the provider, and the live tutor question set in
  `docs/ACCEPTANCE.md` section D has **not** been run against the real model.
  Run `uv run --frozen python -m app.tools.tutor_smoke` from a machine with
  direct internet access to complete it.

  What this attempt did verify, against a genuine network failure rather than a
  simulated one: the adapter surfaces the refusal as `proxy_blocked`, the
  learner sees clearly labelled authored help rather than an error, work is not
  lost, and the credential appears in no response, log or diagnostic.
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
