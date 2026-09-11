import { useCallback, useEffect, useRef, useState } from 'react';
import { api, ApiError } from '@/api/client';

interface QueryState<T> {
  data: T | null;
  error: string | null;
  loading: boolean;
  reload: () => void;
}

/**
 * A small fetch hook that discards a response whose request has been
 * superseded, so a stale payload can never be shown beside newer inputs.
 */
export function useApiQuery<T>(path: string | null, deps: unknown[] = []): QueryState<T> {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [tick, setTick] = useState(0);
  const requestId = useRef(0);

  useEffect(() => {
    if (!path) {
      setData(null);
      setLoading(false);
      return;
    }
    const id = ++requestId.current;
    const controller = new AbortController();
    setLoading(true);
    api
      .get<T>(path, controller.signal)
      .then((payload) => {
        if (id !== requestId.current) return;
        setData(payload);
        setError(null);
        setLoading(false);
      })
      .catch((cause: unknown) => {
        if (id !== requestId.current) return;
        if (cause instanceof DOMException && cause.name === 'AbortError') return;
        const message = cause instanceof ApiError ? cause.message : String(cause);
        setError(message);
        setLoading(false);
      });
    return () => controller.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [path, tick, ...deps]);

  const reload = useCallback(() => setTick((current) => current + 1), []);
  return { data, error, loading, reload };
}
