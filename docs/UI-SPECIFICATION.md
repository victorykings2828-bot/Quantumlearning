# UI specification derived from the supplied reference

## 1. Actual reference

Primary image: `ui-reference/editor-solved_1.png`. Original dimensions: **2880 × 4626 pixels**. Use it as the visual language and laboratory composition, not a requirement to copy every sentence or interaction.

The image shows a warm cream page, a large left-aligned two-line serif heading, a small uppercase brick-red eyebrow, slate introductory copy, and a short red divider. Below is a scientific editor with a narrow control/exercise column and a wide stacked-results column. Panels use nearly white surfaces, thin warm-gray borders, modest corners, compact headers, small uppercase badges, and restrained shadows. Primary buttons and selected steps are dark navy. The wordmark has a square navy Q mark. Plot fills are muted blue; negative amplitudes use rust red. Success and hint blocks use pale green and beige surfaces.

Carry this design across introduction, course overview, lessons, and lab. Do not replace it with a neon dashboard, purple gradients, glass panels, or generic AI illustrations.

## 2. Initial design tokens

These are approximate starting values inferred from the image, not claimed pixel samples. Tune against actual browser renders.

| Token | Starting value | Use |
|---|---|---|
| Page | `#EFEDE4` | Warm cream background |
| Panel | `#FCFAF6` | Cards and navigation |
| Border | `#D8D1C1` | Outlines and separators |
| Text | `#20252A` | Main text |
| Secondary | `#576579` | Labels; verify contrast |
| Navy | `#20364B` | Buttons and selected step |
| Red | `#B7442E` | Eyebrow and negative amplitude cue |
| Blue fill | `#C7D8E8` | Probability/count fills |
| Success fill | `#DCE9E1` | Correct feedback |
| Success text | `#28664B` | Success label |

Use a readable serif stack for display headings, sans-serif for body/controls, and monospace for amplitudes, bit strings, and provenance. System fonts are acceptable initially; self-host licensed fonts if added. Suggested spacing: 4, 8, 12, 16, 24, 32, 48, 64 px. Panel radius approximately 8 px; buttons 4–6 px. Body text at least 16 px. Prefer borders over heavy shadows.

## 3. Required screens

**Introduction:** reuse eyebrow/serif-title/body/divider hierarchy. Suggested heading: “Learn quantum algorithms. See each step.” Explain the product, then place classical/Grover comparison in instrument panels. Final primary CTA: **Explore the course** → `/course`. For returning guests offer a secondary Resume action. The screenshot's circuit-editor headline is not appropriate as the only explanation of the platform.

**Course overview:** use editorial chapter rows or compact bordered sections. Show number, title, outcome, availability, prerequisites, topic count, and actual progress. Expand Chapter 1 into eight topic rows. Primary action: Start Chapter 1 or Continue Topic 1.x. Future chapters show Coming soon without nonfunctional Start buttons.

**Lesson laboratory:** retain two-column character: approximately 28–32% instructions/controls and 68–72% experiment on wide screens. Left: topic, prediction/task, gate/input controls, hints. Right: circuit, playback, amplitude/probability inspection, shot results, explanation of selected step. Keep controls near the affected views.

**Persistent tutor:** a shared-shell Ask the course tutor launcher opens a side drawer on wide screens or a labeled sheet/tab on mobile. Preserve the current experiment. Do not force three narrow columns. Show topic/run scope and visibly label historical run answers. The composer remains accessible from introduction, course, lesson, and progress pages.

**Assessment:** reuse typography, panels, and navy actions. Clearly label test mode and allowed help. Save answers, protect against accidental navigation loss, and show actual score plus skill-specific revision after submission. Success styling follows the evaluator result.

## 4. Correct problems visible in the image

| Visible detail | Required correction |
|---|---|
| Navigation crosses the middle of the screenshot, covering content | Proper top sticky header with reserved space; mobile menu must not obscure charts. |
| Unused vertical region before left controls | Align task/instruction areas with the experiment start. |
| Entangled qubits described as having “no state of their own” | Say each qubit has a **mixed reduced state**; the pair has a joint entangled state. For the shown Bell state each reduced density matrix is I/2 and Bloch-vector length is zero. |
| Shrunken Bloch vector treated as universal proof of entanglement | For a verified pure bipartite joint state, a mixed reduced state establishes entanglement. Mixed local states alone do not prove entanglement for arbitrary mixed joint states. |
| H described as converting any “even mix” to a definite value | Specify H maps `\|0⟩ ↔ \|+⟩` and `\|1⟩ ↔ \|−⟩`; equal Z probabilities alone do not imply this behavior. |
| “Chance = amplitude²” | “Probability = squared magnitude of amplitude”; simple squaring is sufficient only in the real-amplitude examples. |
| 129/127 counts beside rounded 50% labels | Separate exact theory (50%/50%) from observed frequencies (50.39%/49.61% for 256 shots). |
| “Graded by simulator” | “Checked against the task rubric”; the engine computes and the evaluator grades. |
| Footer claims no grades/mastery/unlocks | Update because this requested demo includes assessments and evidence-based progress. |
| Small offline circuit chatbot only at the page bottom | Replace with the requested persistent contextual tutor and honest authored-help fallback. |
| Bell challenge presented prominently | Keep it optional in the sandbox; Chapter 1's assessed path is one-qubit foundations. |

Scientific corrections are supported by the researched blueprint's linked IBM multiple-system, Bloch-sphere, and Hadamard references. The image is a visual input, not a scientific authority.

## 5. Navigation and responsive behavior

Prefer **Introduction**, **Course**, **Quantum Lab**, and **Progress**, plus contextual Tutor access. Keep Grover and Shor inside introduction/lab rather than giving every preview a permanent primary navigation item. Preserve the compact navy wordmark style.

Start with maximum content width around 1200–1280 px and intentional margins. On narrow screens collapse the lab into labeled sections/tabs while preserving selected state. Scroll wide tables inside their panels, not the whole page. Source citations should open a local passage detail or safe external source link without discarding the learner's work.

## 6. Visual acceptance

Capture introduction, course overview, Topic 1.7, Grover, and assessment results at 1440, 1024, and 390 px widths. Compare the actual app with the image and document intentional deviations. Verify visible focus, adequate contrast, non-color cues, readable math, reduced motion, focus restoration after tutor close, no clipped equations, no overlapping header, and no inaccessible chat composer. Visual similarity must coexist with a usable learning flow.
