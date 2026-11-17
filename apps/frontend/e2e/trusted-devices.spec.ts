import {
  expect,
  test,
  type APIRequestContext,
  type Browser,
  type Locator,
  type Page,
} from '@playwright/test'
import {
  DEVICE_COOKIE,
  createAccount,
  cookieValue,
  contextWithOnlyCookie,
  issueResetLink,
  newUser,
  stringField,
  type TestUser,
} from './helpers'
import { deactivateAccount, disposableStack, runSql, type Stack } from './stack'

/*
 * Trusted devices (DECISIONS.md D-070). A device exempts its browser from the
 * account-wide sign-in delay only. Each browser context here is a separate
 * browser with its own device cookie.
 *
 * Scenarios that need a database or service step run only on a disposable
 * stack (AEGIS_E2E_COMPOSE_PROJECT). The others run against any deployment
 * the tests may change.
 */

interface DeviceRow {
  id: string
  current: boolean
}

async function listDevices(request: APIRequestContext): Promise<DeviceRow[]> {
  const response = await request.get('/api/v1/auth/devices')
  expect(response.status(), 'list trusted devices').toBe(200)
  const body: unknown = await response.json()
  if (!Array.isArray(body)) {
    throw new Error('the device list is not an array')
  }
  return body.map((item: unknown) => {
    if (typeof item !== 'object' || item === null || !('current' in item)) {
      throw new Error('a device entry has no current flag')
    }
    return { id: stringField(item, 'id'), current: item.current === true }
  })
}

async function csrfFor(request: APIRequestContext): Promise<string> {
  const response = await request.get('/api/v1/auth/csrf')
  return stringField(await response.json(), 'csrf_token')
}

/** Sign in through the form in a new browser context. */
async function signInInContext(browser: Browser, baseURL: string | undefined, user: TestUser) {
  const context = await browser.newContext({ baseURL })
  const page = await context.newPage()
  await page.goto('/login')
  await page.getByLabel('Email address').fill(user.email)
  await page.getByLabel('Password', { exact: true }).fill(user.password)
  await page.getByRole('button', { name: 'Sign in' }).click()
  await expect(page).toHaveURL(/\/$/)
  return { context, page }
}

/** Open Settings → Security and return the Trusted devices section. */
async function openTrustedDevices(page: Page): Promise<Locator> {
  await page.goto('/settings')
  await page.getByRole('tab', { name: 'Security' }).click()
  const section = page.getByRole('region', { name: 'Trusted devices' })
  await expect(section).toBeVisible()
  return section
}

/** A stack for a test that changes data beyond the web interface, or skip the test. */
function requireStackOrSkip(): Stack | undefined {
  const stack = disposableStack()
  test.skip(!stack, 'needs a disposable stack (AEGIS_E2E_COMPOSE_PROJECT)')
  return stack
}

test.describe('trusted devices in Settings', () => {
  let account: TestUser

  test.beforeAll(async ({ baseURL }) => {
    account = newUser()
    await createAccount(baseURL ?? '', account)
  })

  test('the signed-in browser appears as trusted, without its token', async ({
    browser,
    baseURL,
  }) => {
    const { context, page } = await signInInContext(browser, baseURL, account)
    try {
      const section = await openTrustedDevices(page)
      await expect(section.getByText('This browser')).toBeVisible()
      await expect(
        section.getByRole('button', { name: 'Revoke', exact: true }).first(),
      ).toBeVisible()
      await expect(section.getByText(/Signing out does not remove a trusted browser/)).toBeVisible()
      const token = await cookieValue(context, DEVICE_COOKIE)
      expect(token).toBeTruthy()
      expect(await page.locator('body').innerText()).not.toContain(token ?? '')
    } finally {
      await context.close()
    }
  })

  test('another browser can be revoked; it disappears and the current browser stays listed', async ({
    browser,
    baseURL,
  }) => {
    const current = await signInInContext(browser, baseURL, account)
    const other = await signInInContext(browser, baseURL, account)
    try {
      const section = await openTrustedDevices(current.page)
      const before = await listDevices(current.page.request)
      const otherRow = before.find((device) => !device.current)
      expect(otherRow, 'a second trusted browser exists').toBeDefined()

      const item = section
        .getByRole('listitem')
        .filter({ hasNot: section.getByText('This browser', { exact: true }) })
        .first()
      await item.getByRole('button', { name: 'Revoke', exact: true }).click()
      await expect(item.getByText(/Revoke this browser\?/)).toBeVisible()
      await section.getByRole('button', { name: 'Revoke browser' }).click()

      await expect
        .poll(async () => (await listDevices(current.page.request)).map((device) => device.id))
        .not.toContain(otherRow?.id)
      await expect(section.getByText('This browser')).toBeVisible()
    } finally {
      await current.context.close()
      await other.context.close()
    }
  })

  test('ordinary sign-out keeps the browser trusted; signing in again reuses the same device', async ({
    page,
  }) => {
    await page.goto('/login')
    await page.getByLabel('Email address').fill(account.email)
    await page.getByLabel('Password', { exact: true }).fill(account.password)
    await page.getByRole('button', { name: 'Sign in' }).click()
    await expect(page).toHaveURL(/\/$/)
    const current = (await listDevices(page.request)).find((device) => device.current)
    expect(current).toBeDefined()
    const cookieBefore = await cookieValue(page.context(), DEVICE_COOKIE)

    await page.getByRole('button', { name: 'Sign out' }).click()
    await expect(page.getByText('You have been signed out.')).toBeVisible()
    await page.getByLabel('Email address').fill(account.email)
    await page.getByLabel('Password', { exact: true }).fill(account.password)
    await page.getByRole('button', { name: 'Sign in' }).click()
    await expect(page).toHaveURL(/\/$/)

    expect((await listDevices(page.request)).map((device) => device.id)).toContain(current?.id)
    expect(await cookieValue(page.context(), DEVICE_COOKIE)).toBe(cookieBefore)
  })
})

