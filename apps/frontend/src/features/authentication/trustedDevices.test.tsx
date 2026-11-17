import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { apiError, mockApi } from '../../test/apiMock'
import { describeBrowser } from './devices'
import { TrustedDevices } from './components/TrustedDevices'

const chromeWindows =
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/158.0.0.0 Safari/537.36'

const device = {
  id: '11111111-1111-4111-8111-111111111111',
  created_at: '2026-11-10T09:00:00Z',
  expires_at: '2026-12-10T09:00:00Z',
  last_used_at: '2026-11-16T08:30:00Z',
  user_agent: chromeWindows,
  current: true,
}

const otherDevice = {
  id: '22222222-2222-4222-8222-222222222222',
  created_at: '2026-11-01T09:00:00Z',
  expires_at: '2026-12-01T09:00:00Z',
  last_used_at: null,
  user_agent:
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15 Version/17.0 Safari/605.1.15',
  current: false,
}

describe('trusted browsers', () => {
  it('lists each browser with its dates, names it, and shows no token or identifier', async () => {
    mockApi({ 'GET /auth/devices': { body: [device, otherDevice] } })
    render(<TrustedDevices />)

    const list = await screen.findByRole('list')
    const items = within(list).getAllByRole('listitem')
    expect(items).toHaveLength(2)
    const [first, second] = items
    if (!first || !second) {
      throw new Error('two list items expected')
    }
    expect(within(first).getByText('Chrome on Windows')).toBeInTheDocument()
    expect(within(first).getByText('This browser')).toBeInTheDocument()
    expect(within(second).getByText('Safari on macOS')).toBeInTheDocument()
    expect(within(second).queryByText('This browser')).not.toBeInTheDocument()
    expect(within(second).getByText('Never')).toBeInTheDocument()
    expect(within(first).getByText('Added')).toBeInTheDocument()
    expect(within(first).getByText('Expires')).toBeInTheDocument()
    expect(document.body.textContent).not.toContain(device.id)
    expect(document.body.textContent).not.toContain('Mozilla/5.0')
  })

  it('explains what trust does and does not do', async () => {
    mockApi({ 'GET /auth/devices': { body: [] } })
    render(<TrustedDevices />)

    expect(await screen.findByText(/skips only the account-wide delay/)).toBeInTheDocument()
    expect(screen.getByText(/does not sign anyone in/)).toBeInTheDocument()
    expect(screen.getByText(/Signing out does not remove a trusted browser/)).toBeInTheDocument()
    expect(
      screen.getByText(
        /A password reset or change, and the deactivation of the account, revoke all of them/,
      ),
    ).toBeInTheDocument()
  })

  it('shows an empty state when no browser is trusted', async () => {
    mockApi({ 'GET /auth/devices': { body: [] } })
    render(<TrustedDevices />)

    expect(await screen.findByText('No trusted browsers')).toBeInTheDocument()
    expect(screen.queryByRole('list')).not.toBeInTheDocument()
  })

  it('shows loading, then an error with a way to try again', async () => {
    let attempts = 0
    mockApi({
      'GET /auth/devices': () => {
        attempts += 1
        return attempts === 1
          ? apiError(
              503,
              'service_unavailable',
              'This action is temporarily unavailable. Try again later.',
            )
          : { body: [device] }
      },
    })
    const user = userEvent.setup()
    render(<TrustedDevices />)

    expect(await screen.findByRole('alert')).toHaveTextContent('temporarily unavailable')
    await user.click(screen.getByRole('button', { name: 'Try again' }))
    expect(await screen.findByText('Chrome on Windows')).toBeInTheDocument()
  })

  it('asks for confirmation, and cancelling keeps the browser', async () => {
    const { requests } = mockApi({ 'GET /auth/devices': { body: [otherDevice] } })
    const user = userEvent.setup()
    render(<TrustedDevices />)

    await user.click(await screen.findByRole('button', { name: 'Revoke' }))
    expect(screen.getByText(/Revoke this browser\?/)).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Cancel' }))

    expect(screen.queryByText(/Revoke this browser\?/)).not.toBeInTheDocument()
    expect(requests.some((request) => request.method === 'DELETE')).toBe(false)
    expect(screen.getByText('Safari on macOS')).toBeInTheDocument()
  })

  it('revokes the chosen browser and refreshes the list from the server', async () => {
    let listed = [device, otherDevice]
    const { requests } = mockApi({
      'GET /auth/devices': () => ({ body: listed }),
      [`DELETE /auth/devices/${otherDevice.id}`]: () => {
        listed = [device]
        return { status: 204 }
      },
    })
    const user = userEvent.setup()
    render(<TrustedDevices />)

    const target = (await screen.findByText('Safari on macOS')).closest('li')
    if (!target) {
      throw new Error('the browser is not in the list')
    }
    await user.click(within(target).getByRole('button', { name: 'Revoke' }))
    await user.click(screen.getByRole('button', { name: 'Revoke browser' }))

    await waitForAbsence(() => screen.queryByText('Safari on macOS'))
    expect(screen.getByText('Chrome on Windows')).toBeInTheDocument()
    const deletes = requests.filter((request) => request.method === 'DELETE')
    expect(deletes.map((request) => request.path)).toEqual([`/auth/devices/${otherDevice.id}`])
    expect(deletes[0]?.headers['X-CSRF-Token']).toBeTruthy()
  })

  it('reports a failed revocation and keeps the browser listed', async () => {
    mockApi({
      'GET /auth/devices': { body: [otherDevice] },
      [`DELETE /auth/devices/${otherDevice.id}`]: apiError(
        500,
        'http_error',
        'The server could not complete the request. Try again later.',
      ),
    })
    const user = userEvent.setup()
    render(<TrustedDevices />)

    await user.click(await screen.findByRole('button', { name: 'Revoke' }))
    await user.click(screen.getByRole('button', { name: 'Revoke browser' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('could not complete the request')
    expect(screen.getByText('Safari on macOS')).toBeInTheDocument()
  })

  it('treats a browser that is already gone as revoked and refreshes', async () => {
    let listed = [otherDevice]
    mockApi({
      'GET /auth/devices': () => ({ body: listed }),
      [`DELETE /auth/devices/${otherDevice.id}`]: () => {
        listed = []
        return apiError(404, 'device_not_found', 'No trusted device with this identifier.')
      },
    })
    const user = userEvent.setup()
    render(<TrustedDevices />)

    await user.click(await screen.findByRole('button', { name: 'Revoke' }))
    await user.click(screen.getByRole('button', { name: 'Revoke browser' }))

    expect(await screen.findByText('No trusted browsers')).toBeInTheDocument()
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })
})

describe('browser descriptions', () => {
  it.each([
    [chromeWindows, 'Chrome on Windows'],
    [
      'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) Version/17.0 Safari/605.1.15',
      'Safari on macOS',
    ],
    ['Mozilla/5.0 (X11; Linux x86_64; rv:130.0) Gecko/20100101 Firefox/130.0', 'Firefox on Linux'],
    [
      'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) Version/17.0 Mobile/15E148 Safari/604.1',
      'Safari on iOS',
    ],
    [
      'Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 Chrome/130.0 Mobile Safari/537.36',
      'Chrome on Android',
    ],
    ['curl/8.0', 'Browser'],
    [null, 'Unknown browser'],
  ])('describes %s as %s', (userAgent, expected) => {
    expect(describeBrowser(userAgent)).toBe(expected)
  })
})

/** Wait until an element is gone (the list refreshes asynchronously). */
async function waitForAbsence(query: () => unknown) {
  await waitFor(() => expect(query()).toBeNull())
}
