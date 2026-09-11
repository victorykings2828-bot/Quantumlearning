import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import { startGuestSession } from '@/api/client';

interface SessionState {
  principalId: string | null;
  created: boolean;
  disclosure: string;
  status: 'loading' | 'ready' | 'error';
  error: string | null;
  refresh: () => void;
}

const SessionContext = createContext<SessionState | null>(null);

export function SessionProvider({ children }: { children: ReactNode }) {
  const [principalId, setPrincipalId] = useState<string | null>(null);
  const [created, setCreated] = useState(false);
  const [disclosure, setDisclosure] = useState('');
  const [status, setStatus] = useState<'loading' | 'ready' | 'error'>('loading');
  const [error, setError] = useState<string | null>(null);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setStatus('loading');
    startGuestSession()
      .then((session) => {
        if (cancelled) return;
        setPrincipalId(session.principal_id);
        setCreated(session.created);
        setDisclosure(session.disclosure);
        setStatus('ready');
        setError(null);
      })
      .catch((cause: Error) => {
        if (cancelled) return;
        setStatus('error');
        setError(
          `Could not start a guest session: ${cause.message} The course content is still readable.`,
        );
      });
    return () => {
      cancelled = true;
    };
  }, [tick]);

  const value = useMemo<SessionState>(
    () => ({
      principalId,
      created,
      disclosure,
      status,
      error,
      refresh: () => setTick((current) => current + 1),
    }),
    [principalId, created, disclosure, status, error],
  );

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

export function useSession(): SessionState {
  const context = useContext(SessionContext);
  if (!context) {
    throw new Error('useSession must be used inside SessionProvider');
  }
  return context;
}
