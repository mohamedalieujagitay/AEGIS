import { useEffect, useId, useState, type FormEvent } from 'react'
import { Badge, Button, Input } from '../../../components/ui'
import { adminApi, type PasswordResetIssued } from '../api'
import { errorMessage, fieldErrors } from '../errors'

/**
 * Instance administration needed by authentication (roadmap 2.1): open
 * registration and password reset links. User management is roadmap 2.2.
 * Shown only to instance administrators; the API enforces this itself.
 */
export function InstanceAdministration() {
  return (
    <div className="flex flex-col gap-6">
      <RegistrationSetting />
      <PasswordResetLink />
    </div>
  )
}

function RegistrationSetting() {
  const [enabled, setEnabled] = useState<boolean | null>(null)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string>()
  const labelId = useId()
  const descriptionId = useId()

  useEffect(() => {
    const controller = new AbortController()
    adminApi
      .registration(controller.signal)
      .then((setting) => setEnabled(setting.enabled))
      .catch((caught: unknown) => {
        if (!controller.signal.aborted) {
          setError(errorMessage(caught))
        }
      })
    return () => controller.abort()
  }, [])

  async function toggle() {
    if (enabled === null) {
      return
    }
    setSaving(true)
    setError(undefined)
    try {
      setEnabled((await adminApi.setRegistration(!enabled)).enabled)
    } catch (caught) {
      setError(errorMessage(caught))
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="flex items-center gap-4">
      <div className="flex flex-1 flex-col gap-0.75">
        <strong id={labelId} className="font-semibold text-fg-heading">
          Open registration
        </strong>
        <small id={descriptionId} className="text-sm text-fg-muted">
          Allow anyone who can reach this instance to create an account. Off by default.
        </small>
        {error && (
          <small role="alert" className="text-sm text-danger">
            {error}
          </small>
        )}
      </div>
      {enabled === null ? (
        !error && <Badge tone="neutral">Loading…</Badge>
      ) : (
        <button
          type="button"
          role="switch"
          aria-checked={enabled}
          aria-labelledby={labelId}
          aria-describedby={descriptionId}
          disabled={saving}
          onClick={() => void toggle()}
          className={
            'relative inline-flex h-7 w-12 shrink-0 items-center rounded-full border transition-colors ' +
            'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus ' +
            'disabled:cursor-not-allowed disabled:opacity-60 ' +
            (enabled ? 'border-primary bg-primary' : 'border-line-emphasis bg-surface-muted')
          }
        >
          <span
            aria-hidden="true"
            className={
              'inline-block size-5 rounded-full bg-fg-heading transition-transform ' +
              (enabled ? 'translate-x-6' : 'translate-x-1')
            }
          />
        </button>
      )}
    </div>
  )
}

function PasswordResetLink() {
  const [email, setEmail] = useState('')
  const [issued, setIssued] = useState<PasswordResetIssued & { email: string }>()
  const [error, setError] = useState<string>()
  const [emailError, setEmailError] = useState<string>()
  const [submitting, setSubmitting] = useState(false)
  const [copyStatus, setCopyStatus] = useState<'idle' | 'copied' | 'failed'>('idle')

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(undefined)
    setEmailError(undefined)
    setIssued(undefined)
    setCopyStatus('idle')
    setSubmitting(true)
    try {
      const result = await adminApi.issuePasswordReset(email)
      setIssued({ ...result, email })
      setEmail('')
    } catch (caught) {
      const byField = fieldErrors(caught)
      if (byField['email']) {
        setEmailError(byField['email'])
      } else {
        setError(errorMessage(caught))
      }
    } finally {
      setSubmitting(false)
    }
  }

  const link = issued ? `${window.location.origin}${issued.reset_path}` : ''

  async function copyLink() {
    try {
      await navigator.clipboard.writeText(link)
      setCopyStatus('copied')
    } catch {
      // Clipboard access can be refused (for example outside a secure context).
      setCopyStatus('failed')
    }
  }

  return (
    <div className="flex flex-col gap-3 border-t border-line-soft pt-5">
      <div className="flex flex-col gap-0.75">
        <strong className="font-semibold text-fg-heading">Password reset link</strong>
        <small className="text-sm text-fg-muted">
          Create a one-time link for a user who cannot sign in, and give it to them through a
          trusted channel. AEGIS does not send email. The link is shown only once and replaces any
          earlier link for the same user.
        </small>
      </div>
      <form
        className="flex flex-col gap-3 sm:flex-row sm:items-end"
        onSubmit={(event) => void handleSubmit(event)}
      >
        <div className="flex-1">
          <Input
            label="User's email address"
            type="email"
            autoComplete="off"
            value={email}
            error={emailError}
            onChange={(event) => setEmail(event.target.value)}
          />
        </div>
        <Button type="submit" variant="secondary" disabled={submitting || !email}>
          Create link
        </Button>
      </form>
      {error && (
        <p role="alert" className="text-sm text-danger">
          {error}
        </p>
      )}
      {issued && (
        <output className="flex flex-col gap-2 rounded-control border border-chart-blue/30 bg-chart-blue/8 p-3.5">
          <p className="text-sm text-fg">
            Reset link for <strong className="text-fg-heading">{issued.email}</strong>, valid until{' '}
            {new Date(issued.expires_at).toLocaleString()}:
          </p>
          <code className="block overflow-x-auto rounded-md bg-canvas p-2.5 font-mono text-xs break-all text-fg-heading">
            {link}
          </code>
          <div className="flex items-center gap-3">
            <Button size="sm" variant="secondary" onClick={() => void copyLink()}>
              Copy link
            </Button>
            {copyStatus === 'copied' && <span className="text-sm text-success">Copied</span>}
            {copyStatus === 'failed' && (
              <span role="alert" className="text-sm text-danger">
                Could not copy. Select the link above and copy it manually.
              </span>
            )}
          </div>
        </output>
      )}
    </div>
  )
}
