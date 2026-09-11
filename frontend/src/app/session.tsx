import { useEffect, useMemo, useState, type ReactNode } from 'react';
import { startGuestSession } from '@/api/client';
import { SessionContext, type SessionState } from './sessionContext';

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
