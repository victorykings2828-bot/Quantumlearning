/**
 * Accessible SVG charts.
 *
 * Every chart has a text alternative table, uses non-colour cues, and never
 * draws a negative probability bar. Amplitude sign is shown by direction and
 * by an explicit label, not by colour alone.
 */

import type { AmplitudeView } from '@/api/types';

const WIDTH = 560;

export function AmplitudeChart({
  amplitudes,
  title = 'Amplitudes',
}: {
  amplitudes: AmplitudeView[];
  title?: string;
}) {
  const height = 170;
  const midline = height / 2;
  const columnWidth = WIDTH / Math.max(amplitudes.length, 1);
  const scale = midline - 26;

  return (
    <figure className="chart">
      <svg
        viewBox={`0 0 ${WIDTH} ${height}`}
        role="img"
        aria-label={`${title}. A text table with the same values follows.`}
        className="chart__svg"
      >
        <line x1="0" y1={midline} x2={WIDTH} y2={midline} stroke="var(--border-strong)" />
        <text x="4" y="16" fontSize="11" fill="var(--secondary)">
          +1
        </text>
        <text x="4" y={height - 6} fontSize="11" fill="var(--secondary)">
          -1
        </text>
        {amplitudes.map((amplitude, index) => {
          const value = amplitude.re;
          // A vanishing amplitude is drawn as nothing at all, so a rounding
          // artefact cannot look like a small negative bar.
          const empty = amplitude.magnitude < 1e-9;
          const barHeight = Math.abs(value) * scale;
          const x = index * columnWidth + columnWidth * 0.28;
          const barWidth = columnWidth * 0.44;
          const y = value >= 0 ? midline - barHeight : midline;
          const negative = !empty && value < 0;
          return (
            <g key={amplitude.index}>
              {!empty && (
                <rect
                  x={x}
                  y={y}
                  width={barWidth}
                  height={Math.max(barHeight, 1)}
                  fill={negative ? 'var(--red-mark)' : 'var(--blue-fill)'}
                  stroke={negative ? 'var(--red-mark)' : 'var(--blue-stroke)'}
                />
              )}
              <text
                x={x + barWidth / 2}
                y={midline + (value >= 0 ? 16 : -6)}
                fontSize="11"
                textAnchor="middle"
                fill="var(--secondary)"
                fontFamily="var(--font-mono)"
              >
                {amplitude.label}
              </text>
              {empty && (
                <text
                  x={x + barWidth / 2}
                  y={midline - 6}
                  fontSize="10"
                  textAnchor="middle"
                  fill="var(--muted)"
                >
                  0
                </text>
              )}
            </g>
          );
        })}
      </svg>
      <figcaption className="note">
        Bars above the line are positive amplitudes; bars below are negative. Probability is the
        squared magnitude, so the sign does not appear in the probability panel.
      </figcaption>
    </figure>
  );
}

export function ProbabilityChart({
  labels,
  values,
  title = 'Exact probabilities',
}: {
  labels: string[];
  values: number[];
  title?: string;
}) {
  const height = 150;
  const baseline = height - 28;
  const columnWidth = WIDTH / Math.max(labels.length, 1);
  const scale = baseline - 18;

  return (
    <figure className="chart">
      <svg
        viewBox={`0 0 ${WIDTH} ${height}`}
        role="img"
        aria-label={`${title}. A text table with the same values follows.`}
        className="chart__svg"
      >
        <line x1="0" y1={baseline} x2={WIDTH} y2={baseline} stroke="var(--border-strong)" />
        <text x="4" y="14" fontSize="11" fill="var(--secondary)">
          100%
        </text>
        <text x="4" y={baseline - 2} fontSize="11" fill="var(--secondary)">
          0
        </text>
        {labels.map((label, index) => {
          const value = values[index] ?? 0;
          const barHeight = value * scale;
          const x = index * columnWidth + columnWidth * 0.28;
          const barWidth = columnWidth * 0.44;
          return (
            <g key={label}>
              <rect
                x={x}
                y={baseline - barHeight}
                width={barWidth}
                height={Math.max(barHeight, 0)}
                fill="var(--blue-fill)"
                stroke="var(--blue-stroke)"
              />
              <text
                x={x + barWidth / 2}
                y={baseline - barHeight - 5}
                fontSize="11"
                textAnchor="middle"
                fill="var(--text)"
                fontFamily="var(--font-mono)"
              >
                {(value * 100).toFixed(value === 0 || value === 1 ? 0 : 2)}%
              </text>
              <text
                x={x + barWidth / 2}
                y={baseline + 16}
                fontSize="11"
                textAnchor="middle"
                fill="var(--secondary)"
                fontFamily="var(--font-mono)"
              >
                {label}
              </text>
            </g>
          );
        })}
      </svg>
    </figure>
  );
}

export function CountsChart({
  labels,
  counts,
  shots,
}: {
  labels: string[];
  counts: Record<string, number>;
  shots: number;
}) {
  return (
    <div className="scroll-x">
      <table className="data-table">
        <caption className="visually-hidden">
          Measured counts from {shots} shots, with observed frequencies.
        </caption>
        <thead>
          <tr>
            <th>Outcome</th>
            <th>Observed</th>
            <th className="numeric">Count</th>
            <th className="numeric">Frequency</th>
          </tr>
        </thead>
        <tbody>
          {labels.map((label) => {
            const count = counts[label] ?? 0;
            const fraction = shots > 0 ? count / shots : 0;
            return (
              <tr key={label}>
                <td className="mono">{label}</td>
                <td>
                  <div className="meter" aria-hidden="true">
                    <span style={{ width: `${fraction * 100}%` }} />
                  </div>
                </td>
                <td className="numeric">{count}</td>
                <td className="numeric">{(fraction * 100).toFixed(2)}%</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export function BlochSummary({
  states,
}: {
  states: {
    qubit: number;
    bloch: [number, number, number];
    bloch_length: number;
    is_mixed: boolean;
  }[];
}) {
  return (
    <div className="grid-two">
      {states.map((state) => (
        <div key={state.qubit} className="bloch-card">
          <h3>Qubit {state.qubit}</h3>
          <p className="mono">
            x {state.bloch[0].toFixed(3)} · y {state.bloch[1].toFixed(3)} · z{' '}
            {state.bloch[2].toFixed(3)}
          </p>
          <p className="mono">Bloch vector length {state.bloch_length.toFixed(3)}</p>
          <p className="note">
            {state.is_mixed
              ? 'This qubit has a mixed reduced state. The pair has a joint state that does not factor into two separate qubit states.'
              : 'This qubit has a pure reduced state of its own.'}
          </p>
        </div>
      ))}
    </div>
  );
}
