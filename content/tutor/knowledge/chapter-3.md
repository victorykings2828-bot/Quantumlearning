---
id: chapter-3
title: Multiple qubits and entanglement
version: 2
topics: ch3-1,ch3-2,ch3-3,ch3-4,ch3-5,ch3-6,ch3-7
---

## topic-3-1

Qubit q0 is the least significant bit and top wire. Two-qubit strings are written |q1 q0⟩. Starting at |00⟩, flipping q0 produces |01⟩ at vector index 1; flipping q1 produces |10⟩ at index 2. For three qubits, |q2 q1 q0⟩=|101⟩ is index 5. The label convention is bookkeeping, not a physical difference between qubits.

[IBM Quantum Learning](https://quantum.cloud.ibm.com/learning/en/courses/basics-of-quantum-information/multiple-systems/quantum-information)

## topic-3-2

For q1=(a,b) and q0=(c,d), the joint amplitude vector is (ac,ad,bc,bd). Multiply amplitudes first, then square magnitudes for probabilities. For q1=|+⟩ and q0=|1⟩, only 01 and 11 occur equally. Independent product preparations have factorized probabilities for local measurements; four amplitudes do not mean four independently readable classical bits.

[IBM Quantum Learning](https://quantum.cloud.ibm.com/learning/en/courses/basics-of-quantum-information/multiple-systems/quantum-information)

## topic-3-3

CX flips its target when the control is 1, and acts linearly on a superposition. With q0 controlling q1 it maps 01 to 11 and 11 to 01. A controlled gate does not always produce entanglement: CX leaves |00⟩ and |++⟩ as product states. To make entanglement, both the preparation and operation matter.

[IBM Quantum Learning](https://quantum.cloud.ibm.com/learning/en/courses/basics-of-quantum-information/multiple-systems/quantum-information)

## topic-3-4

H(q0) on |00⟩ gives (|00⟩+|01⟩)/√2. CX(q0,q1) then gives Φ+=(|00⟩+|11⟩)/√2. Each individual qubit has the mixed reduced state I/2, although the pair is pure. Matching Z results alone is insufficient evidence: a classical mixture of 00 and 11 matches that chart. Compare X statistics to distinguish those two preparations.

[IBM Quantum Learning](https://quantum.cloud.ibm.com/learning/en/courses/basics-of-quantum-information/multiple-systems/quantum-information)

## topic-3-5

A joint chart retains how outcomes occur together. A marginal sums over the other qubit. For .6|00⟩+.8|11⟩, P00=.36 and P11=.64, so each qubit has P1=.64. Conditional on measuring q0=0, q1=0 with certainty. Identical local 50/50 charts can hide very different correlations. Conditioning on an event of zero probability is undefined.

[IBM Quantum Learning](https://quantum.cloud.ibm.com/learning/en/courses/basics-of-quantum-information/multiple-systems/quantum-information)

## topic-3-6

A density matrix describes both pure states and probabilistic mixtures. The mixture ½|00⟩⟨00|+½|11⟩⟨11| has no off-diagonal coherence. Φ+ does. They agree in Z and disagree in X. A zero local Bloch vector means a maximally mixed reduced state, not no state. Local mixedness proves entanglement only when the joint state is known pure; mixed separable states can also have mixed marginals.

[IBM Quantum Learning](https://quantum.cloud.ibm.com/learning/en/courses/basics-of-quantum-information/multiple-systems/quantum-information)

## topic-3-7

Alice has unknown input q0 and q1 of a Bell pair; Bob has q2. Alice applies CX(q0,q1), H(q0), then measures q0 into m0 and q1 into m1. Bob applies X if m1=1 and then Z if m0=1. All four branches restore the input state on Bob. The original is consumed, not copied. Bob needs two classical bits; before learning them his reduced state is I/2, so this does not send usable information faster than light.

[IBM Quantum Learning](https://quantum.cloud.ibm.com/learning/en/courses/basics-of-quantum-information/multiple-systems/quantum-information)
