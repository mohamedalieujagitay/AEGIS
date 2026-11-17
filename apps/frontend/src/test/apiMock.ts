import { vi } from 'vitest'

/** One request seen by the mocked API. */
export interface RecordedRequest {
  method: string
  path: string
  headers: Record<string, string>
  body: unknown
  credentials: RequestCredentials | undefined
}

export interface MockResponse {
  status?: number
  body?: unknown
  headers?: Record<string, string>
}

type Handler = MockResponse | ((request: RecordedRequest) => MockResponse)

/**
 * Replace `fetch` with a fake AEGIS API (test environment only).
 *
 * Handlers are keyed by "METHOD /path" relative to /api/v1, for example
 * "POST /auth/login". `GET /auth/csrf` answers with a token unless
 * overridden. Unknown requests fail the test with a 599 response.
 */
export function mockApi(handlers: Record<string, Handler>) {
  const requests: RecordedRequest[] = []
  const fetchMock = vi.fn(async (input: string, init: RequestInit = {}) => {
    const url = new URL(input, 'http://localhost')
    const path = url.pathname.replace(/^\/api\/v1/, '')
    const method = init.method ?? 'GET'
    const headers: Record<string, string> = {}
    for (const [name, value] of Object.entries(init.headers ?? {})) {
      if (typeof value === 'string') {
        headers[name] = value
      }
    }
    const request: RecordedRequest = {
      method,
      path,
      headers,
      body: typeof init.body === 'string' ? JSON.parse(init.body) : undefined,
      credentials: init.credentials,
    }
    requests.push(request)
    const key = `${method} ${path}`
    const handler = handlers[key] ?? (key === 'GET /auth/csrf' ? csrf : undefined)
    if (!handler) {
      return new Response(JSON.stringify({ error: { code: 'unmocked', message: key } }), {
        status: 599,
      })
    }
    const result = typeof handler === 'function' ? handler(request) : handler
    const status = result.status ?? 200
    return new Response(status === 204 ? null : JSON.stringify(result.body ?? {}), {
      status,
      headers: { 'Content-Type': 'application/json', ...result.headers },
    })
  })
  vi.stubGlobal('fetch', fetchMock)
  return { requests, fetchMock }
}

const csrf: MockResponse = { body: { csrf_token: 'anonymous-csrf-token' } }

export function apiError(status: number, code: string, message: string, extra = {}) {
  return { status, body: { error: { code, message, request_id: 'req-1', ...extra } } }
}

export const testUser = {
  id: '6f1c2a6e-0000-4000-8000-000000000001',
  email: 'alice@example.com',
  username: 'alice',
  is_instance_admin: false,
}

export const testAdmin = { ...testUser, username: 'admin', is_instance_admin: true }

export const authOptions = {
  registration_enabled: false,
  session_idle_timeout_minutes: 60,
  session_absolute_timeout_hours: 12,
}

/** Handlers for a signed-in user. */
export function signedIn(user = testUser): Record<string, Handler> {
  return {
    'GET /auth/me': { body: user },
    'GET /auth/options': { body: authOptions },
  }
}

/** Handlers for a visitor without a session. */
export function signedOut(): Record<string, Handler> {
  return {
    'GET /auth/me': apiError(401, 'authentication_required', 'Sign in to continue.'),
    'GET /auth/options': { body: authOptions },
  }
}
