# Chapter 2 — Geometry and measurement bases

Updated research and authoring guide · 12 September 2026 · Reviewer revision 2

This chapter is separate from the other chapter guide. Read it with `LEARNING-TUTOR-AND-ASSESSMENT.md`, which defines the shared onboarding, tutor boundary, animation, and assessment requirements. These updated files supersede the combined guide where they differ. No application code was changed for this deliverable.

The numbered topic lessons below retain the researched science and activities. The author-facing question bank is one source of objective items, not a standalone measure of understanding. The previous 8/10-only chapter policy is superseded by the evidence requirements in the shared specification. Never place this entire authoring document in tutor retrieval: it includes private assessment answers.

## Start here: what this chapter uses

**Learner-facing introduction:** “In Chapter 1, you saw that two states can give the same measurement probabilities yet behave differently after a gate. This chapter explains that difference using phase, a geometric picture, and different ways to measure. You do not need previous complex-number or matrix experience; we will introduce both with small examples.”

Replace a bare prerequisite list with this visible opening section and a **Quick recap** panel. Keep a direct **Start Topic 2.1** action alongside **Review the basics**. Learners can open any published chapter; an optional readiness check recommends help and never blocks entry.

### Quick recap: read, see an example, try one

| Term or skill | Short reminder | Tiny example or action |
|---|---|---|
| Qubit and basis | A pure qubit can be expressed using the reference states \|0⟩ and \|1⟩. | Identify (1,0) as \|0⟩. |
| Amplitude | A coefficient in the state description; it is not itself the probability. | For (3/5,4/5), use squared magnitudes. |
| Probability | Squared amplitude magnitude for the specified basis outcome. | P(1)=16/25. |
| Normalization | All outcome probabilities sum to one. | (1/2,1/2) is not a normalized statevector. |
| H gate | H maps \|0⟩ to \|+⟩ and \|1⟩ to \|−⟩; applying H twice undoes it. | Step H→H from \|0⟩. |
| Relative phase | A phase difference between nonzero amplitudes can affect interference. | \|+⟩ and \|−⟩ share a Z histogram. |
| Global phase | One common phase on the whole vector does not change its physical state. | \|+⟩ and −\|+⟩ are equivalent. |
| Measurement and shots | A shot prepares and runs again; repeating a measurement on a recorded branch is different. | A fair probability need not give exactly 16 zeros in 32 shots. |

These reminders use the Chapter 1 concepts; the following six lessons teach the new mathematical tools. The underlying definitions and gate conventions are supported by [R01], [R03], and [R09] in the reference register.

**Optional four-question check, author key:** (a) P1 for (3/5,−4/5): .64; (b) H→H from \|0⟩: \|0⟩; (c) can a relative sign affect a later H result: yes; (d) do 32 shots guarantee 16 zeros for \|+⟩: no. Explain each answer after submission. Offer the relevant recap card if incorrect, and “Continue anyway.” This checks readiness and supports learning; it does not award understanding evidence for the new chapter.

### New terms introduced here

2.1: complex number, i, magnitude, phase angle. 2.2: vector, matrix, inner product. 2.3: Bloch sphere and coordinate axes. 2.4: rotation and phase gate. 2.5: measurement basis. 2.6: state discrimination and what a histogram does not tell us. Display definitions on first use; do not require learners to memorize this list before beginning.

## Tutor scope in this chapter

Allowed teaching context: orientation/recap content plus **Chapters 1 and 2**. Prioritize the selected topic and retrieve relevant older concepts as needed; do not paste two entire chapters into every request. Content from Chapters 3 onward is excluded, even if previously visited. The entire current chapter is eligible, not only topics already completed.

If asked about entanglement: “That topic is covered in Chapter 3 — Multiple qubits and entanglement. For now, we can focus on how a single qubit's state and measurement basis affect its outcomes.” Use a catalog entry, not future lesson content. If a Chapter 2 topic uses a general word such as “state,” do not misclassify it as a future topic by keyword alone.

## Required animation

Implement the **phase-to-interference animation** in Topic 2.4 described in the shared specification: phase arrows change first; the final H combines them; probabilities update from the verified result. Keep camera movement separate and make the same explanation usable with animation disabled.

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

### 2.1 Complex numbers and phase angles

**Objective:** read a complex amplitude and separate its magnitude from its phase.

**Learner explanation:** “An amplitude needs more information than a probability. Its length determines its contribution to probability; its angle helps determine how it combines with another amplitude. Rotating that angle can leave today's probability chart unchanged while changing the result of a later gate.”

Introduce i²=−1, the complex plane, magnitude, conjugate, and e^(iφ)=cosφ+i sinφ. Keep multiplication visual before requiring symbolic manipulation. Use α=1/√2 and β=e^(iφ)/√2 as the bounded experiment family.

