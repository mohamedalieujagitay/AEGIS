import { describe, expect, it, vi } from 'vitest'
import { apiError, mockApi } from '../test/apiMock'
import { ApiError, apiRequest, setCsrfToken, UNAUTHENTICATED_EVENT } from './api'

describe('API client', () => {
  it('sends the session cookie and never caches responses', async () => {
    const { requests } = mockApi({ 'GET /auth/me': { body: { ok: true } } })

    await expect(apiRequest('/auth/me')).resolves.toEqual({ ok: true })
    expect(requests[0]).toMatchObject({ credentials: 'same-origin' })
    expect(requests[0]?.headers).not.toHaveProperty('X-CSRF-Token')
  })

  it('fetches a CSRF token before the first state-changing request and reuses it', async () => {
    const { requests } = mockApi({ 'POST /thing': { status: 204 } })

    await apiRequest('/thing', { method: 'POST', body: { a: 1 } })
    await apiRequest('/thing', { method: 'POST' })

    expect(requests.map((r) => `${r.method} ${r.path}`)).toEqual([
      'GET /auth/csrf',
      'POST /thing',
      'POST /thing',
    ])
    expect(requests[1]?.headers['X-CSRF-Token']).toBe('anonymous-csrf-token')
    expect(requests[1]?.headers['Content-Type']).toBe('application/json')
    expect(requests[1]?.body).toEqual({ a: 1 })
    expect(requests[2]?.headers['X-CSRF-Token']).toBe('anonymous-csrf-token')
  })

  it('uses a token set by sign-in', async () => {
    const { requests } = mockApi({ 'POST /thing': { status: 204 } })
    setCsrfToken('session-token')

    await apiRequest('/thing', { method: 'POST' })

    expect(requests).toHaveLength(1)
    expect(requests[0]?.headers['X-CSRF-Token']).toBe('session-token')
  })

  it('retries once with a fresh token after a CSRF failure', async () => {
    let attempts = 0
    const { requests } = mockApi({
      'POST /thing': () => {
        attempts += 1
        return attempts === 1
          ? apiError(403, 'csrf_failed', 'The request could not be verified.')
          : { status: 204 }
      },
    })
    setCsrfToken('stale-token')

    await apiRequest('/thing', { method: 'POST' })

    expect(requests.map((r) => r.headers['X-CSRF-Token'] ?? r.path)).toEqual([
      'stale-token',
      '/auth/csrf',
      'anonymous-csrf-token',
    ])
  })

  it('does not retry other 403 errors', async () => {
    const { requests } = mockApi({
      'POST /thing': apiError(403, 'forbidden', 'You do not have permission.'),
    })
    setCsrfToken('token')

    await expect(apiRequest('/thing', { method: 'POST' })).rejects.toMatchObject({
      status: 403,
      code: 'forbidden',
    })
    expect(requests).toHaveLength(1)
  })

  it('raises API errors with their code, message, details and Retry-After', async () => {
    mockApi({
      'GET /thing': {
        ...apiError(429, 'too_many_requests', 'Too many attempts.', {
          details: [{ location: ['body', 'email'], message: 'Bad.', type: 'value_error' }],
        }),
        headers: { 'Retry-After': '30' },
      },
    })

    const error: unknown = await apiRequest('/thing').catch((caught: unknown) => caught)

    expect(error).toBeInstanceOf(ApiError)
    expect(error).toMatchObject({
      status: 429,
      code: 'too_many_requests',
      message: 'Too many attempts.',
      requestId: 'req-1',
      retryAfter: 30,
      details: [{ location: ['body', 'email'], message: 'Bad.', type: 'value_error' }],
    })
  })

  it('uses a generic message when the error is not in the API format', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => new Response('<html>Bad gateway</html>', { status: 502 })),
    )

    await expect(apiRequest('/thing')).rejects.toMatchObject({
      status: 502,
      code: 'http_error',
      message: 'The server could not complete the request. Try again later.',
    })
  })

  it('reports network failures without technical details', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => {
        throw new TypeError('Failed to fetch')
      }),
    )

    await expect(apiRequest('/thing')).rejects.toMatchObject({ code: 'network_error' })
  })

  it('announces lost sessions from non-authentication endpoints', async () => {
    mockApi({
      'GET /thing': apiError(401, 'session_expired', 'Your session has expired.'),
      'GET /auth/me': apiError(401, 'authentication_required', 'Sign in.'),
    })
    const listener = vi.fn()
    window.addEventListener(UNAUTHENTICATED_EVENT, listener)

    await expect(apiRequest('/auth/me')).rejects.toBeInstanceOf(ApiError)
    expect(listener).not.toHaveBeenCalled()
    await expect(apiRequest('/thing')).rejects.toBeInstanceOf(ApiError)
    expect(listener).toHaveBeenCalledOnce()

    window.removeEventListener(UNAUTHENTICATED_EVENT, listener)
  })

  it('never uses browser storage', async () => {
    const setItem = vi.spyOn(Storage.prototype, 'setItem')
    mockApi({ 'POST /thing': { status: 204 } })

    await apiRequest('/thing', { method: 'POST' })

    expect(setItem).not.toHaveBeenCalled()
  })
})
