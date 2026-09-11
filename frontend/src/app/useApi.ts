import { useCallback, useEffect, useRef, useState } from 'react';
import { api, ApiError } from '@/api/client';

interface QueryState<T> {
  data: T | null;
  error: string | null;
  /** True only before the first result. A refresh never blanks the page. */
  loading: boolean;
  /** True while a refresh is in flight over data that is already displayed. */
  refreshing: boolean;
  reload: () => void;
}

/**
 * A small fetch hook that discards a response whose request has been
 * superseded, so a stale payload can never be shown beside newer inputs.
 *
 * A reload keeps the current data on screen. Blanking the page would unmount
 * whatever the learner was working in, losing their circuit, their selected
 * run and the verdict they just received.
 */
export function useApiQuery<T>(path: string | null, deps: unknown[] = []): QueryState<T> {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [tick, setTick] = useState(0);
  const requestId = useRef(0);
  const hasData = useRef(false);

  useEffect(() => {
    if (!path) {
      setData(null);
      hasData.current = false;
      setRefreshing(false);
      return;
    }
    const id = ++requestId.current;
    const controller = new AbortController();
    setRefreshing(true);
    api
      .get<T>(path, controller.signal)
      .then((payload) => {
        if (id !== requestId.current) return;
        setData(payload);
        hasData.current = true;
        setError(null);
        setRefreshing(false);
      })
      .catch((cause: unknown) => {
        if (id !== requestId.current) return;
        if (cause instanceof DOMException && cause.name === 'AbortError') return;
        setError(cause instanceof ApiError ? cause.message : String(cause));
        setRefreshing(false);
      });
    return () => controller.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [path, tick, ...deps]);

  const reload = useCallback(() => setTick((current) => current + 1), []);
  return { data, error, loading: refreshing && data === null, refreshing, reload };
}
