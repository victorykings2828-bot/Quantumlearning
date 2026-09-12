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
| `uv run --frozen python -m app.tools.tutor_smoke` | **HTTP 200 on the user's machine** (see Known limitations); from this sandbox the request could not leave. The build environment's proxy denies outbound CONNECT to `integrate.api.nvidia.com` with 403, as it does for any host outside its allowlist. The smoke test reports `proxy_blocked` and states that this is a network failure, not a rejected credential |

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

## The one-command launchers

`start.sh` (macOS, Linux) and `start.ps1` (Windows) reduce starting the demo to
a single command. Each one checks that Docker is installed and running, creates
`backend/.env` from the example on first run, starts the stack detached, then
**polls the site until it answers** before printing "Ready". `docker compose up
--wait` is deliberately not used: it has a rough edge with the one-shot
`migrate` service, and polling the URL verifies the thing that actually matters.

What was exercised here, with a stub `docker` on the PATH where a real one
could not be used:

| Path | How it was tested | Result |
|---|---|---|
| Docker missing | isolated PATH with no `docker` | prints the install instructions, exits 1 |
| Start succeeds | stub `docker`, a real server on 8080 | polls, prints Ready, exits 0 |
| Containers fail to start | real `docker`, base-image pull blocked by this sandbox | prints the failure and how to see logs, exits 1 |
| Site never answers | stub `docker`, dead port | gives up after the timeout, exits 1 |
| `--stop` | stub `docker` | runs `compose down`, exits 0 |
| `--help` | direct | prints usage only |

`--set-key` writes the key and switches the provider **together**, and the
launcher warns at startup when a key is present while `TUTOR_PROVIDER` is still
`authored`. That half-configured state was reachable before, and it is the one
misconfiguration that looks like it worked: the key is read, ignored, and the
tutor silently stays in authored mode. `--check-ai` runs the smoke test inside
the running container.

**`start.ps1` has not been executed.** No PowerShell exists in this build
environment. It is a line-by-line translation of the shell script whose logic
was tested, but it is unrun, and that is the one part of the quickstart a
Windows user would be the first to try.

**A full `docker compose up` has still never completed anywhere.** CI builds
the backend image successfully, and `docker compose config` validates the
stack, but this sandbox cannot pull the `postgres:17` and `python:3.12-slim`
base layers (403 through its network policy), so the assembled stack has not
been observed running. The launchers are written against that unverified path.

## Known limitations

- **Live NVIDIA verification: DONE, by the user, on their own machine.**
  On 2026-09-12 the user ran `.\start.ps1 -SetKey` on Windows with their own
  key and reported the smoke test's output:

  ```
  status           : HTTP 200
  latency          : 10372 ms
  served model     : nvidia/nemotron-3-super-120b-a12b
  schema validation: passed
  intent           : answer
  cited passages   : chapter-1.z-gate
  ```

  The returned answer ("the Z gate multiplies the amplitude of |1> by -1 …
  |-b|^2 = |b|^2, therefore the Z-basis outcome probabilities remain the same")
  is scientifically correct, cites a real passage, and passed schema
  validation. This confirms the hosted endpoint accepts the adapter's request
  shape, the model honours the required response object, and citation
  validation admits a genuine passage rather than only rejecting forged ones.

  Recorded honestly: **this was observed in the user's terminal output, not
  executed by this build.** The live half of `docs/ACCEPTANCE.md` section D —
  the full prompt set against the real model — has still not been run; one
  live question has.

- **The sandbox this was built in cannot reach the provider.** A real key was supplied and configured correctly:
  the application read it, reported `provider: nvidia` and
  `live_answers_available: true`, and attempted the call. The request never
  left the sandbox, because this environment's network policy denies outbound
  CONNECT to `integrate.api.nvidia.com` with HTTP 403 (`pypi.org` and
  `api.github.com` are reachable; `integrate.api.nvidia.com` and
  `www.google.com` are not). So nothing in this repository's own verification
  record exercises the credential against the provider; that step was completed
  by the user instead, as recorded above.

  What this attempt did verify, against a genuine network failure rather than a
  simulated one: the adapter surfaces the refusal as `proxy_blocked`, the
  learner sees clearly labelled authored help rather than an error, work is not
  lost, and the credential appears in no response, log or diagnostic.

  Re-checked after the launchers were added, with the supplied key written to
  `backend/.env` by `./start.sh --set-key`: the application loads it and reports
  `provider: nvidia`, `key_configured: True`, `live_answers_available: True`,
  and the smoke test reaches the network and returns `proxy_blocked` rather than
  `unauthorized`. Every step up to the outbound request is therefore exercised;
  only the request itself is untested, and only because this sandbox forbids it.
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
