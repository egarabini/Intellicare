type QueryValue = string | number | boolean | null | undefined;

export interface RequestOptions extends Omit<RequestInit, 'body'> {
  query?: Record<string, QueryValue>;
  body?: unknown;
  timeoutMs?: number;
  retry503?: boolean;
}

export class HttpError extends Error {
  status: number;
  payload: unknown;

  constructor(status: number, message: string, payload: unknown) {
    super(message);
    this.name = 'HttpError';
    this.status = status;
    this.payload = payload;
  }
}

function withQuery(path: string, query?: Record<string, QueryValue>): string {
  if (!query) return path;
  const params = new URLSearchParams();
  Object.entries(query).forEach(([key, value]) => {
    if (value === null || value === undefined || value === '') return;
    params.append(key, String(value));
  });
  const encoded = params.toString();
  if (!encoded) return path;
  return `${path}${path.includes('?') ? '&' : '?'}${encoded}`;
}

async function parseResponse(response: Response): Promise<unknown> {
  const contentType = response.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    return response.json();
  }
  return response.text();
}

export function createApiClient(baseUrl: string) {
  async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
    const {
      query,
      body,
      timeoutMs = 30_000,
      retry503 = true,
      headers,
      ...init
    } = options;
    const url = `${baseUrl}${withQuery(path, query)}`;
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    const token = localStorage.getItem('token');

    const doFetch = async () => {
      const response = await fetch(url, {
        ...init,
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
          ...(headers || {}),
        },
        body: body !== undefined ? JSON.stringify(body) : undefined,
        signal: controller.signal,
      });

      const payload = await parseResponse(response);
      if (!response.ok) {
        throw new HttpError(response.status, `HTTP ${response.status} for ${url}`, payload);
      }
      return payload as T;
    };

    try {
      return await doFetch();
    } catch (error) {
      if (retry503 && error instanceof HttpError && error.status === 503) {
        return doFetch();
      }
      throw error;
    } finally {
      clearTimeout(timer);
    }
  }

  return { request };
}

export const moduleUrls = {
  oswaldo:
    import.meta.env.VITE_API_OSWALDO_URL ||
    import.meta.env.VITE_OSWALDO_URL ||
    'http://localhost:8002',
  florence:
    import.meta.env.VITE_API_FLORENCE_URL ||
    import.meta.env.VITE_FLORENCE_URL ||
    'http://localhost:8001',
  geralda:
    import.meta.env.VITE_API_GERALDA_URL ||
    import.meta.env.VITE_GERALDA_URL ||
    'http://localhost:8006',
  wanda:
    import.meta.env.VITE_API_WANDA_URL ||
    import.meta.env.VITE_WANDA_URL ||
    'http://localhost:8004',
  grahame:
    import.meta.env.VITE_API_GRAHAME_URL ||
    import.meta.env.VITE_GRAHAME_URL ||
    'http://localhost:8012',
  zilda:
    import.meta.env.VITE_API_ZILDA_URL ||
    import.meta.env.VITE_ZILDA_URL ||
    'http://localhost:8007',
  donabedian:
    import.meta.env.VITE_API_DONABEDIAN_URL ||
    import.meta.env.VITE_DONABEDIAN_URL ||
    'http://localhost:8003',
};
