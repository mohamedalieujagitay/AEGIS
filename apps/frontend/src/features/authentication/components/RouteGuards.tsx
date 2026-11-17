import { Navigate, Outlet, useLocation } from 'react-router'
import { paths } from '../../../app/router/paths'
import { Button } from '../../../components/ui'
import { AuthProvider } from '../AuthProvider'
import { useAuth } from '../authContext'
import { redirectTarget } from '../redirect'
import { AuthLayout, FormAlert } from './AuthLayout'

/** Root route element: makes the authentication state available to every route. */
export function AuthRoot() {
  return (
    <AuthProvider>
      <Outlet />
    </AuthProvider>
  )
}

function SessionCheck() {
  const { state, retry } = useAuth()
  if (state.status === 'unavailable') {
    return (
      <AuthLayout title="AEGIS is unavailable">
        <FormAlert tone="error">{state.message}</FormAlert>
        <Button onClick={retry}>Try again</Button>
      </AuthLayout>
    )
  }
  return (
    <main className="grid min-h-dvh place-items-center bg-canvas">
      <output className="text-fg-muted">Loading…</output>
    </main>
  )
}

/** Renders the application only for a signed-in user; otherwise goes to the sign-in page. */
export function RequireAuth() {
  const { state } = useAuth()
  const location = useLocation()
  if (state.status === 'loading' || state.status === 'unavailable') {
    return <SessionCheck />
  }
  if (state.status === 'anonymous') {
    return <Navigate to={paths.login} replace state={{ from: location }} />
  }
  return <Outlet />
}

/** Sign-in and registration pages: a signed-in user goes to the application instead. */
export function PublicOnly() {
  const { state } = useAuth()
  const location = useLocation()
  if (state.status === 'loading' || state.status === 'unavailable') {
    return <SessionCheck />
  }
  if (state.status === 'authenticated') {
    return <Navigate to={redirectTarget(location)} replace />
  }
  return <Outlet />
}
