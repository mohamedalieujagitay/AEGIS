import { useEffect, useState, type FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router'
import { paths } from '../../../app/router/paths'
import { Button, Input } from '../../../components/ui'
import { ApiError } from '../../../lib/api'
import { authApi } from '../api'
import { useAuth } from '../authContext'
import { AuthLayout, FormAlert } from '../components/AuthLayout'
import { errorMessage, PASSWORD_MIN_LENGTH, passwordProblem } from '../errors'

const linkClasses =
  'font-medium text-info underline-offset-2 hover:underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus'

/**
 * The reset token from the URL fragment (`#token=...`). A fragment is never
 * sent to the server, so the token does not reach access logs or Referer
 * headers.
 */
function tokenFromFragment(hash: string): string | null {
  return new URLSearchParams(hash.slice(1)).get('token')
}

export function ResetPasswordPage() {
  const { sessionEnded } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const [token] = useState(() => tokenFromFragment(location.hash))

  // Once read, remove the token from the address bar and the history entry.
  // Done through the router, so its own location (not only the browser's) loses it.
  useEffect(() => {
    if (location.hash) {
      void navigate({ pathname: location.pathname, search: location.search }, { replace: true })
    }
  }, [location.hash, location.pathname, location.search, navigate])

  const [password, setPassword] = useState('')
  const [confirmation, setConfirmation] = useState('')
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [formError, setFormError] = useState<string>()
  const [submitting, setSubmitting] = useState(false)
  const [done, setDone] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!token) {
      return
    }
    setFormError(undefined)
    const problem = passwordProblem(password, confirmation)
    if (problem) {
      setErrors({ [problem.includes('match') ? 'confirmation' : 'password']: problem })
      return
    }
    setErrors({})
    setSubmitting(true)
    try {
      await authApi.resetPassword(token, password)
      // Every session of the account was signed out, including this browser's.
      sessionEnded()
      setDone(true)
    } catch (caught) {
      setSubmitting(false)
      if (caught instanceof ApiError && caught.code === 'password_rejected') {
        setErrors({ password: caught.message })
      } else {
        setFormError(errorMessage(caught))
      }
    }
  }

  if (done) {
    return (
      <AuthLayout title="Password changed">
        <FormAlert tone="success">
          Your password has been changed and all your sessions have been signed out.
        </FormAlert>
        <Link to={paths.login} className={linkClasses}>
          Sign in with your new password
        </Link>
      </AuthLayout>
    )
  }

  if (!token) {
    return (
      <AuthLayout title="Reset your password">
        <FormAlert tone="error">
          This page needs the reset link from your administrator. Open the complete link, or ask for
          a new one.
        </FormAlert>
        <Link to={paths.login} className={linkClasses}>
          Back to sign in
        </Link>
      </AuthLayout>
    )
  }

  return (
    <AuthLayout title="Reset your password" description="Choose a new password for your account.">
      {formError && <FormAlert tone="error">{formError}</FormAlert>}
      <form
        className="flex flex-col gap-4.5"
        onSubmit={(event) => void handleSubmit(event)}
        noValidate
      >
        <Input
          label="New password"
          type="password"
          autoComplete="new-password"
          hint={`At least ${PASSWORD_MIN_LENGTH} characters.`}
          required
          value={password}
          error={errors['password']}
          onChange={(event) => setPassword(event.target.value)}
        />
        <Input
          label="Confirm new password"
          type="password"
          autoComplete="new-password"
          required
          value={confirmation}
          error={errors['confirmation']}
          onChange={(event) => setConfirmation(event.target.value)}
        />
        <Button type="submit" disabled={submitting || !password}>
          {submitting ? 'Saving…' : 'Set new password'}
        </Button>
      </form>
    </AuthLayout>
  )
}
