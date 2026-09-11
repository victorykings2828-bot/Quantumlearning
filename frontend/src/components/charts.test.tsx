import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { AmplitudeChart, BlochSummary, CountsChart, ProbabilityChart } from './charts';
import type { AmplitudeView } from '@/api/types';

function amplitude(partial: Partial<AmplitudeView>): AmplitudeView {
  return {
    index: 0,
    label: '|0>',
    re: 0,
    im: 0,
    magnitude: 0,
    probability: 0,
    phase_radians: null,
    ...partial,
  };
}

describe('AmplitudeChart', () => {
  it('draws no bar for a vanishing amplitude', () => {
    const { container } = render(
      <AmplitudeChart
        amplitudes={[
          amplitude({
            index: 0,
            label: '|0>',
            re: 1,
            magnitude: 1,
            probability: 1,
            phase_radians: 0,
          }),
          amplitude({ index: 1, label: '|1>', re: -0, magnitude: 0 }),
        ]}
      />,
    );
    expect(container.querySelectorAll('rect')).toHaveLength(1);
  });

  it('marks a negative amplitude differently from a positive one', () => {
    const { container } = render(
      <AmplitudeChart
        amplitudes={[
          amplitude({
            index: 0,
            re: 0.7071,
            magnitude: 0.7071,
            probability: 0.5,
            phase_radians: 0,
          }),
          amplitude({
            index: 1,
            label: '|1>',
            re: -0.7071,
            magnitude: 0.7071,
            probability: 0.5,
            phase_radians: Math.PI,
          }),
        ]}
      />,
    );
    const rects = Array.from(container.querySelectorAll('rect'));
    expect(rects[0].getAttribute('fill')).not.toEqual(rects[1].getAttribute('fill'));
  });

  it('explains that probability hides the sign', () => {
    render(
      <AmplitudeChart amplitudes={[amplitude({ re: 1, magnitude: 1, probability: 1 })]} />,
    );
    expect(screen.getByText(/squared magnitude/i)).toBeInTheDocument();
  });
});

describe('ProbabilityChart', () => {
  it('renders a percentage label for each outcome', () => {
    render(<ProbabilityChart labels={['|0>', '|1>']} values={[0.36, 0.64]} />);
    expect(screen.getByText('36.00%')).toBeInTheDocument();
    expect(screen.getByText('64.00%')).toBeInTheDocument();
  });
});

describe('CountsChart', () => {
  it('separates counts from frequencies', () => {
    render(
      <CountsChart labels={['|0>', '|1>']} counts={{ '|0>': 129, '|1>': 127 }} shots={256} />,
    );
    expect(screen.getByText('129')).toBeInTheDocument();
    expect(screen.getByText('50.39%')).toBeInTheDocument();
    expect(screen.getByText('49.61%')).toBeInTheDocument();
  });
});

describe('BlochSummary', () => {
  it('describes an entangled qubit as having a mixed reduced state', () => {
    render(
      <BlochSummary
        states={[{ qubit: 0, bloch: [0, 0, 0], bloch_length: 0, is_mixed: true }]}
      />,
    );
    expect(screen.getByText(/mixed reduced state/i)).toBeInTheDocument();
    expect(screen.queryByText(/no state of their own/i)).toBeNull();
  });
});
