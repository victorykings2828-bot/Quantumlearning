# Chapter 3 — Multiple qubits and entanglement

Updated research and authoring guide · 12 September 2026 · Reviewer revision 2

This chapter is separate from the other chapter guide. Read it with `LEARNING-TUTOR-AND-ASSESSMENT.md`, which defines the shared onboarding, tutor boundary, animation, and assessment requirements. These updated files supersede the combined guide where they differ. No application code was changed for this deliverable.

The numbered topic lessons below retain the researched science and activities. The author-facing question bank is one source of objective items, not a standalone measure of understanding. The previous 8/10-only chapter policy is superseded by the evidence requirements in the shared specification. Never place this entire authoring document in tutor retrieval: it includes private assessment answers.

## Start here: what this chapter uses

**Learner-facing introduction:** “You have worked with the state of one qubit. Now we will describe two together and discover information that belongs to the pair. We will build an entangled state, compare it with ordinary shared randomness, and finish with a small teleportation protocol. We will explain tensor products and reduced states as they become useful.”

Show this opening before the topic list. Replace a bare prerequisite label with **Useful ideas — with a quick refresher**. Offer **Review the basics** and **Start Topic 3.1**; a recap score must not lock either action. Learners entering directly can use the embedded explanations and links to earlier lessons.

### Quick recap: read, see an example, try one

| Term or skill | Short reminder | Tiny example or action |
|---|---|---|
| Statevector | A list of amplitudes in a stated basis order. | (1/√2,1/√2) represents \|+⟩. |
| Squared magnitude | Probabilities use the real and imaginary parts together. | \|i/2\|²=1/4. |
| Gate order | The circuit's time order determines the intermediate state. | H then Z differs from Z then H. |
| X, H, Z | X exchanges basis amplitudes; H mixes them; Z reverses the \|1⟩ amplitude's sign. | Review H→Z→H on \|0⟩. |
| Measurement basis | A state can be predictable in one basis and random in another. | \|+⟩ is definite in X but 50/50 in Z. |
| Relative phase | Equal Z probabilities can hide different phase relations. | Compare \|+⟩ and \|−⟩ using X. |
| Conditional outcome | After an ideal projective measurement, the selected outcome changes the state description. | A recorded Z result 1 repeats as 1 with no intervening change. |
| Joint versus local question | Asking about the pair differs from asking about one part. | Before quantum examples, sum a two-coin probability table. |

The final row is taught here as a bridge, not assumed knowledge. Scientific reminders follow [R01], [R03], [R05], and [R10] in the reference register.

**Optional four-question check, author key:** (a) H\|0⟩: \|+⟩; (b) distinguish \|+⟩ and \|−⟩: X basis; (c) repeated unchanged ideal Z measurement after outcome 0: 0; (d) in a classical joint table (.1,.2,.3,.4) ordered q1q0, probability q0=0: .4. Show corrective explanation and allow immediate continuation. Teach the table summation if unfamiliar rather than sending the learner away.

### New terms introduced here

3.1: register and bit ordering. 3.2: tensor product and product state. 3.3: controlled gate. 3.4: Bell state. 3.5: joint, marginal, conditional, and reduced state. 3.6: mixture, separability, entanglement. 3.7: classical communication and feedforward. Introduce a 2×2 table before a formal partial trace; do not assume density-matrix fluency at chapter entry.

## Tutor scope in this chapter

Allowed teaching context: orientation/recap content plus **Chapters 1, 2, and 3**. A question about H can retrieve Chapter 1, and a question about Y readout can retrieve Chapter 2. Neither requires leaving the current page. Chapters 4 onward remain excluded from teaching retrieval.

If asked to construct an oracle: “That topic is covered in Chapter 4 — Reversible functions and quantum oracles. Here we can practice the controlled gates that will help you get ready for it.” Obtain the exact title and availability from the project catalog. If a requested concept is not mapped, ask for clarification; do not invent a chapter number.

## Required animation

