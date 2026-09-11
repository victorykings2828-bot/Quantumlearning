import type { CircuitSpec, InitialStateName, Operation, OperationName } from '@/api/types';

export const STATE_LABELS: Record<InitialStateName, string> = {
  ket0: '|0>',
  ket1: '|1>',
  plus: '|+>',
  minus: '|->',
  card_b: 'Card B (3/5, 4/5)',
  card_c: 'Card C (-3/5, 4/5)',
};

export function initialStateSpec(name: InitialStateName): CircuitSpec['initial_state'] {
  if (name === 'ket0') return { kind: 'basis', basis_index: 0 };
  if (name === 'ket1') return { kind: 'basis', basis_index: 1 };
  return { kind: 'named', named: name };
}

export function buildCircuit(
  initial: InitialStateName,
  operations: OperationName[],
  qubits = 1,
): CircuitSpec {
  return {
    schema_version: 'circuit/v1',
    qubits,
    initial_state: initialStateSpec(initial),
    operations: operations.map<Operation>((op) => ({ op, targets: [0], controls: [] })),
  };
}
