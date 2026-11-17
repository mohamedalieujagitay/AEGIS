import { useState } from 'react'
import { useNavigate } from 'react-router'
import { paths } from '../../../app/router/paths'
import { Button } from '../../../components/ui'
import { useAuth, useCurrentUser } from '../authContext'

/** The signed-in user and the sign-out action, in the top bar. */
export function UserMenu() {
  const user = useCurrentUser()
  const { signOut } = useAuth()
  const navigate = useNavigate()
  const [signingOut, setSigningOut] = useState(false)

  async function handleSignOut() {
    setSigningOut(true)
    try {
      await signOut()
    } catch {
      // The interface is signed out either way; the server session expires on its own.
    }
    void navigate(paths.login, { replace: true })
  }

  return (
    <div className="flex items-center gap-3">
      <span
        aria-hidden="true"
        className="grid size-9 shrink-0 place-items-center rounded-full bg-surface-muted text-sm font-bold text-fg-heading uppercase"
      >
        {user.username.slice(0, 1)}
      </span>
      <span className="hidden min-w-0 flex-col leading-tight sm:flex">
        <span className="truncate text-sm font-semibold text-fg-heading">{user.username}</span>
        <span className="truncate text-xs text-fg-subtle">
          {user.is_instance_admin ? 'Instance administrator' : user.email}
        </span>
      </span>
      <span className="sr-only sm:hidden">Signed in as {user.username}</span>
      <Button
        variant="secondary"
        size="sm"
        onClick={() => void handleSignOut()}
        disabled={signingOut}
      >
        Sign out
      </Button>
    </div>
  )
}