Implement the **Bell-pair preparation animation** in Topic 3.4 described in the shared specification: highlight the gate, move amplitude contributions among labeled basis slots, show the verified resulting joint state and local reduced states, and compare the classical mixture. Do not animate a signal traveling between entangled qubits.

## Scientific conventions

### Complex amplitudes and state validity

A normalized pure qubit is |ψ⟩ = α|0⟩ + β|1⟩, with |α|² + |β|² = 1. For a complex number a+ib, its squared magnitude is a²+b². Probability is never the square of just its real component. A common phase multiplying the entire state changes no measurement probabilities. A phase difference between nonzero components can affect measurements after a basis change. [Single-system quantum information][R01]

Use radians in stored circuit parameters and offer degrees in the UI, with an explicit unit label and conversion. Relative phase is undefined when one amplitude is zero. Do not invent a phase arrow for a zero amplitude. Validate finite numeric input and normalization; offer an explicit Normalize action rather than silently changing the requested state.

### Bit order

Use Qiskit's native ordering throughout: two-qubit kets read **|q1 q0⟩**, and the vector order is |00⟩, |01⟩, |10⟩, |11⟩. q0 is the least significant bit and usually the top circuit wire. In three-qubit displays use |q2 q1 q0⟩. The numeric index is Σ 2^j qj. Always show the convention near charts and provide per-wire labels. Reversing visual wires does not silently reverse the stored vector. [Qiskit bit ordering][R02]

### Measurement modes and frames

Distinguish these three views:

1. **Exact premeasurement state and probabilities:** computed mathematical model.
2. **Recorded conditional trajectory:** one sampled outcome and the state conditioned on it.
3. **Outcome ignored:** an ensemble density matrix, with branches averaged by probability.

For projectors Pm, p(m)=Tr(Pmρ), and a nonzero-probability branch is ρm=PmρPm/p(m). Ignoring the result yields Σm PmρPm. Never normalize a zero-probability branch. [Measurement formulations][R03]

Replaying a trajectory shows its original outcome. Rerunning prepares the input again and samples afresh. Going backward navigates recorded history; it does not physically reverse measurement. Label any interpolated gate animation as a visual transition, not an additional simulated circuit step.

## Topic lessons

### 3.1 Bit ordering and basis labels

**Objective:** map wire values to a ket, vector position, and integer without swapping qubits.

**Experiment: follow the flipped wire.** Begin |00⟩; apply X to q0 or q1. The four-bar chart, ket, and integer index update together. X(q0) produces |01⟩, index 1; X(q1) produces |10⟩, index 2. [Ordering convention][R02]

**Required task:** construct |10⟩ from |00⟩ and label each wire. **Transfer:** on three wires, q2=1,q1=0,q0=1 is |101⟩, index 5. No three-qubit gate editor is needed here; toggles are enough.

**Four hints:** read the ket header → find the least significant bit → use 2^j weights → reveal mapping. Complete with a new wire assignment and a correct vector index. Include the word “ordering” in feedback rather than diagnosing an incorrect qubit label as a physics misunderstanding.

### 3.2 Tensor products and product states

**Objective:** build joint amplitudes from two independent pure preparations.

If q1 has amplitudes (a,b) and q0 has (c,d), the joint vector in this guide's ordering is (ac,ad,bc,bd). Multiply amplitudes, not probabilities; then take squared magnitudes. Product preparations have factorized measurement probabilities for local measurements. Some joint pure states cannot be written this way. [Multiple-system quantum information][R10]

**Experiment: combine two preparation cards.** Show q1 and q0 cards feeding a 2×2 amplitude grid. Presets: |0⟩, |1⟩, |+⟩, |−⟩, |+i⟩. Then introduce a biased real state.

**Required task:** q1=|+⟩, q0=|1⟩ gives (0,1/√2,0,1/√2), with P01=P11=1/2. **Transfer:** q1=(3/5)|0⟩+(4/5)|1⟩ and q0=|+⟩ gives probabilities (0.18,0.18,0.32,0.32).