**Experiment: phase without a probability change.** Provide phase presets 0°, 90°, 180°, 270°, plus a slider. Display two amplitude arrows, real/imaginary numeric values, and Z probabilities. A separate global-phase control rotates both arrows; label it “same physical state.” Reveal an optional final H to expose interference. [Superposition and interference module][R04]

**Required task:** predict Z probabilities for φ=90°, then explain why β=i/√2 does not produce a negative probability. Expected: (1/2,1/2), because |i/√2|²=1/2.

**Transfer:** α=√3/2, β=i/2 gives PZ(0)=3/4 and PZ(1)=1/4. Multiplying both amplitudes by i preserves all measurement statistics.

**Four hints:** inspect arrow lengths → square magnitudes → |a+ib|²=a²+b² → show the worked values and issue a fresh transfer item. Complete with correct magnitude calculation and global/relative-phase classification. Do not grade solely by selecting the target slider value.

**Tutor focus:** clarify why “imaginary” does not mean nonexistent, and why complex amplitude is not negative or complex probability. Do not imply every relative-phase change is visible in every basis.

### 2.2 Vectors, matrices, and operation order

**Objective:** calculate one small matrix-vector product and read circuit order consistently.

**Learner explanation:** “The state is a column of amplitudes. A gate combines those entries using its matrix. The circuit shows the order you perform operations; the matrix expression acts on the state from the right.”

Use the known X, H, and Z matrices first. Introduce the conjugate transpose through the inner product α*γ+β*δ. Explain orthogonal states through inner product zero; contrast |0⟩ and |1⟩ with |0⟩ and |+⟩. Matrix multiplication should support the visual lesson, not become an unrelated algebra course. [Single-system framework][R01]

**Experiment: one output row at a time.** Select input |0⟩, |1⟩, |+⟩, or |−⟩ and gates H then Z or Z then H. Animate the two terms contributing to each output amplitude. Show algebra and circuit arrows together.

**Worked comparison:** from |0⟩, H then Z gives |−⟩; Z then H gives |+⟩. Their Z distributions agree, while an X-basis measurement distinguishes them.

**Required task:** select ZH|0⟩ as the expression for H then Z and fill the second output amplitude. **Transfer:** starting with |1⟩, H then Z yields |+⟩; Z then H yields −|−⟩. Compare states up to global phase, not literal vector equality.

**Four hints:** follow time arrows → identify the first applied gate → calculate the intermediate column → reveal both products. Completion requires the product-order answer and a new-input result.

**Optional depth:** show U†U=I for a unitary gate. Do not require learners to invert general matrices.

### 2.3 The Bloch sphere

**Objective:** connect a normalized pure state to a point and identify the six axis states.

Up to global phase,

|ψ⟩ = cos(θ/2)|0⟩ + e^(iφ)sin(θ/2)|1⟩,

with Bloch vector r=(sinθ cosφ, sinθ sinφ, cosθ). Equivalently, r=(2Re(α*β), 2Im(α*β), |α|²−|β|²). Pure states lie on the surface. Mixed single-qubit states lie inside the ball and will be developed in Chapter 3. The sphere depicts a state description, not the physical location of a particle. [Bloch sphere][R05]

| State | Bloch coordinates |
|---|---|
| \|0⟩ | (0,0,1) |
| \|1⟩ | (0,0,−1) |
| \|+⟩=(\|0⟩+\|1⟩)/√2 | (1,0,0) |
| \|−⟩=(\|0⟩−\|1⟩)/√2 | (−1,0,0) |
| \|+i⟩=(\|0⟩+i\|1⟩)/√2 | (0,1,0) |
| \|−i⟩=(\|0⟩−i\|1⟩)/√2 | (0,−1,0) |

**Experiment: locate the state.** θ spans 0°–180°; φ spans 0°–360° with wraparound. Synchronize the sphere, ket, coordinate table, and Z probabilities. At the poles disable the phase challenge and explain its irrelevance. A global-phase control leaves the sphere unchanged.

**Required task:** place |+i⟩, then change to |−i⟩ without changing Z probabilities. **Transfer:** θ=60°, φ=90° gives r=(0,√3/2,1/2), matching Topic 2.1's transfer state.

**Four hints:** identify the axis → set equal amplitude magnitudes → choose ±90° relative phase → show the coordinates. Require both placement and explanation. Do not award correctness from approximate mouse position alone; offer presets and numeric inputs.

### 2.4 Rotations and phase gates

**Objective:** distinguish a state rotation from a camera rotation and predict a short preparation circuit.

Use Ry(θ)=[[cos(θ/2),−sin(θ/2)],[sin(θ/2),cos(θ/2)]]. It prepares cos(θ/2)|0⟩+sin(θ/2)|1⟩ from |0⟩. [RY gate definition][R06]