test.describe('trusted devices and account changes', () => {
  test('a password reset revokes every trusted browser of the account', async ({
    browser,
    baseURL,
  }) => {
    const user = newUser()
    await createAccount(baseURL ?? '', user)
    const signedIn = await signInInContext(browser, baseURL, user)
    const oldDevice = (await listDevices(signedIn.page.request)).find((device) => device.current)
    await signedIn.context.close()
    expect(oldDevice).toBeDefined()

    const path = await issueResetLink(baseURL ?? '', user.email)
    const resetter = await browser.newContext({ baseURL })
    const renewed = `${user.password} renewed`
    try {
      const resetPage = await resetter.newPage()
      await resetPage.goto(path)
      await resetPage.getByLabel('New password', { exact: true }).fill(renewed)
      await resetPage.getByLabel('Confirm new password').fill(renewed)
      await resetPage.getByRole('button', { name: 'Set new password' }).click()
      await expect(resetPage.getByText(/all your sessions have been signed out/)).toBeVisible()
    } finally {
      await resetter.close()
    }

    const again = await signInInContext(browser, baseURL, { ...user, password: renewed })
    try {
      const devices = await listDevices(again.page.request)
      expect(devices.map((device) => device.id)).not.toContain(oldDevice?.id)
    } finally {
      await again.context.close()
    }
  })

  test('an expired trusted browser is no longer trusted', async ({ browser, baseURL }) => {
    const stack = requireStackOrSkip()
    if (!stack) {
      return
    }
    const user = newUser()
    await createAccount(baseURL ?? '', user)
    const signedIn = await signInInContext(browser, baseURL, user)
    try {
      await runSql(
        stack,
        "UPDATE trusted_devices SET created_at = now() - interval '31 days', expires_at = now() - interval '1 day' WHERE user_id = (SELECT id FROM users WHERE email = :'email')",
        { email: user.email },
      )
      const section = await openTrustedDevices(signedIn.page)
      await expect(section.getByText('No trusted browsers')).toBeVisible()
      expect(await listDevices(signedIn.page.request)).toEqual([])
    } finally {
      await signedIn.context.close()
    }
  })

  test('deactivating an account ends its sessions and revokes its trusted browsers', async ({
    browser,
    baseURL,
  }) => {
    const stack = requireStackOrSkip()
    if (!stack) {
      return
    }
    const user = newUser()
    await createAccount(baseURL ?? '', user)
    const signedIn = await signInInContext(browser, baseURL, user)
    try {
      await deactivateAccount(stack, user.email)
      await signedIn.page.reload()
      await expect(signedIn.page).toHaveURL(/\/login$/)
      const live = await runSql(
        stack,
        "SELECT count(*) FROM trusted_devices WHERE revoked_at IS NULL AND user_id = (SELECT id FROM users WHERE email = :'email')",
        { email: user.email },
      )
      expect(live.trim()).toBe('0')
    } finally {
      await signedIn.context.close()
    }

    const fresh = await browser.newContext({ baseURL })
    try {
      const page = await fresh.newPage()
      await page.goto('/login')
      await page.getByLabel('Email address').fill(user.email)
      await page.getByLabel('Password', { exact: true }).fill(user.password)
      await page.getByRole('button', { name: 'Sign in' }).click()
      await expect(page.getByRole('alert')).toHaveText(
        'The email address or password is incorrect.',
      )
    } finally {
      await fresh.close()
    }
  })
})

