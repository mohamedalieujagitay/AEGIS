import { expect, test, type Browser, type BrowserContext, type Page } from '@playwright/test'
import { createAccount, newUser, type TestUser } from './helpers'

/*
 * Account management (roadmap task 2.2) against the running application. Each
 * test creates its own account, so the per-account change limit (five attempts
 * per 15 minutes) is never shared between tests.
 */

const NEW_PASSWORD = 'a completely different passphrase'

/** A new browser context, signed in through the sign-in form. */
async function signedInContext(browser: Browser, baseURL: string | undefined, user: TestUser) {
  const context = await browser.newContext({ baseURL })
  const page = await context.newPage()
  await page.goto('/login')
  await page.getByLabel('Email address').fill(user.email)
  await page.getByLabel('Password', { exact: true }).fill(user.password)
  await page.getByRole('button', { name: 'Sign in' }).click()
  await expect(page).toHaveURL(/\/$/)
  return { context, page }
}

/** Whether a context's session is still accepted by the server. */
async function isSignedIn(context: BrowserContext): Promise<boolean> {
  const response = await context.request.get('/api/v1/auth/me')
  return response.status() === 200
}

async function openSettingsTab(page: Page, name: 'Account' | 'Security') {
  await page.goto('/settings')
  await page.getByRole('tab', { name }).click()
}

async function changePassword(page: Page, current: string, next: string) {
  await openSettingsTab(page, 'Security')
  const section = page.getByRole('region', { name: 'Password' })
  await section.getByLabel('Current password').fill(current)
  await section.getByLabel('New password', { exact: true }).fill(next)
  await section.getByLabel('Confirm new password').fill(next)
  await section.getByRole('button', { name: 'Change password' }).click()
  await expect(section.getByRole('status')).toContainText('Your password was changed')
}

test.describe('profile', () => {
  test('a username change takes effect and survives a reload', async ({ page, baseURL }) => {
    const user = newUser()
    await createAccount(baseURL ?? '', user)
    await page.goto('/login')
    await page.getByLabel('Email address').fill(user.email)
    await page.getByLabel('Password', { exact: true }).fill(user.password)
    await page.getByRole('button', { name: 'Sign in' }).click()
    await expect(page).toHaveURL(/\/$/)

    await openSettingsTab(page, 'Account')
    const section = page.getByRole('region', { name: 'Account' })
    const renamed = `${user.username}x`
    await section.getByLabel('Username').fill(renamed)
    await section.getByLabel('Current password').fill(user.password)
    await section.getByRole('button', { name: 'Save username' }).click()

    await expect(section.getByRole('status')).toContainText('Your username was changed.')
    await page.reload()
    await expect(page.getByText(renamed, { exact: true })).toBeVisible()
  })
})

test.describe('password', () => {
  test('after a change: the old password fails, the new one works, the current browser stays signed in', async ({
    browser,
    baseURL,
  }) => {
    const user = newUser()
    await createAccount(baseURL ?? '', user)
    const first = await signedInContext(browser, baseURL, user)
    const other = await signedInContext(browser, baseURL, user)
    try {
      await changePassword(first.page, user.password, NEW_PASSWORD)

      // This browser keeps its session after the rotation, across a reload.
      await first.page.reload()
      await expect(first.page).toHaveURL(/\/settings$/)
      expect(await isSignedIn(first.context)).toBe(true)

      // The old password is refused; the new one signs in.
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

        await page.getByLabel('Password', { exact: true }).fill(NEW_PASSWORD)
        await page.getByRole('button', { name: 'Sign in' }).click()
        await expect(page).toHaveURL(/\/$/)
      } finally {
        await fresh.close()
      }

      // The other browser was signed out by the change.
      expect(await isSignedIn(other.context)).toBe(false)
    } finally {
      await first.context.close()
      await other.context.close()
    }
  })

  test('a change revokes trusted devices', async ({ browser, baseURL }) => {
    const user = newUser()
    await createAccount(baseURL ?? '', user)
    const { context, page } = await signedInContext(browser, baseURL, user)
    try {
      const before = await (await context.request.get('/api/v1/auth/devices')).json()
      expect(before.length).toBeGreaterThan(0)

      await changePassword(page, user.password, NEW_PASSWORD)

      const after = await (await context.request.get('/api/v1/auth/devices')).json()
      expect(after).toEqual([])
    } finally {
      await context.close()
    }
  })
})

test.describe('sessions', () => {
  test('one session can be signed out from another, and only that one', async ({
    browser,
    baseURL,
  }) => {
    const user = newUser()
    await createAccount(baseURL ?? '', user)
    const first = await signedInContext(browser, baseURL, user)
    const second = await signedInContext(browser, baseURL, user)
    try {
      await openSettingsTab(first.page, 'Security')
      const sessions = first.page.getByRole('region', { name: 'Active sessions' })
      await expect(sessions.getByRole('listitem')).toHaveCount(2)
      await sessions
        .getByRole('listitem')
        .filter({ hasNotText: 'This browser' })
        .getByRole('button', { name: 'Sign out' })
        .click()
      await sessions.getByRole('button', { name: 'Confirm' }).click()

      await expect(sessions.getByRole('status')).toContainText('That session was signed out.')
      expect(await isSignedIn(second.context)).toBe(false)
      expect(await isSignedIn(first.context)).toBe(true)
    } finally {
      await first.context.close()
      await second.context.close()
    }
  })

  test('signing out other sessions keeps this one and ends the rest', async ({
    browser,
    baseURL,
  }) => {
    const user = newUser()
    await createAccount(baseURL ?? '', user)
    const current = await signedInContext(browser, baseURL, user)
    const second = await signedInContext(browser, baseURL, user)
    const third = await signedInContext(browser, baseURL, user)
    try {
      await openSettingsTab(current.page, 'Security')
      const sessions = current.page.getByRole('region', { name: 'Active sessions' })
      await sessions.getByRole('button', { name: 'Sign out other sessions' }).click()
      await sessions.getByRole('button', { name: 'Sign out other sessions' }).click()

      await expect(sessions.getByRole('status')).toContainText('2 other sessions were signed out.')
      expect(await isSignedIn(second.context)).toBe(false)
      expect(await isSignedIn(third.context)).toBe(false)
      expect(await isSignedIn(current.context)).toBe(true)
    } finally {
      await current.context.close()
      await second.context.close()
      await third.context.close()
    }
  })
})