For this guide, define P(φ)=diag(1,e^(iφ)), S=P(π/2), S†=P(−π/2), and Rz(φ)=diag(e^(−iφ/2),e^(iφ/2)). Thus P(φ)=e^(iφ/2)Rz(φ): the standalone operations agree up to global phase. Do not extend that equivalence naively to controlled versions; a previously global phase can become relative between control branches. [Gate library][R07]

**Experiment: prepare a destination.** Circuit begins at |0⟩ and applies Ry(θ), then P(φ). Offer separate “rotate camera” and “change gate angle” controls. Show original and final vectors with the actual discrete gate frames.

**Required task:** prepare |+i⟩ using θ=90°, φ=90°. **Transfer:** prepare √3/2|0⟩+i/2|1⟩ using θ=60°, φ=90°. Include inverse-angle undo in a unitary-only circuit.

**Four hints:** first set magnitudes → θ affects Z probabilities → φ sets the second amplitude's phase → show the two-gate solution. Evaluate final state fidelity and allowed-gate constraints, accepting equivalent valid circuits.

**Optional experiment:** H→P(φ)→H on |0⟩ has final PZ(0)=cos²(φ/2). Ask for PZ(1)=3/4: φ=120° or 240° works. This is a continuous extension of Chapter 1's interference experiment, not a speedup claim.

### 2.5 X, Y, and Z measurement bases

**Objective:** choose a readout basis and interpret its outcomes.

Z eigenstates are |0⟩ and |1⟩; X eigenstates are |+⟩ and |−⟩; Y eigenstates are |+i⟩ and |−i⟩. Map the +1 eigenvalue to bit 0 and −1 to bit 1. For a Bloch vector r, P(+ along axis j)=(1+rj)/2. More generally, P(+ along unit axis n)=(1+r·n)/2. [Bloch representation][R05], [measurement rules][R03]

**Readout implementation, in execution order:**

| Intended measurement | Gates before computational measurement | Output interpretation |
|---|---|---|
| Z | None | 0 means \|0⟩; 1 means \|1⟩ |
| X | H | 0 means \|+⟩; 1 means \|−⟩ |
| Y | S† then H | 0 means \|+i⟩; 1 means \|−i⟩ |

**Experiment: same preparation, three questions.** Each basis receives independently prepared copies. Show the basis-change gates explicitly. Counts from X, Y, and Z are not three measurements of an unchanged individual qubit. [Stern–Gerlach measurement module][R08]

**Required task:** distinguish |+⟩ from |−⟩ with X readout, and |+i⟩ from |−i⟩ with Y readout. **Transfer:** for θ=60°, φ=90°, predict PZ(0)=0.75, PX(+)=0.5, PY(+)=(2+√3)/4≈0.933012702.

**Physical-frame detail:** H followed by Z measurement leaves the physical qubit in a computational eigenstate. To implement an ideal X measurement whose output state remains in the original coordinates, add H after readout. For Y, undo the basis change with H then S. Alternatively, display the logical projected state as a separate, explicitly labeled representation. Immediate repeatability claims must use a consistent measurement instrument, not accidentally measure a rotated physical state again.

**Four hints:** look for the differing axis → choose its basis → inspect the change-of-basis circuit → reveal probabilities. Require correct basis, outcome labels, and fresh-copy reasoning.

### 2.6 State versus distribution challenge

**Objective:** infer what a measurement does and does not establish.

**Learner explanation:** “One histogram describes one measurement. Different states can make that histogram. Choosing another measurement can reveal a difference, but one random outcome does not generally reveal an unknown state.”

**Experiment: mystery preparations.** Practice sets contain |+⟩/|−⟩, |+i⟩/|−i⟩, and a nonorthogonal pair |0⟩/|+⟩. The learner selects Z, X, or Y, predicts, and gathers fresh-copy data. In assessment mode hide the statevector, preparation label, Bloch vector, and equivalent answer-revealing API fields. Simulator truth is available only after submission.

For orthogonal pairs the matching basis identifies the state ideally in one shot. Nonorthogonal states cannot be perfectly distinguished with certainty from one copy. Unknown-state estimation requires an ensemble and statistical inference. [Limitations on quantum information][R09]

**Required task:** explain why Z cannot distinguish |+⟩ from |−⟩ even with more shots, then identify an effective basis. **Transfer:** compare |+⟩ against |+i⟩. Their squared overlap is 1/2; no guaranteed one-copy identification is possible.

**Optional tomography preview:** estimate rj=(n+−n−)/shots using separate X/Y/Z preparations. Finite-sample estimates can give |r̂|>1; mark this as an unconstrained statistical estimate, not a valid physical state. Do not silently normalize it and claim exact reconstruction. Defer a fitted physical-state estimator to later work.

