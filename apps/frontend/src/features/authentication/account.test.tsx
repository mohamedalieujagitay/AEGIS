import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { createMemoryRouter, RouterProvider } from 'react-router'
import { describe, expect, it } from 'vitest'
import { paths } from '../../app/router/paths'
import { routes } from '../../app/router/routes'
import { apiError, mockApi, signedIn, type MockResponse } from '../../test/apiMock'

const CURRENT_PASSWORD = 'correct horse battery staple'
const NEW_PASSWORD = 'a completely different passphrase'

function renderAt(path: string) {
  const user = userEvent.setup()
  const router = createMemoryRouter(routes, { initialEntries: [path] })
  render(<RouterProvider router={router} />)
  return { user, router }
}

const profileBody = {
  email: 'alice@example.com',
  username: 'alice',
  created_at: '2026-11-01T09:00:00Z',
  is_active: true,
}
const profile: MockResponse = { body: profileBody }

const sessionList = [
  {
    id: 'session-current',
    created_at: '2026-11-17T08:00:00Z',
    last_seen_at: '2026-11-17T09:00:00Z',
    expires_at: '2026-11-17T20:00:00Z',
    user_agent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/130.0 Safari/537.36',
    current: true,
  },
  {
    id: 'session-other',
    created_at: '2026-11-16T08:00:00Z',
    last_seen_at: '2026-11-16T10:00:00Z',
    expires_at: '2026-11-16T20:00:00Z',
    user_agent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) Firefox/131.0',
    current: false,
  },
]

/** The list row of a session, found by its browser description. */
function rowFor(scope: ReturnType<typeof within>, browser: string): ReturnType<typeof within> {
  const row = scope.getByText(browser).closest('li')
  if (row === null) {
    throw new Error(`no session row for ${browser}`)
  }
  return within(row)
}

async function openTab(user: ReturnType<typeof userEvent.setup>, name: string) {
  await user.click(await screen.findByRole('tab', { name }))
}

describe('profile', () => {
  it('shows the email read-only, the creation date and the account status', async () => {
    mockApi({ ...signedIn(), 'GET /account/profile': profile })
    const { user } = renderAt(paths.settings)

    await openTab(user, 'Account')

    const account = within(await screen.findByRole('region', { name: 'Account' }))
    expect(await account.findByText('(read-only)')).toBeInTheDocument()
    expect(account.getByText('alice@example.com', { exact: false })).toBeInTheDocument()
    expect(account.getByText('Active')).toBeInTheDocument()
    expect(account.queryByLabelText('Email address')).toBeNull()
  })

  it('keeps the save button off until the username changes', async () => {
    mockApi({ ...signedIn(), 'GET /account/profile': profile })
    const { user } = renderAt(paths.settings)
    await openTab(user, 'Account')

    const save = await screen.findByRole('button', { name: 'Save username' })
    expect(save).toBeDisabled()

    await user.clear(screen.getByLabelText('Username'))
    await user.type(screen.getByLabelText('Username'), 'alice.smith')
    expect(save).toBeEnabled()
  })

  it('asks for the current password instead of sending a change without it', async () => {
    const { requests } = mockApi({ ...signedIn(), 'GET /account/profile': profile })
    const { user } = renderAt(paths.settings)
    await openTab(user, 'Account')
    await user.clear(await screen.findByLabelText('Username'))
    await user.type(screen.getByLabelText('Username'), 'alice.smith')

    await user.click(screen.getByRole('button', { name: 'Save username' }))

    expect(
      await screen.findByText('Enter your current password to change the username.'),
    ).toBeInTheDocument()
    expect(screen.getByLabelText('Current password')).toHaveAttribute('aria-invalid', 'true')
    expect(requests.some((r) => r.method === 'PATCH')).toBe(false)
  })

  it('changes the username with the current password and shows the new name', async () => {
    const { requests } = mockApi({
      ...signedIn(),
      'GET /account/profile': profile,
      'PATCH /account/profile': {
        body: { ...profileBody, username: 'alice.smith' },
      },
    })
    const { user } = renderAt(paths.settings)
    await openTab(user, 'Account')
    await user.clear(await screen.findByLabelText('Username'))
    await user.type(screen.getByLabelText('Username'), 'alice.smith')
    await user.type(screen.getByLabelText('Current password'), CURRENT_PASSWORD)

    await user.click(screen.getByRole('button', { name: 'Save username' }))

    expect(await screen.findByText('Your username was changed.')).toBeInTheDocument()
    const patch = requests.find((r) => r.method === 'PATCH')
    expect(patch?.body).toEqual({ username: 'alice.smith', current_password: CURRENT_PASSWORD })
    expect(screen.getByLabelText('Current password')).toHaveValue('')
    expect(screen.getByText('alice.smith')).toBeInTheDocument()
  })

  it('reports a wrong current password on its field and clears it', async () => {
    mockApi({
      ...signedIn(),
      'GET /account/profile': profile,
      'PATCH /account/profile': apiError(
        400,
        'current_password_incorrect',
        'The current password is incorrect.',
      ),
    })
    const { user } = renderAt(paths.settings)
    await openTab(user, 'Account')
    await user.clear(await screen.findByLabelText('Username'))
    await user.type(screen.getByLabelText('Username'), 'alice.smith')
    await user.type(screen.getByLabelText('Current password'), 'not the password')

    await user.click(screen.getByRole('button', { name: 'Save username' }))

    expect(await screen.findByText('The current password is incorrect.')).toBeInTheDocument()
    expect(screen.getByLabelText('Current password')).toHaveValue('')
  })

  it('reports a taken username without naming anyone', async () => {
    mockApi({
      ...signedIn(),
      'GET /account/profile': profile,
      'PATCH /account/profile': apiError(
        409,
        'username_unavailable',
        'This username is not available.',
      ),
    })
    const { user } = renderAt(paths.settings)
    await openTab(user, 'Account')
    await user.clear(await screen.findByLabelText('Username'))
    await user.type(screen.getByLabelText('Username'), 'bob')
    await user.type(screen.getByLabelText('Current password'), CURRENT_PASSWORD)

    await user.click(screen.getByRole('button', { name: 'Save username' }))

    expect(await screen.findByText('This username is not available.')).toBeInTheDocument()
  })

  it('rejects an invalid username before sending anything', async () => {
    const { requests } = mockApi({ ...signedIn(), 'GET /account/profile': profile })
    const { user } = renderAt(paths.settings)
    await openTab(user, 'Account')
    await user.clear(await screen.findByLabelText('Username'))
    await user.type(screen.getByLabelText('Username'), 'a!')
    await user.type(screen.getByLabelText('Current password'), CURRENT_PASSWORD)

    await user.click(screen.getByRole('button', { name: 'Save username' }))

    expect(
      await screen.findByText('Use 3 to 32 letters, digits, dots, hyphens and underscores.'),
    ).toBeInTheDocument()
    expect(requests.some((r) => r.method === 'PATCH')).toBe(false)
  })

  it('offers a retry when the profile cannot be loaded', async () => {
    mockApi({
      ...signedIn(),
      'GET /account/profile': apiError(
        500,
        'internal',
        'The server could not complete the request.',
      ),
    })
    const { user } = renderAt(paths.settings)
    await openTab(user, 'Account')

    expect(await screen.findByRole('alert')).toHaveTextContent('could not complete the request')
    expect(screen.getByRole('button', { name: 'Try again' })).toBeInTheDocument()
  })
})

