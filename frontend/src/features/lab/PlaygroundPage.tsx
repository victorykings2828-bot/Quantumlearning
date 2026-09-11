import { useCallback, useEffect, useRef, useState } from 'react';
import { api, ApiError } from '@/api/client';
import { useApiQuery } from '@/app/useApi';
import {
  AmplitudeChart,
  BlochSummary,
  CountsChart,
  ProbabilityChart,
} from '@/components/charts';
import { Loading, Markdown, PageHeader, Panel } from '@/components/primitives';
import type { CircuitSpec, InitialStateName, Operation, RunRecord } from '@/api/types';
import { useTutor } from '@/features/tutor/TutorContext';
import { STATE_LABELS, initialStateSpec } from '@/features/lesson/CircuitEditor';

/** A placed operation, with the wires it acts on. */
interface Placed {
  op: 'x' | 'h' | 'z' | 'cx' | 'cz' | 'measure_z';
  target: number;
  control?: number;
}

interface Preset {
  id: string;
  title: string;
  qubits: number;
  initial_state: InitialStateName;
  operations: string[];
  description: string;
}

interface PlaygroundResponse {
  title: string;
  summary: string;
  bounds_note: string;
  qubits_options: number[];
  gate_palette: Placed['op'][];
  shot_options: number[];
  default_shots: number;
  initial_state_options: InitialStateName[];
  presets: Preset[];
  entanglement_guidance: {
    heading: string;
    body_markdown: string;
    sources: { id: string; title: string; url: string }[];
  };
  bloch_note: string;
  prerequisite_note: string;
}

const LABELS: Record<Placed['op'], string> = {
  x: 'X',
  h: 'H',
  z: 'Z',
  cx: 'CNOT',
  cz: 'CZ',
  measure_z: 'Measure Z',
};

const TWO_WIRE = new Set<Placed['op']>(['cx', 'cz']);

function toCircuit(qubits: number, initial: InitialStateName, placed: Placed[]): CircuitSpec {
  return {
    schema_version: 'circuit/v1',
    qubits,
    initial_state: initialStateSpec(initial),
    operations: placed.map<Operation>((item) => ({
      op: item.op,
      targets: [item.target],
      controls: item.control === undefined ? [] : [item.control],
    })),
  };
}

function fromPreset(preset: Preset): Placed[] {
  return preset.operations.map((token) => {
    if (token === 'cx') return { op: 'cx', target: 1, control: 0 };
    if (token === 'cz') return { op: 'cz', target: 1, control: 0 };
    if (token === 'h1') return { op: 'h', target: 1 };
    return { op: token as Placed['op'], target: 0 };
  });
}

