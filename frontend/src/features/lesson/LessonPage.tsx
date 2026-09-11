import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { api, ApiError } from '@/api/client';
import { useApiQuery } from '@/app/useApi';
import {
  AmplitudeChart,
  BlochSummary,
  CountsChart,
  ProbabilityChart,
} from '@/components/charts';
import { ErrorBanner, Loading, Markdown, PageHeader, Panel } from '@/components/primitives';
import type {
  InitialStateName,
  OperationName,
  RunRecord,
  TaskResult,
  Topic,
} from '@/api/types';
import { useTutor } from '@/features/tutor/TutorContext';
import { CircuitEditor, STATE_LABELS, buildCircuit } from './CircuitEditor';
import { TaskForm, type Submission } from './TaskForm';

export function LessonPage() {
  const { topicId } = useParams<{ topicId: string }>();
  const { data, loading, error, reload } = useApiQuery<Topic>(
    topicId ? `/topics/${topicId}` : null,
    [topicId],
  );

  if (loading) return <Loading label="Loading the topic." />;
  if (error) {
    return (
      <>
        <PageHeader
          eyebrow="Not found"
          title="There is no such topic."
          lede="Chapter 1 has topics 1.1 to 1.8. This address is not a lesson waiting to be unlocked."
        />
        <ErrorBanner message={error} />
        <p>
          <Link className="button button--primary" to="/course/chapter-1">
            Back to the chapter
          </Link>
        </p>
      </>
    );
  }
  if (!data || !topicId) return null;

  return <Lesson key={topicId} topic={data} reload={reload} />;
}

