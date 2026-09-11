---
id: math-prerequisites
version: 1
title: Course arithmetic and notation the lessons rely on
audience: learner
status: authored
topics: [intro, bridge, ch1-1, ch1-2, ch1-3, ch1-4, ch1-5, ch1-6, ch1-7, ch1-8]
---

# Tutor knowledge: course mathematics

This file covers the arithmetic and notation Chapter 1 assumes. A question about this material is in scope even when it contains no quantum vocabulary, because the course needs it.

## fractions-and-percentages

A fraction can be read as a proportion of a whole. 1/4 is one part in four, which is 0.25 or 25%. 3/5 is 0.6 or 60%. To convert a fraction to a percentage, divide and multiply by 100.

Probabilities in this course are written as fractions, decimals, or percentages interchangeably. 1/2, 0.5, and 50% are the same number.

## squares-and-roots

Squaring a number multiplies it by itself. (3/5)^2 = 9/25 = 0.36. (4/5)^2 = 16/25 = 0.64.

A square root undoes a square. (1/sqrt(2))^2 = 1/2, because the square root of 2 multiplied by itself is 2, leaving 1/2. This particular value appears constantly in this course, because 1/sqrt(2) is approximately 0.7071 and its square is exactly one half.

## signed-numbers

Squaring a negative number gives a positive result: (-1/2)^2 = 1/4, the same as (1/2)^2. (-3/5)^2 = 9/25, the same as (3/5)^2.

This is the arithmetic reason a negative amplitude produces a positive probability. The sign is real and it is part of the state description, but squaring the magnitude removes it from the probability.

## probability-totals

A distribution over two outcomes needs non-negative values summing to 1. 0.2 and 0.8 is valid. 0.36 and 0.64 is valid. 0.25 and 0.25 is not, because it sums to 1/2 and leaves half the probability unaccounted for.

Expected count is the number of trials multiplied by the probability. 100 trials at probability 0.64 has expected count 64. An expectation is an average over many repetitions of the whole experiment, not a promise about any single batch.

## vectors-and-notation

A one-qubit state is written as a pair of numbers, (a, b), called an amplitude vector. The ket notation |psi> = a|0> + b|1> says the same thing. The first entry belongs to outcome 0 and the second to outcome 1.

Square brackets, parentheses, and column layout are all used for the same object in different textbooks. This course writes it as an ordered pair and labels each entry with its outcome.

## ordered-operations

Operations in a circuit happen in the order they are drawn, left to right. Two operations that each undo themselves cancel when applied consecutively: two swaps of a classical bit return its original value, and two X gates return the original qubit state.

When a matrix expression is written for a circuit, the order reverses: the circuit H then Z has the matrix expression ZH, because the matrix applied last is written first. This course uses circuit order with arrows, so H -> Z always means H happens first.