export function PlaygroundPage() {
  const { data, loading, error } = useApiQuery<PlaygroundResponse>('/playground');
  const [qubits, setQubits] = useState(2);
  const [initial, setInitial] = useState<InitialStateName>('ket0');
  const [placed, setPlaced] = useState<Placed[]>([
    { op: 'h', target: 0 },
    { op: 'cx', target: 1, control: 0 },
  ]);
  const [wire, setWire] = useState(0);
  const [shots, setShots] = useState(256);
  const [run, setRun] = useState<RunRecord | null>(null);
  const [stepIndex, setStepIndex] = useState(0);
  const [busy, setBusy] = useState(false);
  const [dirty, setDirty] = useState(false);
  const [labError, setLabError] = useState<string | null>(null);
  const token = useRef(0);
  const { setContext } = useTutor();

  useEffect(() => {
    setContext({ topicId: null, runId: null, runLabel: null, stepIndex: null });
  }, [setContext]);

  const execute = useCallback(async () => {
    const id = ++token.current;
    setBusy(true);
    setLabError(null);
    try {
      const revision = await api.post<{ revision_id: string }>('/revisions', {
        topic_id: 'playground',
        kind: 'playground',
        circuit: toCircuit(qubits, initial, placed),
      });
      const result = await api.post<RunRecord>('/runs', {
        revision_id: revision.revision_id,
        shots,
        label: 'Playground run',
      });
      if (id !== token.current) return;
      setRun(result);
      setDirty(false);
      setStepIndex(result.result.frames.length - 1);
      setContext({ runId: result.run_id, runLabel: `run ${result.ordinal}`, stepIndex: null });
    } catch (cause) {
      if (id !== token.current) return;
      setLabError(cause instanceof ApiError ? cause.message : String(cause));
    } finally {
      if (id === token.current) setBusy(false);
    }
  }, [qubits, initial, placed, shots, setContext]);

  if (loading) return <Loading label="Loading the playground." />;
  if (error || !data) return <p className="note">{error ?? 'Not available.'}</p>;

  const frames = run?.result.frames ?? [];
  const frame = frames[Math.min(stepIndex, Math.max(frames.length - 1, 0))];
  const change = (next: Placed[]) => {
    setPlaced(next);
    setDirty(true);
  };

  return (
    <>
      <PageHeader eyebrow="Quantum Lab · Experiment" title={data.title} lede={data.summary} />
      <p className="note note--warning">{data.bounds_note}</p>
      <p className="note note--success">{data.prerequisite_note}</p>

      <div className="lab">
        <div className="lab__column stack">
          <Panel title="Build a circuit">
            <div className="control-grid">
              <label className="field">
                <span>Qubits</span>
                <select
                  value={qubits}
                  onChange={(event) => {
                    const next = Number(event.target.value);
                    setQubits(next);
                    // Drop anything that no longer fits the register.
                    change(
                      placed.filter((item) => item.target < next && (item.control ?? 0) < next),
                    );
                    if (wire >= next) setWire(next - 1);
                  }}
                >
                  {data.qubits_options.map((value) => (
                    <option key={value} value={value}>
                      {value}
                    </option>
                  ))}
                </select>
              </label>
              <label className="field">
                <span>Initial state</span>
                <select
                  value={initial}
                  onChange={(event) => {
                    setInitial(event.target.value as InitialStateName);
                    setDirty(true);
                  }}
                  disabled={qubits > 1}
                >
                  {data.initial_state_options.map((option) => (
                    <option key={option} value={option}>
                      {STATE_LABELS[option]}
                    </option>
                  ))}
                </select>
              </label>
              <label className="field">
                <span>Acts on</span>
                <select value={wire} onChange={(event) => setWire(Number(event.target.value))}>
                  {Array.from({ length: qubits }, (_, index) => index).map((index) => (
                    <option key={index} value={index}>
                      q{index}
                      {qubits > 1 ? ' (two-qubit gates: q0 controls q1)' : ''}
                    </option>
                  ))}
                </select>
              </label>
              <label className="field">
                <span>Shots</span>
                <select
                  value={shots}
                  onChange={(event) => {
                    setShots(Number(event.target.value));
                    setDirty(true);
                  }}
                >
                  {data.shot_options.map((value) => (
                    <option key={value} value={value}>
                      {value}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            {qubits > 1 && (
              <p className="note">
                Named one-qubit presets apply to a single qubit only, so a two-qubit register
                starts in |00&gt;.
              </p>
            )}

            <h3 className="field-heading">Add a gate</h3>
            <div className="button-row">
              {data.gate_palette
                .filter((gate) => qubits > 1 || !TWO_WIRE.has(gate))
                .map((gate) => (
                  <button
                    key={gate}
                    type="button"
                    className="button"
                    onClick={() =>
                      change([
                        ...placed,
                        TWO_WIRE.has(gate)
                          ? { op: gate, target: 1, control: 0 }
                          : { op: gate, target: wire },
                      ])
                    }
                  >
                    {LABELS[gate]}
                  </button>
                ))}
              <button type="button" className="button button--small" onClick={() => change([])}>
                Clear circuit
              </button>
            </div>

            <h3 className="field-heading">Your circuit</h3>
            <ol className="wire" aria-label="Circuit operations in execution order">
              <li className="wire__start mono">
                {qubits > 1 ? '|00>' : STATE_LABELS[initial]}
              </li>
              {placed.length === 0 && <li className="wire__empty">No gates yet</li>}
              {placed.map((item, index) => (
                <li key={`${item.op}-${index}`} className="wire__gate">
                  <span className="wire__index">{index + 1}</span>
                  <span className="wire__name mono">{LABELS[item.op]}</span>
                  <span className="mono" style={{ fontSize: '0.78rem' }}>
                    {item.control === undefined
                      ? `q${item.target}`
                      : `q${item.control}→q${item.target}`}
                  </span>
                  <button
                    type="button"
                    className="button button--small"
                    aria-label={`Remove ${LABELS[item.op]} at position ${index + 1}`}
                    onClick={() => change(placed.filter((_, position) => position !== index))}
                  >
                    Remove
                  </button>
                </li>
              ))}
            </ol>

            <div className="button-row" style={{ marginTop: 'var(--s3)' }}>
              <button
                type="button"
                className="button button--primary"
                onClick={() => void execute()}
                disabled={busy}
              >
                {busy ? 'Computing…' : 'Run'}
              </button>
              <button
                type="button"
                className="button"
                onClick={() => setStepIndex(0)}
                disabled={!run}
              >
                Replay
              </button>
            </div>
            {dirty && run && (
              <p className="note note--warning">
                The circuit has changed since this result was computed. Press Run for the new
                one.
              </p>
            )}
            {labError && <p className="note note--warning">{labError}</p>}
          </Panel>

          <Panel title="Presets">
            <ul className="entry-list">
              {data.presets.map((preset) => (
                <li key={preset.id}>
                  <div>
                    <h3>{preset.title}</h3>
                    <p className="note" style={{ marginTop: 0 }}>
                      {preset.description}
                    </p>
                  </div>
                  <button
                    type="button"
                    className="button button--small"
                    onClick={() => {
                      setQubits(preset.qubits);
                      setInitial(preset.initial_state);
                      change(fromPreset(preset));
                    }}
                  >
                    Load
                  </button>
                </li>
              ))}
            </ul>
          </Panel>
        </div>

        <div className="lab__column stack">
          {run && frame ? (
            <>
              <Panel
                title={`State after step ${frame.step_index}`}
                badge={run.result.result_kind.replace(/_/g, ' ')}
              >
                <div className="button-row">
                  {frames.map((item, index) => (
                    <button
                      key={`${item.branch_id}-${index}`}
                      type="button"
                      className="button button--small"
                      aria-pressed={index === stepIndex}
                      onClick={() => setStepIndex(index)}
                    >
                      {item.step_index}. {item.label.split(':')[0].split(' - ')[0]}
                    </button>
                  ))}
                </div>
                <p className="note">
                  <strong>{frame.label}</strong>
                </p>
                <AmplitudeChart amplitudes={frame.amplitudes} />
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
                        <th className="numeric">Probability</th>
                        <th>Phase</th>
                      </tr>
                    </thead>
                    <tbody>
                      {frame.amplitudes.map((amplitude) => (
                        <tr key={amplitude.index}>
                          <td className="mono">{amplitude.label}</td>
                          <td className="numeric">{amplitude.re.toFixed(6)}</td>
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
                <p className="note mono">
                  {run.engine} {run.engine_version} · run {run.run_id.slice(0, 8)}
                </p>
              </Panel>

              {frame.reduced_states.length > 0 && run.result.qubits > 1 && (
                <Panel title="Each qubit on its own" badge="Reduced state">
                  <BlochSummary states={frame.reduced_states} />
                  <p className="note">{data.bloch_note}</p>
                </Panel>
              )}

              <Panel title="If you measured now" badge={`${run.shots} shots`}>
                <CountsChart
                  labels={run.result.basis_labels}
                  counts={run.result.counts}
                  shots={run.shots}
                />
                <p className="note">
                  Exact probabilities come from the circuit; the counts come from your shots.
                  They are different objects.
                </p>
              </Panel>
            </>
          ) : (
            <Panel title="Nothing computed yet">
              <p className="note">
                Build a circuit and press Run. Every panel here is filled from the computed
                result for the exact circuit on the left.
              </p>
            </Panel>
          )}

          <Panel title={data.entanglement_guidance.heading} badge="Read this before concluding">
            <Markdown text={data.entanglement_guidance.body_markdown} />
            <h3>Sources</h3>
            <ul>
              {data.entanglement_guidance.sources.map((source) => (
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
    </>
  );
}