**Four hints:** specify the basis → compare whole predicted distributions → test orthogonality → reveal the valid inference. Completion includes a statement of uncertainty, not just a correct label.

## Objective item pool — private author keys

These A/B forms supply recognition and calculation items. Stars retain the original essential-concept tags, but no score from this bank alone establishes understanding. Use them with the descriptive and lab evidence below and the shared assessment policy.

| # | Form A prompt → key | Form B prompt → key |
|---:|---|---|
| 1 | Compute \|3/5+4i/5\|² → 1 | Compute \|1/2+i/2\|² → 1/2 |
| 2* | P1 for (√3/2,i/2) → 1/4 | P0 for (1/2,i√3/2) → 1/4 |
| 3 | H then Z on \|0⟩ → \|−⟩; expression ZH\|0⟩ | Z then H on \|0⟩ → \|+⟩; expression HZ\|0⟩ |
| 4 | Locate \|+i⟩ → (0,1,0) | Locate \|−i⟩ → (0,−1,0) |
| 5 | Prepare \|+i⟩ using Ry then P → π/2,π/2 | Prepare \|−⟩ → π/2,π |
| 6* | Read Y using computational measurement → S†,H,measure | Read X → H,measure |
| 7 | PX(+) for \|+⟩ → 1 | PY(+) for \|−i⟩ → 0 |
| 8* | Do \|+⟩ and \|−⟩ share Z probabilities? Can X separate? → yes, yes | Do \|+i⟩ and \|−i⟩ share Z probabilities? Can Y separate? → yes, yes |
| 9* | Does i\|ψ⟩ change a state physically? → no, global phase | At θ=0, does varying φ change the state? → no |
| 10* | Can one copy always distinguish \|0⟩ from \|+⟩? → no, nonorthogonal | Can one copy always distinguish \|+⟩ from \|+i⟩? → no, nonorthogonal |

## Understanding checks beyond the objective bank

Use these authored prompt families for short written answers and adaptive follow-ups. The assessor receives the current item's rubric privately. The ordinary tutor does not. Each family has three 0–2 criteria: scientific claim, mechanism/evidence, and transfer or limitation. A critical false claim prevents that concept being marked demonstrated even if other criteria earn points.

| Family | Initial prompt | Required evidence | Neutral follow-up / changed case |
|---|---|---|---|
| C2-E1 Magnitude | “Why is the probability from i/2 positive?” | Uses modulus squared; gives 1/4; does not square only i or the real part | “What would change for −i/2?” |
| C2-E2 Operation order | “Explain why H then Z and Z then H differ from \|0⟩.” | Correct intermediate states; final \|−⟩ vs \|+⟩; basis-aware comparison | “Start from \|1⟩ instead. Which final states do you expect?” |
| C2-E3 Geometry | “A phase control moves the arrow around the equator. Why are Z odds unchanged?” | Connects equal magnitudes with fixed z; phase changes x/y; names a useful alternative basis | “What happens to that phase control at the north pole?” |
| C2-E4 Readout | “You can prepare either \|+i⟩ or \|−i⟩. Which measurement distinguishes them, and why?” | Y basis; opposite Y eigenvalues; correct bit mapping | “Predict what Z would show instead.” |
| C2-E5 Limits | “A 50/50 Z chart proves this state is \|+⟩. Evaluate this claim.” | Rejects unique identification; gives another compatible state; proposes an informative measurement | “Can one copy always distinguish \|+⟩ from \|+i⟩?” |
| C2-E6 Practical transfer | “Prepare a state with PZ0=.75 and positive imaginary second amplitude, then explain the circuit.” | Valid Ry/P preparation; selected phase and magnitude tied to parameters; successful verified state | Change target to PZ0=.25 with negative imaginary second amplitude |

**Anchor rubric for C2-E5:** claim 2 = explicitly rejects uniqueness, 1 = qualified but ambiguous, 0 = accepts it; evidence 2 = gives a valid distinct state with the same Z distribution, 1 = says “other states” without example, 0 = invalid/no example; transfer 2 = names an appropriate discriminating measurement for the stated pair and predicts it, 1 = names a basis without a correct prediction, 0 = claims more Z shots solve it. For the nonorthogonal follow-up, require recognition that guaranteed one-copy discrimination is impossible.

“They both have equal squared amplitudes in Z, but X gives opposite outcomes for + and −” is a strong short answer. “Quantum things are random and the sphere spins” is not. “Same Z chart means same state” is a critical misconception even inside a long fluent answer. Grammar and length do not earn points.

**Required reviewer walkthrough:** a learner gets every recognition item correct but gives the critical misconception above. Show a follow-up and targeted practice, not “understanding demonstrated.” A second learner uses simple broken English but gives correct predictions, evidence, and a novel circuit; award the supported evidence without a language penalty.

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
