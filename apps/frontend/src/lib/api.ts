/**
 * Client for the AEGIS API (same origin, under /api).
 *
 * - The session is an HttpOnly cookie that scripts cannot read; requests
 *   send it with `credentials: 'same-origin'`. Nothing about the session is
 *   stored in localStorage or sessionStorage.
 * - State-changing requests carry the CSRF token in the X-CSRF-Token header
 *   (DECISIONS.md D-065). The token is kept in memory only: it comes from the
 *   sign-in response or from GET /api/v1/auth/csrf.
 * - Responses are checked against the expected shape before use (see the
 *   `read` helpers). Errors use the API's error format and are raised as
 *   ApiError.
 */

export const API_BASE = '/api/v1'
const CSRF_HEADER = 'X-CSRF-Token'
const UNSAFE_METHODS = new Set(['POST', 'PUT', 'PATCH', 'DELETE'])
const GENERIC_ERROR = 'The server could not complete the request. Try again later.'

/** Fired when the API reports that the session is missing or has expired. */
export const UNAUTHENTICATED_EVENT = 'aegis:unauthenticated'

export interface ApiErrorDetail {
  location: (string | number)[]
  message: string
  type: string
}

export class ApiError extends Error {
  readonly status: number
  readonly code: string
  readonly requestId: string | null
  readonly details: ApiErrorDetail[]
  /** Seconds to wait, from the Retry-After header of a 429 response. */
  readonly retryAfter: number | null

  constructor(
    status: number,
    code: string,
    message: string,
    options: {
      requestId?: string | null
      details?: ApiErrorDetail[]
      retryAfter?: number | null
    } = {},
  ) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.requestId = options.requestId ?? null
    this.details = options.details ?? []
    this.retryAfter = options.retryAfter ?? null
  }
}

// --- reading untrusted JSON ------------------------------------------------

export function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function invalidResponse(): ApiError {
  return new ApiError(0, 'invalid_response', GENERIC_ERROR)
}

/** Typed field access on a response object; throws if the shape is wrong. */
export const read = {
  object(value: unknown): Record<string, unknown> {
    if (!isRecord(value)) {
      throw invalidResponse()
    }
    return value
  },
  string(value: Record<string, unknown>, key: string): string {
    const field = value[key]
    if (typeof field !== 'string') {
      throw invalidResponse()
    }
    return field
  },
  number(value: Record<string, unknown>, key: string): number {
    const field = value[key]
    if (typeof field !== 'number') {
      throw invalidResponse()
    }
    return field
  },
  boolean(value: Record<string, unknown>, key: string): boolean {
    const field = value[key]
    if (typeof field !== 'boolean') {
      throw invalidResponse()
    }
    return field
  },
}

function optionalString(value: unknown): string | null {
  return typeof value === 'string' ? value : null
}

function readDetails(value: unknown): ApiErrorDetail[] {
  if (!Array.isArray(value)) {
    return []
  }
  return value.filter(isRecord).map((detail) => ({
    location: Array.isArray(detail['location'])
      ? detail['location'].filter(
          (part): part is string | number => typeof part === 'string' || typeof part === 'number',
        )
      : [],
    message: optionalString(detail['message']) ?? '',
    type: optionalString(detail['type']) ?? '',
  }))
}

// --- CSRF token -------------------------------------------------------------

let csrfToken: string | null = null

/** Remember the CSRF token returned by the API (sign-in, registration). */
export function setCsrfToken(token: string | null): void {
  csrfToken = token
}

async function fetchCsrfToken(): Promise<string> {
  const token = read.string(read.object(await apiRequest('/auth/csrf')), 'csrf_token')
  csrfToken = token
  return token
}

// --- requests ---------------------------------------------------------------

async function toApiError(response: Response): Promise<ApiError> {
  let body: unknown = null
  try {
    body = await response.json()
  } catch {
    // Not JSON (for example a proxy error page): use the generic message.
  }
  const error = isRecord(body) && isRecord(body['error']) ? body['error'] : {}
  const retryAfter = Number.parseInt(response.headers.get('Retry-After') ?? '', 10)
  return new ApiError(
    response.status,
    optionalString(error['code']) ?? 'http_error',
    optionalString(error['message']) ?? GENERIC_ERROR,
    {
      requestId: optionalString(error['request_id']) ?? response.headers.get('X-Request-ID'),
      details: readDetails(error['details']),
      retryAfter: Number.isFinite(retryAfter) ? retryAfter : null,
    },
  )
}

export interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'
  body?: unknown
  signal?: AbortSignal
}

async function send(path: string, options: RequestOptions): Promise<Response> {
  const method = options.method ?? 'GET'
  const headers: Record<string, string> = { Accept: 'application/json' }
  if (options.body !== undefined) {
    headers['Content-Type'] = 'application/json'
  }
  if (UNSAFE_METHODS.has(method)) {
    headers[CSRF_HEADER] = csrfToken ?? (await fetchCsrfToken())
  }
  try {
    return await fetch(`${API_BASE}${path}`, {
      method,
      headers,
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
      credentials: 'same-origin',
      cache: 'no-store',
      signal: options.signal,
    })
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw error
    }
    throw new ApiError(0, 'network_error', 'AEGIS could not be reached. Check your connection.')
  }
}

/**
 * Send a request and return the parsed JSON body (undefined for 204). The
 * caller checks the shape with the `read` helpers.
 *
 * A state-changing request refused with `csrf_failed` is retried once with a
 * fresh token: the in-memory token can be stale after the session changed in
 * another tab.
 */
export async function apiRequest(path: string, options: RequestOptions = {}): Promise<unknown> {
  let response = await send(path, options)
  if (response.status === 403 && UNSAFE_METHODS.has(options.method ?? 'GET')) {
    const error = await toApiError(response.clone())
    if (error.code === 'csrf_failed') {
      csrfToken = null
      response = await send(path, options)
    }
  }
  if (!response.ok) {
    const error = await toApiError(response)
    if (error.status === 401 && !path.startsWith('/auth/')) {
      window.dispatchEvent(new CustomEvent(UNAUTHENTICATED_EVENT, { detail: error.code }))
    }
    throw error
  }
  if (response.status === 204) {
    return undefined
  }
  try {
    const body: unknown = await response.json()
    return body
  } catch {
    throw invalidResponse()
  }
}