function Lesson({ topic, reload }: { topic: Topic; reload: () => void }) {
  const [initial, setInitial] = useState<InitialStateName>(
    topic.lab.initial_state_options[0] ?? 'ket0',
  );
  const [operations, setOperations] = useState<OperationName[]>([]);
  const [shots, setShots] = useState(topic.lab.default_shots);
  const [run, setRun] = useState<RunRecord | null>(null);
  const [stepIndex, setStepIndex] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [busy, setBusy] = useState(false);
  const [dirty, setDirty] = useState(false);
  const [labError, setLabError] = useState<string | null>(null);
  const [replayNote, setReplayNote] = useState<string | null>(null);
  const [repeatResult, setRepeatResult] = useState<string | null>(null);
  const [equivalentNotation, setEquivalentNotation] = useState(false);
  const [steps, setSteps] = useState<Record<string, boolean>>(topic.completed_steps ?? {});
  const [prediction, setPrediction] = useState<string>(
    topic.recorded_prediction?.selection ?? '',
  );
  const [predictionSaved, setPredictionSaved] = useState(Boolean(topic.recorded_prediction));
  const [taskResults, setTaskResults] = useState<Record<string, TaskResult>>({});
  const [taskBusy, setTaskBusy] = useState<string | null>(null);
  const [hints, setHints] = useState<Record<string, { level: number; text: string }>>({});
  const [passedIds, setPassedIds] = useState<string[]>(topic.passed_task_ids ?? []);
  const runToken = useRef(0);
  const { setContext } = useTutor();

  const fixedPrefix = useMemo<OperationName[]>(() => {
    const task = topic.tasks.find((entry) => entry.constraints?.fixed_prefix);
    return (task?.constraints?.fixed_prefix as OperationName[]) ?? [];
  }, [topic.tasks]);
  const fixedSuffix = useMemo<OperationName[]>(() => {
    const task = topic.tasks.find((entry) => entry.constraints?.fixed_suffix);
    return (task?.constraints?.fixed_suffix as OperationName[]) ?? [];
  }, [topic.tasks]);

  useEffect(() => {
    if (fixedPrefix.length || fixedSuffix.length) {
      setOperations([...fixedPrefix, ...fixedSuffix]);
    }
  }, [fixedPrefix, fixedSuffix]);

  useEffect(() => {
    setContext({ topicId: topic.id, runId: null, runLabel: null, stepIndex: null });
  }, [setContext, topic.id]);

  // An edit invalidates the displayed result: a stale run is never shown as current.
  const markDirty = useCallback(() => {
    setDirty(true);
    setRepeatResult(null);
  }, []);

  const execute = useCallback(async () => {
    const token = ++runToken.current;
    setBusy(true);
    setLabError(null);
    setReplayNote(null);
    setRepeatResult(null);
    try {
      // A shot in the sampling laboratory is one preparation followed by one
      // real measurement, so the recorded trajectory has an outcome to repeat.
      const withMeasurement: OperationName[] = topic.lab.features.remeasure
        ? [...operations, 'measure_z']
        : operations;
      const circuit = buildCircuit(initial, withMeasurement, topic.lab.qubits);
      const revision = await api.post<{ revision_id: string }>('/revisions', {
        topic_id: topic.id,
        circuit,
      });
      const result = await api.post<RunRecord>('/runs', {
        revision_id: revision.revision_id,
        shots,
        label: `Topic ${topic.number} run`,
      });
      if (token !== runToken.current) return;
      setRun(result);
      setDirty(false);
      setStepIndex(result.result.frames.length - 1);
      setContext({
        topicId: topic.id,
        runId: result.run_id,
        runLabel: `run ${result.ordinal}`,
        stepIndex: result.result.frames.length - 1,
      });
    } catch (cause) {
      if (token !== runToken.current) return;
      setLabError(cause instanceof ApiError ? cause.message : String(cause));
    } finally {
      if (token === runToken.current) setBusy(false);
    }
  }, [
    initial,
    operations,
    shots,
    topic.id,
    topic.number,
    topic.lab.qubits,
    topic.lab.features.remeasure,
    setContext,
  ]);

  useEffect(() => {
    if (!playing || !run) return;
    const total = run.result.frames.length;
    const timer = window.setInterval(() => {
      setStepIndex((current) => {
        if (current + 1 >= total) {
          setPlaying(false);
          return current;
        }
        return current + 1;
      });
    }, 700);
    return () => window.clearInterval(timer);
  }, [playing, run]);

  useEffect(() => {
    if (!run) return;
    setContext({ stepIndex });
  }, [stepIndex, run, setContext]);

  const markStep = async (stepId: string) => {
    setSteps((current) => ({ ...current, [stepId]: true }));
    try {
      await api.post(`/topics/${topic.id}/steps`, { step_id: stepId });
    } catch {
      // A failed step record is not fatal; the panel state stays optimistic and
      // the next reload reconciles it from the server.
    }
  };

  const savePrediction = async () => {
    if (!prediction) return;
    await api.post(`/topics/${topic.id}/prediction`, {
      prediction_id: topic.prediction.id,
      selection: prediction,
    });
    setPredictionSaved(true);
  };

  const submitTask = async (taskId: string, submission: Submission) => {
    setTaskBusy(taskId);
    try {
      const body: Record<string, unknown> = { submission };
      const task = topic.tasks.find((entry) => entry.id === taskId);
      if ((task?.kind === 'circuit_goal' || task?.kind === 'run_reading') && run) {
        body.run_id = run.run_id;
      }
      const result = await api.post<TaskResult>(`/tasks/${taskId}/attempts`, body);
      setTaskResults((current) => ({ ...current, [taskId]: result }));
      if (result.passed) {
        setPassedIds((current) => (current.includes(taskId) ? current : [...current, taskId]));
        reload();
      }
    } catch (cause) {
      setTaskResults((current) => ({
        ...current,
        [taskId]: {
          task_id: taskId,
          passed: false,
          reason_code: 'request_failed',
          message: cause instanceof ApiError ? cause.message : String(cause),
          detail: {},
          assisted: false,
          evidence_kind: 'assisted',
          hints_used: 0,
          duplicate: false,
          topic_status: 'in_progress',
          next_task_id: null,
          assessed_skills: [],
        },
      }));
    } finally {
      setTaskBusy(null);
    }
  };

  const requestHint = async (taskId: string) => {
    const nextLevel = (hints[taskId]?.level ?? 0) + 1;
    if (nextLevel > topic.hint_levels) return;
    try {
      const response = await api.post<{ level: number; text: string }>('/hints', {
        topic_id: topic.id,
        task_id: taskId,
        level: nextLevel,
      });
      setHints((current) => ({
        ...current,
        [taskId]: { level: response.level, text: response.text },
      }));
    } catch (cause) {
      setLabError(cause instanceof ApiError ? cause.message : String(cause));
    }
  };

  const frames = run?.result.frames ?? [];
  const frame = frames[Math.min(stepIndex, Math.max(frames.length - 1, 0))];
  const branchCount = run?.result.branches.length ?? 0;
  const requiredSteps = topic.completion.required_step_ids;
  const stepsDone = requiredSteps.filter((id) => steps[id]).length;
  const tasksDone = topic.completion.required_task_ids.filter((id) =>
    passedIds.includes(id),
  ).length;
  const complete =
    stepsDone === requiredSteps.length &&
    tasksDone === topic.completion.required_task_ids.length;

  return (
    <>
      <PageHeader
        eyebrow={`Chapter 1 · Topic ${topic.number}`}
        title={topic.title}
        lede={topic.objective}
      />

      <div className="lab">
        <div className="lab__column stack">
          <Panel
            title="Progress in this topic"
            badge={complete ? 'Complete' : `${stepsDone}/${requiredSteps.length} steps`}
            badgeTone={complete ? 'success' : 'neutral'}
          >
            <p className="note" style={{ marginTop: 0 }}>
              {tasksDone} of {topic.completion.required_task_ids.length} checks passed. Reading
              and pressing Run do not complete a topic on their own.
            </p>
            <ol className="step-list">
              {topic.steps.map((step) => (
                <li key={step.id} data-done={Boolean(steps[step.id])}>
                  <label className="choice">
                    <input
                      type="checkbox"
                      checked={Boolean(steps[step.id])}
                      onChange={() => void markStep(step.id)}
                    />
                    <span>
                      <strong>{step.title}</strong>
                      <br />
                      {step.instruction}
                    </span>
                  </label>
                </li>
              ))}
            </ol>
          </Panel>

          <Panel title="Predict first" badge={predictionSaved ? 'Recorded' : 'Not recorded'}>
            <p>{topic.prediction.prompt}</p>
            <fieldset className="choice-set">
              <legend className="visually-hidden">{topic.prediction.prompt}</legend>
              {topic.prediction.options.map((option) => (
                <label key={option.id} className="choice">
                  <input
                    type="radio"
                    name="prediction"
                    value={option.id}
                    checked={prediction === option.id}
                    onChange={() => setPrediction(option.id)}
                  />
                  <span>{option.label}</span>
                </label>
              ))}
            </fieldset>
            <div className="button-row">
              <button
                type="button"
                className="button"
                onClick={() => void savePrediction()}
                disabled={!prediction}
              >
                Record my prediction
              </button>
            </div>
            <p className="note">
              A prediction is recorded for teaching feedback. An incorrect one never fails the
              topic.
            </p>
          </Panel>

          {(topic.lab.gate_palette.length > 0 ||
            topic.lab.initial_state_options.length > 1) && (
            <Panel title="Laboratory controls">
              <CircuitEditor
                initial={initial}
                initialOptions={topic.lab.initial_state_options}
                operations={operations}
                palette={topic.lab.gate_palette}
                maxGates={topic.lab.max_gates}
                disabled={busy}
                lockedPrefix={fixedPrefix}
                lockedSuffix={fixedSuffix}
                onChangeInitial={(value) => {
                  setInitial(value);
                  markDirty();
                }}
                onChangeOperations={(value) => {
                  setOperations(value);
                  markDirty();
                }}
              />
              <label className="field">
                <span>Shots</span>
                <select
                  value={shots}
                  onChange={(event) => {
                    setShots(Number(event.target.value));
                    markDirty();
                  }}
                >
                  {topic.lab.shot_options.map((value) => (
                    <option key={value} value={value}>
                      {value}
                    </option>
                  ))}
                </select>
              </label>
              <div className="button-row">
                <button
                  type="button"
                  className="button button--primary"
                  onClick={() => void execute()}
                  disabled={busy}
                >
                  {busy
                    ? 'Computing…'
                    : topic.lab.features.new_preparation
                      ? 'New preparation'
                      : 'Run'}
                </button>
                {topic.lab.features.remeasure && (
                  <button
                    type="button"
                    className="button"
                    disabled={!run || busy}
                    onClick={async () => {
                      if (!run) return;
                      const response = await api.post<{
                        repeatable: boolean;
                        outcome?: number;
                        outcome_label?: string;
                        explanation: string;
                      }>(`/runs/${run.run_id}/repeat-measurement`);
                      setRepeatResult(
                        response.repeatable
                          ? `Recorded outcome ${response.outcome ?? response.outcome_label} again, with probability 1. ${response.explanation}`
                          : response.explanation,
                      );
                    }}
                  >
                    Measure this trajectory again
                  </button>
                )}
                {topic.lab.features.replay && (
                  <button
                    type="button"
                    className="button"
                    disabled={!run}
                    onClick={() => {
                      setStepIndex(0);
                      setReplayNote(
                        run?.replay_note ??
                          'Replay shows the saved frames and recorded outcomes of this run. It is not a new measurement.',
                      );
                    }}
                  >
                    Replay
                  </button>
                )}
                <button
                  type="button"
                  className="button"
                  onClick={() => {
                    setInitial(topic.lab.initial_state_options[0] ?? 'ket0');
                    setOperations([...fixedPrefix, ...fixedSuffix]);
                    setShots(topic.lab.default_shots);
                    markDirty();
                    setReplayNote('Preset restored. Your earlier runs are still saved.');
                  }}
                >
                  Reset preset
                </button>
              </div>
              {topic.lab.features.equivalent_notation && (
                <label className="choice" style={{ marginTop: 'var(--s3)' }}>
                  <input
                    type="checkbox"
                    checked={equivalentNotation}
                    onChange={(event) => setEquivalentNotation(event.target.checked)}
                  />
                  <span>
                    Equivalent notation: show every amplitude multiplied by -1.
                    <br />
                    <span className="note">{topic.lab.equivalent_notation_note}</span>
                  </span>
                </label>
              )}
              {repeatResult && <p className="note note--success">{repeatResult}</p>}
              {replayNote && <p className="note">{replayNote}</p>}
              {labError && <p className="note note--warning">{labError}</p>}
            </Panel>
          )}

          {topic.lab.cards && (
            <Panel title="Amplitude cards" badge="Curated">
              <div className="scroll-x">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Card</th>
                      <th>Amplitudes</th>
                      <th>P(0), P(1)</th>
                      <th>Valid?</th>
                    </tr>
                  </thead>
                  <tbody>
                    {topic.lab.cards.map((card) => (
                      <tr key={card.id}>
                        <td>
                          {card.state ? (
                            <button
                              type="button"
                              className="button button--small"
                              onClick={() => {
                                setInitial(card.state as InitialStateName);
                                markDirty();
                              }}
                            >
                              {card.id}
                            </button>
                          ) : (
                            <strong>{card.id}</strong>
                          )}
                        </td>
                        <td className="mono">{card.amplitudes}</td>
                        <td className="mono">{card.probabilities}</td>
                        <td>
                          {card.valid ? (
                            <span className="badge badge--success">Valid</span>
                          ) : (
                            <span className="badge badge--warning">Not normalized</span>
                          )}
                          <br />
                          <span className="note">{card.note}</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p className="note note--warning">
                An invalid vector is rejected rather than silently rescaled. Select a valid card
                before running.
              </p>
            </Panel>
          )}
        </div>

        <div className="lab__column stack">
          <Panel title="What is going on" badge={`Content v${topic.content_version}`}>
            <Markdown text={topic.teach_markdown} />
            {topic.future_payoff && <p className="note note--hint">{topic.future_payoff}</p>}
            {topic.author_caution && (
              <p className="note note--warning">{topic.author_caution}</p>
            )}
            <p className="note mono">{topic.notation_contract}</p>
          </Panel>

          {dirty && run && (
            <p className="note note--warning" role="status">
              The circuit has changed since this result was computed. Press Run to compute the
              new one; the panels below still describe the earlier circuit.
            </p>
          )}

          {run && frame && (
            <>
              <Panel
                title={`State after step ${frame.step_index}`}
                badge={run.result.result_kind.replace(/_/g, ' ')}
                actions={
                  <span className="badge badge--navy">
                    run {run.ordinal} · revision {run.revision_id.slice(0, 8)}
                  </span>
                }
              >
                <div className="button-row">
                  {frames.map((item, index) => (
                    <button
                      key={`${item.branch_id}-${item.step_index}-${index}`}
                      type="button"
                      className="button button--small"
                      aria-pressed={index === stepIndex}
                      onClick={() => setStepIndex(index)}
                    >
                      {item.step_index}. {item.label.split(' - ')[0]}
                    </button>
                  ))}
                </div>
                <div className="button-row" style={{ marginTop: 'var(--s3)' }}>
                  <button
                    type="button"
                    className="button button--small"
                    onClick={() => setPlaying((value) => !value)}
                  >
                    {playing ? 'Pause' : 'Play'}
                  </button>
                  <button
                    type="button"
                    className="button button--small"
                    onClick={() => setStepIndex((value) => Math.max(0, value - 1))}
                    disabled={stepIndex === 0}
                  >
                    Previous step
                  </button>
                  <button
                    type="button"
                    className="button button--small"
                    onClick={() =>
                      setStepIndex((value) => Math.min(frames.length - 1, value + 1))
                    }
                    disabled={stepIndex >= frames.length - 1}
                  >
                    Next step
                  </button>
                  <span className="note" style={{ margin: 0 }}>
                    Playback sets the viewing pace. It is not execution time.
                  </span>
                </div>

                <p className="note">
                  <strong>{frame.label}</strong>
                  {branchCount > 1 && (
                    <>
                      {' '}
                      · branch {frame.branch_id} with probability{' '}
                      {frame.branch_probability.toFixed(4)}
                    </>
                  )}
                </p>

                <AmplitudeChart
                  amplitudes={
                    equivalentNotation
                      ? frame.amplitudes.map((amplitude) => ({
                          ...amplitude,
                          re: -amplitude.re,
                          im: -amplitude.im,
                        }))
                      : frame.amplitudes
                  }
                />
                {equivalentNotation && (
                  <p className="note note--warning">
                    Showing the same physical state with every amplitude multiplied by -1. This
                    is a representation aid, not a measurement.
                  </p>
                )}
                <ProbabilityChart
                  labels={run.result.basis_labels}
                  values={frame.probabilities}
                  title="Exact probabilities at this step"
                />
                <div className="scroll-x">
                  <table className="data-table">
                    <caption className="visually-hidden">
                      Amplitudes at step {frame.step_index}
                    </caption>
                    <thead>
                      <tr>
                        <th>Outcome</th>
                        <th className="numeric">Amplitude</th>
                        <th className="numeric">Squared magnitude</th>
                        <th>Phase</th>
                      </tr>
                    </thead>
                    <tbody>
                      {frame.amplitudes.map((amplitude) => (
                        <tr key={amplitude.index}>
                          <td className="mono">{amplitude.label}</td>
                          <td className="numeric">
                            {(equivalentNotation ? -amplitude.re : amplitude.re).toFixed(6)}
                          </td>
                          <td className="numeric">{amplitude.probability.toFixed(6)}</td>
                          <td className="mono">
                            {amplitude.phase_radians === null
                              ? 'undefined'
                              : `${amplitude.phase_radians.toFixed(4)} rad`}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Panel>

              {branchCount > 1 && (
                <Panel title="Conditional branches" badge="After a real measurement">
                  <div className="scroll-x">
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>Branch</th>
                          <th>Recorded outcomes</th>
                          <th className="numeric">Branch probability</th>
                        </tr>
                      </thead>
                      <tbody>
                        {run.result.branches.map((branch) => (
                          <tr key={branch.branch_id}>
                            <td className="mono">{branch.branch_id}</td>
                            <td className="mono">{branch.outcomes.join(', ')}</td>
                            <td className="numeric">{branch.probability.toFixed(4)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <p className="note">
                    Each branch is a separate conditional trajectory. The ensemble summary below
                    combines them with these probabilities; it is not a single state.
                  </p>
                  <ProbabilityChart
                    labels={run.result.basis_labels}
                    values={run.result.exact_probabilities}
                    title="Ensemble probabilities across branches"
                  />
                </Panel>
              )}

              <Panel title="If you measured now" badge={`${run.shots} shots`}>
                <CountsChart
                  labels={run.result.basis_labels}
                  counts={run.result.counts}
                  shots={run.shots}
                />
                <div className="scroll-x">
                  <table className="data-table">
                    <caption className="visually-hidden">
                      Exact probabilities beside observed frequencies
                    </caption>
                    <thead>
                      <tr>
                        <th>Outcome</th>
                        <th className="numeric">Exact probability</th>
                        <th className="numeric">Observed frequency</th>
                      </tr>
                    </thead>
                    <tbody>
                      {run.result.basis_labels.map((label, index) => (
                        <tr key={label}>
                          <td className="mono">{label}</td>
                          <td className="numeric">
                            {run.result.exact_probabilities[index].toFixed(6)}
                          </td>
                          <td className="numeric">
                            {(((run.result.counts[label] ?? 0) / run.shots) * 100).toFixed(2)}%
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <p className="note">
                  Exact probabilities come from the circuit. Observed frequencies come from your{' '}
                  {run.shots} shots. They are different objects and are never merged.
                </p>
                <p className="note mono">
                  {run.engine} {run.engine_version} · run {run.run_id.slice(0, 8)} · seed{' '}
                  {run.seed ?? 'unseeded'}
                </p>
              </Panel>

              {run.result.qubits > 1 && frame.reduced_states.length > 0 && (
                <Panel title="Each qubit on its own" badge="Reduced state">
                  <BlochSummary states={frame.reduced_states} />
                </Panel>
              )}
            </>
          )}

          <Panel
            title="Checks"
            badge={`${tasksDone}/${topic.completion.required_task_ids.length} passed`}
            badgeTone={complete ? 'success' : 'neutral'}
          >
            {topic.tasks.map((task) => (
              <TaskForm
                key={task.id}
                task={task}
                passed={passedIds.includes(task.id)}
                result={taskResults[task.id] ?? null}
                busy={taskBusy === task.id}
                requiresRun={task.kind === 'circuit_goal' || task.kind === 'run_reading'}
                hintsUsed={hints[task.id]?.level ?? 0}
                hintLevels={topic.hint_levels}
                hintText={hints[task.id]?.text ?? null}
                onRequestHint={() => void requestHint(task.id)}
                onSubmit={(submission) => void submitTask(task.id, submission)}
              />
            ))}
          </Panel>

          {topic.misconceptions && topic.misconceptions.length > 0 && (
            <Panel title="Common sticking points">
              <dl className="definition-list">
                {topic.misconceptions.map((item) => (
                  <div key={item.id}>
                    <dt>{item.trigger}</dt>
                    <dd>{item.response}</dd>
                  </div>
                ))}
              </dl>
            </Panel>
          )}

          {topic.revisit && (
            <Panel
              title="Revisit status"
              badge={topic.revisit.keeps_status}
              badgeTone="warning"
            >
              <p>{topic.revisit.note}</p>
              <p className="note">{topic.revisit.status_explanation}</p>
              <p>
                <Link className="button" to="/lab/grover">
                  Reopen the search preview
                </Link>
              </p>
            </Panel>
          )}

          <Panel title="Sources for this topic">
            <ul>
              {topic.sources.map((source) => (
                <li key={source.id}>
                  <a href={source.url} target="_blank" rel="noreferrer noopener">
                    {source.title}
                  </a>
                </li>
              ))}
            </ul>
          </Panel>
        </div>
      </div>

      <nav className="topic-nav" aria-label="Topic navigation">
        {topic.previous_topic_id ? (
          <Link className="button" to={`/learn/chapter-1/${topic.previous_topic_id}`}>
            ← Previous topic
          </Link>
        ) : (
          <Link className="button" to="/course/chapter-1">
            ← Chapter overview
          </Link>
        )}
        <span className="note" style={{ margin: 0 }}>
          {STATE_LABELS[initial]} · {operations.length} gate
          {operations.length === 1 ? '' : 's'}
        </span>
        {topic.next_topic_id ? (
          <Link
            className="button button--primary"
            to={`/learn/chapter-1/${topic.next_topic_id}`}
          >
            Next topic →
          </Link>
        ) : (
          <Link className="button button--primary" to="/assessments/chapter-1">
            Chapter assessment →
          </Link>
        )}
      </nav>
    </>
  );
}
