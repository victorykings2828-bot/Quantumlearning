# Quantum Learning Laboratory
## Researched learning experience, curriculum, and Chapter 1 demo specification

**Version:** 2.0 learning-content companion · **Research checked:** 11 September 2026  
**Deliverable:** Markdown research and product specification. No application code or working platform is delivered by this document.

## 1. Purpose and relationship to the supplied research

Build an AI-supported learning platform where beginners first see a meaningful quantum algorithm experiment, learn the concepts that explain it, and return to reconstruct the algorithm themselves. The central experience is a laboratory: read a short explanation, predict a result, change an input, inspect the computation one step at a time, and explain the outcome.

This document develops the supplied **Quantum Learning Laboratory — Product and Engineering Blueprint, version 1.0**, together with the supplied notes about algorithm previews and curiosity. Those documents are design inputs; the current request defines this deliverable as researched content and planning, without implementation.

The existing blueprint remains the engineering baseline. Its saved workspaces, simulation engine, action history, replay, assessments, hints, learner evidence, privacy controls, accessibility, and future extensions are retained. This companion specifies the missing beginner-facing content and resolves these scope conflicts:

| Existing item | Updated decision |
|---|---|
| Two complete MVP lessons | Organize that foundation material into **one complete Chapter 1 with eight subtopics**, practice, and an assessment bank. |
| Algorithms introduced only after foundations | Add a separate ungraded preview layer before foundations. Formal algorithm instruction still follows prerequisites. |
| Two-qubit MVP limit | Keep the general foundation playground at one or two qubits. Permit a separately bounded Grover preset for **2–4 qubits**, covering 4, 8, and 16 candidates. Larger examples are analytical only. |
| Lesson completion and an 80% test unlock | Keep completion records and a published pass rule, but unlock instruction using **demonstrated prerequisite skills**. Equivalent diagnostic evidence can satisfy prerequisites. |
| Grover appears late in the roadmap | Its small preview belongs in the demo; its full build-and-explain course remains later. |
| Tutor, assessment, and mastery boundaries | Preserve them: computation supplies numerical facts; authored evaluators grade; AI provides teaching assistance. |

Facts below are supported by linked sources. Numerical lesson examples are worked applications of the stated equations. Activity design, chapter ordering, UI choices, time estimates, and assessment thresholds are **proposals to pilot**, not experimentally established educational results.

## 2. Product promise and first-time journey

### 2.1 What the introduction should actually say

Suggested original learner-facing copy:

> **Learn how quantum algorithms work by experimenting with them.**
>
> You will change inputs, follow circuits step by step, and see how measurement probabilities change. We will begin with a search experiment, then teach the ideas behind it through short lessons and practical challenges.
>
> You do not need previous quantum mechanics or programming experience. Basic arithmetic is enough to start; we will introduce the mathematics when it becomes useful.
>
> The experiments use a quantum simulator running on a classical computer. Its state views help explain the mathematical model. They are not measurements of a physical quantum processor.
>
> An AI tutor is available whenever you need an explanation or a hint.

Do not open with a long history of physics or a list of advanced prerequisites. Do not promise that quantum computers solve every problem faster. Specific algorithms have advantages under specific computational assumptions. Grover's result concerns unstructured search; Shor's result concerns factoring and discrete logarithms. [Grover's original paper][S04], [Shor's original paper][S06].

### 2.2 Recommended journey

| Stage | Learner experience | Completion meaning |
|---|---|---|
| Introduction | Understand the product, simulator label, and learning loop | Orientation viewed; no mastery claim |
| Search preview | Compare a classical search with a small Grover experiment | Grover marked **Seen** |
| Shor mystery | Follow a conceptual route from factoring to periodicity | Shor marked **Seen** |
| Beginner bridge | Check arithmetic, vocabulary, and basic notation | Optional preparation; targeted help if needed |
| Chapter 1 | Complete eight connected foundation subtopics | Evidence for the listed one-qubit skills |
| Revisit | Explain one previously mysterious feature of the preview | Connect new knowledge to the saved experience |
| Further chapters | Develop multi-qubit concepts and algorithms | Unlock by prerequisite evidence |

Suggested initial orientation time is 10–20 minutes, including experimentation; the learner can skip a preview and return. Chapter 1 is approximately 90–140 minutes across multiple visits. Validate these estimates with actual beginners.

### 2.3 Navigation

Provide five clear destinations: **Start**, **Learn**, **Quantum Lab**, **My Progress**, and **Resources**. Keep the tutor accessible from the current lesson or experiment without forcing navigation away.

The Learn area shows chapters and subtopics. The Lab contains algorithms, protocols, and subroutines, accurately labeled: teleportation is a protocol; QFT is a transform/subroutine; QPE is an algorithm used within other algorithms.

## 3. The opening comparison: classical search and Grover

### 3.1 Define the same problem for both methods

Use an unordered set of N candidate labels, exactly one of which satisfies a hidden yes/no test f(x). The task is to return the marked label. A **query** is one use of that test. There is no sorted order or index that a classical method could exploit.

The quantum method requires **coherent oracle access**: a reversible quantum operation encoding the same predicate. One quantum query can act on a superposition, but does not return a readable list of every predicate value. Constructing that operation has a cost outside the simple query count. This is the explicit oracle model used for the comparison. [IBM: Unstructured search][S02].

The preview allows the learner to choose the target to inspect cause and effect. Explain the seeming paradox: the experiment generator knows the chosen target to construct the toy oracle; the search procedure is demonstrated as if it could only access the oracle. This is an instructional instance, not a useful search for an answer the user has already selected.

### 3.2 Classical side: step through actual checks

Default example: N = 8, candidate labels 0–7, target 5. Search in increasing order. Show the queried label, its yes/no answer, and accumulated query count. The successful check is the sixth query in this particular order.

For a uniformly located target and a sequential search that **checks even the last remaining candidate**, the average is (N+1)/2 checks: 4.5 for N = 8, with worst case 8. If the algorithm instead uses the exactly-one-target promise to infer the final unchecked candidate, its worst case is 7 and mean is 4.375. These are different stopping rules, so label the chosen rule. Both have linear asymptotic query cost.

For a fixed budget q < N, a sequential strategy that checks q distinct candidates and, if all fail, guesses one unchecked candidate succeeds with probability (q+1)/N under a uniformly located target. Derivation: q/N for finding it among checked positions, plus 1/N for the final guess. A strategy that only reports checked successes achieves q/N. Include the guessing baseline so the comparison does not disadvantage classical search.

### 3.3 Quantum side: what is happening

The standard single-target demonstration prepares a uniform superposition, applies a phase oracle, applies a diffusion reflection, repeats that pair k times, then measures a candidate. The probability of observing the target is

**P(target) = sin²((2k+1)θ), where θ = arcsin(1/√N).**

This expression assumes an ideal noiseless model, exactly one marked state, uniform initial preparation, the specified phase oracle, and the usual diffusion operation. It does not apply unchanged to arbitrary initial states. The useful first probability peak occurs near k = π/(4θ) − 1/2; evaluate nearby nonnegative integers. More iterations can move away from that peak. [IBM: Grover analysis][S03].