**Four hints:** expand one tensor factor → connect each pair of coefficients → square each product magnitude → reveal the vector. Require one amplitude and one marginal calculation. Do not suggest two qubits provide four independently readable classical bits.

### 3.3 Controlled gates

**Objective:** predict CNOT on basis states and coherent superpositions without inserting a hidden measurement.

For control q0 and target q1, CNOT maps |00⟩→|00⟩, |01⟩→|11⟩, |10⟩→|10⟩, |11⟩→|01⟩. It acts linearly on a superposition. The control is not measured by the gate. [Multiple-system operations][R10]

**Experiment: test, then break a claim.** Start with the truth table, then compare three inputs: control |0⟩/target |0⟩; control |+⟩/target |0⟩; both |+⟩. Allow control/target reversal and show the labels prominently.

**Required task:** identify that CNOT can entangle |+⟩control|0⟩target but does not entangle every input. With target |+⟩, controlled-X leaves that target unchanged, so |+⟩|+⟩ remains a product state. **Transfer:** repeat CNOT twice and recover the original state.

**Optional CZ comparison:** CZ flips only the |11⟩ amplitude. Applied to |+⟩|+⟩ it changes the state even though immediate Z probabilities remain uniform. This is a bridge to phase oracles; keep the gate definitions separate from a classical conditional statement.

**Four hints:** apply the basis rule → track each amplitude → inspect the target's X eigenstate → show the counterexample. Complete with an explanation of why “CNOT means entangled” is false.

### 3.4 Bell-state preparation

**Objective:** construct and distinguish the four Bell states.

From |00⟩, H(q0) gives (|00⟩+|01⟩)/√2. CNOT(q0→q1) gives |Φ+⟩=(|00⟩+|11⟩)/√2. A local Z makes Φ−; a local X makes Ψ+; combining X and Z makes Ψ− up to a global phase. Bell states are maximally entangled two-qubit pure states. [Entanglement in action][R11]

**Experiment: build, perturb, undo.** Preserve the original screenshot's Bell challenge, but label grading as the authored evaluator using simulator results. Add targets Φ+, Φ−, Ψ+, Ψ−. Display both complex joint amplitudes and local reduced-state panels.

**Required task:** construct Φ+ and explain why preparing both qubits independently in |+⟩ fails. **Transfer:** produce Φ− without changing Z probabilities, and choose a measurement that reveals the sign difference.

| State | Nonzero amplitudes | ⟨XX⟩ | ⟨YY⟩ | ⟨ZZ⟩ |
|---|---|---:|---:|---:|
| Φ+ | 00:+1/√2; 11:+1/√2 | 1 | −1 | 1 |
| Φ− | 00:+1/√2; 11:−1/√2 | −1 | 1 | 1 |
| Ψ+ | 01:+1/√2; 10:+1/√2 | 1 | 1 | −1 |
| Ψ− | 01:+1/√2; 10:−1/√2 | −1 | −1 | −1 |

This table is derived by applying the specified Pauli matrices to the four vectors. “Always agree” must name the basis: Φ+ agrees in Z and X but anticorrelates in Y.

**Four hints:** create a coherent branch → couple q0 to q1 → use a phase or bit flip to change Bell target → reveal one valid circuit. Grade the target pure-state fidelity, not only the two nonzero histogram bars.

### 3.5 Joint, marginal, and conditional statistics

**Objective:** distinguish a pair's distribution from either qubit's local statistics and from a selected measurement branch.

Marginalize by summing probabilities, not amplitudes. For example, P(q0=0)=P00+P10. For a selected outcome, P(A|B)=P(A,B)/P(B), provided the denominator is nonzero. Reduced density matrices capture all local measurement statistics, beyond one basis's marginal probabilities. [Density matrices and reduced states][R12]

**Experiment: three linked views.** Show a joint 2×2 probability grid, two marginal charts, and a conditional selector. Compare Φ+, |+⟩|+⟩, and |00⟩. For Φ+, both local Z distributions are 50/50 while Z outcomes agree. Independent |+⟩ states also have 50/50 local distributions, but four joint outcomes occur.

