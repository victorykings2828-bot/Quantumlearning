import { useCallback, useMemo, useState, type ReactNode } from 'react';
import { TutorCtx, type TutorScope, type TutorState } from './context';

const EMPTY: TutorScope = {
  topicId: null,
  runId: null,
  runLabel: null,
  stepIndex: null,
  mode: 'practice',
};

export function TutorProvider({ children }: { children: ReactNode }) {
  const [scope, setScope] = useState<TutorScope>(EMPTY);
  const [open, setOpen] = useState(false);

  // Stable identity, and a no-op when nothing actually changes: callers set the
  // scope from effects, so an unstable setter would loop.
  const setContext = useCallback((next: Partial<TutorScope>) => {
    setScope((current) => {
      const merged = { ...current, ...next };
      const unchanged = (Object.keys(merged) as (keyof TutorScope)[]).every(
        (key) => merged[key] === current[key],
      );
      return unchanged ? current : merged;
    });
  }, []);

  const value = useMemo<TutorState>(
    () => ({ ...scope, open, setOpen, setContext }),
    [scope, open, setContext],
  );

  return <TutorCtx.Provider value={value}>{children}</TutorCtx.Provider>;
}
