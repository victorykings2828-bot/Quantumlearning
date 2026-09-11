# Quantum Learning Laboratory — Claude Code build kit

Prepared 11 September 2026. This package gives Claude Code the requirements, engineering contracts, source material, tutor knowledge, and acceptance checks for building the working demo in one extensible GitHub repository.

**This is a build package, not an implemented website.** Your UI reference `editor-solved_1.png` has been supplied and analyzed. No GitHub repository URL has been supplied. No repository has been created or changed remotely, no NVIDIA key has been used, and no live AI integration has been tested.

## 1. The decisions to build around

1. **No login in the demo.** Start immediately as a guest. Save progress against a secure server-issued guest session so authentication can be added later without replacing the learning system.
2. **Introduction → course overview → Chapter 1.** The introduction includes the classical/Grover comparison, optional Shor mystery, and beginner orientation. Its final primary action goes to the course overview, not directly into a lesson.
3. **Browse openly; gate assessed work by prerequisites.** Everyone can see the chapter map, descriptions, and algorithm previews. Guided tasks and assessments require demonstrated prerequisite skills. Completing Chapter 1 is the default route, with a diagnostic route available later. Unimplemented chapters say **Coming soon**, not **Locked**.
4. **Build all eight Chapter 1 topics properly.** Each includes explanation, prediction, parameter-dependent experiment, stepped results, practice, transfer, and deterministic checks.
5. **Persistent, course-scoped tutor.** It helps with the current topic, earlier topics, their mathematical prerequisites, the introduction, and using this platform. It redirects unrelated requests without answering their unrelated substance.
6. **Markdown knowledge, retrieved per question.** Supplying Markdown to a model is context/retrieval, not model training. The application must load the right passages on every relevant request.
7. **NVIDIA Nemotron 3 Super as the initial prototype model.** Its catalog currently lists a free endpoint. The hosted trial has account-specific limits and is for internal testing/evaluation. Keep the provider replaceable for production.
8. **One project from demo to product.** Keep stable content IDs, guest ownership, database migrations, API contracts, simulation interfaces, and versioned assessments from the first working release.

## 2. What to give Claude Code

Copy this package into the intended project root. Its files can coexist with an existing project; inspect conflicts before replacing anything.

| File | Purpose |
|---|---|
| `CLAUDE.md` | Concise persistent project instructions for Claude Code |
| `CLAUDE-CODE-BUILD-PROMPT.md` | The build request to paste into Claude Code |
| `docs/BUILD-GUIDE.md` | Architecture, routes, persistence, API, security, and delivery contracts |
| `docs/ACCEPTANCE.md` | What must be tested before claiming the demo is complete |
| `docs/UI-REFERENCE.md` | Reference-image index and detailed visual specification |
| `docs/NVIDIA-SETUP.md` | Model decision, server-side configuration, trial limits, and smoke test |
| `docs/BUILD-STATUS.md` | Initial implementation status; Claude updates this as it builds |
| `docs/reference/researched-blueprint.md` | Complete researched curriculum, Chapter 1 tasks, and answer bank |
| `docs/reference/original-engineering-blueprint.md` | Prior architecture for context; this package overrides its login/MVP conflicts |
| `docs/reference/checks.original.yml` | Unmodified supplied workflow, retained for comparison |
| `content/tutor/system-policy.md` | Tutor behavior policy, separate from educational source text |
| `content/tutor/knowledge/chapter-1.md` | Initial original educational knowledge with source links and stable section IDs |
| `templates/checks.yml` | Extended GitHub Actions workflow; install when its commands exist |
| `templates/backend.env.example` | Variable contract; safe placeholders, no credentials |
| `templates/gitignore.txt` | Patterns to merge into the project's existing `.gitignore` |

The package deliberately does not install a workflow that fails immediately in a documentation-only repository. Claude must create the required project commands, then install `templates/checks.yml` as `.github/workflows/checks.yml`. Never hide missing application components behind always-green checks.

Anthropic documents `CLAUDE.md` as project context for Claude Code. Keep it short and point to detailed files rather than pasting the entire research corpus into it. [Claude Code memory documentation](https://code.claude.com/docs/en/memory).

## 3. GitHub setup

### If you already have a repository

Clone/open that repository and check its current branch, uncommitted work, architecture, and instructions. Add this kit as project documentation; do not replace existing source directories simply because their names differ. Use a branch such as `feat/quantum-learning-demo` after verifying the name is available. Preserve existing project conventions when compatible with the requirements.

### If you do not have a repository

Create an empty **private** GitHub repository for the internal demo, clone it, and copy the kit contents into the root. Private is a proposed initial visibility, not permission to publish the material publicly. Let Claude create the actual frontend/backend inside that repository. Use ordinary Git commits and pull requests; do not use a separate throwaway demo repository.

Do not paste the NVIDIA key into Claude chat, an issue, a commit, or the frontend. Add it locally to ignored `backend/.env`, and later to the deployment's secret settings. A GitHub Actions secret alone does not configure a deployed backend.

GitHub stores code and runs CI. **GitHub Pages alone cannot host this Python API, database, and secret-bearing tutor service**; it is static hosting. Use the container deployment specified in the build guide or a compatible application host. [GitHub Pages documentation](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages).

## 4. Give Claude the visual references

The supplied `checks.yml` is a CI workflow. Your actual visual reference is included at `docs/ui-reference/editor-solved_1.png` and analyzed in `docs/UI-SPECIFICATION.md`.

Claude must inspect the actual image before implementing the UI. Preserve the cream editorial style, serif headings, navy controls, red accents, and bordered scientific panels. The specification explains which layout and scientific-copy problems to correct. Matching the reference does not mean reproducing its floating navigation overlap or inaccurate local-state wording.

## 5. Run the build

Open Claude Code at the project root and paste the contents of `CLAUDE-CODE-BUILD-PROMPT.md`. It should inspect first, then implement each phase and verify it. Do not accept a landing page with hardcoded graphs as completion.

The researched blueprint defines the educational activities. The build guide defines how those activities must function. The tutor knowledge file is only for answering learner questions; it must not receive the private assessment answer bank.

When you resume a later Claude session, use:

> Read CLAUDE.md, docs/BUILD-STATUS.md, and the acceptance checklist. Inspect the actual repository and the last relevant changes. Continue the next incomplete demo phase. Verify previous claims when needed, preserve working functionality, and update the status with tests actually run. Do not restart or redesign the project.

## 6. What should be demonstrated to you

A real browser walkthrough from introduction to course overview, all eight Chapter 1 topics, a submitted assessment, persisted guest progress after refresh, replay versus rerun behavior, and a real NVIDIA-backed tutor answer when the key is configured. Also demonstrate an unrelated request being redirected, an AI outage using authored help, and later chapters correctly labeled Coming soon.

The final build report must distinguish **implemented**, **tested locally**, **tested in CI**, **verified with the live NVIDIA API**, and **deployed**. None of those statuses may be substituted for another.

After you approve the demo, extend the same modules and content system for the later chapters. That approval is the boundary for expanding the product scope; it is not a reason to leave authorized demo features incomplete.