**Required task:** calculate both marginals and P(q1=1|q0=1) for Φ+. Answers: both marginals 50/50, conditional probability 1. **Transfer:** use √0.36|00⟩+√0.64|11⟩. Both marginals become (0.36,0.64), agreement remains certain, and local states are mixed.

Show q0 measurement on Φ+ in three stages: before measurement; a branch selected as 0 or 1; result ignored. In a selected Z branch, the pair is |00⟩ or |11⟩. In the ignored-outcome view the pair is a classical mixture of those states.

**Four hints:** locate the relevant cells → sum their probabilities → restrict to the selected event → divide by the event probability. Zero-probability conditions must show “undefined,” not 0%. Complete with correct marginal and conditional reasoning on a changed input.

### 3.6 Mixtures versus entanglement

**Objective:** explain why local randomness or a single correlated histogram does not establish entanglement.

Introduce ρ=Σk pk|ψk⟩⟨ψk| as an ensemble description. A mixed bipartite state is separable if it can be expressed as a probability mixture of product states. A pure joint state is entangled exactly when its reduced state is mixed. The last criterion requires knowing that the joint state is pure; it is invalid for arbitrary mixed joint states. [Preskill, states and ensembles][R13]

**Experiment: same Z plot, different states.** Compare:

- Bell state ρBell=|Φ+⟩⟨Φ+|.
- Classical mixture ρmix=(|00⟩⟨00|+|11⟩⟨11|)/2, created by selecting 00 or 11 with an ordinary fair random bit for each preparation.
- Product state |+⟩|+⟩.

The first two have identical Z distributions and local reduced states I/2. The Bell density matrix has off-diagonal entries ρ00,11=ρ11,00=1/2; the mixture does not. Never represent the mixture by averaging its component amplitude vectors: that produces the wrong object.

| Quantity | Φ+ | Classical 00/11 mixture | \|+⟩\|+⟩ |
|---|---:|---:|---:|
| Z probabilities, ordered 00/01/10/11 | 1/2,0,0,1/2 | 1/2,0,0,1/2 | 1/4 each |
| X probabilities, ordered ++/+−/−+/−− | 1/2,0,0,1/2 | 1/4 each | 1,0,0,0 |
| Global purity Tr(ρ²) | 1 | 1/2 | 1 |
| Either local purity | 1/2 | 1/2 | 1 |
| Either local Bloch length | 0 | 0 | 1 |
| Entangled? | Yes | No | No |

**Required task:** select a basis that separates the named Bell and mixture preparations and explain why the Z chart was insufficient. **Transfer:** classify a mixture of |++⟩ and |−−⟩. It is separable despite perfect X correlation and locally mixed states.

**Evidence boundaries:** the simulator can inspect the specified density matrix and use a two-qubit entanglement measure. Measurements alone require additional assumptions and enough data. Distinguishing the two named presets is not a universal entanglement test. One off-diagonal entry is not by itself proof either; product superpositions have coherences. [Qiskit quantum-information measures][R14]

For normalized pure vectors (a,b,c,d), the two-qubit product condition is ad−bc=0. Concurrence is 2|ad−bc|. For mixed two-qubit states use the proper density-matrix concurrence routine rather than that pure-vector formula. Tolerances must make “numerically near separable” explicit.

**Optional depth, not a required new topic:** a CHSH experiment tests a local-hidden-variable bound under specified assumptions. Use the published IBM tutorial if implementing it later. Do not call the simple X/Z preset comparison a loophole-free Bell test or imply every entangled state violates every chosen CHSH setting. [CHSH tutorial][R15]

**Four hints:** compare global versus local information → inspect preparation type → change basis → show both density matrices and the separable decomposition. Complete with the key claim: “Each qubit has a mixed reduced state; it does not have its own pure state vector.” Never say “it has no state.”

### 3.7 Teleportation protocol

**Objective:** trace how an input state is transferred using a shared Bell pair, two classical bits, and conditional corrections.

