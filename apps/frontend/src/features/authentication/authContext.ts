import { createContext, useContext } from 'react'
import type { User } from './api'

export type AuthState =
  | { status: 'loading' }
  /** The session could not be checked (for example, the API is unreachable). */
  | { status: 'unavailable'; message: string }
  | { status: 'anonymous'; reason?: 'expired' | 'signed_out' | 'signed_out_unconfirmed' }
  | { status: 'authenticated'; user: User }

export interface AuthContextValue {
  state: AuthState
  signIn: (email: string, password: string) => Promise<User>
  register: (email: string, username: string, password: string) => Promise<User>
  signOut: () => Promise<void>
  /** Mark the browser as signed out after the server ended the session (password reset). */
  sessionEnded: () => void
  /** Replace the signed-in user's details (after a username change). */
  updateUser: (user: User) => void
  /** Check the session again (after `unavailable`). */
  retry: () => void
}

export const AuthContext = createContext<AuthContextValue | null>(null)

export function useAuth(): AuthContextValue {
  const value = useContext(AuthContext)
  if (!value) {
    throw new Error('useAuth must be used inside <AuthProvider>')
  }
  return value
}

/** The signed-in user. Only for components rendered behind <RequireAuth>. */
export function useCurrentUser(): User {
  const { state } = useAuth()
  if (state.status !== 'authenticated') {
    throw new Error('useCurrentUser requires a signed-in user')
  }
  return state.user
}
