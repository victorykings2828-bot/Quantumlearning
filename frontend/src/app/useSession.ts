import { useContext } from 'react';
import { SessionContext, type SessionState } from './sessionContext';

export function useSession(): SessionState {
  const context = useContext(SessionContext);
  if (!context) {
    throw new Error('useSession must be used inside SessionProvider');
  }
  return context;
}
