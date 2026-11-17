import { apiRequest, read, setCsrfToken } from '../../lib/api'

export interface User {
  id: string
  email: string
  username: string
  is_instance_admin: boolean
}

export interface AuthOptions {
  registration_enabled: boolean
  session_idle_timeout_minutes: number
  session_absolute_timeout_hours: number
}

export interface PasswordResetIssued {
  reset_token: string
  reset_path: string
  expires_at: string
}

function toUser(value: unknown): User {
  const user = read.object(value)
  return {
    id: read.string(user, 'id'),
    email: read.string(user, 'email'),
    username: read.string(user, 'username'),
    is_instance_admin: read.boolean(user, 'is_instance_admin'),
  }
}

/** Sign-in and registration return a new CSRF token, bound to the new session. */
function startSession(value: unknown): User {
  const session = read.object(value)
  const user = toUser(session['user'])
  setCsrfToken(read.string(session, 'csrf_token'))
  return user
}

function toRegistration(value: unknown): { enabled: boolean } {
  return { enabled: read.boolean(read.object(value), 'enabled') }
}

export const authApi = {
  me: async (signal?: AbortSignal) => toUser(await apiRequest('/auth/me', { signal })),

  options: async (signal?: AbortSignal): Promise<AuthOptions> => {
    const options = read.object(await apiRequest('/auth/options', { signal }))
    return {
      registration_enabled: read.boolean(options, 'registration_enabled'),
      session_idle_timeout_minutes: read.number(options, 'session_idle_timeout_minutes'),
      session_absolute_timeout_hours: read.number(options, 'session_absolute_timeout_hours'),
    }
  },

  login: async (email: string, password: string) =>
    startSession(await apiRequest('/auth/login', { method: 'POST', body: { email, password } })),

  register: async (email: string, username: string, password: string) =>
    startSession(
      await apiRequest('/auth/register', {
        method: 'POST',
        body: { email, username, password },
      }),
    ),

  logout: async () => {
    try {
      await apiRequest('/auth/logout', { method: 'POST' })
    } finally {
      // The server cleared the CSRF cookie; the next request fetches a new token.
      setCsrfToken(null)
    }
  },

  resetPassword: async (token: string, newPassword: string) => {
    try {
      await apiRequest('/auth/password/reset', {
        method: 'POST',
        body: { token, new_password: newPassword },
      })
    } finally {
      setCsrfToken(null)
    }
  },
}

export const adminApi = {
  registration: async (signal?: AbortSignal) =>
    toRegistration(await apiRequest('/admin/settings/registration', { signal })),

  setRegistration: async (enabled: boolean) =>
    toRegistration(
      await apiRequest('/admin/settings/registration', { method: 'PUT', body: { enabled } }),
    ),

  issuePasswordReset: async (email: string): Promise<PasswordResetIssued> => {
    const issued = read.object(
      await apiRequest('/admin/password-resets', { method: 'POST', body: { email } }),
    )
    return {
      reset_token: read.string(issued, 'reset_token'),
      reset_path: read.string(issued, 'reset_path'),
      expires_at: read.string(issued, 'expires_at'),
    }
  },
}
