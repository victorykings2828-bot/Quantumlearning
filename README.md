# Quantum Learning Laboratory

A working learning demo where beginners meet a real quantum algorithm first,
then learn the ideas that explain it, then come back and explain it themselves.

Every number on screen is computed by Qiskit for the exact circuit displayed.
Values that come from a formula rather than a simulated circuit are labelled
**analytical prediction**, and the Shor walkthrough is labelled
**conceptual walkthrough** because no Shor circuit is executed.

## What is implemented

- **Introduction** with the simulator label, honest claim boundaries, a
  classical-versus-Grover comparison, and a closing action to the course map.
- **Bounded Grover preview** for N = 4, 8 and 16, 0–8 iterations, with the
  oracle and diffusion blocks expandable, the overshoot visible, and the
  "what if preparation is missing?" variant explicitly outside the standard
  success formula.
- **Shor mystery** as a conceptual storyboard with exact classical arithmetic.
- **Beginner bridge**: five arithmetic checks, vocabulary, and honest use-case
  boundaries. Nothing here is graded and nothing here gates access.
- **All eight Chapter 1 topics**, each with authored teaching text, a
  prediction, a parameter-dependent experiment, stepped results, a four-level
  hint ladder, checkpoints, a transfer item, and completion evidence.
- **Two assessment forms** with the published 8/10 plus essential-item rule.
- **Course map** for 13 chapters with explicit published / coming-soon states
  and prerequisite reasons. No chapter is ever labelled "Locked".
- **Course tutor** with allowlisted Markdown retrieval, an evaluated scope
  policy, an NVIDIA adapter, response validation against the server's own
  envelope, verified run facts, and authored help on every failure path.
- **One and two qubit playground** at `/lab/playground`, inside the published
  bounds, with each qubit's reduced state shown and an explanation of why
  matching histograms are not evidence of entanglement.
- **Guest sessions** with no sign-up: an opaque token in an HttpOnly cookie,
  only its hash stored, CSRF and origin checks on every mutation.

## Quickstart: run it on your laptop

If you have never run a project like this before, follow this section exactly.
It takes about fifteen minutes, most of which is waiting for downloads.

### Step 1 — install two things

1. **Docker Desktop** — <https://www.docker.com/products/docker-desktop/>
   Download it, run the installer, accept the defaults, and restart your
   computer if it asks. On Windows it will enable WSL2 for you.
2. **Git** — <https://git-scm.com/downloads>
   Download, run the installer, accept every default.

Open **Docker Desktop** once and leave it running. You are ready when its
window shows a green "Engine running" indicator at the bottom left.

### Step 2 — open a terminal

- **Windows:** press the Start button, type `powershell`, open **Windows
  PowerShell**.
- **macOS:** press Cmd+Space, type `terminal`, press Enter.

You type commands here one at a time and press Enter after each.

### Step 3 — download the project

```powershell
cd $HOME
git clone https://github.com/victorykings2828-bot/Quantumlearning.git
cd Quantumlearning
git checkout claude/new-session-qdtc6d
```

On macOS the first line is `cd ~` instead; everything else is identical.

### Step 4 — start it

```powershell
docker compose up --build
```

The first run downloads and builds everything, so it takes five to fifteen
minutes. You will see a lot of scrolling text. That is normal. Wait until the
scrolling stops and you see lines mentioning `api` and `web`.

Leave this window open. Closing it stops the app.

### Step 5 — use it

Open your browser at **<http://localhost:8080>**.

That is the whole demo: the introduction, the search experiment, all eight
Chapter 1 topics, the assessment and the laboratory. No sign-up, no account.

To stop it, click the terminal window and press **Ctrl+C**. To start it again
later, `cd` back into the folder and run `docker compose up` (no `--build`
needed the second time).

### Step 6 — turn on the AI tutor (optional)

**Everything above works without an API key.** The tutor still answers, using
the written course material, and labels those answers "Authored course help".

To get live AI answers instead, put your key in a file called `backend/.env`.

In the same terminal, from the `Quantumlearning` folder:

