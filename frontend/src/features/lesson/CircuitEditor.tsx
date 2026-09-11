import type { CircuitSpec, InitialStateName, Operation, OperationName } from '@/api/types';

const GATE_LABELS: Record<OperationName, string> = {
  x: 'X',
  h: 'H',
  z: 'Z',
  cx: 'CNOT',
  cz: 'CZ',
  mcz: 'MCZ',
  measure_z: 'Measure Z',
};

const GATE_DESCRIPTIONS: Record<OperationName, string> = {
  x: 'Exchanges the two amplitudes.',
  h: 'Maps |0> to |+> and |1> to |->. Deterministic, not a coin flip.',
  z: 'Changes the sign of the second amplitude. Immediate Z probabilities do not change.',
  cx: 'Controlled NOT.',
  cz: 'Controlled Z.',
  mcz: 'Multi-controlled Z.',
  measure_z: 'A real Z-basis measurement inside the circuit. This ends interference.',
};

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

export function CircuitEditor({
  initial,
  initialOptions,
  operations,
  palette,
  maxGates,
  disabled = false,
  lockedPrefix = [],
  lockedSuffix = [],
  onChangeInitial,
  onChangeOperations,
}: {
  initial: InitialStateName;
  initialOptions: InitialStateName[];
  operations: OperationName[];
  palette: OperationName[];
  maxGates: number;
  disabled?: boolean;
  lockedPrefix?: OperationName[];
  lockedSuffix?: OperationName[];
  onChangeInitial: (value: InitialStateName) => void;
  onChangeOperations: (value: OperationName[]) => void;
}) {
  const editableStart = lockedPrefix.length;
  const editableEnd = operations.length - lockedSuffix.length;

  const addGate = (gate: OperationName) => {
    if (operations.length >= maxGates) return;
    const next = [...operations];
    next.splice(editableEnd, 0, gate);
    onChangeOperations(next);
  };

  const removeGate = (index: number) => {
    if (index < editableStart || index >= editableEnd) return;
    onChangeOperations(operations.filter((_, position) => position !== index));
  };

  const moveGate = (index: number, direction: -1 | 1) => {
    const target = index + direction;
    if (index < editableStart || index >= editableEnd) return;
    if (target < editableStart || target >= editableEnd) return;
    const next = [...operations];
    [next[index], next[target]] = [next[target], next[index]];
    onChangeOperations(next);
  };

  return (
    <div className="circuit-editor">
      {initialOptions.length > 1 && (
        <label className="field">
          <span>Initial state</span>
          <select
            value={initial}
            disabled={disabled}
            onChange={(event) => onChangeInitial(event.target.value as InitialStateName)}
          >
            {initialOptions.map((option) => (
              <option key={option} value={option}>
                {STATE_LABELS[option]}
              </option>
            ))}
          </select>
        </label>
      )}

      <h3 className="field-heading">Your circuit</h3>
      <ol className="wire" aria-label="Circuit operations in execution order">
        <li className="wire__start mono">{STATE_LABELS[initial]}</li>
        {operations.length === 0 && <li className="wire__empty">No gates yet</li>}
        {operations.map((operation, index) => {
          const locked = index < editableStart || index >= editableEnd;
          return (
            <li key={`${operation}-${index}`} className="wire__gate" data-locked={locked}>
              <span className="wire__index">{index + 1}</span>
              <span className="wire__name mono">{GATE_LABELS[operation]}</span>
              {locked ? (
                <span className="badge">fixed</span>
              ) : (
                <span className="wire__controls">
                  <button
                    type="button"
                    className="button button--small"
                    onClick={() => moveGate(index, -1)}
                    disabled={disabled || index <= editableStart}
                    aria-label={`Move ${GATE_LABELS[operation]} at position ${index + 1} earlier`}
                  >
                    ←
                  </button>
                  <button
                    type="button"
                    className="button button--small"
                    onClick={() => moveGate(index, 1)}
                    disabled={disabled || index >= editableEnd - 1}
                    aria-label={`Move ${GATE_LABELS[operation]} at position ${index + 1} later`}
                  >
                    →
                  </button>
                  <button
                    type="button"
                    className="button button--small"
                    onClick={() => removeGate(index)}
                    disabled={disabled}
                    aria-label={`Remove ${GATE_LABELS[operation]} at position ${index + 1}`}
                  >
                    Remove
                  </button>
                </span>
              )}
            </li>
          );
        })}
      </ol>

      {palette.length > 0 && (
        <>
          <h3 className="field-heading">Add a gate</h3>
          <div className="button-row">
            {palette.map((gate) => (
              <button
                key={gate}
                type="button"
                className="button"
                onClick={() => addGate(gate)}
                disabled={disabled || operations.length >= maxGates}
                title={GATE_DESCRIPTIONS[gate]}
              >
                {GATE_LABELS[gate]}
              </button>
            ))}
            <button
              type="button"
              className="button button--small"
              onClick={() => onChangeOperations([...lockedPrefix, ...lockedSuffix])}
              disabled={disabled}
            >
              Clear circuit
            </button>
          </div>
          <p className="note">
            At most {maxGates} gates. Operations run in the order shown, left to right.
          </p>
        </>
      )}
    </div>
  );
}
