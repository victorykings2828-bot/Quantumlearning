import { createContext } from 'react';

export interface TutorScope {
  topicId: string | null;
  runId: string | null;
  runLabel: string | null;
  stepIndex: number | null;
  mode: 'practice' | 'test';
}

export interface TutorState extends TutorScope {
  open: boolean;
  setOpen: (open: boolean) => void;
  setContext: (scope: Partial<TutorScope>) => void;
}

export const TutorCtx = createContext<TutorState | null>(null);
