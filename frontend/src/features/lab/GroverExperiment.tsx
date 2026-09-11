import { useCallback, useEffect, useRef, useState } from 'react';
import { api, ApiError } from '@/api/client';
import { useApiQuery } from '@/app/useApi';
import { AmplitudeChart, CountsChart, ProbabilityChart } from '@/components/charts';
import { Panel } from '@/components/primitives';
import type { GroverRunRecord } from '@/api/types';
import { useTutor } from '@/features/tutor/TutorContext';

const CANDIDATES = [4, 8, 16] as const;
const SHOTS = [1, 16, 64, 256, 1024] as const;

interface AnalysisRow {
  iterations: number;
  ideal_target_probability: number;
  classical_check_and_guess: number;
  classical_checked_only: number;
}

interface AnalysisResponse {
  result_kind: string;
  candidates: number;
  best_iterations: number;
  rows: AnalysisRow[];
  classical_stopping_rules: Record<string, number>;
  assumptions: string[];
  formula: string;
  note: string;
}

interface ClassicalTraceResponse {
  candidates: number;
  target: number;
  trace: { query: number; candidate: number; matches: boolean }[];
  queries_used: number;
  stopping_rules: Record<string, number>;
  note: string;
}

export function GroverExperiment({ compact = false }: { compact?: boolean }) {
  const [candidates, setCandidates] = useState<number>(4);
  const [target, setTarget] = useState(2);
  const [iterations, setIterations] = useState(1);
  const [shots, setShots] = useState<number>(256);
  const [preparation, setPreparation] = useState<'uniform' | 'missing'>('uniform');

  const [run, setRun] = useState<GroverRunRecord | null>(null);
  const [previousRun, setPreviousRun] = useState<GroverRunRecord | null>(null);
  const [stepIndex, setStepIndex] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [replayNotice, setReplayNotice] = useState<string | null>(null);
  const runToken = useRef(0);
  const { setContext } = useTutor();

  const analysis = useApiQuery<AnalysisResponse>(`/grover/analysis?candidates=${candidates}`, [
    candidates,
  ]);
  const classical = useApiQuery<ClassicalTraceResponse>(
    `/grover/classical-trace?candidates=${candidates}&target=${Math.min(target, candidates - 1)}`,
    [candidates, target],
  );

  useEffect(() => {
    if (target > candidates - 1) setTarget(candidates - 1);
  }, [candidates, target]);

  const execute = useCallback(async () => {
    const token = ++runToken.current;
    setBusy(true);
    setError(null);
    setReplayNotice(null);
    try {
      const result = await api.post<GroverRunRecord>('/grover/runs', {
        candidates,
        target: Math.min(target, candidates - 1),
        iterations,
        shots,
        preparation,
      });
      // Ignore a response whose request has been superseded by a newer one.
      if (token !== runToken.current) return;
      setRun((current) => {
        setPreviousRun(current);
        return result;
      });
      setStepIndex(result.result.frames.length - 1);
      setContext({
        runId: result.run_id,
        runLabel: result.label,
        stepIndex: null,
        topicId: null,
      });
    } catch (cause) {
      if (token !== runToken.current) return;
      setError(cause instanceof ApiError ? cause.message : String(cause));
    } finally {
      if (token === runToken.current) setBusy(false);
    }
  }, [candidates, target, iterations, shots, preparation, setContext]);

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
    }, 650);
    return () => window.clearInterval(timer);
  }, [playing, run]);

  const frames = run?.result.frames ?? [];
  const frame = frames[Math.min(stepIndex, frames.length - 1)];
  const activeTarget = Math.min(target, candidates - 1);

  return (
    <div className="stack">
      <Panel title="Search experiment" badge="Ideal circuit simulation">
        <div className="control-grid">
          <label className="field">
            <span>Search space</span>
            <select
              value={candidates}
              onChange={(event) => setCandidates(Number(event.target.value))}
            >
              {CANDIDATES.map((value) => (
                <option key={value} value={value}>
                  N = {value} ({Math.log2(value)} search qubits)
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>Target candidate</span>
            <select
              value={activeTarget}
              onChange={(event) => setTarget(Number(event.target.value))}
            >
              {Array.from({ length: candidates }, (_, index) => index).map((value) => (
                <option key={value} value={value}>
                  {value} ({value.toString(2).padStart(Math.log2(candidates), '0')})
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>Grover iterations</span>
            <input
              type="number"
              min={0}
              max={8}
              value={iterations}
              onChange={(event) =>
                setIterations(Math.max(0, Math.min(8, Number(event.target.value))))
              }
            />
          </label>
          <label className="field">
            <span>Shots</span>
            <select value={shots} onChange={(event) => setShots(Number(event.target.value))}>
              {SHOTS.map((value) => (
                <option key={value} value={value}>
                  {value}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>Initial preparation</span>
            <select
              value={preparation}
              onChange={(event) => setPreparation(event.target.value as 'uniform' | 'missing')}
            >
              <option value="uniform">Standard uniform preparation</option>
              <option value="missing">What if preparation is missing?</option>
            </select>
          </label>
        </div>

        {preparation === 'missing' && (
          <p className="note note--warning">
            This variant starts in |0…0&gt; and is explicitly outside the standard success
            formula. The uniform-start prediction curve does not apply to it, and it is not
            general amplitude amplification.
          </p>
        )}

        <div className="button-row">
          <button
            type="button"
            className="button button--primary"
            onClick={execute}
            disabled={busy}
          >
            {busy ? 'Computing…' : 'Run'}
          </button>
          <button
            type="button"
            className="button"
            onClick={() => setPlaying((value) => !value)}
            disabled={!run}
          >
            {playing ? 'Pause' : 'Play'}
          </button>
          <button
            type="button"
            className="button"
            onClick={() => setStepIndex((value) => Math.max(0, value - 1))}
            disabled={!run || stepIndex === 0}
          >
            Previous step
          </button>
          <button
            type="button"
            className="button"
            onClick={() => setStepIndex((value) => Math.min(frames.length - 1, value + 1))}
            disabled={!run || stepIndex >= frames.length - 1}
          >
            Next step
          </button>
          <button
            type="button"
            className="button"
            onClick={() => {
              setStepIndex(0);
              setReplayNotice(
                'Replay is showing the recorded frames and outcomes of this saved run. It is not a new measurement.',
              );
            }}
            disabled={!run}
          >
            Replay
          </button>
          <button
            type="button"
            className="button"
            onClick={() => {
              setCandidates(4);
              setTarget(2);
              setIterations(1);
              setShots(256);
              setPreparation('uniform');
              setReplayNotice('Preset restored. Earlier saved runs are kept.');
            }}
          >
            Reset preset
          </button>
        </div>

        {busy && (
          <p className="note" role="status" aria-live="polite">
            Computing the circuit. The panels below still show the previous verified result
            until the new one arrives.
          </p>
        )}
        {error && (
          <p className="note note--warning" role="alert">
            {error}
          </p>
        )}
        {replayNotice && <p className="note">{replayNotice}</p>}
      </Panel>

      {run && frame && (
        <>
          <Panel
            title={`State after step ${frame.step_index}`}
            badge={run.result.result_kind.replace(/_/g, ' ')}
            actions={
              <span className="badge badge--navy">
                {run.label} · seed {run.seed ?? 'unseeded'}
              </span>
            }
          >
            <ol className="stage-list">
              {run.stages.map((stage) => (
                <li key={stage.name}>
                  <button
                    type="button"
                    className="button button--small"
                    aria-pressed={stepIndex === stage.end_step}
                    onClick={() => setStepIndex(stage.end_step)}
                  >
                    {stage.name}
                  </button>
                </li>
              ))}
            </ol>
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
                  Amplitudes and probabilities at step {frame.step_index}
                </caption>
                <thead>
                  <tr>
                    <th>Candidate</th>
                    <th className="numeric">Amplitude</th>
                    <th className="numeric">Probability</th>
                    <th>Phase</th>
                  </tr>
                </thead>
                <tbody>
                  {frame.amplitudes.map((amplitude) => (
                    <tr
                      key={amplitude.index}
                      data-target={amplitude.index === activeTarget ? 'true' : undefined}
                    >
                      <td className="mono">
                        {amplitude.label}
                        {amplitude.index === activeTarget && ' — marked'}
                      </td>
                      <td className="numeric">{amplitude.re.toFixed(4)}</td>
                      <td className="numeric">{amplitude.probability.toFixed(4)}</td>
                      <td className="mono">
                        {amplitude.phase_radians === null
                          ? 'undefined'
                          : `${amplitude.phase_radians.toFixed(3)} rad`}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="note">
              An amplitude whose magnitude is zero has no defined phase, so the table prints
              &ldquo;undefined&rdquo; rather than an invented angle.
            </p>
          </Panel>

          <Panel title="If you measured now" badge={`${run.shots} shots · final state`}>
            <CountsChart
              labels={run.result.basis_labels}
              counts={run.result.counts}
              shots={run.shots}
            />
            <p className="note">
              Exact target probability from the simulated circuit:{' '}
              <span className="mono">
                {run.result.exact_probabilities[activeTarget].toFixed(6)}
              </span>
              {run.formula_applies && run.analytical_target_probability !== null && (
                <>
                  {' '}
                  · analytical prediction{' '}
                  <span className="mono">{run.analytical_target_probability.toFixed(6)}</span>
                </>
              )}
            </p>
            {!run.formula_applies && run.formula_note && (
              <p className="note note--warning">{run.formula_note}</p>
            )}
            <p className="note">{run.cost_note}</p>
            <p className="note mono">
              {run.engine} {run.engine_version} · run {run.run_id.slice(0, 8)} · revision{' '}
              {run.revision_id.slice(0, 8)}
            </p>
          </Panel>

          {previousRun && (
            <Panel title="Compare with your previous run" badge="Saved runs">
              <div className="scroll-x">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Run</th>
                      <th className="numeric">N</th>
                      <th className="numeric">Iterations</th>
                      <th className="numeric">Shots</th>
                      <th className="numeric">Exact target probability</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[previousRun, run].map((entry) => (
                      <tr key={entry.run_id}>
                        <td>{entry.label}</td>
                        <td className="numeric">{entry.candidates}</td>
                        <td className="numeric">{String(entry.context?.iterations ?? '—')}</td>
                        <td className="numeric">{entry.shots}</td>
                        <td className="numeric">
                          {entry.result.exact_probabilities[entry.target].toFixed(6)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Panel>
          )}
        </>
      )}

      {!compact && analysis.data && (
        <Panel title="Iteration count and the classical baseline" badge="Analytical prediction">
          <p className="note">{analysis.data.note}</p>
          <p className="mono">{analysis.data.formula}</p>
          <div className="scroll-x">
            <table className="data-table">
              <caption className="visually-hidden">
                Ideal target probability by iteration count for N = {analysis.data.candidates}
              </caption>
              <thead>
                <tr>
                  <th className="numeric">Grover iterations</th>
                  <th className="numeric">Ideal target probability</th>
                  <th className="numeric">Classical check-and-guess</th>
                  <th className="numeric">Classical checked only</th>
                </tr>
              </thead>
              <tbody>
                {analysis.data.rows.map((row) => (
                  <tr
                    key={row.iterations}
                    data-peak={row.iterations === analysis.data!.best_iterations || undefined}
                  >
                    <td className="numeric">
                      {row.iterations}
                      {row.iterations === analysis.data!.best_iterations && ' ← first peak'}
                    </td>
                    <td className="numeric">
                      {(row.ideal_target_probability * 100).toFixed(4)}%
                    </td>
                    <td className="numeric">
                      {(row.classical_check_and_guess * 100).toFixed(2)}%
                    </td>
                    <td className="numeric">
                      {(row.classical_checked_only * 100).toFixed(2)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <h3>Assumptions this formula depends on</h3>
          <ul>
            {analysis.data.assumptions.map((assumption) => (
              <li key={assumption}>{assumption}</li>
            ))}
          </ul>
        </Panel>
      )}

      {!compact && classical.data && (
        <Panel title="The classical side, one query at a time" badge="Analytical prediction">
          <p className="note">{classical.data.note}</p>
          <div className="scroll-x">
            <table className="data-table">
              <thead>
                <tr>
                  <th className="numeric">Query</th>
                  <th>Candidate checked</th>
                  <th>Answer</th>
                </tr>
              </thead>
              <tbody>
                {classical.data.trace.map((entry) => (
                  <tr key={entry.query}>
                    <td className="numeric">{entry.query}</td>
                    <td className="mono">{entry.candidate}</td>
                    <td>{entry.matches ? 'yes — this is the marked candidate' : 'no'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="note">
            Found after <strong>{classical.data.queries_used}</strong> queries scanning in
            increasing order. Averaged over a uniformly located target, checking every candidate
            needs {classical.data.stopping_rules.checks_every_candidate_mean.toFixed(3)} checks
            with worst case {classical.data.stopping_rules.checks_every_candidate_worst}; using
            the exactly-one-target promise to infer the last candidate needs{' '}
            {classical.data.stopping_rules.uses_promise_mean.toFixed(3)} with worst case{' '}
            {classical.data.stopping_rules.uses_promise_worst}. Both are linear in N.
          </p>
        </Panel>
      )}
    </div>
  );
}
