import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from 'react';

export interface TutorScope {
  topicId: string | null;
  runId: string | null;
  runLabel: string | null;
  stepIndex: number | null;
  mode: 'practice' | 'test';
}

interface TutorState extends TutorScope {
  open: boolean;
  setOpen: (open: boolean) => void;
  setContext: (scope: Partial<TutorScope>) => void;
}

const EMPTY: TutorScope = {
  topicId: null,
  runId: null,
  runLabel: null,
  stepIndex: null,
  mode: 'practice',
};

const TutorCtx = createContext<TutorState | null>(null);

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

export function useTutor(): TutorState {
  const context = useContext(TutorCtx);
  if (!context) {
    throw new Error('useTutor must be used inside TutorProvider');
  }
  return context;
}
