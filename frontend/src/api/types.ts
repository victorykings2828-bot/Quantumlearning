/**
 * Domain types used by the UI.
 *
 * These mirror the committed OpenAPI contract in src/api/schema.d.ts. The
 * generated file is the contract of record; these aliases keep the components
 * readable where the generated response objects are loosely typed dictionaries.
 */

export type ResultKind =
  | 'ideal_circuit_simulation'
  | 'sampled_simulator_outcomes'
  | 'analytical_prediction'
  | 'conceptual_walkthrough';

export type Publication = 'published' | 'coming_soon';
export type Readiness = 'ready' | 'prerequisites_needed' | 'not_assessed';

export interface AccessDecision {
  publication: Publication;
  readiness: Readiness;
  reason_code: string;
  reason: string;
  missing_skills: string[];
}

export interface AmplitudeView {
  index: number;
  label: string;
  re: number;
  im: number;
  magnitude: number;
  probability: number;
  phase_radians: number | null;
}

export interface ReducedQubitState {
  qubit: number;
  bloch: [number, number, number];
  bloch_length: number;
  purity: number;
  is_mixed: boolean;
}

export interface StateFrame {
  step_index: number;
  branch_id: string;
  branch_probability: number;
  kind: 'preparation' | 'unitary' | 'measurement';
  operation: string | null;
  label: string;
  amplitudes: AmplitudeView[];
  probabilities: number[];
  measured_outcome: number | null;
  measured_qubit: number | null;
  reduced_states: ReducedQubitState[];
}

export interface BranchSummary {
  branch_id: string;
  probability: number;
  outcomes: number[];
}

export interface RunResult {
  result_kind: ResultKind;
  engine: string;
  engine_version: string;
  circuit_schema_version: string;
  qubits: number;
  frames: StateFrame[];
  branches: BranchSummary[];
  exact_probabilities: number[];
  basis_labels: string[];
  counts: Record<string, number>;
  shots: number;
  seed: number | null;
  notes: string[];
}

export interface RunRecord {
  run_id: string;
  revision_id: string;
  ordinal: number;
  label: string;
  shots: number;
  seed: number | null;
  engine: string;
  engine_version: string;
  created_at: string;
  result: RunResult;
  context?: Record<string, unknown>;
  read_kind?: string;
  replay_note?: string;
}

export interface GroverRunRecord extends RunRecord {
  stages: { name: string; end_step: number }[];
  target: number;
  candidates: number;
  analytical_target_probability: number | null;
  formula_applies: boolean;
  formula_note?: string;
  oracle_query_count: number;
  cost_note: string;
}

export type OperationName = 'x' | 'h' | 'z' | 'cx' | 'cz' | 'mcz' | 'measure_z';

export interface Operation {
  op: OperationName;
  targets: number[];
  controls: number[];
}

export type InitialStateName = 'ket0' | 'ket1' | 'plus' | 'minus' | 'card_b' | 'card_c';

export interface CircuitSpec {
  schema_version: 'circuit/v1';
  qubits: number;
  initial_state: {
    kind: 'basis' | 'named' | 'amplitudes';
    basis_index?: number;
    named?: InitialStateName | null;
    amplitudes?: { re: number; im: number }[] | null;
  };
  operations: Operation[];
}

export interface TaskOption {
  id: string;
  label: string;
}

export interface TopicTask {
  id: string;
  kind: string;
  title: string;
  prompt: string;
  assessed_skills: string[];
  item_family: string;
  options?: TaskOption[];
  fields?: { id: string; label: string; placeholder?: string; kind?: string }[];
  left?: TaskOption[];
  right?: TaskOption[];
  categories?: TaskOption[];
  items?: TaskOption[];
  parts?: { id: string; kind: string; prompt: string; options: TaskOption[] }[];
  goal_kind?: string;
  constraints?: Record<string, unknown>;
  acceptance_note?: string;
  tolerance?: number;
  free_text?: { enabled: boolean; prompt: string; graded: boolean };
  records_preview_note?: string;
}

export interface TopicStep {
  id: string;
  title: string;
  instruction: string;
}

