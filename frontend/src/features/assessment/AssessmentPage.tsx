import { useCallback, useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { api, ApiError } from '@/api/client';
import { useApiQuery } from '@/app/useApi';
import { ErrorBanner, Loading, PageHeader, Panel } from '@/components/primitives';
import type { CircuitSpec, OperationName } from '@/api/types';
import { useTutor } from '@/features/tutor/TutorContext';
import { CircuitEditor, buildCircuit } from '@/features/lesson/CircuitEditor';

interface AssessmentItem {
  number: number;
  id: string;
  kind: string;
  prompt: string;
  assessed_skills: string[];
  item_family: string;
  options?: { id: string; label: string }[];
  fields?: { id: string; label: string; placeholder?: string }[];
  categories?: { id: string; label: string }[];
  items?: { id: string; label: string }[];
  parts?: {
    id: string;
    kind: string;
    prompt: string;
    options: { id: string; label: string }[];
  }[];
  constraints?: Record<string, unknown>;
  goal_kind?: string;
}

interface AssessmentResponse {
  title: string;
  items_per_form: number;
  pass_policy: {
    minimum_score: number;
    essential_item_numbers: number[];
    requires_practice_complete: boolean;
    note: string;
    numeric_tolerance: number;
  };
  test_mode_help: string;
  practice_complete: boolean;
  practice_note: string;
  forms: Record<string, AssessmentItem[]>;
  attempts: { attempt_id: string; form: string; mode: string; status: string }[];
}

interface AttemptResponse {
  attempt_id: string;
  form: string;
  mode: string;
  status: string;
  answers: Record<string, unknown>;
  items: AssessmentItem[];
  pass_policy: AssessmentResponse['pass_policy'];
  test_mode_help: string;
}

interface ResultResponse {
  attempt_id: string;
  score: number;
  max_score: number;
  passed: boolean;
  essential_items_passed: boolean;
  practice_complete: boolean;
  per_item: {
    item_id: string;
    number: number;
    passed: boolean;
    assessed_skills: string[];
  }[];
  revision_guidance: { skill_id: string; advice: string }[];
  duplicate: boolean;
}

export function AssessmentPage() {
  const { data, loading, error, reload } =
    useApiQuery<AssessmentResponse>('/assessments/chapter-1');
  const [attempt, setAttempt] = useState<AttemptResponse | null>(null);
  const [answers, setAnswers] = useState<Record<string, unknown>>({});
  const [result, setResult] = useState<ResultResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [saveState, setSaveState] = useState<'idle' | 'saving' | 'saved'>('idle');
  const [pageError, setPageError] = useState<string | null>(null);
  const saveTimer = useRef<number | null>(null);
  const pending = useRef<Record<string, unknown> | null>(null);
  const { setContext } = useTutor();

  useEffect(() => {
    setContext({ topicId: null, runId: null, runLabel: null, stepIndex: null, mode: 'test' });
    return () => setContext({ mode: 'practice' });
  }, [setContext]);

  useEffect(() => {
    if (attempt) {
      setContext({ mode: attempt.mode === 'test' ? 'test' : 'practice' });
    }
  }, [attempt, setContext]);

  // Answers are saved on the server so a reload or an accidental navigation
  // does not lose them.
  const scheduleSave = useCallback(
    (next: Record<string, unknown>) => {
      if (!attempt || attempt.status !== 'in_progress') return;
      if (saveTimer.current) window.clearTimeout(saveTimer.current);
      pending.current = next;
      setSaveState('saving');
      saveTimer.current = window.setTimeout(() => {
        api
          .patch(`/assessments/attempts/${attempt.attempt_id}`, { answers: next })
          .then(() => {
            pending.current = null;
            setSaveState('saved');
          })
          .catch(() => setSaveState('idle'));
      }, 400);
    },
    [attempt],
  );

  useEffect(() => {
    if (!attempt || attempt.status !== 'in_progress') return;
    const guard = (event: BeforeUnloadEvent) => {
      if (Object.keys(answers).length > 0 && !result) {
        event.preventDefault();
        event.returnValue = '';
      }
    };
    // If the page is hidden while a save is still debounced, send it now with
    // keepalive so a learner who navigates away does not lose that answer.
    const flush = () => {
      if (!pending.current) return;
      const body = JSON.stringify({ answers: pending.current });
      pending.current = null;
      const csrf = document.cookie
        .split('; ')
        .find((row) => row.startsWith('qll_csrf='))
        ?.slice('qll_csrf='.length);
      void fetch(`/api/v1/assessments/attempts/${attempt.attempt_id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          ...(csrf ? { 'x-qll-csrf': decodeURIComponent(csrf) } : {}),
        },
        credentials: 'same-origin',
        keepalive: true,
        body,
      }).catch(() => undefined);
    };
    window.addEventListener('beforeunload', guard);
    window.addEventListener('pagehide', flush);
    return () => {
      window.removeEventListener('beforeunload', guard);
      window.removeEventListener('pagehide', flush);
      flush();
    };
  }, [attempt, answers, result]);

  if (loading) return <Loading label="Loading the assessment." />;
  if (error) return <ErrorBanner message={error} />;
  if (!data) return null;

  const start = async (form: 'A' | 'B', mode: 'test' | 'practice') => {
    setBusy(true);
    setPageError(null);
    try {
      const response = await api.post<AttemptResponse>('/assessments/chapter-1/attempts', {
        form,
        mode,
      });
      setAttempt(response);
      setAnswers(response.answers ?? {});
      setResult(null);
    } catch (cause) {
      setPageError(cause instanceof ApiError ? cause.message : String(cause));
    } finally {
      setBusy(false);
    }
  };

  const setAnswer = (itemId: string, value: unknown) => {
    const next = { ...answers, [itemId]: value };
    setAnswers(next);
    scheduleSave(next);
  };

  const submit = async () => {
    if (!attempt) return;
    setBusy(true);
    try {
      if (saveTimer.current) window.clearTimeout(saveTimer.current);
      await api.patch(`/assessments/attempts/${attempt.attempt_id}`, { answers });
      const response = await api.post<ResultResponse>(
        `/assessments/attempts/${attempt.attempt_id}/submit`,
      );
      setResult(response);
      reload();
    } catch (cause) {
      setPageError(cause instanceof ApiError ? cause.message : String(cause));
    } finally {
      setBusy(false);
    }
  };

  const convert = async () => {
    if (!attempt) return;
    await api.post(`/assessments/attempts/${attempt.attempt_id}/convert-to-practice`);
    setAttempt({ ...attempt, mode: 'practice' });
  };

  return (
    <>
      <PageHeader
        eyebrow="Chapter 1"
        title={data.title}
        lede={`Ten items, one point each. Pass mark ${data.pass_policy.minimum_score} out of 10, with items ${data.pass_policy.essential_item_numbers.join(', ')} required.`}
      />

      <p className="note">{data.pass_policy.note}</p>
      {!data.practice_complete && <p className="note note--warning">{data.practice_note}</p>}
      {pageError && <ErrorBanner message={pageError} />}

      {!attempt && (
        <Panel title="Choose a form" badge="Two equivalent forms">
          <p>
            Form A and Form B assess the same objectives with different instances. A test
            attempt records independent evidence; a practice attempt records assisted evidence
            and allows substantive help.
          </p>
          <div className="button-row">
            <button
              type="button"
              className="button button--primary"
              onClick={() => void start('A', 'test')}
              disabled={busy}
            >
              Start Form A as a test
            </button>
            <button
              type="button"
              className="button"
              onClick={() => void start('B', 'test')}
              disabled={busy}
            >
              Start Form B as a test
            </button>
            <button
              type="button"
              className="button"
              onClick={() => void start('A', 'practice')}
              disabled={busy}
            >
              Practise with Form A
            </button>
          </div>
          {data.attempts.length > 0 && (
            <>
              <h3>Your attempts</h3>
              <ul>
                {data.attempts.map((entry) => (
                  <li key={entry.attempt_id}>
                    Form {entry.form} · {entry.mode} · {entry.status}
                  </li>
                ))}
              </ul>
            </>
          )}
        </Panel>
      )}

      {attempt && !result && (
        <>
          <Panel
            title={`Form ${attempt.form}`}
            badge={attempt.mode === 'test' ? 'Test mode' : 'Practice mode'}
            badgeTone={attempt.mode === 'test' ? 'navy' : 'warning'}
            actions={
              <span className="badge">
                {saveState === 'saving'
                  ? 'Saving…'
                  : saveState === 'saved'
                    ? 'Answers saved'
                    : 'Answers save as you work'}
              </span>
            }
          >
            <p className="note">{attempt.test_mode_help}</p>
            {attempt.mode === 'test' && (
              <div className="button-row">
                <button
                  type="button"
                  className="button button--small"
                  onClick={() => void convert()}
                >
                  Switch this attempt to practice
                </button>
                <span className="note" style={{ margin: 0 }}>
                  The platform performs this switch and records the assistance. The tutor cannot
                  do it.
                </span>
              </div>
            )}
          </Panel>

          <ol className="assessment-items">
            {attempt.items.map((item) => (
              <li key={item.id}>
                <Panel
                  title={`Item ${item.number}`}
                  badge={
                    data.pass_policy.essential_item_numbers.includes(item.number)
                      ? 'Essential'
                      : undefined
                  }
                  badgeTone="warning"
                >
                  <p>{item.prompt}</p>
                  <ItemInput
                    item={item}
                    value={answers[item.id]}
                    onChange={(value) => setAnswer(item.id, value)}
                  />
                </Panel>
              </li>
            ))}
          </ol>

          <div className="button-row">
            <button
              type="button"
              className="button button--primary"
              onClick={() => void submit()}
              disabled={busy}
            >
              {busy ? 'Submitting…' : 'Submit for marking'}
            </button>
            <span className="note" style={{ margin: 0 }}>
              {Object.keys(answers).length} of {attempt.items.length} items answered.
            </span>
          </div>
        </>
      )}

      {result && (
        <>
          <Panel
            title="Result"
            badge={result.passed ? 'Passed' : 'Not yet passed'}
            badgeTone={result.passed ? 'success' : 'warning'}
          >
            <p className="score">
              {result.score} / {result.max_score}
            </p>
            <ul>
              <li>
                Pass mark {data.pass_policy.minimum_score}:{' '}
                {result.score >= data.pass_policy.minimum_score ? 'met' : 'not met'}
              </li>
              <li>
                Essential items ({data.pass_policy.essential_item_numbers.join(', ')}):{' '}
                {result.essential_items_passed ? 'all correct' : 'at least one incorrect'}
              </li>
              <li>
                Required practice complete: {result.practice_complete ? 'yes' : 'not yet'}
              </li>
            </ul>
            {result.duplicate && (
              <p className="note">
                This attempt was already marked. The original outcome is shown and no extra
                evidence was recorded.
              </p>
            )}
          </Panel>

          <Panel title="Item by item">
            <div className="scroll-x">
              <table className="data-table">
                <thead>
                  <tr>
                    <th className="numeric">Item</th>
                    <th>Outcome</th>
                    <th>Skills assessed</th>
                  </tr>
                </thead>
                <tbody>
                  {result.per_item.map((entry) => (
                    <tr key={entry.item_id}>
                      <td className="numeric">{entry.number}</td>
                      <td>
                        <span
                          className={
                            entry.passed ? 'badge badge--success' : 'badge badge--warning'
                          }
                        >
                          {entry.passed ? 'Correct' : 'Incorrect'}
                        </span>
                      </td>
                      <td className="note" style={{ margin: 0 }}>
                        {entry.assessed_skills.join(', ')}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Panel>

          {result.revision_guidance.length > 0 && (
            <Panel title="What to revise" badge="Skill specific">
              <dl className="definition-list">
                {result.revision_guidance.map((entry) => (
                  <div key={entry.skill_id}>
                    <dt className="mono">{entry.skill_id}</dt>
                    <dd>{entry.advice}</dd>
                  </div>
                ))}
              </dl>
            </Panel>
          )}

          <p className="button-row">
            <Link className="button" to="/progress">
              See your progress
            </Link>
            <button
              type="button"
              className="button"
              onClick={() => {
                setAttempt(null);
                setResult(null);
                setAnswers({});
              }}
            >
              Back to the forms
            </button>
          </p>
        </>
      )}
    </>
  );
}

function ItemInput({
  item,
  value,
  onChange,
}: {
  item: AssessmentItem;
  value: unknown;
  onChange: (value: unknown) => void;
}) {
  if (item.kind === 'single_select' && item.options) {
    return (
      <fieldset className="choice-set">
        <legend className="visually-hidden">{item.prompt}</legend>
        {item.options.map((option) => (
          <label key={option.id} className="choice">
            <input
              type="radio"
              name={item.id}
              checked={value === option.id}
              onChange={() => onChange(option.id)}
            />
            <span>{option.label}</span>
          </label>
        ))}
      </fieldset>
    );
  }

  if (item.kind === 'numeric_fields' && item.fields) {
    const current = (value as Record<string, string>) ?? {};
    return (
      <div className="numeric-fields">
        {item.fields.map((field) => (
          <label key={field.id} className="field">
            <span>{field.label}</span>
            <input
              type="text"
              inputMode="decimal"
              className="inline-input"
              value={current[field.id] ?? ''}
              placeholder={field.placeholder}
              onChange={(event) => onChange({ ...current, [field.id]: event.target.value })}
            />
          </label>
        ))}
      </div>
    );
  }

  if (item.kind === 'classification' && item.items && item.categories) {
    const current = (value as Record<string, string>) ?? {};
    return (
      <div className="matching">
        {item.items.map((entry) => (
          <label key={entry.id} className="field">
            <span className="mono">{entry.label}</span>
            <select
              value={current[entry.id] ?? ''}
              onChange={(event) => onChange({ ...current, [entry.id]: event.target.value })}
            >
              <option value="">Choose…</option>
              {item.categories!.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.label}
                </option>
              ))}
            </select>
          </label>
        ))}
      </div>
    );
  }

  if (item.kind === 'compound' && item.parts) {
    const current = (value as Record<string, string>) ?? {};
    return (
      <div className="stack">
        {item.parts.map((part) => (
          <fieldset key={part.id} className="choice-set">
            <legend>{part.prompt}</legend>
            {part.options.map((option) => (
              <label key={option.id} className="choice">
                <input
                  type="radio"
                  name={`${item.id}-${part.id}`}
                  checked={current[part.id] === option.id}
                  onChange={() => onChange({ ...current, [part.id]: option.id })}
                />
                <span>{option.label}</span>
              </label>
            ))}
          </fieldset>
        ))}
      </div>
    );
  }

  if (item.kind === 'circuit_goal') {
    return (
      <AssessmentCircuit
        item={item}
        value={value as CircuitSpec | undefined}
        onChange={onChange}
      />
    );
  }

  return <p className="note">This item type is not supported by this build.</p>;
}

function AssessmentCircuit({
  item,
  value,
  onChange,
}: {
  item: AssessmentItem;
  value: CircuitSpec | undefined;
  onChange: (value: CircuitSpec) => void;
}) {
  const constraints = item.constraints ?? {};
  const allowed = (constraints.allowed_operations as OperationName[]) ?? ['x'];
  const maxOperations = (constraints.max_operations as number) ?? 3;
  const initial = (constraints.initial_state as string) === 'ket1' ? 'ket1' : 'ket0';
  const operations = value?.operations.map((operation) => operation.op as OperationName) ?? [];

  return (
    <>
      <CircuitEditor
        initial={initial}
        initialOptions={[initial]}
        operations={operations}
        palette={allowed}
        maxGates={maxOperations}
        onChangeInitial={() => undefined}
        onChangeOperations={(next) => onChange(buildCircuit(initial, next))}
      />
      <p className="note">
        Any allowed circuit reaching the published goal is accepted. The evaluator checks the
        computed result, not a particular gate string.
      </p>
    </>
  );
}
