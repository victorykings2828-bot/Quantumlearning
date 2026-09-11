import { useState } from 'react';
import type { TaskResult, TopicTask } from '@/api/types';

export type Submission = Record<string, unknown>;

export function TaskForm({
  task,
  passed,
  result,
  busy,
  requiresRun,
  onSubmit,
  onRequestHint,
  hintsUsed,
  hintLevels,
  hintText,
}: {
  task: TopicTask;
  passed: boolean;
  result: TaskResult | null;
  busy: boolean;
  requiresRun: boolean;
  onSubmit: (submission: Submission) => void;
  onRequestHint: () => void;
  hintsUsed: number;
  hintLevels: number;
  hintText: string | null;
}) {
  const [selection, setSelection] = useState<string>('');
  const [values, setValues] = useState<Record<string, string>>({});
  const [mapping, setMapping] = useState<Record<string, string>>({});
  const [parts, setParts] = useState<Record<string, string>>({});
  const [freeText, setFreeText] = useState('');

  const submit = () => {
    switch (task.kind) {
      case 'single_select':
        onSubmit({ selection, free_text: freeText || undefined });
        break;
      case 'numeric_fields':
        onSubmit({ values });
        break;
      case 'matching':
        onSubmit({ matches: mapping });
        break;
      case 'classification':
        onSubmit({ assignments: mapping });
        break;
      case 'compound':
        onSubmit({ parts });
        break;
      case 'run_reading':
        onSubmit({ values, selection });
        break;
      case 'circuit_goal':
        onSubmit({});
        break;
      default:
        onSubmit({});
    }
  };

  return (
    <div className="task" data-passed={passed}>
      <h3>{task.title}</h3>
      <p>{task.prompt}</p>

      {task.kind === 'single_select' && task.options && (
        <fieldset className="choice-set">
          <legend className="visually-hidden">{task.title}</legend>
          {task.options.map((option) => (
            <label key={option.id} className="choice">
              <input
                type="radio"
                name={task.id}
                value={option.id}
                checked={selection === option.id}
                onChange={() => setSelection(option.id)}
              />
              <span>{option.label}</span>
            </label>
          ))}
        </fieldset>
      )}

      {(task.kind === 'numeric_fields' || task.kind === 'run_reading') && task.fields && (
        <div className="numeric-fields">
          {task.fields.map((field) => (
            <label key={field.id} className="field">
              <span>{field.label}</span>
              <input
                type="text"
                inputMode="decimal"
                className="inline-input"
                placeholder={field.placeholder ?? 'decimal or fraction'}
                value={values[field.id] ?? ''}
                onChange={(event) =>
                  setValues((current) => ({ ...current, [field.id]: event.target.value }))
                }
              />
            </label>
          ))}
        </div>
      )}

      {task.kind === 'run_reading' && task.options && (
        <fieldset className="choice-set">
          <legend>Why need the counts not split equally?</legend>
          {task.options.map((option) => (
            <label key={option.id} className="choice">
              <input
                type="radio"
                name={`${task.id}-reason`}
                value={option.id}
                checked={selection === option.id}
                onChange={() => setSelection(option.id)}
              />
              <span>{option.label}</span>
            </label>
          ))}
        </fieldset>
      )}

      {task.kind === 'matching' && task.left && task.right && (
        <div className="matching">
          {task.left.map((item) => (
            <label key={item.id} className="field">
              <span>{item.label}</span>
              <select
                value={mapping[item.id] ?? ''}
                onChange={(event) =>
                  setMapping((current) => ({ ...current, [item.id]: event.target.value }))
                }
              >
                <option value="">Choose…</option>
                {task.right!.map((option) => (
                  <option key={option.id} value={option.id}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
          ))}
        </div>
      )}

      {task.kind === 'classification' && task.items && task.categories && (
        <div className="matching">
          {task.items.map((item) => (
            <label key={item.id} className="field">
              <span className="mono">{item.label}</span>
              <select
                value={mapping[item.id] ?? ''}
                onChange={(event) =>
                  setMapping((current) => ({ ...current, [item.id]: event.target.value }))
                }
              >
                <option value="">Choose…</option>
                {task.categories!.map((category) => (
                  <option key={category.id} value={category.id}>
                    {category.label}
                  </option>
                ))}
              </select>
            </label>
          ))}
        </div>
      )}

      {task.kind === 'compound' && task.parts && (
        <div className="stack">
          {task.parts.map((part) => (
            <fieldset key={part.id} className="choice-set">
              <legend>{part.prompt}</legend>
              {part.options.map((option) => (
                <label key={option.id} className="choice">
                  <input
                    type="radio"
                    name={`${task.id}-${part.id}`}
                    value={option.id}
                    checked={parts[part.id] === option.id}
                    onChange={() =>
                      setParts((current) => ({ ...current, [part.id]: option.id }))
                    }
                  />
                  <span>{option.label}</span>
                </label>
              ))}
            </fieldset>
          ))}
        </div>
      )}

      {task.kind === 'circuit_goal' && (
        <p className="note">
          Build the circuit in the laboratory, press Run, then submit. The evaluator checks the
          computed result against the published goal, not a particular gate string.
        </p>
      )}

      {task.acceptance_note && <p className="note">{task.acceptance_note}</p>}

      {task.free_text?.enabled && (
        <label className="field">
          <span>{task.free_text.prompt}</span>
          <textarea
            rows={3}
            value={freeText}
            onChange={(event) => setFreeText(event.target.value)}
          />
        </label>
      )}

      <div className="button-row">
        <button
          type="button"
          className="button button--primary"
          onClick={submit}
          disabled={busy || (requiresRun && task.kind === 'circuit_goal' && false)}
        >
          {busy ? 'Checking…' : 'Check my answer'}
        </button>
        <button
          type="button"
          className="button"
          onClick={onRequestHint}
          disabled={busy || hintsUsed >= hintLevels}
        >
          {hintsUsed === 0
            ? `Show a hint (1 of ${hintLevels})`
            : hintsUsed >= hintLevels
              ? 'All hints shown'
              : `Next hint (${hintsUsed + 1} of ${hintLevels})`}
        </button>
        {hintsUsed > 0 && (
          <span className="badge badge--warning">Assistance recorded: level {hintsUsed}</span>
        )}
      </div>

      {hintText && (
        <div className="note note--hint" role="status">
          <strong>Hint {hintsUsed}</strong>
          <p style={{ margin: 'var(--s1) 0 0' }}>{hintText}</p>
        </div>
      )}

      {result && (
        <div
          className={result.passed ? 'note note--success' : 'note note--warning'}
          role="status"
          aria-live="polite"
        >
          <p style={{ margin: 0 }}>
            <strong>
              {result.passed ? 'Correct' : 'Not yet'} · checked against the task rubric
            </strong>
          </p>
          <p style={{ margin: 'var(--s1) 0 0' }}>{result.message}</p>
          {result.passed && (
            <p className="note" style={{ margin: 'var(--s2) 0 0' }}>
              Recorded as <strong>{result.evidence_kind}</strong> evidence
              {result.assisted ? ' because hints were used on this task.' : '.'}
            </p>
          )}
          {result.duplicate && (
            <p className="note" style={{ margin: 'var(--s2) 0 0' }}>
              This was a duplicate submission, so the original outcome is shown and no extra
              evidence was recorded.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
