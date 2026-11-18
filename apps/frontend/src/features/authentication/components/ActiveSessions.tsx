import { useCallback, useEffect, useState } from 'react'
import { Badge, Button, EmptyState } from '../../../components/ui'
import { ShieldCheckIcon } from '../../../components/icons/icons'
import { accountApi, type ActiveSession } from '../account'
import { useAuth } from '../authContext'
import { describeBrowser } from '../devices'
import { errorMessage } from '../errors'

function formatDate(value: string): string {
  return new Date(value).toLocaleString()
}

type Pending = { kind: 'session'; id: string } | { kind: 'others' } | undefined

/**
 * The signed-in user's active sessions, with the current one marked. Only the
 * server's list is shown: no token, no hash and no address. Revoking the current
 * session signs this browser out, as logout does.
 */
export function ActiveSessions() {
  const { sessionEnded } = useAuth()
  const [sessions, setSessions] = useState<ActiveSession[]>()
  const [loadError, setLoadError] = useState<string>()
  const [pending, setPending] = useState<Pending>()
  const [busy, setBusy] = useState(false)
  const [actionError, setActionError] = useState<string>()
  const [notice, setNotice] = useState<string>()

  const load = useCallback((signal?: AbortSignal) => {
    return accountApi
      .sessions(signal)
      .then((list) => {
        setSessions(list)
        setLoadError(undefined)
      })
      .catch((caught: unknown) => {
        if (!signal?.aborted) {
          setLoadError(errorMessage(caught))
        }
      })
  }, [])

  useEffect(() => {
    const controller = new AbortController()
    void load(controller.signal)
    return () => controller.abort()
  }, [load])

  async function revokeSession(session: ActiveSession) {
    setBusy(true)
    setActionError(undefined)
    setNotice(undefined)
    try {
      await accountApi.revokeSession(session.id)
    } catch (caught) {
      setActionError(errorMessage(caught))
      setBusy(false)
      return
    }
    setPending(undefined)
    setBusy(false)
    if (session.current) {
      // This browser was signed out by the server: show the sign-in page.
      sessionEnded()
      return
    }
    setNotice('That session was signed out.')
    await load()
  }

  async function revokeOthers() {
    setBusy(true)
    setActionError(undefined)
    setNotice(undefined)
    try {
      const count = await accountApi.revokeOtherSessions()
      setNotice(
        count === 1
          ? '1 other session was signed out.'
          : `${count} other sessions were signed out.`,
      )
    } catch (caught) {
      setActionError(errorMessage(caught))
      setBusy(false)
      return
    }
    setPending(undefined)
    setBusy(false)
    await load()
  }

  if (loadError !== undefined) {
    return (
      <div role="alert" className="flex flex-col items-start gap-3 text-sm text-danger">
        <p>{loadError}</p>
        <Button size="sm" variant="secondary" onClick={() => void load()}>
          Try again
        </Button>
      </div>
    )
  }

  if (sessions === undefined) {
    return <output className="text-sm text-fg-muted">Loading your sessions…</output>
  }

  const others = sessions.filter((session) => !session.current)

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-fg-muted">
          Browsers signed in to your account. A session ends after a period of inactivity or at its
          maximum lifetime, whichever comes first.
        </p>
        {others.length > 0 && pending?.kind !== 'others' && (
          <Button size="sm" variant="secondary" onClick={() => setPending({ kind: 'others' })}>
            Sign out other sessions
          </Button>
        )}
      </div>

      {pending?.kind === 'others' && (
        <div className="flex flex-col gap-2 rounded-control border border-line p-3.5">
          <p className="text-sm text-fg">
            Sign out{' '}
            {others.length === 1 ? 'the other session' : `all ${others.length} other sessions`}?
            This browser stays signed in. Trusted browsers are not affected.
          </p>
          <div className="flex gap-2">
            <Button size="sm" variant="danger" disabled={busy} onClick={() => void revokeOthers()}>
              {busy ? 'Signing out…' : 'Sign out other sessions'}
            </Button>
            <Button
              size="sm"
              variant="secondary"
              disabled={busy}
              onClick={() => setPending(undefined)}
            >
              Cancel
            </Button>
          </div>
        </div>
      )}

      {sessions.length === 0 && (
        <EmptyState
          icon={ShieldCheckIcon}
          title="No active sessions"
          description="Sessions appear here while they can still be used."
        />
      )}

      {sessions.length > 0 && (
        <ul className="flex flex-col">
          {sessions.map((session) => {
            const confirming = pending?.kind === 'session' && pending.id === session.id
            return (
              <li
                key={session.id}
                className="flex flex-col gap-3 border-b border-line-soft py-4 last:border-b-0 sm:flex-row sm:items-center"
              >
                <div className="flex flex-1 flex-col gap-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <strong className="font-semibold text-fg-heading">
                      {describeBrowser(session.userAgent)}
                    </strong>
                    {session.current && <Badge tone="info">This browser</Badge>}
                  </div>
                  <dl className="grid grid-cols-[auto_1fr] gap-x-3 text-sm text-fg-muted">
                    <dt>Signed in</dt>
                    <dd>{formatDate(session.createdAt)}</dd>
                    <dt>Last active</dt>
                    <dd>{formatDate(session.lastSeenAt)}</dd>
                    <dt>Ends</dt>
                    <dd>{formatDate(session.expiresAt)}</dd>
                  </dl>
                </div>

                {!confirming && (
                  <Button
                    size="sm"
                    variant="danger"
                    disabled={busy}
                    onClick={() => {
                      setActionError(undefined)
                      setNotice(undefined)
                      setPending({ kind: 'session', id: session.id })
                    }}
                  >
                    {session.current ? 'Sign out this browser' : 'Sign out'}
                  </Button>
                )}

                {confirming && (
                  <div className="flex flex-col gap-2 sm:items-end">
                    <p className="text-sm text-fg">
                      {session.current
                        ? 'Sign out of this browser now?'
                        : 'Sign out this session? It will need to sign in again.'}
                    </p>
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="danger"
                        disabled={busy}
                        onClick={() => void revokeSession(session)}
                      >
                        {busy ? 'Signing out…' : 'Confirm'}
                      </Button>
                      <Button
                        size="sm"
                        variant="secondary"
                        disabled={busy}
                        onClick={() => setPending(undefined)}
                      >
                        Cancel
                      </Button>
                    </div>
                  </div>
                )}
              </li>
            )
          })}
        </ul>
      )}

      {notice !== undefined && <output className="block text-sm text-success">{notice}</output>}
      {actionError !== undefined && (
        <p role="alert" className="text-sm text-danger">
          {actionError}
        </p>
      )}
    </div>
  )
}
