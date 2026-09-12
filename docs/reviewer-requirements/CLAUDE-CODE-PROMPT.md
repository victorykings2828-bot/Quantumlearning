# Claude Code implementation prompt

Copy the following prompt into Claude Code with this folder available. Replace the document folder location if needed; do not paste API keys into the prompt.

---

Extend the existing Quantumlearning project in place. Implement the reviewer requirements below as working features. Preserve its introduction, editorial cream/navy UI, guest access, existing Chapter 1, course navigation, validated simulation and deployment structure. No login is required. Do not redesign the website or replace the working application with a new scaffold.

Read these supplied documents first:

1. `REPOSITORY-REVIEW.md`: targeted review of commit c76df990554262b9e715c59fa253236d784bdeed.
2. `LEARNING-TUTOR-AND-ASSESSMENT.md`: shared policies and acceptance criteria.
3. `CHAPTER-2.md`: six topics, scientific content, practical tasks and private assessment evidence.
4. `CHAPTER-3.md`: seven topics, including the fixed three-qubit teleportation protocol.

The latest user requirements in this prompt and shared specification supersede conflicting earlier instructions about hard chapter locks, tutor access and descriptive assessment. Inspect repository instructions and the current working tree. Preserve uncommitted work and adapt to newer code. Do not revert to the reviewed commit. Report the actual starting commit and any material differences from the review.

## Required learning flow

Retain introduction → course page → chapter → topics. Add a beginner-friendly chapter entry section with what the learner will do, useful prior ideas in plain language, brief recall definitions, one worked example and optional ungraded diagnostic. Supply the specific recaps from each chapter guide; improve Chapter 1's entry consistently.

Use open access to implemented chapters with recommended order. A prerequisite is helpful preparation, not a gate. Keep coming-soon chapters clearly unavailable. Distinguish navigation availability, practice completion and evidence of understanding. All Chapter 2 and Chapter 3 topics must have readable lessons, usable interactions, tasks, answers/feedback and resumable progress; do not mark chapters available while shipping placeholder lessons.

Keep chapter content separate in the content system. Reuse existing layouts and contracts. Show math with accessible explanations and text alternatives. Provide preview/predict → execute step by step → interpret → check understanding. Preserve the learner's circuit and selected run/frame while submitting answers or using the tutor.

## Tutor boundary — implement before indexing new lessons

On Chapter 1 pages the tutor may use Chapter 1 and approved beginner recall only. On Chapter 2 it may use Chapters 1 and 2. On Chapter 3 it may use Chapters 1–3. The full current chapter is eligible. Returning to an earlier chapter reduces scope, regardless of earlier visits or completions.

Review `backend/app/tutoring/service.py` and `knowledge.py`. Replace the Chapter 1-only scope mapping with trusted chapter metadata. Remove unrestricted retrieval fallback and ensure missing metadata fails closed. Separate the introduction preview collection from full future lessons. Filter every context channel: retrieval, history, summaries, cache, selected lab facts and assessment feedback. Partition conversations and caches by chapter and policy version.

Create a metadata-only future-topic directory from the actual curriculum catalog. A future question should name its chapter and redirect to an eligible concept, without teaching the future content. Example on Chapter 2: “That is taught in Chapter 3 — Multiple qubits and entanglement.” Handle aliases, ambiguous terms and mixed questions. Future routing and off-course redirection must work without an API key. Do not invent chapter titles. A future title may be visible; its full lesson body must not enter the request.

Export tutor material separately from private answer keys and rubrics. These authoring documents contain answers and must never be indexed wholesale. Keep valid source citations through the content loader; test the exported link format. The normal tutor cannot access examiner keys or write grades.

## Scientific implementation

Use the chapter guides' explicit state, phase, basis and qubit-order conventions. Qiskit display ordering is |q1 q0⟩ for two qubits. Build numerical acceptance fixtures before connecting the UI. Inspect the existing simulator before deciding what to extend.

The reviewed circuit schema already accepts complex amplitudes and four qubits; reuse that. Extend validated operations as needed for S/S†, phase/rotation gates, basis changes and the bounded protocol. Keep finite-angle checks, normalization checks, operation limits, existing shot counts and old saved-circuit compatibility. Never trust arbitrary client-provided matrices or run facts.

Chapter 2 must distinguish relative/global phase, gate order, Bloch coordinates, rotations and X/Y/Z readout. To read Y through Z measurement, execute S† then H, and label the resulting outcomes as Y eigenvalues. Do not confuse a basis-change circuit's final physical state with the original-basis post-measurement state.

Chapter 3 must support product states, controlled gates, Bell states, joint/marginal statistics and a genuine mixed-state comparison. A zero-length reduced Bloch vector is a mixed state, not “no state,” and does not by itself prove entanglement. Matched Z statistics alone do not distinguish a Bell state from the specified classical mixture. Handle mixed-state goals with density/reduced-state evidence, not a fabricated statevector.