```powershell
copy backend\.env.example backend\.env
notepad backend\.env
```

On macOS: `cp backend/.env.example backend/.env` then `open -e backend/.env`.

Notepad opens. Change these two lines, save, and close it:

```
TUTOR_PROVIDER=nvidia
NVIDIA_API_KEY=paste-your-key-here
```

Then restart the app:

```powershell
docker compose up --build
```

`backend/.env` is ignored by Git, so your key cannot be committed by accident.

### Step 7 — check whether the key actually works

This is the one step that tells you for certain. In a **second** terminal
window, from the same folder:

```powershell
docker compose exec api python -m app.tools.tutor_smoke
```

Read the `status` line:

| What it says | What it means | What to do |
|---|---|---|
| `status : HTTP 200` | The key works. The tutor gives live AI answers. | Nothing. You are done. |
| `FAILED (unauthorized)` | The key was reached and rejected. | Generate a new key at <https://build.nvidia.com> and repeat Step 6. |
| `FAILED (rate_limited)` | The key works but the free allowance is used up. | Wait, or use a different account. The app keeps working with authored help. |
| `FAILED (proxy_blocked)` or `FAILED (connect_error)` | Your network blocked the connection. Not a key problem. | Try another network, or turn off a VPN or corporate firewall. |

This command prints the model, the status and a short sample answer. It never
prints your key.

### If something goes wrong

| Problem | Fix |
|---|---|
| `docker : The term 'docker' is not recognized` | Docker Desktop is not installed or not started. Open it and wait for "Engine running". |
| `port is already allocated` | Something else uses port 8080. Run `docker compose down`, then start again with `$env:WEB_PORT=8081; docker compose up` and use <http://localhost:8081>. |
| The page will not load | Give it another minute; the database has to start first. Then refresh. |
| You want to start completely fresh | `docker compose down -v` deletes the saved progress and the database. |

> **One honest note.** The application, its tests and the browser walkthrough
> were all run and verified. The *container images* were never built during
> development, because that environment could not download base images. The
> compose file and both Dockerfiles are validated and the configuration is
> checked, but your `docker compose up --build` will be the first real build.
> If it fails, the native route below works and is the one that was exercised.

---

## Requirements

