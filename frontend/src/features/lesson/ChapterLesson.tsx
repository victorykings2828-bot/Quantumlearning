import { useEffect, useRef, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { api } from '@/api/client';
import { useApiQuery } from '@/app/useApi';
import { BlochSummary, ProbabilityChart, CountsChart } from '@/components/charts';
import { Loading, Markdown, PageHeader, Panel, ErrorBanner } from '@/components/primitives';
import type { RunRecord, Topic } from '@/api/types';
import { useTutor } from '@/features/tutor/useTutor';

type LessonTopic = Topic & { lab: Topic['lab'] & { variants: string[] } };

export function ChapterLesson() {
  const { topicId, chapterId } = useParams();
  const { data, loading, error } = useApiQuery<LessonTopic>(`/topics/${topicId}`, [topicId]);
  if (loading) return <Loading label="Loading this lesson." />;
  if (error) return <ErrorBanner message={error} />;
  if (!data || chapterId !== `chapter-${data.id.split('-')[0]}`)
    return <p>No such topic in this chapter.</p>;
  return <ChapterExperiment key={data.id} topic={data} chapterId={chapterId} />;
}

function ChapterExperiment({ topic, chapterId }: { topic: LessonTopic; chapterId: string }) {
  const [variant, setVariant] = useState('A');
  const [angle, setAngle] = useState(Math.PI / 2);
  const [basis, setBasis] = useState('Z');
  const [correction, setCorrection] = useState(true);
  const [run, setRun] = useState<RunRecord | null>(null);
  const [step, setStep] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);
  const [motion, setMotion] = useState(
    () => !window.matchMedia('(prefers-reduced-motion: reduce)').matches,
  );
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [prediction, setPrediction] = useState(topic.recorded_prediction?.selection ?? '');
  const [read, setRead] = useState(Boolean(topic.completed_steps?.[`${topic.id}-read`]));
  const request = useRef(0);
  const { setContext } = useTutor();
  useEffect(() => {
    setContext({
      topicId: topic.id,
      runId: null,
      runLabel: null,
      stepIndex: null,
      mode: 'practice',
    });
    let active = true;
    const generation = ++request.current;
    api
      .get<{ runs: { run_id: string }[] }>(`/topics/${topic.id}/runs`)
      .then(async (history) => {
        if (!history.runs?.length) return;
        const saved = await api.get<RunRecord>(`/runs/${history.runs[0].run_id}`);
        if (active && request.current === generation) {
          setRun(saved);
          setStep(0);
          const inputs = saved.context?.inputs as
            | { variant?: string; angle?: number; basis?: string; correction?: boolean }
            | undefined;
          if (inputs) {
            setVariant(inputs.variant ?? 'A');
            setAngle(inputs.angle ?? Math.PI / 2);
            setBasis(inputs.basis ?? 'Z');
            setCorrection(inputs.correction ?? true);
          }
        }
      })
      .catch(() => {
        /* A first visit has no run to restore. */
      });
    return () => {
      active = false;
      request.current += 1;
    };
  }, [topic.id, setContext]);
  useEffect(() => {
    if (!playing || !run) return;
    const timer = window.setInterval(
      () =>
        setStep((current) => {
          if (current >= run.result.frames.length - 1) {
            setPlaying(false);
            return current;
          }
          return current + 1;
        }),
      1100 / speed,
    );
    return () => window.clearInterval(timer);
  }, [playing, run, speed]);
  useEffect(() => {
    setContext({
      topicId: topic.id,
      runId: run?.run_id ?? null,
      runLabel: run ? `run ${run.ordinal}` : null,
      stepIndex: run ? step : null,
    });
  }, [run, step, topic.id, setContext]);
  function changed() {
    request.current += 1;
    setRun(null);
    setPlaying(false);
    setBusy(false);
  }
  async function execute() {
    const token = ++request.current;
    setBusy(true);
    setError('');
    setPlaying(false);
    try {
      await api.post(`/topics/${topic.id}/prediction`, {
        prediction_id: `${topic.id}-predict`,
        selection: prediction,
      });
      const result = await api.post<RunRecord>(`/chapter-labs/${topic.id}`, {
        variant,
        angle,
        basis,
        correction,
        shots: 256,
      });
      if (token === request.current) {
        setRun(result);
        setStep(0);
      }
    } catch (e) {
      if (token === request.current) setError(String(e));
    } finally {
      if (token === request.current) setBusy(false);
    }
  }
  const frame = run?.result.frames[step];
  const animation = ['2-4', '3-4'].includes(topic.id);
  return (
    <>
      <PageHeader
        eyebrow={`Chapter ${chapterId.split('-')[1]} · Topic ${topic.number}`}
        title={topic.title}
        lede={topic.objective}
      />
      <Panel title="Understand the idea">
        <Markdown text={topic.teach_markdown} />
        <p>
          <button
            className="button"
            disabled={read}
            onClick={async () => {
              try {
                await api.post(`/topics/${topic.id}/steps`, { step_id: `${topic.id}-read` });
                setRead(true);
              } catch (e) {
                setError(String(e));
              }
            }}
          >
            {read ? 'Reading recorded' : 'I have read this explanation'}
          </button>
        </p>
        <p className="note">
          Reading records practice. The understanding check asks you to explain and apply the
          idea.
        </p>
      </Panel>
      <Panel title="Predict, then explore">
        <div className="chapter-controls">
          {topic.id !== '2-4' && (
            <label>
              Preparation / experiment
              <select
                value={variant}
                onChange={(e) => {
                  setVariant(e.target.value);
                  changed();
                }}
              >
                {topic.lab.variants.map((label, i) => (
                  <option key={i} value={['A', 'B', 'C'][i]}>
                    {label}
                  </option>
                ))}
              </select>
            </label>
          )}
          {['2-1', '2-3', '2-4'].includes(topic.id) && (
            <label>
              Phase φ: {(angle / Math.PI).toFixed(2)}π radians
              <input
                type="range"
                min="0"
                max={2 * Math.PI}
                step={Math.PI / 8}
                value={angle}
                onChange={(e) => {
                  setAngle(Number(e.target.value));
                  changed();
                }}
              />
              <span className="button-row">
                {[0, Math.PI / 2, Math.PI].map((value) => (
                  <button
                    className="button"
                    key={value}
                    onClick={() => {
                      setAngle(value);
                      changed();
                    }}
                  >
                    {value === 0 ? '0' : value === Math.PI ? 'π' : 'π/2'}
                  </button>
                ))}
              </span>
            </label>
          )}
          {topic.id !== '3-7' && (
            <label>
              Readout basis
              <select
                value={basis}
                onChange={(e) => {
                  setBasis(e.target.value);
                  changed();
                }}
              >
                {['Z', 'X', 'Y'].map((value) => (
                  <option key={value}>{value}</option>
                ))}
              </select>
            </label>
          )}
          {topic.id === '3-7' && (
            <label>
              <input
                type="checkbox"
                checked={correction}
                onChange={(e) => {
                  setCorrection(e.target.checked);
                  changed();
                }}
              />{' '}
              Apply Bob's conditional corrections
            </label>
          )}
        </div>
        <label>
          Your prediction
          <textarea
            value={prediction}
            maxLength={1000}
            onChange={(e) => setPrediction(e.target.value)}
            placeholder="What will change? Why?"
          />
        </label>
        <button
          className="button button--primary"
          onClick={execute}
          disabled={busy || !prediction.trim()}
        >
          {busy ? 'Computing…' : 'Save prediction and run'}
        </button>
        {error && <ErrorBanner message={error} />}
      </Panel>
      {run && frame && (
        <>
          <Panel title={`Step ${frame.step_index}: ${frame.label}`} badge="Qiskit simulation">
            <div className="button-row">
              <button
                className="button"
                disabled={step === 0}
                onClick={() => {
                  setPlaying(false);
                  setStep(step - 1);
                }}
              >
                Previous
              </button>
              <button
                className="button"
                disabled={step >= run.result.frames.length - 1}
                onClick={() => {
                  setPlaying(false);
                  setStep(step + 1);
                }}
              >
                Next step
              </button>
              <button
                className="button"
                onClick={() => {
                  setStep(0);
                  setPlaying(false);
                }}
              >
                Replay from start
              </button>
              <button
                className="button"
                disabled={!motion}
                onClick={() => {
                  if (step === run.result.frames.length - 1) setStep(0);
                  setPlaying(!playing);
                }}
              >
                {playing ? 'Pause' : 'Play'}
              </button>
              <label>
                Speed
                <select value={speed} onChange={(e) => setSpeed(Number(e.target.value))}>
                  <option value="0.5">Slow</option>
                  <option value="1">Normal</option>
                  <option value="2">Fast</option>
                </select>
              </label>
              <label>
                <input
                  type="checkbox"
                  checked={motion}
                  onChange={(e) => {
                    setMotion(e.target.checked);
                    setPlaying(false);
                  }}
                />{' '}
                Motion
              </label>
            </div>
            <p className="note">
              Steps replay saved computed states. Movement between steps illustrates the
              mathematics; it is not a measured particle trajectory. Teleportation frames show
              labelled alternative branches, not a single sequential history.
            </p>
            {animation && frame.amplitudes.length > 0 && (
              <svg
                className="phase-diagram"
                viewBox="0 0 600 180"
                role="img"
                aria-label="Complex amplitude arrows; horizontal real component, vertical imaginary component"
              >
                {frame.amplitudes.map((a, i) => (
                  <g key={a.index} transform={`translate(${75 + i * 140},85)`}>
                    <circle r="55" fill="none" stroke="#c8c0ae" />
                    <path d="M-60 0 H60 M0 -60 V60" stroke="#c8c0ae" />
                    <line
                      x1="0"
                      y1="0"
                      x2={a.re * 55}
                      y2={-a.im * 55}
                      stroke="#b34832"
                      strokeWidth="4"
                      style={{ transition: motion ? 'all 450ms ease' : 'none' }}
                    />
                    <circle cx={a.re * 55} cy={-a.im * 55} r="4" fill="#1d3548" />
                    <text y="80" textAnchor="middle">
                      {a.label}
                    </text>
                  </g>
                ))}
              </svg>
            )}
            <table>
              <caption>Selected frame: exact amplitudes and probabilities</caption>
              <thead>
                <tr>
                  <th>Outcome</th>
                  <th>Amplitude</th>
                  <th>Probability</th>
                </tr>
              </thead>
              <tbody>
                {run.result.basis_labels.map((label, i) => (
                  <tr key={label}>
                    <td>{label}</td>
                    <td>
                      {frame.amplitudes[i]
                        ? `${frame.amplitudes[i].re.toFixed(4)} ${frame.amplitudes[i].im < 0 ? '−' : '+'} ${Math.abs(frame.amplitudes[i].im).toFixed(4)}i`
                        : 'Mixed state: no single amplitude'}
                    </td>
                    <td>{(100 * frame.probabilities[i]).toFixed(2)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <ProbabilityChart labels={run.result.basis_labels} values={frame.probabilities} />
            <BlochSummary states={frame.reduced_states} />
            <div className="grid-two">
              {frame.reduced_states.map(({ qubit, bloch }) => {
                const sx = (62 * (bloch[0] - bloch[1])) / Math.sqrt(2);
                const sy =
                  62 * ((bloch[0] + bloch[1]) / Math.sqrt(6) - Math.sqrt(2 / 3) * bloch[2]);
                return (
                  <svg
                    key={qubit}
                    viewBox="0 0 180 190"
                    style={{ maxHeight: 210, width: '100%' }}
                    role="img"
                    aria-label={`Bloch sphere, qubit ${qubit}. Coordinates are listed above.`}
                  >
                    <g transform="translate(90,85)">
                      <circle r="62" fill="#e6e0d1" stroke="#b6ae9c" />
                      <ellipse
                        rx="62"
                        ry="35.8"
                        fill="none"
                        stroke="#b6ae9c"
                        strokeDasharray="4 4"
                      />
                      <path d="M-44 -25 L44 25 M44 -25 L-44 25 M0 51 V-51" stroke="#b6ae9c" />
                      <text x="47" y="34">
                        x
                      </text>
                      <text x="-55" y="34">
                        y
                      </text>
                      <text y="-56">z</text>
                      <line
                        x1="0"
                        y1="0"
                        x2={sx}
                        y2={sy}
                        stroke="#b34832"
                        strokeWidth="3"
                        style={{ transition: motion && animation ? 'all 450ms ease' : 'none' }}
                      />
                      <circle cx={sx} cy={sy} r="4" fill="#1d3548" />
                      <text y="94" textAnchor="middle">
                        Qubit {qubit}: projected Bloch vector
                      </text>
                    </g>
                  </svg>
                );
              })}
            </div>
            {topic.id === '3-5' && (
              <>
                <h3>Marginal and conditional probabilities</h3>
                <p>Derived by summing the exact joint probabilities of this frame.</p>
                <p>
                  P(q0=1) = {(frame.probabilities[1] + frame.probabilities[3]).toFixed(4)};
                  P(q1=1) = {(frame.probabilities[2] + frame.probabilities[3]).toFixed(4)}.
                </p>
                <p>
                  P(q1=1 given q0=0) ={' '}
                  {frame.probabilities[0] + frame.probabilities[2] > 1e-12
                    ? (
                        frame.probabilities[2] /
                        (frame.probabilities[0] + frame.probabilities[2])
                      ).toFixed(4)
                    : 'undefined: conditioning event has zero probability'}
                  .
                </p>
              </>
            )}
          </Panel>
          <Panel title="If we measure the final state">
            <CountsChart
              labels={run.result.basis_labels}
              counts={run.result.counts}
              shots={run.result.shots}
            />
            {run.result.notes.map((note) => (
              <p className="note" key={note}>
                {note}
              </p>
            ))}
          </Panel>
        </>
      )}
      <Panel title="Explain and transfer">
        <p>
          Compare your prediction with the result. Try a different input or readout basis before
          taking a fresh understanding check.
        </p>
        <Link
          className="button button--primary"
          to={`/evidence/${chapterId}?topic=${topic.id}`}
        >
          Check my understanding
        </Link>
        <ul>
          {topic.sources.map((s) => (
            <li key={s.id}>
              <a href={s.url} target="_blank" rel="noreferrer">
                {s.title}
              </a>
            </li>
          ))}
        </ul>
      </Panel>
      <p className="button-row">
        <Link className="button" to={`/course/${chapterId}`}>
          Chapter overview
        </Link>
        {topic.next_topic_id && (
          <Link className="button" to={`/learn/${chapterId}/${topic.next_topic_id}`}>
            Next topic
          </Link>
        )}
      </p>
    </>
  );
}