**Learner explanation:** “Teleportation transfers a quantum state to a receiving qubit using a previously shared entangled pair and a classical message. The sender's original state is consumed by the protocol. The message alone does not contain a classical recipe for an arbitrary unknown qubit, and the receiver needs the message before applying the appropriate correction.” [Quantum teleportation][R16]

**Bounded three-qubit lab:** q0 is the input; q1 is Alice's Bell half; q2 is Bob's Bell half. Use |q2 q1 q0⟩ for vectors. The input selector knows the preparation for instructional checking; the protocol must not read its amplitudes to choose corrections. Supply the six axis states and √3/2|0⟩+i/2|1⟩.

Execution order:

1. Prepare |ψ⟩ on q0, and |0⟩ on q1/q2.
2. H(q1), then CNOT(q1→q2) creates the shared pair.
3. CNOT(q0→q1), then H(q0).
4. Measure q0 into **m0**, q1 into **m1**.
5. Deliver the labeled classical bits to Bob.
6. Apply X(q2) if m1=1, then Z(q2) if m0=1.

| m0 | m1 | Bob before correction, up to global phase | Correction in time order |
|---:|---:|---|---|
| 0 | 0 | \|ψ⟩ | None |
| 0 | 1 | X\|ψ⟩ | X |
| 1 | 0 | Z\|ψ⟩ | Z |
| 1 | 1 | XZ\|ψ⟩ | X then Z |

All four branches have probability 1/4 in the ideal protocol for every normalized input. After correction Bob's reduced state equals |ψ⟩⟨ψ|. Before the classical outcome is available, averaging his four possible conditional states gives I/2. This is an explicit calculation demonstrating why the receiver cannot read the input state from his local statistics before receiving the bits.

**Experiment: deliver or withhold the bits.** Provide a fresh-run mode and a branch-inspection mode. Branch inspection may select one of the four conditional outcomes but must be labeled as inspection, not as control over random measurement. Freeze the animation at “message not delivered.” Show Bob's unconditional state separately from the omniscient simulator's conditional view.

**Required task:** supply the correct gates for all four branches. **Transfer:** repeat with the complex non-axis input and deliberately omit a correction. For that input, missing X gives squared fidelity 0, missing Z gives 1/4, and missing both gives 3/4 in their respective affected branches; Bob's recovered Z histogram alone is not a sufficient check.

**Four hints:** read the named classical bits → identify the bit flip → identify the phase flip → reveal the correction table. Grade all nonzero branches, not only a lucky 00 outcome. Require a short structured explanation of classical communication and why the original state is not copied.

**Implementation boundary:** this is a local ideal simulation of the protocol. Do not claim physical transmission between devices, hardware execution, faster-than-light signaling, or material teleportation. A three-qubit circuit with deferred coherent controls can be mathematically related but does not fulfill the requested classical-message interaction unless actual measurement branches and feedforward are represented honestly.

## Objective item pool — private author keys

These A/B forms supply recognition and calculation items. Stars retain the original essential-concept tags, but no score from this bank alone establishes understanding. Use them with the descriptive and lab evidence below and the shared assessment policy.

| # | Form A prompt → key | Form B prompt → key |
|---:|---|---|
| 1* | X(q0) on \|00⟩ → \|01⟩ | X(q1) on \|00⟩ → \|10⟩ |
| 2 | q1=\|+⟩,q0=\|1⟩ → (0,s,0,s), s=1/√2 | q1=\|1⟩,q0=\|+⟩ → (0,0,s,s) |
| 3 | CNOT(q0→q1) on \|01⟩ → \|11⟩ | Same gate on \|11⟩ → \|01⟩ |
| 4 | Does CNOT entangle \|++⟩? → no | Does CNOT entangle \|00⟩? → no |
| 5* | Build Φ+ from \|00⟩ → e.g. H(q0),CX(0,1), fidelity target | Build Φ− → same plus Z(q0), fidelity target |
| 6 | Φ+ has P(q0=1)=? and P(q1=1\|q0=1)=? → 1/2 and 1 | Ψ+ has P(q0=1)=? and P(q1=0\|q0=1)=? → 1/2 and 1 |
| 7* | Does perfect Z agreement prove entanglement? → no; 00/11 mixture counterexample | Does local I/2 prove entanglement? → no; same counterexample |
| 8* | Compare Φ+ and 00/11 mixture in X → correlated pair versus four equal outcomes | Compare Φ− and same mixture in X → anticorrelated pair versus four equal outcomes |
| 9* | Teleport m0=0,m1=1 → X; m0=1,m1=0 → Z | Teleport m0=1,m1=1 → X then Z; 00 → none |
| 10* | Can Bob recover before receiving classical bits? → not generally; local state I/2 | Does teleportation leave an independent original copy at Alice? → no |

