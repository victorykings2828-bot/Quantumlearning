# Implementation notes

Short record of the decisions that are not obvious from the code, for whoever
picks this up next.

## Why the engine returns branches rather than one state

A circuit containing a real `measure_z` produces conditional trajectories, not
a single state. The engine returns one frame per branch with its branch
probability, plus a separate ensemble distribution. Topic 1.7 depends on this:
H → Measure → H must show both conditional branches and an ensemble summary,
and must not be confused with H → Z → H.

## Why shots are sampled per trajectory

Sampling from the final distribution would be wrong for any circuit with a
mid-circuit measurement. Each shot walks the whole circuit, sampling at each
measurement, because a shot restarts the preparation.

## Why the evaluator never reads counts for a probability goal

A 50/50 goal is checked against `exact_probabilities`, which comes from the
circuit. A sampled histogram is never consulted, so a learner can never fail a
task by getting an unlucky sample.

## Why state goals use fidelity

`states_equivalent` compares |⟨a|b⟩|², so a global phase cancels. `X → Z` from
|0⟩ reaches −|1⟩, which is the same physical state as |1⟩ and passes a |1⟩
state goal. A distribution goal uses probabilities only and makes no claim
about the state.

## Why hints are not in the public topic payload

`public_topic` strips `hints` and adds `hint_levels`. A learner who reads the
network response cannot see the worked solution without requesting it, and the
request records the assistance, which is what separates independent evidence
from assisted completion.

## Why the tutor's scope decision happens before the provider call

An unrelated request never reaches the model at all. Scope classification
combines retrieval grounding, approved concept metadata, discourse context and
task-intent detection; a capability request (change my grade, show another
learner's answers) is answered from authored text without a model call.

## Why provider output is validated against a server-built envelope

The server knows which passage IDs and fact IDs it supplied. Any other ID in
the response is a fabrication, and the answer is rejected in favour of authored
help. Numerical claims about a run use `[[fact:ID]]` references that the server
substitutes from the engine result, so the model cannot state a number the run
did not produce.

## Why topic progress uses an upsert

Two requests can touch a topic for the first time simultaneously. Creating the
row with `ON CONFLICT DO NOTHING` and re-selecting means neither request fails.
Step completion merges inside the database for the same reason.

## Where the answer keys live

`content/assessments/` holds the rubrics and the answer key. Nothing in
`content/curriculum/` contains an answer. `loader.public_assessment()` strips
the key, and a test asserts that no learner endpoint response contains it.