describe('password change', () => {
  async function openSecurity(user: ReturnType<typeof userEvent.setup>) {
    await openTab(user, 'Security')
    const section = await screen.findByRole('region', { name: 'Password' })
    return within(section)
  }

  it('refuses a confirmation that does not match, without sending anything', async () => {
    const { requests } = mockApi({ ...signedIn(), 'GET /account/sessions': { body: sessionList } })
    const { user } = renderAt(paths.settings)
    const section = await openSecurity(user)

    await user.type(section.getByLabelText('Current password'), CURRENT_PASSWORD)
    await user.type(section.getByLabelText('New password'), NEW_PASSWORD)
    await user.type(section.getByLabelText('Confirm new password'), `${NEW_PASSWORD} extra`)
    await user.click(section.getByRole('button', { name: 'Change password' }))

    expect(await section.findByText('The passwords do not match.')).toBeInTheDocument()
    expect(requests.some((r) => r.path === '/account/password')).toBe(false)
  })

  it('changes the password, reports what was signed out and uses the rotated CSRF token next', async () => {
    const { requests } = mockApi({
      ...signedIn(),
      'GET /account/sessions': { body: sessionList },
      'POST /account/password': { body: { csrf_token: 'rotated-csrf-token' } },
      'POST /account/sessions/revoke-others': { body: { revoked: 1 } },
    })
    const { user } = renderAt(paths.settings)
    const section = await openSecurity(user)

    await user.type(section.getByLabelText('Current password'), CURRENT_PASSWORD)
    await user.type(section.getByLabelText('New password'), NEW_PASSWORD)
    await user.type(section.getByLabelText('Confirm new password'), NEW_PASSWORD)
    await user.click(section.getByRole('button', { name: 'Change password' }))

    expect(
      await section.findByText(/Other browsers and trusted devices were signed out/),
    ).toBeInTheDocument()
    const change = requests.find((r) => r.path === '/account/password')
    expect(change?.body).toEqual({
      current_password: CURRENT_PASSWORD,
      new_password: NEW_PASSWORD,
    })
    expect(section.getByLabelText('Current password')).toHaveValue('')

    // A later state-changing request carries the rotated token, not the old one.
    await user.click(screen.getByRole('button', { name: 'Sign out other sessions' }))
    await user.click(screen.getByRole('button', { name: 'Sign out other sessions' }))
    expect(
      requests.find((r) => r.path === '/account/sessions/revoke-others')?.headers['X-CSRF-Token'],
    ).toBe('rotated-csrf-token')
  })

  it('reports a wrong current password on its field', async () => {
    mockApi({
      ...signedIn(),
      'POST /account/password': apiError(
        400,
        'current_password_incorrect',
        'The current password is incorrect.',
      ),
    })
    const { user } = renderAt(paths.settings)
    const section = await openSecurity(user)

    await user.type(section.getByLabelText('Current password'), 'not the password')
    await user.type(section.getByLabelText('New password'), NEW_PASSWORD)
    await user.type(section.getByLabelText('Confirm new password'), NEW_PASSWORD)
    await user.click(section.getByRole('button', { name: 'Change password' }))

    expect(await section.findByText('The current password is incorrect.')).toBeInTheDocument()
  })

  it('reports a rejected new password on the new password field', async () => {
    mockApi({
      ...signedIn(),
      'POST /account/password': apiError(
        422,
        'password_rejected',
        'The password does not meet the requirements.',
      ),
    })
    const { user } = renderAt(paths.settings)
    const section = await openSecurity(user)

    await user.type(section.getByLabelText('Current password'), CURRENT_PASSWORD)
    await user.type(section.getByLabelText('New password'), 'password password')
    await user.type(section.getByLabelText('Confirm new password'), 'password password')
    await user.click(section.getByRole('button', { name: 'Change password' }))

    expect(
      await section.findByText('The password does not meet the requirements.'),
    ).toBeInTheDocument()
  })
})

