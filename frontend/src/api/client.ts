/**
 * Same-origin API client.
 *
 * The browser never calls a model provider and never receives the session
 * token in a response body: the session lives in an HttpOnly cookie, and only
 * the CSRF token is readable so it can be echoed on mutations.
 */

export const API_BASE = '/api/v1';
const CSRF_COOKIE = import.meta.env.VITE_CSRF_COOKIE ?? 'qll_csrf';
const CSRF_HEADER = 'x-qll-csrf';

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;

  constructor(status: number, code: string, message: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
  }
}

function readCsrfToken(): string | null {
  const match = document.cookie.split('; ').find((row) => row.startsWith(`${CSRF_COOKIE}=`));
  return match ? decodeURIComponent(match.slice(CSRF_COOKIE.length + 1)) : null;
}

type RequestOptions = {
  method?: 'GET' | 'POST' | 'PATCH' | 'DELETE';
  body?: unknown;
  signal?: AbortSignal;
};

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const method = options.method ?? 'GET';
  const headers: Record<string, string> = { Accept: 'application/json' };
  if (options.body !== undefined) {
    headers['Content-Type'] = 'application/json';
  }
  if (method !== 'GET') {
    const csrf = readCsrfToken();
    if (csrf) {
      headers[CSRF_HEADER] = csrf;
    }
  }

  const response = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    credentials: 'same-origin',
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
    signal: options.signal,
  });

  if (response.status === 204) {
    return undefined as T;
  }

  const text = await response.text();
  const payload = text ? JSON.parse(text) : null;

  if (!response.ok) {
    const detail = payload?.detail;
    if (detail && typeof detail === 'object') {
      throw new ApiError(
        response.status,
        String(detail.code ?? 'error'),
        String(detail.message ?? 'The request failed.'),
      );
    }
    if (Array.isArray(detail) && detail.length > 0) {
      throw new ApiError(
        response.status,
        'validation_error',
        String(detail[0].msg ?? 'Invalid request.'),
      );
    }
    throw new ApiError(
      response.status,
      'error',
      `Request failed with status ${response.status}.`,
    );
  }

  return payload as T;
}

export const api = {
  get: <T>(path: string, signal?: AbortSignal) => request<T>(path, { signal }),
  post: <T>(path: string, body?: unknown, signal?: AbortSignal) =>
    request<T>(path, { method: 'POST', body: body ?? {}, signal }),
  patch: <T>(path: string, body?: unknown, signal?: AbortSignal) =>
    request<T>(path, { method: 'PATCH', body: body ?? {}, signal }),
};

/** Create or reuse the guest session. This is the only bootstrap call. */
export async function startGuestSession() {
  return api.post<{
    principal_id: string;
    created: boolean;
    expires_at: string;
    csrf_token: string;
    disclosure: string;
  }>('/guest-session');
}