Implement Topic 3.7 as a supported three-qubit teleportation lab with explicit measurement outcome mapping and conditional corrections. Validate all four branches and Bob's reduced state for several inputs, including a complex-phase input. A fortunate 00 branch must not count as protocol success. Keep the public input bounded; a dedicated validated protocol representation is acceptable if general classical feed-forward would expand scope unnecessarily.

## Two explanatory animations

Implement only the two required animations first, using existing frontend rendering tools where practical:

1. Chapter 2 Topic 2.4: H → P(φ) → H. Rotate a complex amplitude arrow, keep intermediate Z probabilities unchanged, then show interference producing cos²(φ/2). Include φ=0, π/2, π and prediction before reveal.
2. Chapter 3 Topic 3.4: H(q0) → CX(q0,q1). Show the 01 amplitude contribution moving to 11, local reduced-state endpoints and the comparison with a classical mixture in Z and X.

Supply play/pause/step/replay/speed controls, keyboard access, reduced motion and an equivalent static table. Computed values must agree with the simulator. Cosmetic motion must not masquerade as a physical trajectory. Prevent stale animation frames after input changes. Follow the detailed scientific caveats in the shared specification.

## Assessment that gathers evidence

Extend the assessment system beyond MCQs. Use reviewed prediction-and-reason MCQs, descriptive explanations, counterexamples, error diagnosis, unfamiliar lab variants and neutral follow-ups. Add the chapter-specific item families and explicit 0/1/2 anchors for claim, mechanism and transfer. Include comparable targeted evidence checks for Chapter 1 using its established objectives; avoid changing its scientific scope.

Keep objective answers and simulator checks deterministic. Add a separate server-side AI assessor for descriptions. Its privileged input contains the active private rubric, reference evidence, exact learner response and verified run facts. It returns criterion scores, actual supporting quotes, misconception IDs and a sufficient/insufficient/uncertain recommendation. Validate schemas, quotes and IDs and reject contradictions with simulator facts. It cannot directly mark chapters complete. Treat learner text as data and test grading prompt injection.

Implement the shared pilot policy: two independent item families per essential concept, including transfer; an explanation at least 5/6 with no zero criterion; applicable practical checks passed; no unresolved critical misconception. MCQ perfection alone is insufficient. Mark assisted attempts separately and offer a fresh independent variant after help. Do not reward long writing, exact keywords or polished English over correct reasoning.

Persist answers before model calls. Support pending, provisional, needs-review and reviewed outcomes, immutable evidence versions and a review/override path. Provider timeout or malformed output must not cause lost work, a false pass or a zero score. During independent assessment the tutor may clarify wording, but switching to answer help marks the attempt assisted. Keep the assessment chapter ceiling frozen for that attempt.

Reuse the existing NVIDIA adapter and credentials mechanism. Keep keys server-side. The latest recorded live model is nvidia/nemotron-3-super-120b-a12b; preserve configuration rather than silently switching models. A separate configurable assessor model is acceptable. Bound tokens, timeouts, calls and retries. Without a key, authored help and deterministic checks work; descriptive answers remain pending/manual-review with an honest status.

Create a calibration dataset format and evaluation command. Include short correct answers, fluent errors, partial understanding, language variations and injections. Provide a reviewer workflow for two human ratings and adjudication. Report held-out agreement, critical false passes, false rejections and abstention. Label synthetic fixtures as synthetic; they verify software behavior, not educator agreement. Do not invent educator reviews or claim assessment accuracy before calibration.

## Verification and completion

Add meaningful tests for the new contracts and regressions; run the project's required checks. At minimum cover:

- Chapter eligibility, empty retrieval, missing metadata, future routing, returning to an earlier chapter, history/cache boundaries and invalid topic/chapter combinations.
- Numerical phase/basis/Bloch fixtures, tensor ordering, CNOT on product counterexamples, Bell versus mixture in X/Z and all teleportation branches.
- Both animations at endpoint values, stepping, changed inputs, motion disabled and keyboard use.
- Persisting descriptive answers, schema/quote validation, injection handling, provider outage, assisted evidence, rubric versions and server-owned completion.
- Perfect MCQs plus a critical misconception does not demonstrate the concept; concise valid reasoning is accepted; a new transfer item is required after a revealed answer.
- Existing Chapter 1, guest identity, no lost circuit/run on task submission, restart/resume and production build.

Inspect the actual frontend test structure and use its established tools. Use a deterministic provider adapter for CI, plus a separate opt-in live acceptance command. Never claim fake-adapter tests establish live model quality. Run live tests only with an available appropriately configured key; report missing credentials honestly without blocking unrelated implementation.

Update README, BUILD-STATUS and ACCEPTANCE-RESULTS with exact commands, results and remaining gaps. Reconcile older claims that live NVIDIA or CI has never run with the later evidence. Do not mark deployment, container acceptance, educator calibration or full live tutor quality complete unless actually verified.

Finish with a concise implementation summary, changed-file map, commands and outcomes, how to launch the website, a reviewer walkthrough, and any remaining limitations. Complete the working implementation rather than stopping after a plan. Do not deploy, push, merge or publish without the user's authorization for those actions.

---