The algorithm uses O(√N) oracle queries for constant success probability, compared with classical linear query scaling for this problem. That is a **quadratic query advantage**. It is not an end-to-end time claim about this web demo. [Grover's original paper][S04].

### 3.4 Fully worked four-candidate example

Use N = 4 and mark candidate 2, represented as `|10⟩`. Display amplitudes in the order `|00⟩, |01⟩, |10⟩, |11⟩`.

| Step | Amplitudes | Probabilities | What the learner should notice |
|---|---|---|---|
| Initial register | (1, 0, 0, 0) | (1, 0, 0, 0) | The reset register is a known basis state. |
| Prepare uniformly | (1/2, 1/2, 1/2, 1/2) | (1/4, 1/4, 1/4, 1/4) | Every candidate has equal initial probability. |
| Oracle | (1/2, 1/2, −1/2, 1/2) | (1/4, 1/4, 1/4, 1/4) | A sign changes; probabilities have not changed yet. |
| Diffusion | (0, 0, 1, 0) | (0, 0, 1, 0) | The marked outcome now has probability 1. |
| Measurement | Recorded outcome 2 | One observed candidate | A shot returns a candidate, not the amplitude table. |

Worked arithmetic: after the oracle the mean amplitude is 1/4. Diffusion maps each amplitude a to 2×mean − a. Unmarked amplitudes become 1/2 − 1/2 = 0; the marked amplitude becomes 1/2 − (−1/2) = 1. This table is an independently worked small instance of the reflection used in [IBM's Grover analysis][S03].

Keep this derivation behind **Explain the numbers** in the preview; it becomes core learning in the full Grover chapter.

### 3.5 Show the overshoot, not just a perfect result

These values are calculated from the equation in section 3.3, not measured counts:

| Candidates | Grover iterations | Ideal target probability |
|---:|---:|---:|
| 4 | 0 | 25% |
| 4 | 1 | 100% |
| 4 | 2 | 25% |
| 8 | 0 | 12.5% |
| 8 | 1 | 78.125% |
| 8 | 2 | 94.53125% |
| 8 | 3 | 33.0078125% |
| 16 | 3 | approximately 96.1319% |

For N = 8 and a budget of two oracle queries, the specified classical check-and-guess baseline succeeds with probability 3/8 = 37.5%; standard two-iteration Grover succeeds with probability 121/128 ≈ 94.53%. Both output a candidate. If confirming a candidate is required, count the extra verification query and any retries for either strategy. Two quantum iterations are not a certainty guarantee.

Offer separate columns for oracle queries, gates, shots, and simulator runtime. Show no artificial “quantum speed multiplier.” One 256-shot Grover histogram with k = 2 represents 256 complete preparations and 512 phase-oracle uses, before optional candidate verification; it is not a single two-query search.

### 3.6 Preview controls and behavior

| Control | Demo choices and behavior |
|---|---|
| Search-space size | N = 4, 8, or 16; show 2, 3, or 4 search qubits. |
| Target | Any integer from 0 through N−1; show the corresponding bit string. |
| Iterations | 0–8; include an optional **Compare iteration counts** view. |
| Shots | 1, 16, 64, 256, or 1,024. |
| Initial preparation | Standard uniform preparation by default. An optional **What if preparation is missing?** experiment starts in `\|0…0⟩` and is explicitly outside the standard success formula. |
| Run | Compute a new run using the selected parameters. |
| Play / Pause | Advance or stop the view through the recorded computed steps. |
| Next / Previous step | Select a saved step, including pre-measurement and recorded post-measurement frames. |
| Replay | Replay the same recorded run, including the same measurement outcomes. |
| Reset | Restore the published preset and start position; retain prior saved runs. |
| Compare | Keep two runs side by side with their parameters and provenance. |

Every run synchronizes candidate tiles, probability bars, amplitude values, phase markers, circuit, and stage timeline. Expand preparation/oracle/diffusion blocks to show their actual circuit operations. The chart cannot change before the matching computed result arrives.

For the optional nonuniform preparation, keep the same standard diffusion block and compute the actual resulting circuit. Do not relabel it as general amplitude amplification or show the uniform-start prediction curve as if it remained valid. The learner can compare the result with the standard preparation.

Use this closing prompt: **“The oracle changed a sign before any probability changed. Why did the next operation make that sign matter?”** Save the inspected run and that question as the learner's first Grover mystery.

## 4. Shor as a conceptual mystery

Shor should be a short storyboard, with the persistent label **Conceptual walkthrough with exact classical arithmetic; no Shor circuit executed**.

Suggested opening: **“Factoring 15 is easy. We use it to reveal a method that connects factors to a hidden repetition pattern.”** Avoid implying that factoring this tiny number demonstrates a practical speed advantage.

| Storyboard stage | Content |
|---|---|
| Factoring problem | Find integers greater than 1 whose product is 15. |
| Choose a base | Use a = 2, with gcd(2,15) = 1. |
| Repeated modular powers | Show 2ˣ mod 15 for x = 0,1,2,3,4,5,6,7: **1,2,4,8,1,2,4,8**. |
| Hidden period | The smallest positive r with 2ʳ mod 15 = 1 is r = 4. |
| Quantum subroutine | Introduce controlled modular operations and phase estimation as future tools for learning about the order. |
| Fourier analysis and measurement | Show an inverse QFT stage and a sampled value related to a rational phase; it does not directly print r. |
| Classical processing | Explain that rational reconstruction and verification produce an order candidate; some measurements are unhelpful. |
| Factors | With valid r = 4, compute gcd(2²−1,15)=3 and gcd(2²+1,15)=5. |

The later lesson must teach retries: an unsuitable order, an unhelpful measured phase, or a trivial gcd can require another attempt. Shor's algorithm runs in polynomial time in the input bit length on the theoretical quantum model; a toy demonstration does not establish the physical resources for large instances. [IBM: Shor's algorithm][S05], [Shor's original paper][S06].

The modular-power table is explanatory classical arithmetic. Do not portray displaying the table as the quantum order-finding algorithm. Future concept chips are **Modular arithmetic**, **Controlled operations**, **Eigenphases**, **QFT**, **QPE**, and **Classical post-processing**. The preview remains accessible even while formal exercises require those prerequisites.

## 5. Beginner bridge: what learners need before Chapter 1

### 5.1 Required arithmetic, introduced in place

| Preparation | A small check | Recovery activity |
|---|---|---|
| Fractions and percentages | Convert 1/4 to 25%. | Four-part probability bar. |
| Squares and square roots | Calculate (1/√2)². | Show multiplication yielding 1/2. |
| Signed numbers | Compare (−1/2)² with (1/2)². | Both become 1/4. |
| Probability totals | Decide whether 0.2 + 0.8 is a valid two-outcome distribution. | Fill a unit-length bar. |
| Ordered operations | Follow “swap, then swap again.” | Two-step classical bit exercise. |

Calculus, programming, and a university physics course are unnecessary for the proposed Chapter 1 activities. Matrix multiplication is optional depth here and becomes required before constructing multi-qubit algorithms. Complex numbers are acknowledged immediately, then taught properly in Chapter 2. Never tell learners that negative real amplitudes cover all quantum states.

### 5.2 Vocabulary: introduce now and expand later

| Term | Beginner definition | First formal lesson |
|---|---|---|
| Algorithm | A procedure for producing an output from an input. | Introduction |
| Classical bit | A unit of information with values 0 or 1. | 1.1 |
| Qubit | A quantum system described using a two-dimensional state space. | 1.1 |
| Computational basis | The reference states `\|0⟩` and `\|1⟩` for a qubit. | 1.1 |
| Ket notation | Symbols such as `\|0⟩` and `\|ψ⟩` naming state vectors. | 1.1 |
| Amplitude | A coefficient in a quantum state vector; generally a complex number. | 1.2 |
| Probability | The chance of a specified measurement outcome. | 1.2 |
| Normalization | The squared amplitude magnitudes sum to 1. | 1.2 |
| Measurement | An operation that produces a classical outcome and generally changes the state. | 1.3 |
| Shot | One preparation and execution with measurement. | 1.3 |
| Gate | In this chapter, a reversible unitary operation on a qubit. Measurement is shown separately. | 1.4 |
| Circuit | An ordered arrangement of operations on labeled wires. | 1.4 |
| Superposition | A linear combination of basis states; the statement depends on the chosen basis. | 1.5 |
| Relative phase | A phase difference between nonzero amplitudes. | 1.6; extended in Chapter 2 |
| Global phase | One phase factor multiplying the entire state vector. | 1.6 |
| Interference | Amplitude contributions combine before probabilities are calculated. | 1.7 |
| Oracle | An operation encoding a problem-specific function or predicate. | Preview; Chapter 4 |
| Query complexity | Number of uses of an oracle under a stated model. | Preview; Chapters 4–6 |
| Entanglement | For pure states, a joint state that cannot be factored into individual subsystem states. | Chapter 3 |
| QFT / QPE | Quantum Fourier transform / quantum phase estimation. | Preview; Chapters 8–9 |

Definitions are grounded in [IBM: Single-system quantum information][S01], [IBM: Circuits introduction][S20], [IBM: Global phase and limitations][S08], [IBM: Multiple systems][S10], and [IBM: Query-algorithm introduction][S21]. The pure-state entanglement definition needs a broader separability definition when mixed states are introduced.

### 5.3 Use-case cards with honest claims

| Area | What to teach | Boundary |
|---|---|---|
| Unstructured search | Grover amplifies marked outcomes using an oracle. | Advantage is conditional on the oracle/access and cost model. [S02][S02] |
| Factoring and number theory | Shor uses quantum order finding with classical arithmetic. | No claim that the demo factors cryptographic-size numbers. [S05][S05] |
| Quantum-system simulation | Quantum algorithms can model quantum systems; later connect observables and Hamiltonians. | Costs depend on the Hamiltonian, desired precision, state preparation, and readout. [S22][S22] |
| Chemistry and optimization research | VQE and QAOA combine parameterized circuits with classical optimization. | Do not promise a general practical advantage or guaranteed global optimum. [S17][S17] |
| Quantum communication | Teleportation transfers a state using entanglement and classical communication. | It neither transports matter nor enables faster-than-light messaging. [S11][S11] |

## 6. Chapter and subtopic map

Chapter numbers describe a recommended route. The prerequisite graph determines access to guided instruction and assessments. Algorithm previews do not demand mastery.

| Chapter | Subtopics | Prerequisites | Demonstration of learning |
|---|---|---|---|
| **1. One qubit: states to interference — complete demo** | 1.1 bits/basis; 1.2 amplitudes/probability; 1.3 measurement/shots; 1.4 X/circuits; 1.5 H/superposition; 1.6 Z/phase; 1.7 interference; 1.8 capstone/revisit | Beginner bridge as needed | Predict, construct, and explain a short one-qubit circuit. |
| **2. Geometry and measurement bases** | 2.1 complex numbers and phase angles; 2.2 vectors/matrices; 2.3 Bloch sphere; 2.4 rotations; 2.5 X/Y/Z measurements; 2.6 state-versus-distribution challenge | Chapter 1 amplitude, phase, and gate skills | Distinguish equal-Z-probability states using another basis. |
| **3. Multiple qubits and entanglement** | 3.1 bit ordering; 3.2 tensor products; 3.3 controlled gates; 3.4 Bell preparation; 3.5 joint/marginal statistics; 3.6 mixtures versus entanglement; 3.7 teleportation protocol | Vectors, measurement, H/X/Z | Build a Bell state and explain why one correlation plot alone is insufficient evidence of entanglement. |
| **4. Reversible functions and quantum oracles** | 4.1 reversible computation; 4.2 ancillas; 4.3 bit oracles; 4.4 phase kickback; 4.5 uncomputation; 4.6 promises and cost models | Controlled gates, superposition, phase | Translate a small truth table to a verified oracle and clean up workspace. |
| **5. First query algorithms** | 5.1 Deutsch; 5.2 Bernstein–Vazirani; 5.3 Deutsch–Jozsa; 5.4 deterministic versus randomized baselines; 5.5 oracle-debugging challenge | Chapter 4 oracle skills, interference | State the problem promise, derive an output, and compare matching models. |
| **6. Grover, revisited in full** | 6.1 search model; 6.2 preparation; 6.3 phase marking/kickback; 6.4 diffusion; 6.5 iteration count; 6.6 measurement/retries; 6.7 query versus gate cost; 6.8 build, break, debug, optimize; 6.9 transfer | Multi-qubit states, phase, interference, oracle, measurement | Build and modify a small search circuit and predict overshoot. |
| **7. Hidden XOR structure: Simon — optional branch** | 7.1 XOR; 7.2 binary linear algebra; 7.3 Simon promise; 7.4 sampled constraints; 7.5 recover/verify hidden string | Query algorithms and algebra over two-element field | Collect enough independent equations and solve for a hidden string. |
| **8. Quantum Fourier transform** | 8.1 complex roots of unity; 8.2 amplitude transform; 8.3 controlled phases; 8.4 inverse QFT; 8.5 output ordering; 8.6 readout limitations | Complex phase, matrices, multi-qubit circuits | Construct a small QFT and verify its action on selected states. |
| **9. Quantum phase estimation** | 9.1 eigenvectors/eigenvalues; 9.2 controlled powers; 9.3 phase kickback; 9.4 inverse QFT; 9.5 finite precision; 9.6 input superpositions | QFT, controlled gates, eigenvalue bridge | Recover an exactly representable phase, then explain a non-exact distribution. |
| **10. Shor and order finding** | 10.1 modular arithmetic/gcd; 10.2 orders; 10.3 modular multiplication; 10.4 QPE/order finding; 10.5 continued fractions; 10.6 verification/retries; 10.7 resources | QPE, modular arithmetic, classical reconstruction | Trace one complete small factoring attempt and identify an unsuccessful branch. |
| **11. Noise and quantum error correction** | 11.1 density matrices; 11.2 noise channels; 11.3 sampling versus noise; 11.4 bit-flip repetition code; 11.5 phase errors; 11.6 syndrome measurements; 11.7 stabilizer/logical-qubit overview | Multi-qubit measurement and linear algebra | Explain what a chosen code corrects and what it does not. |
| **12. Variational and simulation branches** | 12.1 observables/expectation values; 12.2 Hamiltonians; 12.3 hybrid optimization; 12.4 VQE; 12.5 QAOA; 12.6 benchmark design; 12.7 quantum dynamics | Relevant linear algebra, multi-qubit circuits, probability | Interpret an objective trace and justify comparison assumptions. |
| **13. Advanced extensions** | 13.1 generalized amplitude amplification; 13.2 amplitude estimation; 13.3 quantum walks; 13.4 complexity; 13.5 surface codes and fault tolerance | Branch-specific evidence | Complete a reviewed project with explicit assumptions and limitations. |

The mathematical progression is informed by [IBM's query-algorithm introduction][S21], [Deutsch–Jozsa][S12], [Simon][S13], [phase estimation][S14], [Shor][S05], [Preskill's state/ensemble notes][S07], and [Preskill's algorithm notes][S22]. The exact chapter organization is a product proposal.

### 6.1 Algorithm accuracy notes for future authors

- **Deutsch:** determine whether a one-bit Boolean function is constant or balanced; one ideal quantum query versus two classical queries for exact identification.
- **Bernstein–Vazirani:** recover a hidden n-bit string s from a parity oracle f(x)=s·x modulo 2. The ideal query comparison is one quantum query versus n classical queries for exact recovery. IBM presents this linear-function problem within its Deutsch–Jozsa discussion. [IBM: Deutsch–Jozsa and linear functions][S12].
- **Deutsch–Jozsa:** require the constant-or-balanced promise. The exponential query separation is against exact deterministic classical computation; bounded-error randomized classical methods change that comparison. [IBM: Deutsch–Jozsa][S12].
- **Simon:** measurement supplies constraints orthogonal to a hidden XOR string; it does not directly reveal the string. Include the promise and the classical linear-system stage. [IBM: Simon][S13].
- **QFT/QPE:** QFT transforms amplitudes. QPE estimates an eigenvalue phase using an appropriate input state and controlled powers; inverse QFT is part of the standard procedure. Neither exposes an arbitrary amplitude vector in one measurement. [IBM: Phase-estimation procedure][S14].
- **Teleportation:** use a shared entangled pair and two classical bits; demonstrate conditional corrections and consumption of the original state. [IBM: Teleportation][S11].

## 7. Chapter 1: complete demo content specification

### 7.1 Chapter outcome and scope

After this chapter, a learner should be able to read a one-qubit state, obtain Z-basis probabilities, distinguish a probability from a sampled frequency, apply X/H/Z, and explain how a relative sign affects a later H operation. This establishes foundation skills; it is not mastery of quantum algorithms.

All eight subtopics below belong in the complete demo. They reuse one small laboratory with different authored presets and task constraints.

**Notation contract:** `|ψ⟩ = α|0⟩ + β|1⟩` has amplitude vector (α,β). Circuit arrows indicate chronological order: `H → Z` means H first, then Z, whose matrix expression is ZH. Measurements are in the computational/Z basis unless labeled otherwise. All core examples are ideal, noiseless, single-qubit experiments.

**Shared controls:** choose an allowed initial state; insert/remove/reorder allowed gates; run; play/pause; step forward/back; reset preset; replay recorded run; choose shots; compare runs; request a hint. Defaults use discrete inputs. Free complex-amplitude entry and continuous rotation controls are Chapter 2 extensions.

**Shared panels:** instruction and prediction; labeled circuit; current amplitudes; exact probabilities; measured counts; a textual state summary; selected step and run; contextual tutor. Introduce phase markers only when needed. A Bloch sphere is optional enrichment in this chapter, not a prerequisite for its assessments.

**Shared completion contract:** submit a prediction, run the required comparisons, answer the named checkpoint questions correctly after feedback, and complete the transfer task. An initially incorrect prediction does not fail the topic. Assisted success completes practice; independent skill evidence comes from unassisted checks. Reading time, scrolling, and pressing Run do not establish understanding.

**Shared hint ladder:** H1 recalls the relevant concept; H2 directs attention to a panel or operation; H3 gives the next calculation; H4 reveals a worked solution. The topic-specific H1/H2 prompts appear below; its worked trace supplies H3/H4. After H4, offer a new transfer variant before recording independent success.

### Topic 1.1 — Bits, qubits, and the computational basis

**Objective:** distinguish a state description from a measurement result and read basis notation.

**Teach:** A classical bit has value 0 or 1. In this laboratory a qubit has reference states `|0⟩` and `|1⟩`. We represent them by (1,0) and (0,1). The two entries label amplitudes associated with the two basis outcomes; they are not two separate qubits. A measurement gives a classical result, such as 0. These reference states are the starting point for describing more general qubit states. [Preskill: Qubit states][S07].

**Inputs:** state preset `|0⟩` or `|1⟩`; one shot or 16 shots. No gate palette yet.

**Predict:** “You selected `|1⟩`. Which outcome is possible in an ideal Z measurement?”

**Experiment, step by step:**

1. Select `|0⟩`; show (1,0), P(0)=1, P(1)=0.
2. Run one measurement; show classical outcome 0.
3. Reset preparation; select `|1⟩`; show (0,1), P(0)=0, P(1)=1.
4. Run 16 independent shots; all 16 outcomes are 1 in this ideal model.

**Checkpoint:** match `|0⟩` to its vector and probability bars; separately identify which UI label describes a recorded classical result. Accept the two correct matches, not a prose judgment by AI.

**Transfer:** the platform presents (0,1) without a ket label. Learner selects `|1⟩` and predicts outcome 1.

**Hints:** H1 “Which basis label belongs to the nonzero entry?” H2 “Read the labels beneath the two amplitude entries.”

**Misconception response:** if the learner calls (1,0) “two qubits,” highlight the single wire and two outcome labels. The number of amplitudes differs from the number of qubits.

**Complete when:** both presets have been inspected and the checkpoint and transfer matches are correct. Skill: `basis.read_single_qubit`.

### Topic 1.2 — Amplitudes become probabilities

**Objective:** calculate squared magnitudes and check normalization.

**Teach:** For `α|0⟩ + β|1⟩`, Z-measurement probabilities are |α|² and |β|². A normalized state satisfies |α|²+|β|²=1. An amplitude can be negative or complex; an outcome probability cannot be negative. We begin with real coefficients so the arithmetic is visible. [IBM: Single-system states][S01].

**Inputs:** curated amplitude cards; switch between amplitude bars and probability bars. A “Check this candidate vector” panel accepts only the listed cards and explains invalid examples rather than simulating them.

| Card | Amplitudes | P(0), P(1) | Valid? |
|---|---|---|---|
| A | (1,0) | (1,0) | Yes |
| B | (3/5,4/5) | (9/25,16/25) = (0.36,0.64) | Yes |
| C | (−3/5,4/5) | (0.36,0.64) | Yes |
| D | (1/√2,1/√2) | (0.5,0.5) | Yes |
| E | (1/2,1/2) | Squared magnitudes sum to 1/2 | No, as a normalized state vector |

**Predict:** “Does changing 3/5 to −3/5 make the corresponding probability negative?”

**Experiment:** select B; reveal each square separately; add to 1; compare C; then inspect E. Keep an invalid vector in the arithmetic panel with **Not normalized**, and require selecting a valid card before execution. Do not silently normalize E.

**Checkpoint:** enter 0.36 and 0.64 for B, and select “same Z probabilities” for B versus C. Also select the reason E is invalid.

**Transfer:** use (4/5,−3/5). Expected probabilities are (0.64,0.36). The sign must not become a negative probability.

**Hints:** H1 “Square the magnitude of each entry.” H2 “Compare amplitude height with probability height; they use different scales.”

**Future payoff:** “A probability chart can hide a sign difference. Later operations may reveal that difference.”

**Complete when:** calculations and the normalization check are correct. Skills: `amplitude.born_rule`, `state.normalization`.

### Topic 1.3 — Measurement, shots, and replay

**Objective:** distinguish repeated preparation from repeated measurement of an already measured qubit.

**Teach:** In an ideal projective Z measurement, an outcome is sampled using the state's probabilities and the conditional state becomes the corresponding basis state. Immediately repeating that same measurement with no intervening operation gives the same outcome. By contrast, independent shots restart the preparation. [Preskill: States and ensembles, measurement postulate][S07].

**Inputs:** prepared states D and B from 1.2; 1, 16, 64, 256, or 1,024 shots; **New preparation** and **Measure this trajectory again** as distinct actions.

**Predict:** “For 16 fresh preparations of D, must the result be exactly eight zeros?”

**Experiment:**

1. Select D. Exact probabilities stay at (0.5,0.5).
2. Run one shot. Show whichever outcome was actually sampled and its conditional basis state.
3. Measure that trajectory again. The recorded outcome must match the first outcome in this ideal same-basis case.
4. Run 16 fresh shots. Show actual counts, total, and frequencies separately from probabilities.
5. Repeat with 256 shots. Explain that larger samples typically estimate probabilities more closely, but an individual larger sample is not guaranteed to be closer.
6. Replay the saved run. The samples remain unchanged; a new run may differ.

**Checkpoint:** choose “exactly eight is possible, not required”; identify which action starts a new preparation; read the observed frequency directly from the current result.

**Transfer:** for state B and 100 shots, the expected number of ones is 64. Ask whether exactly 64 is required: no. This is an expectation from 100×0.64, not a promised count.

**Hints:** H1 “Does each trial restart the preparation?” H2 “Check whether the panel says exact probability or observed frequency.”

**Complete when:** the three distinctions are correct. Never grade a learner by demanding a particular random histogram. Skills: `measurement.conditioned_state`, `sampling.shots_vs_remeasure`, `sampling.probability_vs_frequency`.

### Topic 1.4 — Read a circuit and use the X gate

**Objective:** follow operation order and predict a basis-state flip.

**Teach:** A circuit wire identifies the qubit, and operations are applied in the displayed order. X swaps the two amplitudes: (α,β) becomes (β,α). It exchanges `|0⟩` and `|1⟩`; applying X twice restores the input. In the gate model, this is a reversible operation. [IBM: X gate][S16].

**Inputs:** `|0⟩`, `|1⟩`, or B; add/remove X up to four times; place final Z measurement.

**Predict:** “Starting from `|1⟩`, what will two X gates produce?”

| Trace | Initial state | After first X | After second X |
|---|---|---|---|
| A | (1,0) | (0,1) | (1,0) |
| B | (0,1) | (1,0) | (0,1) |
| C | (3/5,4/5) | (4/5,3/5) | (3/5,4/5) |

**Guided task:** from `|0⟩`, make final P(1)=1 using only X, with at most three gates. Accept one X or three X gates. If the task separately asks for the fewest gates, only then require one.

**Checkpoint:** identify the output of two X gates on `|1⟩`; then explain via a selected statement that the amplitudes swapped twice.

**Transfer:** start from B, apply X, and enter P(0)=0.64. This tests amplitude movement beyond basis memorization.

**Hints:** H1 “X exchanges the two entries.” H2 “Inspect the amplitude table immediately after the first gate.”

**Complete when:** the constructed goal and both checks succeed. Accept any circuit meeting the published constraints and state goal. Skills: `circuit.read_order`, `gate.x_predict`, `circuit.construct_goal`.

### Topic 1.5 — H and superposition

**Objective:** understand H as a specific linear operation, not a randomizer.

**Teach:** The Hadamard gate maps `|0⟩` to `|+⟩=(|0⟩+|1⟩)/√2`, and `|1⟩` to `|−⟩=(|0⟩−|1⟩)/√2`. Both have equal Z-measurement probabilities. H also maps `|+⟩` back to `|0⟩` and `|−⟩` back to `|1⟩`. A superposition is defined relative to a basis; it is not a classical list of answers that measurement can print. [IBM: H gate][S15].

**Inputs:** initial `|0⟩` or `|1⟩`; one or two H gates; shots selector.

**Predict:** “Will two H gates necessarily leave the probabilities at 50/50?”

| Input | After H | Z probabilities | After a second H |
|---|---|---|---|
| `\|0⟩` | (1/√2,1/√2) | (1/2,1/2) | `\|0⟩` |
| `\|1⟩` | (1/√2,−1/√2) | (1/2,1/2) | `\|1⟩` |

**Guided task:** create a 50/50 Z distribution from `|0⟩` using X/H, at most three gates, with no intermediate measurement. Evaluate the final probabilities, not exact gate-string matching. For example, H and X→H both satisfy this distribution goal despite preparing different states.

**Checkpoint:** select “H follows a deterministic state transformation; measurement can be random.” Compare the signs in the two first-H outputs.

**Transfer:** start from `|1⟩` and predict H→H→H. The final state is `|−⟩`; Z probabilities are equal.

**Hints:** H1 “H can undo H.” H2 “Compare the first and second H snapshots rather than only the measurement counts.”

**Complete when:** the distribution goal, checkpoint, and transfer prediction succeed. Skills: `gate.h_predict`, `superposition.read`, `state_vs_distribution.distinguish`.

### Topic 1.6 — Z, relative phase, and global phase

**Objective:** recognize a relative sign change while avoiding the claim that every minus sign is observable.

**Teach:** Z maps (α,β) to (α,−β), so it leaves the immediate Z-basis probabilities unchanged. On `|+⟩` it produces `|−⟩`. On `|1⟩` it produces `−|1⟩`; for that entire one-qubit state this is a global phase, not a new distinguishable state. [IBM: Z gate][S18].

Multiplying **every** amplitude by the same unit-magnitude factor changes global phase and leaves all physical predictions for the state unchanged. Changing the relative phase of populated components can affect later interference. [IBM: Global phase][S08].

**Inputs:** start with `|+⟩`, `|0⟩`, or `|1⟩`; add Z; optional **Equivalent notation** switch displays a whole-vector sign change. That switch is a representation aid, not a measurement or a physical claim of detecting global phase.

**Predict:** “After Z on `|+⟩`, which panel changes: amplitudes, immediate Z probabilities, or both?”

**Experiment:** prepare `|0⟩`; apply H; record (a,a), where a=1/√2; apply Z and inspect (a,−a). Keep both probability bars at 1/2. Next inspect Z on `|1⟩`, and compare `|1⟩` with `−|1⟩` using the equivalent-notation overlay.

**Checkpoint:** classify `(a,a)` versus `(a,−a)` as different relative phases; classify `(a,a)` versus `(−a,−a)` as global-phase-equivalent. Select “unchanged” for immediate Z probabilities.

**Transfer:** two consecutive Z gates on `|+⟩` restore `|+⟩`. Predict both the amplitude signs and probabilities.

**Hints:** H1 “Did one populated component change sign, or did the whole vector?” H2 “Check the sign column as well as the bars.”

**Complete when:** all classifications and the transfer succeed. Skills: `gate.z_predict`, `phase.relative`, `phase.global_equivalence`.

**Author caution:** do not turn “global phase of a whole state is unobservable” into a blanket rule for dropping phases from controlled operations. A phase that becomes conditional can be a relative phase in a larger system; teach this in Chapter 4.

### Topic 1.7 — Interference: why H–H and H–Z–H differ

**Objective:** add amplitudes before squaring and locate the step at which probabilities change.

**Teach through a worked calculation:** H maps `(α,β)` to `((α+β)/√2,(α−β)/√2)`. With input `(a,a)`, a=1/√2, the result is (1,0). With `(a,−a)`, the result is (0,1). One output receives adding contributions and the other receives cancelling contributions. The following arithmetic is obtained directly from the [Hadamard matrix][S15].

| Circuit from `\|0⟩` | After first H | After optional Z | Final state after H | Final P(1) |
|---|---|---|---|---:|
| H → H | (a,a) | (a,a) | (1,0) | 0 |
| H → Z → H | (a,a) | (a,−a) | (0,1) | 1 |

**Visual arithmetic:** after H on `(a,a)`, show contributions +1/2 and +1/2 into output 0, and +1/2 and −1/2 into output 1. For `(a,−a)`, show +1/2 and −1/2 into output 0, and +1/2 and +1/2 into output 1. Square only the resulting sums. Label these arrows **amplitude contributions**, not literal particle paths.

**Inputs:** two comparison circuits; toggle the middle Z; move Z before the first H or after the last H; optional early-measurement variant.

**Predict:** “At which step do the two circuits first have different Z probabilities?” Correct: after their final H, not immediately after Z.

**Guided task:** with fixed first and final H gates, choose whether a Z belongs between them to make P(1)=1. It belongs between them. Check the goal using the computed final state.

**Measurement variant:** compare H→H with H→Measure Z→H. For the second circuit, the intermediate outcome is 0 or 1; either branch followed by H gives equal final Z probabilities. Show both conditional branches and a separate ensemble summary. Do not imply that inspecting a simulator snapshot performs this measurement.

**Transfer:** starting from `|1⟩`, predict H→Z→H. Worked result: `|1⟩ → |−⟩ → |+⟩ → |0⟩`. A final Z placed after H→H on `|0⟩` instead leaves `|0⟩` unchanged.

**Hints:** H1 “Add the signed contributions before taking the square.” H2 “Compare the amplitudes just before the last H.”

**Complete when:** the placement task, probability-divergence checkpoint, and reversed-input transfer succeed. Skill: `interference.phase_to_probability`.

### Topic 1.8 — Build, explain, and revisit the mystery

**Objective:** combine foundation skills in a new task and connect them to the search preview.

**Capstone A: design a selectable output.** Starting from `|0⟩`, two H gates are fixed. The learner controls the middle slot: empty or Z. They must make two versions, one with final P(0)=1 and one with final P(1)=1, submit both, and identify the role of the middle operation. Expected choices: empty gives 0; Z gives 1.

**Capstone B: diagnose a changed input.** The same H→Z→H circuit now starts from `|1⟩`. The learner predicts output 0 and explains the changed result using the supplied amplitude trace. Selecting an explanation is graded; an optional free-text explanation receives feedback only.

**Capstone C: separate theory and observation.** Show the learner's actual H-only sampled run. They identify the exact probabilities, measured counts, and shot total, then select why those counts need not split equally.

**Revisit Grover:** open the earlier saved N=4 run at its oracle step. Ask: “Which idea from Chapter 1 explains why a sign can matter even before probability bars change?” Expected response: relative phase can affect later interference. Do not ask them to derive multi-qubit diffusion yet.

**Revisit status:** keep Grover at **Seen**, with a linked note **Recognizes phase-to-probability connection**. Completing one foundation chapter does not earn Grover **Can Explain** or **Mastered**.

**Hints:** H1 “Use your H–H versus H–Z–H comparison.” H2 “Inspect the state immediately before the last H.” A revealed capstone answer leads to an equivalent new-input practice task.

**Complete when:** the three capstone checks and revisit response are complete. Then offer the chapter assessment. Keep all earlier activities available for review.

## 8. Chapter 1 assessment, answers, and progression rules

### 8.1 Authored assessment bank

Administer ten one-point items per form. Circuit tasks use the stated constraints and a deterministic state/distribution evaluator. Numeric answers can accept exact fractions or decimals within an authored absolute tolerance, proposed as 0.001. The answer key below is author-facing; it is never sent to the tutor during a live unassisted test.

| # | Form A prompt | Answer / evaluator | Form B equivalent |
|---:|---|---|---|
| 1 | Identify the ket for vector (0,1). | `\|1⟩` | (1,0) → `\|0⟩` |
| 2 | P(1) for `(3/5,−4/5)`? | 16/25 = 0.64 | P(1) for `(4/5,−3/5)` → 0.36 |
| 3 | Is `(1/2,1/2)` normalized? Select the reason. | No; sum of squared magnitudes is 1/2. | `(1/√2,−1/√2)` → yes; sum is 1. |
| 4 | Must 16 fresh measurements of `\|+⟩` contain eight zeros? | No; equal probabilities do not fix finite counts. | Must 64 shots contain 32 ones? → no. |
| 5 | An ideal Z measurement gave 1. What does an immediate same-basis remeasurement give, without another gate? | 1 with probability 1. | First result 0 → repeat 0. |
| 6 | Starting from `\|1⟩`, construct P(0)=1 using at most three X gates. | Any allowed odd-X circuit. | Start `\|0⟩`, target P(1)=1. |
| 7 | State after H on `\|1⟩`? | `\|−⟩` | H on `\|0⟩` → `\|+⟩` |
| 8 | Classify `\|+⟩` versus `−\|+⟩`; and `\|+⟩` versus `\|−⟩`. | Global-phase-equivalent; relative-phase difference. Both required. | `\|−⟩` versus `−\|−⟩`; and `−\|+⟩` versus `\|−⟩`: same categories. |
| 9 | Select the first step where H→H and H→Z→H from `\|0⟩` have different Z probabilities. | Their final H. | Repeat for initial `\|1⟩`. |
| 10 | From `\|1⟩`, with fixed first/final H gates, choose empty or Z in the middle to obtain `\|0⟩`; select the reason. | Z; the relative sign changes the final H interference. Both required. | From `\|0⟩`, target `\|1⟩` → Z, same reason. |

Suggested chapter pass: at least 8/10, with items 2, 4, 8, 9, and 10 correct, and all required practice activities complete. This is a **pilot policy**, not a universal definition of mastery. If only an essential skill remains weak, offer a targeted parallel item after revision instead of requiring an endless full-chapter repeat.

Topic-level diagnostic evidence can substitute for already demonstrated practice requirements. Diagnostic items must use equivalent objectives and evaluator rules. A learner is not forced to re-watch an explanation to unlock a concept they have demonstrated.

### 8.2 Separate three records

1. **Activity completion:** the learner finished the required actions and responses, possibly with help.
2. **Independent evidence:** the learner solved a new, appropriate item without substantive hints.
3. **Review recommendation:** a previously demonstrated skill may benefit from practice; this does not erase historical achievement.

For initial access decisions, a proposed prerequisite-ready rule is two unassisted successful checks from distinct item families for each required skill, including one transfer check where appropriate. A mixed-skill capstone only contributes evidence to components that its rubric actually evaluates. These thresholds require pilot calibration.

### 8.3 Examples of concept-based unlocking

| Destination | Evidence needed |
|---|---|
| Chapter 2 measurement-basis lab | Born rule, H behavior, and relative-phase discrimination |
| Bell-state guided lab | Tensor products, controlled-X behavior, H preparation, measurement |
| Grover guided construction | Multi-qubit states, state preparation, oracle semantics, relative phase, interference, measurement |
| QPE guided lab | Eigenvalue bridge, controlled powers, phase kickback, inverse QFT |
| Shor guided lab | QPE/order-finding concepts, modular arithmetic, rational reconstruction and verification |

A preview is always available independently of these gates. Reading-only material can remain browsable with prerequisite advice; grading readiness should not make reference material inaccessible.

## 9. The tutor available throughout learning

### 9.1 What the tutor should receive

For a question about an experiment, supply the approved lesson passage, current learning objective, selected run and step, verified amplitudes/probabilities or counts, circuit settings, attempt mode, relevant recent submitted answers, and hints already delivered. Supply only the learner evidence needed for that question.

The tutor should say **“Explaining run 12, step 3: after Z”** when discussing a particular result. If the learner changes the circuit while a reply is being prepared, keep that reply attached to its original run and offer a new explanation for the new run.

### 9.2 Expected behaviors

| Learner asks | Desired response behavior |
|---|---|
| “Why is this negative?” | Identify the signed amplitude and the gate that changed it; distinguish it from probability. |
| “Why did Z do nothing?” | Explain the unchanged immediate Z probabilities and invite an H comparison. |
| “Why are my counts not half?” | Read actual count/shot facts and explain finite sampling. |
| “Show each step.” | Navigate or cite recorded stateframes and explain one transition at a time. |
| “What is an oracle?” | Use the approved predicate example and the visible cost-model definition. |
| “What did I get wrong?” | Explain a submitted rubric mismatch; do not label an unfinished exploratory circuit as wrong. |
| “Give me the answer.” | In practice, offer the next hint level and eventually a labeled worked solution. In a test, offer to move that attempt to practice. |
| “Can quantum computers do everything faster?” | Use the bounded claims in the lesson sources and ask which problem the learner means. |

Illustrative original response for Topic 1.6:

> At the selected step, Z changed the second amplitude's sign. Squaring its magnitude still gives the same probability. Try the next H operation and compare how the signed contributions combine.

Numerical values in a live answer should be inserted from the actual result, not copied from this sample. If there is no completed run, the tutor should identify its explanation as a general example rather than describe a nonexistent experiment.

### 9.3 Authority and failure handling

- The tutor can explain, ask diagnostic questions, and suggest a validated experiment.
- It cannot assign final grades, change mastery records, unlock content, or fabricate simulation outputs.
- It can explain a deterministic decision by citing the rubric result and evidence.
- It may provide nonbinding feedback on open-ended prose; ambiguous AI interpretation must not block Chapter 1 progression.
- If retrieval or numerical grounding fails, provide an authored help card and a retry option.
- If the tutor is unavailable, lessons, saved work, deterministic checks, and progression remain usable.
- Keep help available during tests for navigation, accessibility, and permitted wording clarification. Substantive solution assistance changes the attempt to practice before the hint is revealed.

### 9.4 Weakness-based adaptation

Use observable errors to select a short follow-up:

| Evidence | Possible misconception | Next activity |
|---|---|---|
| Treats −3/5 as a negative probability in two different items | Amplitude confused with probability | Signed-square card and a fresh reversed-amplitude example |
| Predicts 50/50 after every H | H treated as a randomizer | H on `\|+⟩` and `\|−⟩`, then a new two-H task |
| Claims Z always changes measured counts | Basis probabilities confused with phase | Compare H and H→Z before adding final H |
| Claims Z never matters | No phase-to-interference connection | H→H versus H→Z→H |
| Treats more shots as changing the exact state probabilities | Sampling confused with evolution | Fixed-circuit exact bars beside two shot counts |

Ask a discriminating question before confirming a misconception. Do not infer weakness from asking for help, exploratory edits, slow reading, or a random histogram. Preserve the existing blueprint's evidence history and make recommendations explainable: **“This exercise revisits phase because your last two submitted comparisons confused signs with probabilities.”**

## 10. Quantum Lab and persistent algorithm mysteries

### 10.1 Lab modes and availability

| Mode | Meaning |
|---|---|
| Preview | Curiosity experiment or conceptual story; no grade and no prerequisite mastery. |
| Guided | Authored sequence with explicit checkpoints and hints. |
| Experiment | Change allowed parameters and compare results. |
| Build | Construct and submit a circuit or protocol under stated constraints. |

**Mastered is an evidence status, not a fifth execution mode.** Keep it separate from how a learner is currently using the lab.

The demo releases the Grover preview and Shor storyboard. The lab catalog can show future Deutsch, Deutsch–Jozsa, Bernstein–Vazirani, Simon, QFT, QPE, and teleportation entries with meaningful descriptions and prerequisite maps. Mark unimplemented experiences **Planned**, not as working simulations that happen to be locked.

### 10.2 Algorithm evidence levels

| Status | Evidence required |
|---|---|
| Seen | Opened an actual preview and reached its main result/story step. |
| Understood | Passed an authored check about the algorithm's core mechanism and assumptions. |
| Can Explain | Passed structured reasoning items about why the mechanism works. |
| Can Modify | Successfully changed a parameter/oracle and predicted its effect. |
| Can Build | Constructed a valid solution under the algorithm's task constraints. |
| Can Transfer | Applied the mechanism to a new problem instance or encoding. |
| Mastered | Met published requirements across explanation, construction, modification, and independent transfer, with sufficient diverse evidence. |

Store these as evidence-backed capabilities, with a suggested progression, rather than assuming every learner has an identical sequence. In particular, a learner may construct a circuit before being able to explain it. Do not automatically promote all lower capabilities from one successful build.

Save the algorithm version, preview type, parameter choices, run/step inspected, reflection, date, and links to later evidence. Optional self-reported understanding is separate from evaluated capability.

### 10.3 Explicit payoff moments

- After relative phase: reopen the saved oracle step and locate the changed amplitude sign.
- After interference: compare probability redistribution with the Chapter 1 H examples.
- After controlled gates: explain how phase marking can be implemented through an oracle.
- At full Grover: begin with **“Return to your earlier search experiment. Now build the operations that made it work.”**
- At QPE and modular arithmetic: reopen the Shor storyboard and replace each future-concept chip with the learned explanation.

## 11. Rules for truthful visualizations

### 11.1 Always identify the result type

| Label | Meaning | Examples |
|---|---|---|
| **Ideal circuit simulation** | A declared circuit was numerically evolved under the ideal model. | Chapter 1 stateframes; small Grover runs |
| **Sampled simulator outcomes** | Measurements were sampled from that model. | Shot histograms |
| **Analytical prediction** | Values were evaluated from a mathematical formula under stated assumptions. | Grover iteration/scaling curve |
| **Conceptual walkthrough** | A storyboard explains a mechanism without executing the full algorithm. | Shor mystery |
| **Hardware measurement — future** | A named device returned actual measured results. | Later hardware integration |

The calculations in this document are reference values. They are not evidence that a platform simulator has been implemented or that hardware has been run.

### 11.2 State and animation contracts

- Every visible panel must share the same circuit revision, run, branch, and selected step.
- Pre-measurement probabilities, a single conditional post-measurement state, and many-shot counts must be separate objects.
- Playback speed controls viewing pace, not quantum execution time. Provide discrete Step, slow Play, and reduced-motion mode.
- Only verified endpoints support numerical state claims. If a tween is merely visual interpolation, do not label its intermediate pixels as computed quantum states.
- Do not animate measurement as a reversible smooth rotation. A previous-step command reads history; it does not physically undo measurement.
- An amplitude's phase is undefined when its magnitude is zero. Display a dash or **undefined**, not a fabricated angle.
- Show real sign or complex phase with both text and visual encoding; probability bars are never negative.
- Simulator inspection does not measure the modeled system. On hardware, a full intermediate statevector is not directly returned by a shot.
- A Bloch sphere represents one qubit. Local spheres for an entangled register do not encode the entire joint state. Pure single-qubit states lie on the surface; mixed single-qubit states can lie inside. [IBM: Bloch sphere][S09], [IBM: Multiple systems][S10].
- Use q0 on the top circuit wire and as the least significant bit. Label displayed basis strings `|q[n−1]…q0⟩`; keep decimal labels consistent. [IBM: Bit ordering][S19].

### 11.3 Professional presentation

Use neutral backgrounds, readable typography, restrained accents, and stable chart scales. Prioritize a large experiment area, concise explanation column, and optional tutor panel. Keep formulas expandable and labels close to their visual objects.

Avoid particle backgrounds, unnecessary glow, decorative scientific imagery, and motion without a teaching purpose. Provide keyboard gate insertion, accessible numerical tables, visible focus, screen-reader summaries, and reduced motion. All essential information must remain understandable without color or 3D interaction.

## 12. What must work in the demo

### 12.1 Release scope

**Required:** introduction; classical/Grover comparison; bounded Grover preview; Shor storyboard; beginner bridge; all Chapter 1 topics; both assessment forms; contextual tutor and authored fallback; recorded step playback; parameter changes; saved progress; concept evidence; revisit links; keyboard/text alternatives.

**Preserved platform capabilities:** save/resume, immutable revisions, event history, deterministic grading, progressive hints, privacy controls, a one/two-qubit playground, and an extensible curriculum map. The original architecture can support these features; this document does not prescribe a stack migration.

**Later deliverables:** fully taught multi-qubit and advanced chapters; generalized editable algorithm builders; arbitrary complex states; noise models; hardware jobs; instructor tools. Roadmap chapters must have honest availability labels.

### 12.2 Reference fixtures for future implementation verification

These are mathematically expected outputs, not a report of software tests already run:

| Fixture | Expected result |
|---|---|
| X twice on either basis state | Original state |
| H twice on either basis state | Original state |
| H→Z→H on `\|0⟩` | `\|1⟩` |
| H→Z→H on `\|1⟩` | `\|0⟩` |
| Z on `(3/5,4/5)` | `(3/5,−4/5)`; unchanged Z probabilities |
| H→Z→Z→H on `\|0⟩` | `\|0⟩` |
| State comparison of `\|+⟩` and `−\|+⟩` | Equivalent up to global phase |
| Distribution comparison of `\|+⟩` and `\|−⟩` in Z | Equal distributions, different pure states |
| H→Measure Z→H on `\|0⟩` | Either intermediate branch; final Z probabilities 1/2,1/2 |
| N=4 Grover, one iteration, target 2 | Target probability 1 |
| N=4 Grover, two iterations | Target probability 1/4 |
| N=8 Grover, two iterations | Target probability 121/128 |
| N=8 Grover, three iterations | Target probability 169/512 |
| Invalid `(1/2,1/2)` preparation | Reject as not normalized; no silent correction |

Use phase-invariant pure-state comparison when the task asks for a state, and probability comparison when the task asks for a distribution. Keep engineering tolerances separate from learner answer tolerances. Retain the original blueprint's independent numerical verification requirement.

### 12.3 Acceptance walkthrough

1. A beginner sees the introduction, runs N=4 Grover, changes the target, and observes the correct new marked outcome.
2. They choose N=8 and compare k=2 with k=3; the latter has lower ideal target probability.
3. They inspect the Shor storyboard, see its conceptual label, and receive only a Seen record.
4. They complete all eight Chapter 1 subtopics using actual parameter-dependent results, not fixed animated clips.
5. A wrong prediction receives teaching feedback; a valid alternative circuit passes the applicable goal.
6. A sampled histogram never causes a grading failure solely because it differs from expected proportions.
7. Replay preserves measured outcomes; a new run creates a distinct record. Rapid edits cannot combine old charts with a new circuit.
8. The tutor answers about the selected run and step. It cannot change assessment results or algorithm capability states.
9. With the tutor unavailable, the learner can use authored hints, submit an assessment, and continue.
10. Passing updates only the skills supported by evaluated evidence; Grover remains Seen until its own objectives are demonstrated.
11. On return, the learner resumes the saved topic and reopens their original Grover mystery.
12. All of this can be completed with keyboard controls and textual/numerical alternatives.

### 12.4 Review and delivery sequence

**Content review:** a quantum educator checks definitions, exact examples, oracle assumptions, and distractors. A beginner reviewer checks vocabulary and reading load. This document is researched and numerically checked; it has not received that independent educator review.

**Implementation planning:** create the shared simulation/playback slice, then the complete Chapter 1 activity flow, then previews and the contextual tutor, then persistence/accessibility checks. The original engineering roadmap can retain its deployment and security work, but its earlier timeline should be re-estimated for eight subtopics and the new previews.

**Pilot evaluation:** observe whether learners can explain H–Z–H from a changed input, distinguish probability from frequency, and reconnect phase to the Grover preview. Collect delayed transfer evidence before claiming improved learning outcomes. Completion and enthusiasm are useful product signals, but are not sufficient evidence of understanding.

## 13. Source register and editorial maintenance

Links below were checked during this research. They support the scientific content, not the proposed UI, chapter durations, or pass thresholds. Tutorials that contain code are reading resources; their code is not included or implemented here. Use original explanations and author-created diagrams, with attribution, rather than copying course pages wholesale.

| ID | Source and author/provider | Principal use |
|---|---|---|
| S01 | [Single-system quantum information — IBM Quantum Learning][S01] | Qubit vectors, amplitudes, normalization, Born rule |
| S02 | [Unstructured search — IBM Quantum Learning][S02] | Search predicate and oracle model |
| S03 | [Grover analysis — IBM Quantum Learning][S03] | Reflection, rotation, iteration probability |
| S04 | [A fast quantum mechanical algorithm for database search — Lov K. Grover, 1996][S04] | Original search algorithm and query advantage |
| S05 | [Shor's algorithm — IBM Quantum Learning][S05] | Order finding, gcd steps, post-processing |
| S06 | [Polynomial-Time Algorithms for Prime Factorization and Discrete Logarithms on a Quantum Computer — Peter W. Shor][S06] | Original theoretical algorithm and complexity |
| S07 | [Quantum Information, Chapter 2: States and Ensembles — John Preskill, Caltech][S07] | Measurement postulate, states, mixtures, foundational reference |
| S08 | [Limitations on quantum information — IBM Quantum Learning][S08] | Global phase, distinguishability, no-cloning |
| S09 | [Bloch sphere — IBM Quantum Learning][S09] | Pure/mixed single-qubit geometric representation |
| S10 | [Multiple-system quantum information — IBM Quantum Learning][S10] | Composite states and entanglement |
| S11 | [Teleportation — IBM Quantum Learning][S11] | Entangled resource, classical bits, correction steps |
| S12 | [The Deutsch–Jozsa algorithm — IBM Quantum Learning][S12] | Promise problem, comparisons, linear-function/BV discussion |
| S13 | [Simon's algorithm — IBM Quantum Learning][S13] | Hidden XOR string and sampled constraints |
| S14 | [The phase-estimation procedure — IBM Quantum Learning][S14] | QFT, controlled powers, phase readout |
| S15 | [H gate — IBM Quantum Documentation][S15] | Hadamard matrix and inverse |
| S16 | [X gate — IBM Quantum Documentation][S16] | Amplitude-swap matrix |
| S17 | [Variational Quantum Algorithms — Cerezo et al., 2021][S17] | Hybrid methods and trainability/accuracy/efficiency challenges |
| S18 | [Z gate — IBM Quantum Documentation][S18] | Phase-flip matrix |
| S19 | [Bit ordering — IBM Quantum Documentation][S19] | Basis and circuit indexing conventions |
| S20 | [Quantum circuits: Introduction — IBM Quantum Learning][S20] | Circuit-model context |
| S21 | [Quantum query algorithms: Introduction — IBM Quantum Learning][S21] | Role and limitations of the query model |
| S22 | [Quantum Information, Chapter 6: Quantum Algorithms — John Preskill, Caltech][S22] | Quantum circuits, algorithms, and simulation background |

**Reading route for learners:** begin with the platform's short Chapter 1 cards; offer S01, S15, S16, and S18 for optional mathematical details. Offer S02–S03 when returning to Grover, and S14–S05 when reaching QPE and Shor. Preskill's notes and original papers are advanced reference material, not required beginner reading.

**Editorial update policy:** record source title/URL, access date, supported claims, and content version. Review scientific claims when lessons change; re-check software documentation before implementation. Do not infer present-day hardware capability from the date of an old paper or from a vendor's forward-looking statement. Mark open research questions as open and distinguish a proved query result from an empirical benchmark.

[S01]: https://quantum.cloud.ibm.com/learning/en/courses/basics-of-quantum-information/single-systems/quantum-information
[S02]: https://quantum.cloud.ibm.com/learning/en/courses/fundamentals-of-quantum-algorithms/grover-algorithm/unstructured-search
[S03]: https://quantum.cloud.ibm.com/learning/en/courses/fundamentals-of-quantum-algorithms/grover-algorithm/analysis
[S04]: https://arxiv.org/abs/quant-ph/9605043
[S05]: https://quantum.cloud.ibm.com/learning/en/courses/fundamentals-of-quantum-algorithms/phase-estimation-and-factoring/shor-algorithm
[S06]: https://arxiv.org/abs/quant-ph/9508027
[S07]: https://www.preskill.caltech.edu/ph219/chap2_15.pdf
[S08]: https://quantum.cloud.ibm.com/learning/en/courses/basics-of-quantum-information/quantum-circuits/limitations-on-quantum-information
[S09]: https://quantum.cloud.ibm.com/learning/en/courses/general-formulation-of-quantum-information/density-matrices/bloch-sphere
[S10]: https://quantum.cloud.ibm.com/learning/en/courses/basics-of-quantum-information/multiple-systems/quantum-information
[S11]: https://quantum.cloud.ibm.com/learning/en/courses/utility-scale-quantum-computing/teleportation
[S12]: https://quantum.cloud.ibm.com/learning/en/courses/fundamentals-of-quantum-algorithms/quantum-query-algorithms/deutsch-jozsa-algorithm
[S13]: https://quantum.cloud.ibm.com/learning/en/courses/fundamentals-of-quantum-algorithms/quantum-query-algorithms/simon-algorithm
[S14]: https://quantum.cloud.ibm.com/learning/en/courses/fundamentals-of-quantum-algorithms/phase-estimation-and-factoring/phase-estimation-procedure
[S15]: https://quantum.cloud.ibm.com/docs/en/api/qiskit/qiskit.circuit.library.HGate
[S16]: https://quantum.cloud.ibm.com/docs/en/api/qiskit/qiskit.circuit.library.XGate
[S17]: https://arxiv.org/abs/2012.09265
[S18]: https://quantum.cloud.ibm.com/docs/en/api/qiskit/qiskit.circuit.library.ZGate
[S19]: https://quantum.cloud.ibm.com/docs/en/guides/bit-ordering
[S20]: https://quantum.cloud.ibm.com/learning/en/courses/basics-of-quantum-information/quantum-circuits/introduction
[S21]: https://quantum.cloud.ibm.com/learning/en/courses/fundamentals-of-quantum-algorithms/quantum-query-algorithms/introduction
[S22]: https://www.preskill.caltech.edu/ph219/chap6_20_6A_2022.pdf
