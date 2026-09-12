---
id: chapter-2
title: Geometry and measurement bases
version: 2
topics: ch2-1,ch2-2,ch2-3,ch2-4,ch2-5,ch2-6
---

## topic-2-1

An amplitude a+ib has squared magnitude a²+b². The imaginary unit satisfies i²=−1, but a probability uses the squared magnitude, never the square of i alone. A phase rotates the amplitude arrow without changing its length. A common phase rotates the whole state without changing any measurement statistics; relative phase can change interference.

[IBM Quantum Learning](https://quantum.cloud.ibm.com/learning/en/courses/basics-of-quantum-information/single-systems/quantum-information)

## topic-2-2

A state is a column vector. X swaps its entries; Z changes the sign of the second entry; H maps (a,b) to ((a+b)/√2,(a−b)/√2). Applying X then H means HX|ψ⟩ because the rightmost matrix acts first. Gates need not commute. Starting at |0⟩, X then H gives |−⟩ while H then X gives |+⟩. Both have equal Z probabilities, so inspect phase or measure in X.

[IBM Quantum Learning](https://quantum.cloud.ibm.com/learning/en/courses/basics-of-quantum-information/single-systems/quantum-information)

## topic-2-3

A pure qubit can be written cos(θ/2)|0⟩ + e^(iφ)sin(θ/2)|1⟩. Its Bloch coordinates are (sinθ cosφ, sinθ sinφ, cosθ). |0⟩ is north, |1⟩ south; |+⟩ lies on +x and |+i⟩ on +y. This sphere represents a state mathematically, not an electron orbit. Global phase has no separate point. Mixed states lie inside the sphere.

[IBM Quantum Learning](https://quantum.cloud.ibm.com/learning/en/courses/basics-of-quantum-information/single-systems/quantum-information)

## topic-2-4

P(φ)=diag(1,e^(iφ)) changes relative phase. Rz(φ)=diag(e^(−iφ/2),e^(iφ/2)) differs from P only by a global phase for this single-qubit comparison. H→P(φ)→H converts phase into a Z distribution: P0=cos²(φ/2), P1=sin²(φ/2). Ry rotates through real superpositions. A diagram transition is not a measured trajectory.

[IBM Quantum Learning](https://quantum.cloud.ibm.com/learning/en/courses/basics-of-quantum-information/single-systems/quantum-information)

## topic-2-5

Measurement asks a question in a chosen basis. X has eigenstates |+⟩ and |−⟩; Y has (|0⟩±i|1⟩)/√2. To implement X readout using Z measurement, apply H first. For Y, execute S† then H. The returned 0/1 labels mean the +1/−1 eigenvalues of the chosen observable. Readout rotates the state; distinguish its final physical state from the original-basis projected state.

[IBM Quantum Learning](https://quantum.cloud.ibm.com/learning/en/courses/basics-of-quantum-information/single-systems/quantum-information)

## topic-2-6

A single histogram does not identify a quantum state. |+⟩, |−⟩ and |+i⟩ have the same Z probabilities. X distinguishes plus and minus; Y reveals the imaginary relative phase. Repeated preparations let us estimate x=P_X(+)-P_X(−), and similarly y and z. Finite samples have uncertainty; a single shot cannot determine an arbitrary unknown state.

[IBM Quantum Learning](https://quantum.cloud.ibm.com/learning/en/courses/basics-of-quantum-information/single-systems/quantum-information)
