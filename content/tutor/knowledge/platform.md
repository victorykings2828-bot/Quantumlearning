---
id: platform
version: 1
title: Using the Quantum Learning Laboratory
audience: learner
status: authored
topics: [intro, platform, grover-preview, shor-preview, ch1-1, ch1-2, ch1-3, ch1-4, ch1-5, ch1-6, ch1-7, ch1-8]
---

# Tutor knowledge: using this platform

## controls

**Run** computes a new experiment from the current circuit and settings. Each shot restarts the declared preparation.

**Play** and **Pause** move the view through the computed steps at a viewing pace. Playback speed is a viewing control. It is not a measure of how fast anything executes, and it is not quantum execution time.

**Next step** and **Previous step** select a saved frame. Previous step reads history. It does not physically undo a measurement.

**Replay** shows a saved run again, including the outcomes it actually recorded. It is not a new measurement.

**Reset preset** restores the authored starting settings for the topic and keeps your earlier saved runs.

**Compare** keeps two runs side by side with their parameters and provenance so you can see which settings produced which numbers.

## panels

The **amplitude** panel shows the signed or complex value for each basis outcome. The **probability** panel shows exact model probabilities computed from the circuit. The **counts** panel shows observed results from your shots. These are three different objects and the app never mixes them into one chart.

When an amplitude's magnitude is zero, its phase is undefined and the app shows a dash rather than inventing an angle.

Every panel on screen shares one circuit revision, run, branch, and selected step. If you edit the circuit while a result is still arriving, the app discards the stale result rather than showing it beside the new circuit.

## result-labels

**Ideal circuit simulation** means a declared circuit was numerically evolved under the ideal noiseless model. **Sampled simulator outcomes** means measurements were sampled from that model. **Analytical prediction** means a value came from a formula under stated assumptions, not from running a circuit. **Conceptual walkthrough** means a storyboard explains a mechanism without executing the algorithm.

## progress-and-access

The Course page shows the recommended route. **Coming soon** means a chapter is not implemented yet; there is no hidden lesson behind the label. **Prerequisites needed** means published assessed work requires specific demonstrated evidence, and the app names which skills are missing.

Chapter descriptions and algorithm previews are always browsable and never require prior mastery.

Progress separates three things: activity completion, which you may reach with help; independent evidence, which comes from unassisted success on a new item; and review recommendations, which suggest practice without erasing past achievement.

## tutor-scope-and-limits

The tutor explains and hints. The authored evaluator determines correctness, and it runs on the server without the tutor's involvement. The tutor cannot assign grades, change mastery, unlock chapters, or read another learner's data.

During an unassisted test the tutor answers navigation, accessibility and wording questions only. Asking for substantive help moves the attempt to practice first, and the platform records that assistance.

## guest-sessions

This demo has no sign-up. A private guest session is created on your first visit and your progress, runs, attempts and tutor history are saved against it on the server.

That session lives in this browser. Clearing site data, using private browsing, or switching device will not carry the progress across, and an anonymous session cannot be recovered once its cookie is gone. Reset my demo progress clears the current guest's records and nobody else's.