test.describe('trusted-device security', () => {
  test('device management needs a session', async ({ browser, baseURL }) => {
    const context = await browser.newContext({ baseURL })
    try {
      expect((await context.request.get('/api/v1/auth/devices')).status()).toBe(401)
      const token = await csrfFor(context.request)
      const revoked = await context.request.delete(
        '/api/v1/auth/devices/00000000-0000-4000-8000-000000000001',
        {
          headers: { 'X-CSRF-Token': token },
        },
      )
      expect(revoked.status()).toBe(401)
    } finally {
      await context.close()
    }
  })

  test('revoking a trusted browser is refused without a valid CSRF token', async ({
    browser,
    baseURL,
  }) => {
    const user = newUser()
    await createAccount(baseURL ?? '', user)
    const signedIn = await signInInContext(browser, baseURL, user)
    try {
      const [own] = await listDevices(signedIn.page.request)
      expect(own).toBeDefined()
      const path = `/api/v1/auth/devices/${own?.id ?? ''}`
      const missing = await signedIn.page.request.delete(path)
      expect(missing.status()).toBe(403)
      expect((await missing.json()).error.code).toBe('csrf_failed')
      const wrong = await signedIn.page.request.delete(path, {
        headers: { 'X-CSRF-Token': 'v1.1.not.valid' },
      })
      expect(wrong.status()).toBe(403)
      expect((await listDevices(signedIn.page.request)).map((device) => device.id)).toContain(
        own?.id,
      )
    } finally {
      await signedIn.context.close()
    }
  })

  test("a user cannot see or revoke another user's trusted browser", async ({
    browser,
    baseURL,
  }) => {
    const owner = newUser()
    const other = newUser()
    await createAccount(baseURL ?? '', owner)
    await createAccount(baseURL ?? '', other)
    const ownerSession = await signInInContext(browser, baseURL, owner)
    const otherSession = await signInInContext(browser, baseURL, other)
    try {
      const ownerDevice = (await listDevices(ownerSession.page.request))[0]
      expect(ownerDevice).toBeDefined()
      expect(
        (await listDevices(otherSession.page.request)).map((device) => device.id),
      ).not.toContain(ownerDevice?.id)

      const attempt = await otherSession.page.request.delete(
        `/api/v1/auth/devices/${ownerDevice?.id ?? ''}`,
        {
          headers: { 'X-CSRF-Token': await csrfFor(otherSession.page.request) },
        },
      )
      expect(attempt.status()).toBe(404)
      expect((await attempt.json()).error.code).toBe('device_not_found')
      expect((await listDevices(ownerSession.page.request)).map((device) => device.id)).toContain(
        ownerDevice?.id,
      )
    } finally {
      await ownerSession.context.close()
      await otherSession.context.close()
    }
  })

  test('a trusted-device cookie alone does not authenticate a user', async ({
    browser,
    baseURL,
  }) => {
    const user = newUser()
    await createAccount(baseURL ?? '', user)
    const signedIn = await signInInContext(browser, baseURL, user)
    const device = await cookieValue(signedIn.context, DEVICE_COOKIE)
    expect(device).toBeTruthy()
    const replay = await contextWithOnlyCookie(browser, baseURL, signedIn.context, DEVICE_COOKIE)
    await signedIn.context.close()
    try {
      expect((await replay.request.get('/api/v1/auth/me')).status()).toBe(401)
      expect((await replay.request.get('/api/v1/auth/devices')).status()).toBe(401)
      const page = await replay.newPage()
      await page.goto('/')
      await expect(page).toHaveURL(/\/login$/)
    } finally {
      await replay.close()
    }
  })

  test('the trusted-browser exemption keeps the per-address and account-and-address limits', async ({
    browser,
    baseURL,
  }) => {
    const user = newUser()
    await createAccount(baseURL ?? '', user)
    const signedIn = await signInInContext(browser, baseURL, user)
    const trusted = await contextWithOnlyCookie(browser, baseURL, signedIn.context, DEVICE_COOKIE)
    await signedIn.context.close()
    try {
      const token = await csrfFor(trusted.request)
      const statuses: number[] = []
      for (let attempt = 0; attempt < 6; attempt += 1) {
        // Sequential on purpose: each attempt must be counted before the next one.
        // eslint-disable-next-line no-await-in-loop
        const response = await trusted.request.post('/api/v1/auth/login', {
          data: { email: user.email, password: 'a wrong passphrase entirely' },
          headers: { 'X-CSRF-Token': token },
        })
        statuses.push(response.status())
      }
      expect(statuses).toEqual([401, 401, 401, 401, 401, 401])
      const blocked = await trusted.request.post('/api/v1/auth/login', {
        data: { email: user.email, password: user.password },
        headers: { 'X-CSRF-Token': token },
      })
      expect(blocked.status()).toBe(429)
      expect(blocked.headers()['retry-after']).toBeTruthy()
    } finally {
      await trusted.close()
    }
  })
})
