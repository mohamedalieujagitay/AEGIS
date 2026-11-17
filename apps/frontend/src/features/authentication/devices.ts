import { apiRequest, read } from '../../lib/api'

/**
 * A browser trusted for sign-in (DECISIONS.md D-070). The server returns no
 * token and no hash: `id` identifies the record for revocation only.
 */
export interface TrustedDevice {
  id: string
  createdAt: string
  expiresAt: string
  lastUsedAt: string | null
  userAgent: string | null
  current: boolean
}

function toDevice(value: unknown): TrustedDevice {
  const device = read.object(value)
  const lastUsed = device['last_used_at']
  const agent = device['user_agent']
  return {
    id: read.string(device, 'id'),
    createdAt: read.string(device, 'created_at'),
    expiresAt: read.string(device, 'expires_at'),
    lastUsedAt: typeof lastUsed === 'string' ? lastUsed : null,
    userAgent: typeof agent === 'string' ? agent : null,
    current: read.boolean(device, 'current'),
  }
}

export const devicesApi = {
  list: async (signal?: AbortSignal): Promise<TrustedDevice[]> => {
    const value = await apiRequest('/auth/devices', { signal })
    if (!Array.isArray(value)) {
      throw new Error('unexpected response')
    }
    return value.map(toDevice)
  },

  revoke: async (id: string) => {
    await apiRequest(`/auth/devices/${encodeURIComponent(id)}`, { method: 'DELETE' })
  },
}

/**
 * A short description of a browser from its user-agent string, such as
 * "Chrome on Windows". The full string is never shown.
 */
export function describeBrowser(userAgent: string | null): string {
  if (!userAgent) {
    return 'Unknown browser'
  }
  const browser = /Edg\//.test(userAgent)
    ? 'Edge'
    : /OPR\/|Opera/.test(userAgent)
      ? 'Opera'
      : /Firefox\//.test(userAgent)
        ? 'Firefox'
        : /Chrome\//.test(userAgent)
          ? 'Chrome'
          : /Safari\//.test(userAgent)
            ? 'Safari'
            : 'Browser'
  const system = /Windows/.test(userAgent)
    ? 'Windows'
    : /Android/.test(userAgent)
      ? 'Android'
      : /iPhone|iPad|iOS/.test(userAgent)
        ? 'iOS'
        : /Mac OS X|Macintosh/.test(userAgent)
          ? 'macOS'
          : /Linux/.test(userAgent)
            ? 'Linux'
            : null
  return system ? `${browser} on ${system}` : browser
}
