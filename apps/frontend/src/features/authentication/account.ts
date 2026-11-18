import { apiRequest, read, setCsrfToken } from '../../lib/api'

/**
 * The signed-in user's account details (roadmap task 2.2). The email address
 * is shown but cannot be changed: there is no email verification in v0.1.0.
 */
export interface Profile {
  email: string
  username: string
  createdAt: string
  isActive: boolean
}

/**
 * A session of the signed-in user. The server returns no token, no hash and no
 * address: `id` identifies the session for revocation only.
 */
export interface ActiveSession {
  id: string
  createdAt: string
  lastSeenAt: string
  expiresAt: string
  userAgent: string | null
  current: boolean
}

function toProfile(value: unknown): Profile {
  const body = read.object(value)
  return {
    email: read.string(body, 'email'),
    username: read.string(body, 'username'),
    createdAt: read.string(body, 'created_at'),
    isActive: read.boolean(body, 'is_active'),
  }
}

function toSession(value: unknown): ActiveSession {
  const session = read.object(value)
  const agent = session['user_agent']
  return {
    id: read.string(session, 'id'),
    createdAt: read.string(session, 'created_at'),
    lastSeenAt: read.string(session, 'last_seen_at'),
    expiresAt: read.string(session, 'expires_at'),
    userAgent: typeof agent === 'string' ? agent : null,
    current: read.boolean(session, 'current'),
  }
}

function toList<T>(value: unknown, item: (entry: unknown) => T): T[] {
  if (!Array.isArray(value)) {
    throw new Error('unexpected response')
  }
  return value.map(item)
}

export const accountApi = {
  profile: async (signal?: AbortSignal): Promise<Profile> =>
    toProfile(await apiRequest('/account/profile', { signal })),

  /** Change the username. The current password is required (DECISIONS.md D-074). */
  updateUsername: async (username: string, currentPassword: string): Promise<Profile> =>
    toProfile(
      await apiRequest('/account/profile', {
        method: 'PATCH',
        body: { username, current_password: currentPassword },
      }),
    ),

  /**
   * Change the password. The server rotates this browser's session and signs
   * out every other session and trusted device; the new CSRF token replaces the
   * old one here.
   */
  changePassword: async (currentPassword: string, newPassword: string): Promise<void> => {
    const body = read.object(
      await apiRequest('/account/password', {
        method: 'POST',
        body: { current_password: currentPassword, new_password: newPassword },
      }),
    )
    setCsrfToken(read.string(body, 'csrf_token'))
  },

  sessions: async (signal?: AbortSignal): Promise<ActiveSession[]> =>
    toList(await apiRequest('/account/sessions', { signal }), toSession),

  revokeSession: async (id: string): Promise<void> => {
    await apiRequest(`/account/sessions/${encodeURIComponent(id)}`, { method: 'DELETE' })
  },

  /** Sign out every session except this one. Returns how many were signed out. */
  revokeOtherSessions: async (): Promise<number> =>
    read.number(
      read.object(await apiRequest('/account/sessions/revoke-others', { method: 'POST' })),
      'revoked',
    ),
}