## Understanding checks beyond the objective bank

Use three 0–2 criteria per descriptive family: claim, mechanism/evidence, and transfer or limitation. Keep keys private and reject unsupported or contradictory claims. The shared document defines how the assessor's suggestions become versioned evidence through server policy.

| Family | Initial prompt | Required evidence | Neutral follow-up / changed case |
|---|---|---|---|
| C3-E1 Ordering | “Why did X on the top q0 wire produce \|01⟩?” | q0 least significant; ket reads q1q0; index 1 | “Predict X on q1 instead.” |
| C3-E2 Controlled gates | “Does a CNOT always create entanglement?” | Rejects always; correct input-dependent counterexample; coherent action not measurement | “What if its target starts in \|+⟩?” |
| C3-E3 Bell evidence | “Only 00 and 11 appear equally often. Is that enough to prove entanglement?” | No; classical mixture counterexample; distinction requires more than this chart | “Choose a measurement to distinguish Φ+ from that mixture.” |
| C3-E4 Marginals | “Both local charts are 50/50. What do they leave out?” | Joint correlations; product and Bell comparison; correct conditional example | “Repeat for .6\|00⟩+.8\|11⟩.” |
| C3-E5 Reduced state | “A zero-length local Bloch vector means the qubit has no state. Is that correct?” | Mixed reduced state I/2; no individual pure vector; zero length alone does not establish entanglement | “Name a separable joint state with the same local states.” |
| C3-E6 Teleportation | “Explain what Bob needs when m0=1 and m1=0.” | Z correction; needs classical outcome; input not copied | Test branch 11 and an input with complex amplitudes; predict failure if correction is omitted |

**Anchor rubric for C3-E3:** claim 2 = explicitly says the plot is insufficient, 1 = tentative with no clear basis, 0 = says entanglement is proved; evidence 2 = explicit 50/50 mixture of 00 and 11, 1 = generic shared randomness, 0 = claims all correlation is quantum; transfer 2 = predicts Φ+ correlated in X while the named mixture has four equal outcomes, 1 = proposes X without the expected difference, 0 = repeats only Z measurements. Clarify that this distinguishes those two presets; it is not a universal entanglement criterion.

**Required reviewer walkthrough:** present the same Z chart twice, once from a Bell state and once from a mixture, while withholding preparation truth in the assessment view. Require an experiment choice, a prediction, and an explanation. A learner who says “they agree, therefore entangled” must not pass the entanglement concept even with a perfect MCQ score.

**Teleportation practical evidence:** evaluate all four branches for each required input, not a fortunate 00 branch. Save the learner's correction choices before revealing fidelity. Do not assume that correctly repeating the correction table proves the learner understands why classical communication is needed; include the separate descriptive family.

## Verification status

The original combined research ran 127 independent complex-arithmetic assertions covering the two chapters together. That number is not a separate test count for each file and is not website validation. The scientific examples are preserved here; the new assessment thresholds, question variants, and teaching design require implementation and educator calibration.

## References: References and reading route

Accessed 12 September 2026. Read the platform lesson first; offer the relevant reference as optional depth. IBM learning materials supply foundational exposition, Qiskit documentation supplies API/convention details, and Preskill supplies an independent academic reference. The lesson activities and worked fixture choices are authored for this platform.

