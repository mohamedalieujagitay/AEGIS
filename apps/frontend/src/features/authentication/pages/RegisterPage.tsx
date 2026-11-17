import { useEffect, useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router'
import { paths } from '../../../app/router/paths'
import { Button, Input } from '../../../components/ui'
import { ApiError } from '../../../lib/api'
import { authApi } from '../api'
import { useAuth } from '../authContext'
import { AuthLayout, FormAlert } from '../components/AuthLayout'
import { errorMessage, fieldErrors, PASSWORD_MIN_LENGTH, passwordProblem } from '../errors'

const linkClasses =
  'font-medium text-info underline-offset-2 hover:underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus'

type Availability = 'checking' | 'open' | 'closed'

export function RegisterPage() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [availability, setAvailability] = useState<Availability>('checking')
  const [email, setEmail] = useState('')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [confirmation, setConfirmation] = useState('')
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [formError, setFormError] = useState<string>()
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    const controller = new AbortController()
    authApi
      .options(controller.signal)
      .then((options) => setAvailability(options.registration_enabled ? 'open' : 'closed'))
      .catch(() => setAvailability('closed'))
    return () => controller.abort()
  }, [])

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setFormError(undefined)
    const problem = passwordProblem(password, confirmation)
    if (problem) {
      setErrors({ [problem.includes('match') ? 'confirmation' : 'password']: problem })
      return
    }
    setErrors({})
    setSubmitting(true)
    try {
      await register(email, username, password)
      void navigate(paths.overview, { replace: true })
    } catch (caught) {
      setSubmitting(false)
      if (caught instanceof ApiError && caught.code === 'password_rejected') {
        setErrors({ password: caught.message })
      } else if (caught instanceof ApiError && caught.code === 'registration_disabled') {
        setAvailability('closed')
      } else {
        const byField = fieldErrors(caught)
        setErrors(byField)
        if (Object.keys(byField).length === 0) {
          setFormError(errorMessage(caught))
        }
      }
    }
  }

  if (availability !== 'open') {
    return (
      <AuthLayout title="Create an account">
        {availability === 'checking' ? (
          <output className="text-fg-muted">Loading…</output>
        ) : (
          <FormAlert tone="info">
            Open registration is turned off on this AEGIS instance. Ask your administrator for an
            account.
          </FormAlert>
        )}
        <Link to={paths.login} className={linkClasses}>
          Back to sign in
        </Link>
      </AuthLayout>
    )
  }

  return (
    <AuthLayout title="Create an account" description="Register a new AEGIS account.">
      {formError && <FormAlert tone="error">{formError}</FormAlert>}
      <form
        className="flex flex-col gap-4.5"
        onSubmit={(event) => void handleSubmit(event)}
        noValidate
      >
        <Input
          label="Email address"
          type="email"
          autoComplete="email"
          required
          value={email}
          error={errors['email']}
          onChange={(event) => setEmail(event.target.value)}
        />
        <Input
          label="Username"
          autoComplete="username"
          hint="3 to 32 characters: letters, digits, dots, hyphens and underscores."
          required
          value={username}
          error={errors['username']}
          onChange={(event) => setUsername(event.target.value)}
        />
        <Input
          label="Password"
          type="password"
          autoComplete="new-password"
          hint={`At least ${PASSWORD_MIN_LENGTH} characters. A passphrase of several words works well.`}
          required
          value={password}
          error={errors['password']}
          onChange={(event) => setPassword(event.target.value)}
        />
        <Input
          label="Confirm password"
          type="password"
          autoComplete="new-password"
          required
          value={confirmation}
          error={errors['confirmation']}
          onChange={(event) => setConfirmation(event.target.value)}
        />
        <Button type="submit" disabled={submitting || !email || !username || !password}>
          {submitting ? 'Creating account…' : 'Create account'}
        </Button>
      </form>
      <p className="mt-5 text-sm text-fg-muted">
        Already have an account?{' '}
        <Link to={paths.login} className={linkClasses}>
          Sign in
        </Link>
      </p>
    </AuthLayout>
  )
}
