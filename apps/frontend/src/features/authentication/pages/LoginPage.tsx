import { useEffect, useState, type FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router'
import { paths } from '../../../app/router/paths'
import { Button, Input } from '../../../components/ui'
import { authApi } from '../api'
import { useAuth } from '../authContext'
import { AuthLayout, FormAlert } from '../components/AuthLayout'
import { errorMessage } from '../errors'
import { redirectTarget } from '../redirect'

const linkClasses =
  'font-medium text-info underline-offset-2 hover:underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus'

export function LoginPage() {
  const { state, signIn } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string>()
  const [submitting, setSubmitting] = useState(false)
  const [registrationEnabled, setRegistrationEnabled] = useState(false)

  useEffect(() => {
    const controller = new AbortController()
    authApi
      .options(controller.signal)
      .then((options) => setRegistrationEnabled(options.registration_enabled))
      .catch(() => setRegistrationEnabled(false))
    return () => controller.abort()
  }, [])

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(undefined)
    setSubmitting(true)
    try {
      await signIn(email, password)
      void navigate(redirectTarget(location), { replace: true })
    } catch (caught) {
      setError(errorMessage(caught))
      setPassword('')
      setSubmitting(false)
    }
  }

  const reason = state.status === 'anonymous' ? state.reason : undefined

  return (
    <AuthLayout title="Sign in" description="Sign in to your AEGIS account.">
      {error && <FormAlert tone="error">{error}</FormAlert>}
      {!error && reason === 'expired' && (
        <FormAlert tone="info">Your session has expired. Sign in again.</FormAlert>
      )}
      {!error && reason === 'signed_out' && (
        <FormAlert tone="success">You have been signed out.</FormAlert>
      )}
      {!error && reason === 'signed_out_unconfirmed' && (
        <FormAlert tone="info">
          You are signed out of this browser. The server did not confirm that your session ended; it
          expires on its own after a period of inactivity.
        </FormAlert>
      )}
      <form
        className="flex flex-col gap-4.5"
        onSubmit={(event) => void handleSubmit(event)}
        noValidate
      >
        <Input
          label="Email address"
          type="email"
          name="email"
          autoComplete="username"
          required
          value={email}
          onChange={(event) => setEmail(event.target.value)}
        />
        <Input
          label="Password"
          type="password"
          name="password"
          autoComplete="current-password"
          required
          value={password}
          onChange={(event) => setPassword(event.target.value)}
        />
        <Button type="submit" disabled={submitting || !email || !password}>
          {submitting ? 'Signing in…' : 'Sign in'}
        </Button>
      </form>
      <p className="mt-5 text-sm text-fg-muted">
        Forgot your password? Ask your AEGIS administrator for a reset link.
      </p>
      {registrationEnabled && (
        <p className="mt-2 text-sm text-fg-muted">
          No account?{' '}
          <Link to={paths.register} className={linkClasses}>
            Create one
          </Link>
        </p>
      )}
    </AuthLayout>
  )
}
