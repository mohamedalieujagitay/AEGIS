import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import { ApiError, UNAUTHENTICATED_EVENT } from '../../lib/api'
import { authApi } from './api'
import { AuthContext, type AuthContextValue, type AuthState } from './authContext'

/**
 * Holds the signed-in user. The session itself is an HttpOnly cookie that
 * scripts cannot read, so the provider asks the API (GET /auth/me) on start.
 * Nothing is stored in the browser's storage.
 */
/** Ask the API who is signed in, and report the result. */
async function checkSession(
  setState: (state: AuthState) => void,
  signal?: AbortSignal,
): Promise<void> {
  try {
    setState({ status: 'authenticated', user: await authApi.me(signal) })
  } catch (error) {
    if (signal?.aborted) {
      return
    }
    if (error instanceof ApiError && error.status === 401) {
      setState({ status: 'anonymous' })
    } else {
      setState({
        status: 'unavailable',
        message:
          error instanceof ApiError
            ? error.message
            : 'AEGIS could not be reached. Try again later.',
      })
    }
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({ status: 'loading' })

  useEffect(() => {
    const controller = new AbortController()
    void checkSession(setState, controller.signal)
    return () => controller.abort()
  }, [])

  // Any API call that finds the session gone signs the interface out.
  useEffect(() => {
    function handleUnauthenticated(event: Event) {
      const code: unknown = event instanceof CustomEvent ? event.detail : undefined
      setState({ status: 'anonymous', reason: code === 'session_expired' ? 'expired' : undefined })
    }
    window.addEventListener(UNAUTHENTICATED_EVENT, handleUnauthenticated)
    return () => window.removeEventListener(UNAUTHENTICATED_EVENT, handleUnauthenticated)
  }, [])

  const signIn = useCallback(async (email: string, password: string) => {
    const user = await authApi.login(email, password)
    setState({ status: 'authenticated', user })
    return user
  }, [])

  const register = useCallback(async (email: string, username: string, password: string) => {
    const user = await authApi.register(email, username, password)
    setState({ status: 'authenticated', user })
    return user
  }, [])

  /**
   * Sign out of this browser. If the server cannot be reached, the browser is
   * still signed out here, but the message says the server did not confirm it:
   * the server session then ends by itself at its idle or absolute timeout.
   */
  const signOut = useCallback(async () => {
    let reason: 'signed_out' | 'signed_out_unconfirmed' = 'signed_out'
    try {
      await authApi.logout()
    } catch {
      reason = 'signed_out_unconfirmed'
    }
    setState({ status: 'anonymous', reason })
  }, [])

  const sessionEnded = useCallback(() => setState({ status: 'anonymous' }), [])

  const retry = useCallback(() => {
    setState({ status: 'loading' })
    void checkSession(setState)
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({ state, signIn, register, signOut, sessionEnded, retry }),
    [state, signIn, register, signOut, sessionEnded, retry],
  )

  return <AuthContext value={value}>{children}</AuthContext>
}