describe('active sessions', () => {
  async function openSessions(user: ReturnType<typeof userEvent.setup>) {
    await openTab(user, 'Security')
    const section = await screen.findByRole('region', { name: 'Active sessions' })
    return within(section)
  }

  it('lists the sessions, marks this browser and shows no address or token', async () => {
    mockApi({ ...signedIn(), 'GET /account/sessions': { body: sessionList } })
    const { user } = renderAt(paths.settings)

    const section = await openSessions(user)

    expect(await section.findByText('This browser')).toBeInTheDocument()
    expect(section.getAllByRole('listitem')).toHaveLength(2)
    expect(section.getByText('Chrome on Windows')).toBeInTheDocument()
    expect(section.getByText('Firefox on macOS')).toBeInTheDocument()
    expect(section.queryByText(/\d+\.\d+\.\d+\.\d+/)).toBeNull()
    expect(section.queryByText(/token|hash/i)).toBeNull()
  })

  it('asks before signing out another session, then refreshes the list', async () => {
    const { requests } = mockApi({
      ...signedIn(),
      'GET /account/sessions': { body: sessionList },
      'DELETE /account/sessions/session-other': { status: 204 },
    })
    const { user } = renderAt(paths.settings)
    const section = await openSessions(user)

    await section.findByText('Firefox on macOS')
    await user.click(rowFor(section, 'Firefox on macOS').getByRole('button', { name: 'Sign out' }))
    expect(
      await section.findByText('Sign out this session? It will need to sign in again.'),
    ).toBeInTheDocument()
    expect(requests.some((r) => r.method === 'DELETE')).toBe(false)

    await user.click(section.getByRole('button', { name: 'Confirm' }))

    expect(await section.findByText('That session was signed out.')).toBeInTheDocument()
    expect(requests.filter((r) => r.path === '/account/sessions').length).toBeGreaterThan(1)
  })

  it('signs this browser out when its own session is revoked', async () => {
    mockApi({
      ...signedIn(),
      'GET /account/sessions': { body: sessionList },
      'DELETE /account/sessions/session-current': { status: 204 },
    })
    const { user, router } = renderAt(paths.settings)
    const section = await openSessions(user)

    await section.findByText('Chrome on Windows')
    await user.click(
      rowFor(section, 'Chrome on Windows').getByRole('button', { name: 'Sign out this browser' }),
    )
    await user.click(section.getByRole('button', { name: 'Confirm' }))

    expect(await screen.findByRole('heading', { level: 1, name: 'Sign in' })).toBeInTheDocument()
    expect(router.state.location.pathname).toBe(paths.login)
  })

  it('signs out every other session in one action and reports the count', async () => {
    mockApi({
      ...signedIn(),
      'GET /account/sessions': { body: sessionList },
      'POST /account/sessions/revoke-others': { body: { revoked: 1 } },
    })
    const { user } = renderAt(paths.settings)
    const section = await openSessions(user)

    await user.click(await section.findByRole('button', { name: 'Sign out other sessions' }))
    await user.click(section.getByRole('button', { name: 'Sign out other sessions' }))

    expect(await section.findByText('1 other session was signed out.')).toBeInTheDocument()
  })

  it('shows an error with a retry when the list cannot be loaded', async () => {
    mockApi({
      ...signedIn(),
      'GET /account/sessions': apiError(
        500,
        'internal',
        'The server could not complete the request.',
      ),
    })
    const { user } = renderAt(paths.settings)
    const section = await openSessions(user)

    expect(await section.findByRole('alert')).toHaveTextContent('could not complete the request')
    expect(section.getByRole('button', { name: 'Try again' })).toBeInTheDocument()
  })
})