export interface TopicLab {
  mode: string;
  qubits: number;
  initial_state_options: InitialStateName[];
  gate_palette: OperationName[];
  max_gates: number;
  shot_options: number[];
  default_shots: number;
  panels: string[];
  features: Record<string, boolean>;
  cards?: {
    id: string;
    state: InitialStateName | null;
    amplitudes: string;
    probabilities: string;
    valid: boolean;
    note: string;
  }[];
  comparison?: {
    left: { label: string; operations: OperationName[] };
    right: { label: string; operations: OperationName[] };
  };
  equivalent_notation_note?: string;
}

export interface Topic {
  id: string;
  slug: string;
  number: string;
  title: string;
  objective: string;
  learning_objectives: string[];
  prerequisite_skills: string[];
  skills: string[];
  estimated_minutes: number;
  teach_markdown: string;
  sources: { id: string; title: string; url: string }[];
  lab: TopicLab;
  prediction: { id: string; prompt: string; kind: string; options: TaskOption[] };
  steps: TopicStep[];
  tasks: TopicTask[];
  traces?: Record<string, string>[];
  misconceptions?: { id: string; trigger: string; response: string }[];
  completion: { required_step_ids: string[]; required_task_ids: string[] };
  hint_levels: number;
  previous_topic_id: string | null;
  next_topic_id: string | null;
  notation_contract: string;
  content_version: number;
  access: AccessDecision;
  progress?: TopicSummary;
  completed_steps: Record<string, boolean>;
  recorded_prediction: { prediction_id: string; selection: string } | null;
  passed_task_ids: string[];
  future_payoff?: string;
  author_caution?: string;
  revisit?: Record<string, string>;
}

export interface TopicSummary {
  topic_id: string;
  number: string;
  title: string;
  slug: string;
  status: 'not_started' | 'in_progress' | 'complete';
  steps_completed: number;
  steps_required: number;
  tasks_passed: number;
  tasks_required: number;
  skills: string[];
  prerequisite_skills: string[];
  estimated_minutes: number | null;
}

export interface ChapterEntry {
  id: string;
  number: number;
  title: string;
  outcome: string;
  subtopic_titles: string[];
  topic_count: number;
  prerequisite_skills: string[];
  publication: Publication;
  demonstration: string;
  coming_soon_note: string | null;
  access: AccessDecision;
  progress?: { topics_complete: number; topics_total: number; next_topic_id: string | null };
  topics?: TopicSummary[];
}

export interface CourseResponse {
  id: string;
  title: string;
  subtitle: string;
  route_note: string;
  chapters: ChapterEntry[];
  browsing_note: string;
  skill_labels: Record<string, string>;
  skill_label_note: string;
}

export interface SkillProgress {
  skill_id: string;
  demonstrated: boolean;
  independent_count: number;
  assisted_count: number;
  item_families: string[];
  required_independent: number;
  required_families: number;
}

export interface ChapterProgress {
  chapter_id: string;
  topics: TopicSummary[];
  topics_complete: number;
  topics_total: number;
  skills: SkillProgress[];
  next_topic_id: string | null;
}

export interface TaskResult {
  task_id: string;
  passed: boolean;
  reason_code: string;
  message: string;
  detail: Record<string, unknown>;
  assisted: boolean;
  evidence_kind: string;
  hints_used: number;
  duplicate: boolean;
  topic_status: string;
  next_task_id: string | null;
  assessed_skills: string[];
}

export interface TutorCitation {
  passage_id: string;
  title: string;
  version: number;
  sources: { title: string; url: string }[];
}

export interface TutorAnswer {
  intent: 'answer' | 'hint' | 'clarify' | 'redirect';
  answer_markdown: string;
  citations: TutorCitation[];
  fact_ids: string[];
  facts: { id: string; label: string; value: string }[];
  followup_question: string | null;
  source_label: string;
  provider: string | null;
  provider_model: string | null;
  latency_ms: number | null;
  scope_reason: string;
  run_id: string | null;
  run_label: string | null;
  step_index: number | null;
  notice: string | null;
  policy_version: number;
}
