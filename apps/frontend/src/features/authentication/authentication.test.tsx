import { act, render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { createMemoryRouter, RouterProvider } from 'react-router'
import { describe, expect, it, vi } from 'vitest'
import { paths } from '../../app/router/paths'
import { routes } from '../../app/router/routes'
import { isRecord, UNAUTHENTICATED_EVENT } from '../../lib/api'
import {
  apiError,
  authOptions,
  mockApi,
  signedIn,
  signedOut,
  testAdmin,
  testUser,
} from '../../test/apiMock'

const PASSWORD = 'correct horse battery staple'

function renderAt(path: string) {
  const user = userEvent.setup()
  const router = createMemoryRouter(routes, { initialEntries: [path] })
  render(<RouterProvider router={router} />)
  return { user, router }
}

const session = { body: { user: testUser, csrf_token: 'session-csrf-token' } }

describe('sign-in', () => {
  it('sends visitors without a session to the sign-in page, then back where they were', async () => {
    const { requests } = mockApi({ ...signedOut(), 'POST /auth/login': session })
    const { user, router } = renderAt(paths.assets)

    expect(await screen.findByRole('heading', { level: 1, name: 'Sign in' })).toBeInTheDocument()
    expect(router.state.location.pathname).toBe(paths.login)

    await user.type(screen.getByLabelText('Email address'), 'alice@example.com')
    await user.type(screen.getByLabelText('Password'), PASSWORD)
    await user.click(screen.getByRole('button', { name: 'Sign in' }))

    expect(await screen.findByRole('heading', { level: 1, name: 'Assets' })).toBeInTheDocument()
    expect(router.state.location.pathname).toBe(paths.assets)
    expect(screen.getByText('alice')).toBeInTheDocument()

    const login = requests.find((r) => r.path === '/auth/login')
    expect(login?.body).toEqual({ email: 'alice@example.com', password: PASSWORD })
    expect(login?.headers['X-CSRF-Token']).toBe('anonymous-csrf-token')
  })

  it('shows the generic error and clears the password after a failed sign-in', async () => {
    mockApi({
      ...signedOut(),
      'POST /auth/login': apiError(401, 'invalid_credentials', 'Incorrect email or password.'),
    })
    const { user } = renderAt(paths.login)

    await user.type(await screen.findByLabelText('Email address'), 'alice@example.com')
    await user.type(screen.getByLabelText('Password'), 'wrong password')
    await user.click(screen.getByRole('button', { name: 'Sign in' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Incorrect email or password.')
    expect(screen.getByLabelText('Password')).toHaveValue('')
  })

  it('tells the user how long to wait when throttled', async () => {
    mockApi({
      ...signedOut(),
      'POST /auth/login': {
        ...apiError(429, 'too_many_requests', 'Too many attempts. Wait a moment and try again.'),
        headers: { 'Retry-After': '120' },
      },
    })
    const { user } = renderAt(paths.login)

    await user.type(await screen.findByLabelText('Email address'), 'alice@example.com')
    await user.type(screen.getByLabelText('Password'), PASSWORD)
    await user.click(screen.getByRole('button', { name: 'Sign in' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('try again in about 2 minutes')
  })

  it('offers registration only when the instance allows it', async () => {
    mockApi({
      ...signedOut(),
      'GET /auth/options': { body: { ...authOptions, registration_enabled: true } },
    })
    renderAt(paths.login)

    expect(await screen.findByRole('link', { name: 'Create one' })).toHaveAttribute(
      'href',
      paths.register,
    )
  })

  it('does not show registration when it is disabled', async () => {
    mockApi(signedOut())
    renderAt(paths.login)

    await screen.findByRole('heading', { level: 1, name: 'Sign in' })
    expect(screen.queryByRole('link', { name: 'Create one' })).not.toBeInTheDocument()
    expect(screen.getByText(/Ask your AEGIS administrator for a reset link/)).toBeInTheDocument()
  })

  it('sends signed-in users away from the sign-in page', async () => {
    mockApi(signedIn())
    const { router } = renderAt(paths.login)

    expect(await screen.findByRole('heading', { level: 1, name: 'Overview' })).toBeInTheDocument()
    expect(router.state.location.pathname).toBe(paths.overview)
  })

  it('never stores anything in browser storage', async () => {
    const setItem = vi.spyOn(Storage.prototype, 'setItem')
    mockApi({ ...signedOut(), 'POST /auth/login': session })
    const { user } = renderAt(paths.login)

    await user.type(await screen.findByLabelText('Email address'), 'alice@example.com')
    await user.type(screen.getByLabelText('Password'), PASSWORD)
    await user.click(screen.getByRole('button', { name: 'Sign in' }))
    await screen.findByRole('heading', { level: 1, name: 'Overview' })

    expect(setItem).not.toHaveBeenCalled()
    expect(document.cookie).toBe('')
  })
})

describe('session', () => {
  it('signs out on the server and returns to the sign-in page', async () => {
    const { requests } = mockApi({
      ...signedIn(),
      'POST /auth/logout': { status: 204 },
    })
    const { user, router } = renderAt(paths.overview)

    await user.click(await screen.findByRole('button', { name: 'Sign out' }))

    expect(await screen.findByText('You have been signed out.')).toBeInTheDocument()
    expect(router.state.location.pathname).toBe(paths.login)
    expect(requests.some((r) => r.method === 'POST' && r.path === '/auth/logout')).toBe(true)
  })

  it('returns to the sign-in page when the session expires', async () => {
    mockApi(signedIn())
    const { router } = renderAt(paths.findings)
    await screen.findByRole('heading', { level: 1, name: 'Findings' })

    act(() => {
      window.dispatchEvent(new CustomEvent(UNAUTHENTICATED_EVENT, { detail: 'session_expired' }))
    })

    expect(await screen.findByText('Your session has expired. Sign in again.')).toBeInTheDocument()
    expect(router.state.location.pathname).toBe(paths.login)
  })

  it('explains when the API cannot be reached and can try again', async () => {
    let available = false
    mockApi({
      'GET /auth/me': () =>
        available ? { body: testUser } : apiError(503, 'service_unavailable', 'Try again later.'),
      'GET /auth/options': { body: authOptions },
    })
    const { user } = renderAt(paths.overview)

    expect(
      await screen.findByRole('heading', { level: 1, name: 'AEGIS is unavailable' }),
    ).toBeInTheDocument()
    available = true
    await user.click(screen.getByRole('button', { name: 'Try again' }))

    expect(await screen.findByRole('heading', { level: 1, name: 'Overview' })).toBeInTheDocument()
  })
})

describe('registration', () => {
  const open = { 'GET /auth/options': { body: { ...authOptions, registration_enabled: true } } }

  async function fillIn(user: ReturnType<typeof userEvent.setup>, confirmation = PASSWORD) {
    await user.type(await screen.findByLabelText('Email address'), 'new@example.com')
    await user.type(screen.getByLabelText('Username'), 'newuser')
    await user.type(screen.getByLabelText('Password'), PASSWORD)
    await user.type(screen.getByLabelText('Confirm password'), confirmation)
    await user.click(screen.getByRole('button', { name: 'Create account' }))
  }

  it('explains when registration is turned off', async () => {
    mockApi(signedOut())
    renderAt(paths.register)

    expect(await screen.findByText(/Open registration is turned off/)).toBeInTheDocument()
    expect(screen.queryByLabelText('Username')).not.toBeInTheDocument()
  })

  it('checks that the passwords match before sending anything', async () => {
    const { requests } = mockApi({ ...signedOut(), ...open })
    const { user } = renderAt(paths.register)

    await fillIn(user, 'something else entirely')

    expect(screen.getByLabelText('Confirm password')).toHaveAccessibleDescription(
      'The passwords do not match.',
    )
    expect(requests.some((r) => r.path === '/auth/register')).toBe(false)
  })

  it('creates the account and signs in', async () => {
    const { requests } = mockApi({
      ...signedOut(),
      ...open,
      'POST /auth/register': { status: 201, body: session.body },
    })
    const { user } = renderAt(paths.register)

    await fillIn(user)

    expect(await screen.findByRole('heading', { level: 1, name: 'Overview' })).toBeInTheDocument()
    expect(requests.find((r) => r.path === '/auth/register')?.body).toEqual({
      email: 'new@example.com',
      username: 'newuser',
      password: PASSWORD,
    })
  })

  it('shows the server password policy and field errors next to the fields', async () => {
    let call = 0
    mockApi({
      ...signedOut(),
      ...open,
      'POST /auth/register': () => {
        call += 1
        return call === 1
          ? apiError(422, 'password_rejected', 'Do not include your username.')
          : apiError(422, 'validation_error', 'The request is not valid.', {
              details: [
                {
                  location: ['body', 'email'],
                  message: 'Enter a valid email address.',
                  type: 'value_error',
                },
              ],
            })
      },
    })
    const { user } = renderAt(paths.register)

    await fillIn(user)
    expect(await screen.findByLabelText('Password')).toHaveAccessibleDescription(
      expect.stringContaining('Do not include your username.'),
    )

    await user.click(screen.getByRole('button', { name: 'Create account' }))
    expect(await screen.findByLabelText('Email address')).toHaveAccessibleDescription(
      'Enter a valid email address.',
    )
  })
})

describe('password reset', () => {
  /** The address of a reset link, as the administrator hands it out. */
  function resetLink(fragment: string) {
    return `${paths.resetPassword}${fragment}`
  }

  it('reads the token from the link, removes it from the address bar and resets', async () => {
    const { requests } = mockApi({ ...signedOut(), 'POST /auth/password/reset': { status: 204 } })
    const { user, router } = renderAt(resetLink('#token=reset-token-from-admin'))

    await user.type(await screen.findByLabelText('New password'), PASSWORD)
    expect(router.state.location.hash).toBe('')
    await user.type(screen.getByLabelText('Confirm new password'), PASSWORD)
    await user.click(screen.getByRole('button', { name: 'Set new password' }))

    expect(await screen.findByText(/all your sessions have been signed out/)).toBeInTheDocument()
    expect(requests.find((r) => r.path === '/auth/password/reset')?.body).toEqual({
      token: 'reset-token-from-admin',
      new_password: PASSWORD,
    })
  })

  it('reports invalid or expired links', async () => {
    mockApi({
      ...signedOut(),
      'POST /auth/password/reset': apiError(
        400,
        'invalid_reset_token',
        'This reset link is invalid or has expired. Ask your administrator for a new one.',
      ),
    })
    const { user } = renderAt(resetLink('#token=used-token'))

    await user.type(await screen.findByLabelText('New password'), PASSWORD)
    await user.type(screen.getByLabelText('Confirm new password'), PASSWORD)
    await user.click(screen.getByRole('button', { name: 'Set new password' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('invalid or has expired')
  })

  it('needs the complete link', async () => {
    mockApi(signedOut())
    renderAt(resetLink(''))

    expect(await screen.findByText(/needs the reset link/)).toBeInTheDocument()
  })
})

describe('settings', () => {
  it('shows the real session policy', async () => {
    mockApi(signedIn())
    const { user } = renderAt(paths.settings)

    await user.click(await screen.findByRole('tab', { name: 'Security' }))

    expect(
      await screen.findByText(/Signed out after 60 minutes of inactivity, and after 12 hours/),
    ).toBeInTheDocument()
    expect(screen.queryByRole('region', { name: 'Instance administration' })).toBeNull()
  })

  it('lets an instance administrator switch registration and create reset links', async () => {
    const { requests } = mockApi({
      ...signedIn(testAdmin),
      'GET /admin/settings/registration': { body: { enabled: false } },
      'PUT /admin/settings/registration': { body: { enabled: true } },
      'POST /admin/password-resets': (request) =>
        isRecord(request.body) && request.body['email'] === 'ghost@example.com'
          ? apiError(404, 'user_not_found', 'No account uses this email address.')
          : {
              status: 201,
              body: {
                reset_token: 'abc',
                reset_path: '/reset-password#token=abc',
                expires_at: '2026-11-17T10:00:00Z',
              },
            },
    })
    const { user } = renderAt(paths.settings)
    await user.click(await screen.findByRole('tab', { name: 'Security' }))
    const admin = await screen.findByRole('region', { name: 'Instance administration' })

    const toggle = await within(admin).findByRole('switch', { name: 'Open registration' })
    expect(toggle).toHaveAttribute('aria-checked', 'false')
    await user.click(toggle)
    expect(await within(admin).findByRole('switch', { checked: true })).toBeInTheDocument()
    expect(requests.find((r) => r.method === 'PUT')?.body).toEqual({ enabled: true })

    const email = within(admin).getByLabelText("User's email address")
    await user.type(email, 'ghost@example.com')
    await user.click(within(admin).getByRole('button', { name: 'Create link' }))
    expect(await within(admin).findByRole('alert')).toHaveTextContent('No account uses')

    await user.clear(email)
    await user.type(email, 'alice@example.com')
    await user.click(within(admin).getByRole('button', { name: 'Create link' }))
    expect(
      await within(admin).findByText(`${window.location.origin}/reset-password#token=abc`),
    ).toBeInTheDocument()
  })
})

describe('reset page while already signed in', () => {
  it('stays reachable for a signed-in user, and ends this browser session after the reset', async () => {
    mockApi({
      ...signedIn(),
      'POST /auth/password/reset': { status: 204 },
    })
    const { user, router } = renderAt(`${paths.resetPassword}#token=reset-token-value`)

    // Not redirected to the application: the form is shown to the signed-in user.
    expect(
      await screen.findByRole('heading', { level: 1, name: 'Reset your password' }),
    ).toBeInTheDocument()
    expect(router.state.location.pathname).toBe(paths.resetPassword)

    await user.type(screen.getByLabelText('New password'), PASSWORD)
    await user.type(screen.getByLabelText('Confirm new password'), PASSWORD)
    await user.click(screen.getByRole('button', { name: 'Set new password' }))

    expect(await screen.findByText(/all your sessions have been signed out/)).toBeInTheDocument()
    expect(screen.queryByText('alice')).not.toBeInTheDocument()
  })
})

describe('failed sign-out', () => {
  it('does not claim the server ended the session when the sign-out request fails', async () => {
    mockApi({
      ...signedIn(),
      'POST /auth/logout': apiError(
        500,
        'http_error',
        'The server could not complete the request.',
      ),
    })
    const { user, router } = renderAt(paths.overview)

    await user.click(await screen.findByRole('button', { name: 'Sign out' }))

    expect(await screen.findByText(/did not confirm that your session ended/)).toBeInTheDocument()
    expect(screen.queryByText('You have been signed out.')).not.toBeInTheDocument()
    expect(router.state.location.pathname).toBe(paths.login)
  })

  it('still signs the browser out locally when the server cannot be reached', async () => {
    mockApi({ ...signedIn() })
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: string, init?: RequestInit) => {
        if (init?.method === 'POST' && input.endsWith('/auth/logout')) {
          throw new TypeError('Failed to fetch')
        }
        return new Response(JSON.stringify(input.endsWith('/auth/me') ? testUser : authOptions), {
          headers: { 'Content-Type': 'application/json' },
        })
      }),
    )
    const { user, router } = renderAt(paths.overview)

    await user.click(await screen.findByRole('button', { name: 'Sign out' }))

    expect(await screen.findByRole('heading', { level: 1, name: 'Sign in' })).toBeInTheDocument()
    expect(router.state.location.pathname).toBe(paths.login)
  })
})

describe('reset link copy', () => {
  /** user-event installs the clipboard before the test runs; spy on that object. */
  function stubClipboard(outcome: 'copied' | 'denied') {
    return vi
      .spyOn(navigator.clipboard, 'writeText')
      .mockImplementation(() =>
        outcome === 'copied'
          ? Promise.resolve()
          : Promise.reject(new DOMException('denied', 'NotAllowedError')),
      )
  }

  async function issueLink(user: ReturnType<typeof userEvent.setup>) {
    mockApi({
      ...signedIn(testAdmin),
      'GET /admin/settings/registration': { body: { enabled: false } },
      'POST /admin/password-resets': {
        status: 201,
        body: {
          reset_token: 'copy-token',
          reset_path: '/reset-password#token=copy-token',
          expires_at: '2026-11-17T10:00:00Z',
        },
      },
    })
    renderAt(paths.settings)
    await user.click(await screen.findByRole('tab', { name: 'Security' }))
    const admin = await screen.findByRole('region', { name: 'Instance administration' })
    await user.type(within(admin).getByLabelText("User's email address"), 'alice@example.com')
    await user.click(within(admin).getByRole('button', { name: 'Create link' }))
    await within(admin).findByText(/Reset link for/)
    return admin
  }

  it('copies the full link and confirms it', async () => {
    const user = userEvent.setup()
    const writeText = stubClipboard('copied')
    const admin = await issueLink(user)

    await user.click(within(admin).getByRole('button', { name: 'Copy link' }))

    expect(writeText).toHaveBeenCalledWith(
      `${window.location.origin}/reset-password#token=copy-token`,
    )
    expect(await within(admin).findByText('Copied')).toBeInTheDocument()
  })

  it('says when copying fails and keeps the link selectable', async () => {
    const user = userEvent.setup()
    stubClipboard('denied')
    const admin = await issueLink(user)

    await user.click(within(admin).getByRole('button', { name: 'Copy link' }))

    expect(await within(admin).findByRole('alert')).toHaveTextContent('Could not copy')
    expect(within(admin).queryByText('Copied')).not.toBeInTheDocument()
    expect(
      within(admin).getByText(`${window.location.origin}/reset-password#token=copy-token`),
    ).toBeInTheDocument()
  })
})
