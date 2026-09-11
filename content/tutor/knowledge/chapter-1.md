---
id: chapter-1
version: 1
title: One-qubit foundations and preview connections
audience: learner
status: researched_seed
independent_educator_review: pending
topics: [intro, grover-preview, shor-preview, ch1-1, ch1-2, ch1-3, ch1-4, ch1-5, ch1-6, ch1-7, ch1-8]
---

# Tutor knowledge: Chapter 1

This is original educational text grounded in the linked references. The application may use it for the internal demo through an explicit server allowlist. It is not an assessment answer key, an engineering instruction file, or evidence of completed expert review. Passage IDs are the file ID plus the heading key, such as `chapter-1.basis`.

## basis

A one-qubit pure state can be written as α|0⟩ + β|1⟩. The two entries α and β are amplitudes associated with the computational basis, not two qubits. The basis vectors are (1,0) and (0,1). A measurement produces a classical result; it does not print the full state vector.

Source: [IBM single-system quantum information](https://quantum.cloud.ibm.com/learning/en/courses/basics-of-quantum-information/single-systems/quantum-information).

## probabilities

The Born rule assigns P(0)=|α|² and P(1)=|β|² for computational-basis measurement. Valid normalized pure-state vectors satisfy |α|²+|β|²=1. Amplitudes can be negative or complex; probabilities are nonnegative real numbers.

Worked example: (3/5,−4/5) has squared magnitudes 9/25 and 16/25, summing to 1. The vector (1/2,1/2) is not normalized because its squared magnitudes sum to 1/2. This lab rejects invalid initial vectors instead of silently changing them.

Source: [IBM single-system quantum information](https://quantum.cloud.ibm.com/learning/en/courses/basics-of-quantum-information/single-systems/quantum-information). Example arithmetic is independently worked.

## measurement

In an ideal projective computational-basis measurement, the outcome is sampled from the corresponding probabilities and the conditional state becomes the measured basis state. Repeating the same measurement immediately, with no intervening operation, returns that outcome with probability 1. Fresh shots instead restart the stated preparation.

Source: [Preskill, States and Ensembles, measurement postulate](https://www.preskill.caltech.edu/ph219/chap2_15.pdf).

## sampling

Exact probabilities describe the model. Counts and frequencies describe a finite sample. Equal probabilities do not require equal counts in every batch. For example, if an actual 256-shot run has 129 zeros and 127 ones, its observed frequencies are approximately 50.39% and 49.61%; its underlying probabilities may still be 50% each.

More independent shots generally improve estimation, but a particular larger sample is not guaranteed to be closer. Expected count is shots multiplied by probability. An expectation is not a promise for one random batch. This example illustrates arithmetic; use run facts for the learner's actual counts.

Background: [Preskill, measurement and repeated preparations](https://www.preskill.caltech.edu/ph219/chap2_15.pdf). Frequencies are independently calculated.

## x-gate

X exchanges the two amplitudes: (α,β) becomes (β,α). It maps |0⟩ to |1⟩ and |1⟩ to |0⟩. Applying X twice restores the input. In a circuit, read operations in the displayed execution order; the latest gate acts on the state produced by earlier operations.

Source: [IBM X gate](https://quantum.cloud.ibm.com/docs/en/api/qiskit/qiskit.circuit.library.XGate).

## h-gate

H maps |0⟩ to |+⟩=(|0⟩+|1⟩)/√2, and |1⟩ to |−⟩=(|0⟩−|1⟩)/√2. It also maps |+⟩ back to |0⟩ and |−⟩ back to |1⟩. For general amplitudes, H maps (α,β) to ((α+β)/√2,(α−β)/√2). H is not a random operation; randomness arises when a measurement has uncertain outcomes.

Source: [IBM H gate](https://quantum.cloud.ibm.com/docs/en/api/qiskit/qiskit.circuit.library.HGate).

## z-gate

Z changes (α,β) to (α,−β). Immediate computational-basis probabilities remain unchanged because amplitude magnitudes stay the same. Whether this sign matters to later operations depends on the state and the later operations. Z on |1⟩ changes the whole state only by a global minus sign; Z on |+⟩ creates |−⟩.

Source: [IBM Z gate](https://quantum.cloud.ibm.com/docs/en/api/qiskit/qiskit.circuit.library.ZGate).

## phase

A common phase factor multiplying every amplitude of the entire state is global phase. Such statevectors describe the same physical state. A relative phase difference between populated components can change later interference. Equal probabilities in one measurement basis do not imply that two states are identical. Do not infer that every phase may be dropped from a controlled operation: a conditional phase can be relative in a larger system.

Source: [IBM global phase and limitations](https://quantum.cloud.ibm.com/learning/en/courses/basics-of-quantum-information/quantum-circuits/limitations-on-quantum-information).

## interference

Compute amplitudes by adding contributions first, then calculate probabilities from squared magnitudes. From |0⟩, H→H returns |0⟩. From |0⟩, H→Z→H gives |1⟩. The Z step changes the relative sign while leaving immediate Z probabilities unchanged; the last H turns that difference into different output probabilities.

Worked arithmetic: with a=1/√2, H(a,a)=(1,0), while H(a,−a)=(0,1). If an actual projective Z measurement is inserted between two H gates, each conditional branch gives equal final Z probabilities after the last H. Inspecting a saved simulator snapshot does not insert a measurement.

Sources: [IBM H matrix](https://quantum.cloud.ibm.com/docs/en/api/qiskit/qiskit.circuit.library.HGate), [Preskill measurement postulate](https://www.preskill.caltech.edu/ph219/chap2_15.pdf). These are worked applications, not observed run data.

## grover-connection

The preview uses a predicate with exactly one marked item among N candidates. Standard Grover prepares a uniform state, phase-marks the target, applies diffusion, and repeats before measurement. Under the stated ideal assumptions, P(target)=sin²((2k+1)θ) with θ=arcsin(1/√N). More iterations can reduce success after passing a probability peak.

The oracle step illustrates why a phase change can matter even before immediate probability bars change. Full oracle construction and diffusion are taught later. The preview's query comparison is not a wall-clock speed claim about a classical simulator. The toy target selector defines the oracle instance; it does not prove that searching for an already-known answer is useful.

Sources: [IBM Grover analysis](https://quantum.cloud.ibm.com/learning/en/courses/fundamentals-of-quantum-algorithms/grover-algorithm/analysis), [unstructured search model](https://quantum.cloud.ibm.com/learning/en/courses/fundamentals-of-quantum-algorithms/grover-algorithm/unstructured-search).

## shor-connection

The Shor preview is a conceptual story. For base 2 modulo 15, the powers repeat 1,2,4,8 with order 4. Given that valid order, gcd(4−1,15)=3 and gcd(4+1,15)=5. The quantum method connects order finding to phase estimation; classical reconstruction and verification remain necessary. Factoring 15 in a storyboard is not a demonstration of practical quantum speed advantage.

Source: [IBM Shor's algorithm](https://quantum.cloud.ibm.com/learning/en/courses/fundamentals-of-quantum-algorithms/phase-estimation-and-factoring/shor-algorithm). The small modular/gcd example is independently worked.

## local-states

An entangled qubit still has a local reduced density matrix. In a Bell pair, each qubit's local state is maximally mixed, I/2, with a zero-length Bloch vector. For a known pure bipartite joint state, a mixed reduced state demonstrates entanglement. A mixed local state alone does not prove that an arbitrary mixed joint state is entangled. The joint state must be considered.

Sources: [IBM multiple systems](https://quantum.cloud.ibm.com/learning/en/courses/basics-of-quantum-information/multiple-systems/quantum-information), [IBM Bloch sphere](https://quantum.cloud.ibm.com/learning/en/courses/general-formulation-of-quantum-information/density-matrices/bloch-sphere).

## platform-help

Run creates a new experiment. Replay shows the saved experiment, including its recorded outcomes. Reset preset restores the authored settings. The Course page shows the recommended learning route. Coming soon means a chapter is not yet implemented; Prerequisites needed means published assessed work requires specified evidence. The tutor explains and hints; the task evaluator determines correctness. Guest progress belongs to the current saved browser session, with the limitations explained in the app.

Source: authored product behavior specified in docs/BUILD-GUIDE.md. This passage must be updated if the implemented behavior changes.
