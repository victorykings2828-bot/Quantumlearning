import { createContext } from 'react';

export interface SessionState {
  principalId: string | null;
  created: boolean;
  disclosure: string;
  status: 'loading' | 'ready' | 'error';
  error: string | null;
  refresh: () => void;
}

export const SessionContext = createContext<SessionState | null>(null);
