import { useCallback, useEffect, useState } from 'react'
import { ShieldCheckIcon } from '../../../components/icons/icons'
import { Badge, Button, EmptyState } from '../../../components/ui'
import { ApiError } from '../../../lib/api'
import { describeBrowser, devicesApi, type TrustedDevice } from '../devices'
import { errorMessage } from '../errors'

function formatDate(value: string): string {
  return new Date(value).toLocaleString()
}

/**
 * The signed-in user's trusted browsers, with individual revocation (D-070).
 * The server enforces ownership; this component only shows what it returns.
 */
export function TrustedDevices() {
  const [devices, setDevices] = useState<TrustedDevice[]>()
  const [loadError, setLoadError] = useState<string>()
  const [confirmingId, setConfirmingId] = useState<string>()
  const [revokingId, setRevokingId] = useState<string>()
  const [actionError, setActionError] = useState<string>()

  /** Load the list from the server. Used on first render, after a revocation and on retry. */
  const load = useCallback((signal?: AbortSignal) => {
    return devicesApi
      .list(signal)
      .then((list) => {
        setDevices(list)
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

  async function revoke(device: TrustedDevice) {
    setRevokingId(device.id)
    setActionError(undefined)
    try {
      await devicesApi.revoke(device.id)
    } catch (caught) {
      // A browser that is already gone (revoked in another tab) is not an error.
      if (!(caught instanceof ApiError && caught.status === 404)) {
        setActionError(errorMessage(caught))
        setRevokingId(undefined)
        return
      }
    }
    setConfirmingId(undefined)
    setRevokingId(undefined)
    // Refresh from the server rather than removing the row locally.
    await load()
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-2 text-sm text-fg-muted">
        <p>
          A trusted browser skips only the account-wide delay that AEGIS applies after many failed
          sign-ins. It does not sign anyone in: the password is still required, and the delay for
          each address and account is unchanged.
        </p>
        <p>
          Signing out does not remove a trusted browser. Revoke it here, or it expires after 30
          days. A password reset or change, and the deactivation of the account, revoke all of them.
        </p>
      </div>

      {devices === undefined && loadError === undefined && (
        <output className="text-sm text-fg-muted">Loading trusted browsers…</output>
      )}

      {loadError !== undefined && (
        <div role="alert" className="flex flex-col items-start gap-3 text-sm text-danger">
          <p>{loadError}</p>
          <Button size="sm" variant="secondary" onClick={() => void load()}>
            Try again
          </Button>
        </div>
      )}

      {devices !== undefined && devices.length === 0 && (
        <EmptyState
          icon={ShieldCheckIcon}
          title="No trusted browsers"
          description="A browser is trusted for 30 days after you sign in from it. Browsers appear here while they are trusted."
        />
      )}

      {devices !== undefined && devices.length > 0 && (
        <ul className="flex flex-col">
          {devices.map((device) => {
            const confirming = confirmingId === device.id
            const busy = revokingId === device.id
            return (
              <li
                key={device.id}
                className="flex flex-col gap-3 border-b border-line-soft py-4 last:border-b-0 sm:flex-row sm:items-center"
              >
                <div className="flex flex-1 flex-col gap-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <strong className="font-semibold text-fg-heading">
                      {describeBrowser(device.userAgent)}
                    </strong>
                    {device.current && <Badge tone="info">This browser</Badge>}
                  </div>
                  <dl className="grid grid-cols-[auto_1fr] gap-x-3 text-sm text-fg-muted">
                    <dt>Added</dt>
                    <dd>{formatDate(device.createdAt)}</dd>
                    <dt>Last used</dt>
                    <dd>{device.lastUsedAt ? formatDate(device.lastUsedAt) : 'Never'}</dd>
                    <dt>Expires</dt>
                    <dd>{formatDate(device.expiresAt)}</dd>
                  </dl>
                </div>

                {!confirming && (
                  <Button
                    size="sm"
                    variant="danger"
                    onClick={() => {
                      setActionError(undefined)
                      setConfirmingId(device.id)
                    }}
                  >
                    Revoke
                  </Button>
                )}

                {confirming && (
                  <div className="flex flex-col gap-2 sm:items-end">
                    <p className="text-sm text-fg">
                      {device.current
                        ? 'Revoke this browser? Its next sign-in will be subject to the full account delay.'
                        : 'Revoke this browser? Its next sign-in will be subject to the full account delay.'}
                    </p>
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="danger"
                        disabled={busy}
                        onClick={() => void revoke(device)}
                      >
                        {busy ? 'Revoking…' : 'Revoke browser'}
                      </Button>
                      <Button
                        size="sm"
                        variant="secondary"
                        disabled={busy}
                        onClick={() => setConfirmingId(undefined)}
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

      {actionError !== undefined && (
        <p role="alert" className="text-sm text-danger">
          {actionError}
        </p>
      )}
    </div>
  )
}