| ID | Source | Supports |
|---|---|---|
| R01 | [IBM: Single-system quantum information][R01] | Complex amplitudes, normalization, vectors, unitary operations |
| R02 | [Qiskit: Bit ordering][R02] | Wire, integer, vector, and bitstring conventions |
| R03 | [IBM: Mathematical formulations of measurements][R03] | Outcome probabilities and conditional states |
| R04 | [IBM: Superposition with Qiskit][R04] | Phase and interference teaching context |
| R05 | [IBM: Bloch sphere][R05] | Coordinates, axis states, pure and mixed geometry |
| R06 | [Qiskit: RYGate, version 1.4 reference][R06] | Rotation matrix definition; not a recommended dependency pin |
| R07 | [Qiskit: Circuit gate library, version 1.3 reference][R07] | Gate family names and S gate; verify installed API separately |
| R08 | [IBM: Stern–Gerlach measurements with Qiskit][R08] | Measurement axes and change of basis |
| R09 | [IBM: Limitations on quantum information][R09] | Global phase and limitations on distinguishability |
| R10 | [IBM: Multiple-system quantum information][R10] | Tensor products and controlled operations |
| R11 | [IBM: Entanglement in action introduction][R11] | Bell state versus classical correlation |
| R12 | [IBM: Multiple systems and reduced states][R12] | Ensembles and reduced states |
| R13 | [John Preskill, Caltech: Quantum Information, Chapter 2][R13] | Density operators, Schmidt decomposition, pure-state entanglement |
| R14 | [Qiskit: Quantum-information utilities][R14] | Partial trace, purity, fidelity, concurrence |
| R15 | [IBM: CHSH inequality tutorial][R15] | Optional Bell-test extension and its distinct goal |
| R16 | [IBM: Quantum teleportation][R16] | Protocol resources, measurements, and conditional corrections |
| R17 | [Qiskit: DensityMatrix, version 2.1 reference][R17] | Mixed-state representation and measurement API |

[R01]: https://quantum.cloud.ibm.com/learning/en/courses/basics-of-quantum-information/single-systems/quantum-information
[R02]: https://quantum.cloud.ibm.com/docs/en/guides/bit-ordering
[R03]: https://quantum.cloud.ibm.com/learning/en/courses/general-formulation-of-quantum-information/general-measurements/formulations-of-measurements
[R04]: https://quantum.cloud.ibm.com/learning/en/modules/quantum-mechanics/superposition-with-qiskit
[R05]: https://quantum.cloud.ibm.com/learning/en/courses/general-formulation-of-quantum-information/density-matrices/bloch-sphere
[R06]: https://quantum.cloud.ibm.com/docs/en/api/qiskit/1.4/qiskit.circuit.library.RYGate
[R07]: https://quantum.cloud.ibm.com/docs/en/api/qiskit/1.3/circuit_library
[R08]: https://quantum.cloud.ibm.com/learning/en/modules/quantum-mechanics/stern-gerlach-measurements-with-qiskit
[R09]: https://quantum.cloud.ibm.com/learning/en/courses/basics-of-quantum-information/quantum-circuits/limitations-on-quantum-information
[R10]: https://quantum.cloud.ibm.com/learning/en/courses/basics-of-quantum-information/multiple-systems/quantum-information
[R11]: https://quantum.cloud.ibm.com/learning/en/courses/basics-of-quantum-information/entanglement-in-action/introduction
[R12]: https://quantum.cloud.ibm.com/learning/en/courses/general-formulation-of-quantum-information/density-matrices/multiple-systems
[R13]: https://www.preskill.caltech.edu/ph219/chap2_15.pdf
[R14]: https://quantum.cloud.ibm.com/docs/en/api/qiskit/quantum_info
[R15]: https://quantum.cloud.ibm.com/docs/en/tutorials/chsh-inequality
[R16]: https://quantum.cloud.ibm.com/learning/en/courses/basics-of-quantum-information/entanglement-in-action/quantum-teleportation
[R17]: https://quantum.cloud.ibm.com/docs/en/api/qiskit/2.1/qiskit.quantum_info.DensityMatrix
