import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { Badge, Button, Input } from '../../../components/ui'
import { ApiError } from '../../../lib/api'
import { accountApi, type Profile } from '../account'
import { useAuth, useCurrentUser } from '../authContext'
import { errorMessage, fieldErrors } from '../errors'

const USERNAME_HINT = '3 to 32 letters, digits, dots, hyphens and underscores.'
const USERNAME_PATTERN = /^[A-Za-z0-9._-]{3,32}$/

function formatDate(value: string): string {
  return new Date(value).toLocaleDateString()
}

/**
 * The signed-in user's profile: read-only email, creation date and status, and
 * a username change that needs the current password (roadmap task 2.2).
 */
export function ProfileSettings() {
  const user = useCurrentUser()
  const { updateUser } = useAuth()
  const [profile, setProfile] = useState<Profile>()
  const [loadError, setLoadError] = useState<string>()
  const [username, setUsername] = useState('')
  const [currentPassword, setCurrentPassword] = useState('')
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [formError, setFormError] = useState<string>()
  const [saved, setSaved] = useState<string>()
  const [saving, setSaving] = useState(false)

  const load = useCallback((signal?: AbortSignal) => {
    return accountApi
      .profile(signal)
      .then((loaded) => {
        setProfile(loaded)
        setUsername(loaded.username)
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

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSaved(undefined)
    setFormError(undefined)
    const problems: Record<string, string> = {}
    if (!USERNAME_PATTERN.test(username)) {
      problems['username'] = 'Use 3 to 32 letters, digits, dots, hyphens and underscores.'
    }
    if (!currentPassword) {
      problems['currentPassword'] = 'Enter your current password to change the username.'
    }
    if (Object.keys(problems).length > 0) {
      setErrors(problems)
      return
    }
    setErrors({})
    setSaving(true)
    try {
      const updated = await accountApi.updateUsername(username, currentPassword)
      setProfile(updated)
      setUsername(updated.username)
      updateUser({ ...user, username: updated.username })
      setSaved('Your username was changed.')
    } catch (caught) {
      if (caught instanceof ApiError && caught.code === 'current_password_incorrect') {
        setErrors({ currentPassword: caught.message })
      } else {
        const byField = fieldErrors(caught)
        if (Object.keys(byField).length > 0) {
          setErrors({
            ...(byField['username'] ? { username: byField['username'] } : {}),
            ...(byField['current_password']
              ? { currentPassword: byField['current_password'] }
              : {}),
          })
        } else {
          setFormError(errorMessage(caught))
        }
      }
    } finally {
      // The password is never kept after an attempt, successful or not.
      setCurrentPassword('')
      setSaving(false)
    }
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

  if (profile === undefined) {
    return <output className="text-sm text-fg-muted">Loading your profile…</output>
  }

  const unchanged = username === profile.username

  return (
    <div className="flex flex-col gap-6">
      <dl className="grid grid-cols-[auto_1fr] items-center gap-x-6 gap-y-3 text-sm">
        <dt className="text-fg-muted">Email address</dt>
        <dd className="text-fg">
          {profile.email} <span className="text-fg-muted">(read-only)</span>
        </dd>
        <dt className="text-fg-muted">Account created</dt>
        <dd className="text-fg">{formatDate(profile.createdAt)}</dd>
        <dt className="text-fg-muted">Status</dt>
        <dd>
          <Badge tone={profile.isActive ? 'success' : 'danger'}>
            {profile.isActive ? 'Active' : 'Inactive'}
          </Badge>
        </dd>
      </dl>

      <form
        className="flex flex-col gap-4"
        onSubmit={(event) => void handleSubmit(event)}
        noValidate
      >
        <Input
          label="Username"
          autoComplete="username"
          hint={USERNAME_HINT}
          value={username}
          error={errors['username']}
          onChange={(event) => setUsername(event.target.value)}
        />
        <Input
          label="Current password"
          type="password"
          autoComplete="current-password"
          hint="Required to change the username."
          value={currentPassword}
          error={errors['currentPassword']}
          onChange={(event) => setCurrentPassword(event.target.value)}
        />
        {formError !== undefined && (
          <p role="alert" className="text-sm text-danger">
            {formError}
          </p>
        )}
        {saved !== undefined && <output className="block text-sm text-success">{saved}</output>}
        <div>
          <Button type="submit" disabled={saving || unchanged}>
            {saving ? 'Saving…' : 'Save username'}
          </Button>
        </div>
      </form>
    </div>
  )
}
