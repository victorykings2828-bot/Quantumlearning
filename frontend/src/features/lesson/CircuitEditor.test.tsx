import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { CircuitEditor } from './CircuitEditor';
import { buildCircuit } from './circuit';

describe('buildCircuit', () => {
  it('maps a named preset onto the validated schema', () => {
    expect(buildCircuit('card_b', ['h', 'z'])).toEqual({
      schema_version: 'circuit/v1',
      qubits: 1,
      initial_state: { kind: 'named', named: 'card_b' },
      operations: [
        { op: 'h', targets: [0], controls: [] },
        { op: 'z', targets: [0], controls: [] },
      ],
    });
  });

  it('maps the basis presets to basis indices', () => {
    expect(buildCircuit('ket1', []).initial_state).toEqual({ kind: 'basis', basis_index: 1 });
  });
});

describe('CircuitEditor', () => {
  it('adds a gate between a fixed prefix and a fixed suffix', async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(
      <CircuitEditor
        initial="ket0"
        initialOptions={['ket0']}
        operations={['h', 'h']}
        palette={['z']}
        maxGates={3}
        lockedPrefix={['h']}
        lockedSuffix={['h']}
        onChangeInitial={() => undefined}
        onChangeOperations={onChange}
      />,
    );
    await user.click(screen.getByRole('button', { name: 'Z' }));
    expect(onChange).toHaveBeenCalledWith(['h', 'z', 'h']);
  });

  it('refuses to add beyond the published gate limit', async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(
      <CircuitEditor
        initial="ket0"
        initialOptions={['ket0']}
        operations={['x', 'x', 'x']}
        palette={['x']}
        maxGates={3}
        onChangeInitial={() => undefined}
        onChangeOperations={onChange}
      />,
    );
    const button = screen.getByRole('button', { name: 'X' });
    expect(button).toBeDisabled();
    await user.click(button).catch(() => undefined);
    expect(onChange).not.toHaveBeenCalled();
  });

  it('supports keyboard gate insertion and removal', async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(
      <CircuitEditor
        initial="ket0"
        initialOptions={['ket0']}
        operations={['x']}
        palette={['h']}
        maxGates={4}
        onChangeInitial={() => undefined}
        onChangeOperations={onChange}
      />,
    );
    await user.tab();
    await user.tab();
    await user.tab();
    await user.keyboard('{Enter}');
    expect(onChange).toHaveBeenCalled();
  });

  it('marks fixed gates as not removable', () => {
    render(
      <CircuitEditor
        initial="ket0"
        initialOptions={['ket0']}
        operations={['h', 'h']}
        palette={['z']}
        maxGates={3}
        lockedPrefix={['h']}
        lockedSuffix={['h']}
        onChangeInitial={() => undefined}
        onChangeOperations={() => undefined}
      />,
    );
    expect(screen.getAllByText('fixed')).toHaveLength(2);
    expect(screen.queryByRole('button', { name: /Remove/ })).toBeNull();
  });
});
