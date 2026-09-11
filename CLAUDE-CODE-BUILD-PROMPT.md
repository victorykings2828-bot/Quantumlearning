# Paste this request into Claude Code at the project root

Build my Quantum Learning Laboratory as a real, fully functional demo in this repository. This demo must grow into the full platform in the same project after I approve it. Implement the application, not another planning document or a visual-only mockup.

Start by inspecting the repository, current branch, uncommitted changes, existing instructions, package files, and the supplied build kit. Read CLAUDE.md, docs/BUILD-GUIDE.md, docs/ACCEPTANCE.md, docs/NVIDIA-SETUP.md, docs/UI-REFERENCE.md, and the researched blueprint. Preserve compatible existing work. If a requirement cannot be fulfilled yet, record the precise reason and keep implementing independent requirements.

## Product experience

The app opens with an introduction explaining what we teach and how the student will learn. Include a properly labeled classical-versus-Grover search comparison, the ungraded Grover experiment, a short conceptual Shor mystery, and the beginner orientation. End the introduction with a clear action taking the learner to the course overview.

The course overview shows chapters, their subtopics, what the learner will learn, prerequisites, availability, and genuine progress. Chapter 1 must work fully. Later chapters must have accurate descriptions and Coming soon labels until implemented. Never present a fake locked chapter as something that becomes functional after a pass.

No login or signup is required for this demo. Create a secure guest session on the backend and save progress, attempts, run history, and tutor history against it. Explain that clearing site data loses access to anonymous progress. Keep identity separate from evidence so a future account can claim guest progress without a redesign.

Use open browsing and prerequisite-based readiness: anyone can inspect chapter descriptions and previews. The default learning path proceeds through Chapter 1's required topics and checks. Graded tasks in future published chapters require demonstrated prerequisite skills. Do not implement a brittle `previousChapter.completed` chain as the entire access model. Include a server-side access-policy interface and explicit reasons for ready, prerequisite-needed, and coming-soon states.

## Complete Chapter 1

Implement all eight topics from docs/reference/researched-blueprint.md:

1. Bits, qubits, and computational basis.
2. Amplitudes, probabilities, and normalization.
3. Measurement, shots, and replay.
4. Circuit order and X.
5. H and superposition.
6. Z, relative phase, and global phase.
7. Interference: H–H versus H–Z–H.
8. Build/explain capstone and revisit the Grover mystery.

Each topic needs its actual authored explanation, prediction, input controls, experiment, synchronized numerical views, guided task, hints, checkpoint, transfer question, and completion evidence. Implement the two chapter assessment forms and the published scoring rules. Keep answer keys private to the server. A working chapter means the user can complete the whole sequence and resume later, not just navigate its pages.

## Simulation and learning integrity

Use a bounded Qiskit-backed engine behind a provider-neutral interface. A one-qubit foundation circuit and restricted 2–4-qubit Grover presets are sufficient. Keep any general playground at the published one/two-qubit bounds. Use analytical charts only when clearly labeled and tied to their assumptions.

Compute actual results for the selected inputs. Implement play, pause, step, reset, recorded replay, and new run. A shot restarts preparation; remeasuring the same collapsed trajectory is a different operation. Keep exact probabilities, sampled counts, and recorded conditional states separate. All charts and tutor explanations must reference a single revision/run/step/branch identity. Ignore stale responses after edits.

Do not grade random counts against an exact 50/50 requirement. Accept state solutions up to global phase and distribution solutions by the correct probability metric. A valid alternative circuit must pass if the published goal allows it. The AI must not change grades, unlocks, or mastery.

## Persistent tutor and NVIDIA

Use the initial model `nvidia/nemotron-3-super-120b-a12b` through the server-side NVIDIA adapter described in docs/NVIDIA-SETUP.md. Keep model ID, base URL, credentials, timeouts, budgets, and provider mode configurable. Do not claim the free trial is unlimited or suitable for production. Do not require a local GPU to use the hosted endpoint.

Use content/tutor/system-policy.md as the tutor behavior specification. Build a versioned Markdown knowledge loader with stable passage IDs and retrieval from content/tutor/knowledge/. Expand the supplied seed with approved lesson content while excluding private assessment answers and engineering instructions. This is retrieval/context, not training the NVIDIA model.

The tutor helps with the current topic, previous topics, necessary course mathematics, the introduction, and platform usage. It should understand contextual follow-ups such as “why did that happen?” using authorized run facts and recent conversation. It must redirect unrelated questions without supplying their requested content. For mixed requests, answer only the relevant part. Recheck scope on every turn; a prior valid quantum question does not make future requests automatically valid.

Use server-side routing, allowlisted retrieval, structured response validation, and an evaluated scope policy. Do not rely on a keyword check or a system prompt alone. The tutor cannot browse arbitrary websites, execute learner code, access other guests' data, or receive hidden answer keys. Numerical claims about a run must use verified facts. Show citations to actual retrieved passages. Provide authored help when the provider is unavailable, times out, exceeds quota, or returns invalid output.

Do not expose unchecked streamed content, private reasoning traces, or guessed citations. Show progress while waiting and then render validated answer blocks. Test the live provider separately when the user has configured a key; deterministic CI uses an explicit test adapter. Never show a test adapter as a live NVIDIA conversation.

## Visual reference

Inspect the images listed in docs/UI-REFERENCE.md when present and derive the visual structure from them. Match hierarchy, spacing, typography, borders, colors, navigation, and panel arrangement. Improve accessibility, responsiveness, and readability without replacing the requested look with a generic AI dashboard.

If images are missing, record visual matching as pending and continue backend, simulation, content, tests, and a provisional neutral layout. Do not claim to have seen or matched an image that is not present. The product must feel like a professional scientific learning tool: purposeful controls and diagrams, no decorative particles or unnecessary glow.

## Build process

Work through the phases in the build guide. Establish one genuine end-to-end experiment early, then finish the whole demo. Create real dependency lockfiles, database migrations, deterministic exported contracts and generated client types, required scripts, and the expanded CI workflow. Use the supplied checks as a baseline, preserving their checks and adding meaningful integration, browser, content, ownership, and tutor-policy verification.

Keep CI independent of private API credentials and paid services. Run the browser against the real backend and PostgreSQL. Include keyboard interaction, refresh/resume, stale-response handling, replay, quota fallback, unrelated-question redirects, and secret-leak tests. Test the production container build and documented local startup.

Write a straightforward README with tested startup commands for Windows and Docker, environment configuration, how to add the API key safely, how to run checks, and how to review the demo. Update docs/BUILD-STATUS.md after each phase with evidence and remaining work. Do not check a task complete because a file exists.

Do not stop at a plan or a styled homepage. Continue until the authorized demo acceptance criteria pass, or a specific external input prevents the remaining dependent work. Finish with a concise report listing implemented behavior, tests actually passed, live API verification status, visual-reference status, local startup instructions, and any remaining limitations. Do not claim deployment or GitHub publication unless actually performed and authorized.