- Python 3.12 and [uv](https://docs.astral.sh/uv/) 0.8.17 or newer
- Node 24 and npm (Node 22 also works for local development)
- PostgreSQL 17 (16 works for local development)
- Docker, for the container route

## Run it with Docker

```bash
docker compose up --build
```

This starts PostgreSQL, runs the Alembic migration as a one-shot service,
starts the API, and serves the built frontend behind nginx with `/api`
reverse-proxied to the backend. Open <http://localhost:8080>.

The database is kept in the named volume `quantum-db`. To stop and keep it:

```bash
docker compose down
```

To stop and discard it: `docker compose down -v`.

## Run it natively

Three terminals. On Windows use PowerShell and run each block in its own
window, rather than backgrounding them in one shell.

**1. Database**

```bash
docker compose up -d db
```

Or use a local PostgreSQL and create a `quantum` database owned by a `quantum`
role.

**2. Backend**

```bash
cd backend
uv sync --frozen
uv run --frozen alembic upgrade head
uv run --frozen uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

PowerShell equivalent:

```powershell
cd backend
uv sync --frozen
uv run --frozen alembic upgrade head
uv run --frozen uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**3. Frontend**

```bash
cd frontend
npm ci
npm run dev
```

Open <http://localhost:5173>. Vite forwards `/api` to the backend unchanged, so
the browser only ever sees one origin.

## Configuration

Copy the example file and edit the copy. `backend/.env` is git-ignored and must
never be committed.

```bash
cp backend/.env.example backend/.env
```

| Variable | Meaning |
|---|---|
| `APP_ENV` | `development`, `test`, or `production` |
| `DATABASE_URL` | SQLAlchemy URL for PostgreSQL |
| `PUBLIC_ORIGIN` | The origin the browser uses; checked on every mutation |
| `SESSION_SECRET` | Required in production; the app refuses to start without it |
| `SESSION_TTL_DAYS` | Guest session lifetime, renewed server-side |
| `COOKIE_SECURE` | `true` in any HTTPS deployment |
| `TUTOR_PROVIDER` | `authored`, `nvidia`, or `fake` (tests only) |
| `NVIDIA_API_KEY` | Server-side only. Never in frontend code or a `VITE_` variable |
| `NVIDIA_BASE_URL`, `NVIDIA_MODEL` | Provider endpoint and model id |
| `TUTOR_*` | Temperature, budgets, timeouts, and rate limits |
| `SIMULATION_MAX_OPERATIONS`, `SIMULATION_MAX_SHOTS` | Application bounds |

### Adding the NVIDIA key safely

1. Get a key from the model's official catalog page after signing in.
2. Put it in `backend/.env` as `NVIDIA_API_KEY=...` and set
   `TUTOR_PROVIDER=nvidia`.
3. Never paste it into a chat, an issue, a commit, or the frontend. For a
   deployment, use the host's secret settings; a GitHub Actions secret alone
   does not configure a deployed backend.
4. Verify it with the opt-in smoke test:

```bash
cd backend
uv run --frozen python -m app.tools.tutor_smoke
```

It prints the model, status, latency, and a short non-sensitive excerpt. It
never prints the credential. Ordinary CI does not run it.

With `TUTOR_PROVIDER=authored` the whole course still works; the tutor shows
clearly labelled authored help instead of a live answer.

## Checks

Backend:

```bash
cd backend
uv sync --frozen
uv lock --check
uv run --frozen ruff check .
uv run --frozen ruff format --check .
uv run --frozen python -m app.tools.validate_content
uv run --frozen python export_contracts.py --check
uv run --frozen alembic upgrade head
uv run --frozen pytest -q
```

Frontend:

```bash
cd frontend
npm ci
npm run generate:types
npm run lint
npm run typecheck
npm run test:unit
npm run build
npm run format:check
npm run test:e2e
```

`npm run test:e2e` starts the real FastAPI service and Vite itself and drives a
real browser against them. Only the tutor provider is an explicit test adapter;
simulation, evaluation, and persistence are genuine. It needs a `quantum_e2e`
database:

```bash
createdb quantum_e2e   # or: psql -c 'CREATE DATABASE quantum_e2e OWNER quantum;'
cd backend && DATABASE_URL=postgresql+psycopg://quantum:quantum_local_only@127.0.0.1:5432/quantum_e2e \
  uv run --frozen alembic upgrade head
```

## Reviewing the demo

1. Open the introduction. Read the simulator label, run the search experiment,
   change the target, and watch the marked outcome follow it.
2. Set N = 8 and compare 2 iterations with 3. The second is worse; that is the
   overshoot, and the app says so.
3. Open the Shor mystery. It is a storyboard and it says so on every screen.
4. Follow **Explore the course**. Chapter 1 is published; the other twelve say
   Coming soon and have no working lesson route.
5. Work through Topic 1.7. Compare H→H with H→Z→H, step both to the frame
   before the final H, and see identical probability bars with different
   amplitude signs.
6. Submit an assessment form, then reload. The answers and the result persist.
7. Ask the tutor "why did the minus disappear?", then "recommend a movie". The
   first is answered with citations; the second is redirected without being
   answered.
8. Open **Progress**. Independent evidence, assisted completion, and review
   recommendations are separate columns.

## Repository layout

```
backend/     FastAPI, the Qiskit engine, evaluator, tutor, Alembic migrations
frontend/    React, TypeScript, Vite, Playwright browser tests
content/     Versioned curriculum, private rubrics, tutor knowledge and policy
contracts/   Deterministic OpenAPI export, committed
infra/       Container and reverse-proxy configuration
docs/        Requirements, build guide, acceptance criteria, build status
```

## Honest limitations

See `docs/BUILD-STATUS.md` for what has been run, what has not, and why. In
particular, live NVIDIA verification requires a key this build did not have.
