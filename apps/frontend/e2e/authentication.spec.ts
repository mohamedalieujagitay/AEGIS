import { expect, test, type Page, type TestInfo } from '@playwright/test'
import {
  administratorApi,
  createAccount,
  issueResetLink,
  newUser,
  setRegistration,
  type TestUser,
} from './helpers'

/*
 * Public registration is limited to five attempts per address per hour
 * (DECISIONS.md D-066), and all tests here share one address. Accounts are
 * therefore created once per block, in beforeAll, and the tests use them.
 */

async function signInThroughTheForm(page: Page, email: string, password: string) {
  await page.getByLabel('Email address').fill(email)
  await page.getByLabel('Password', { exact: true }).fill(password)
  await page.getByRole('button', { name: 'Sign in' }).click()
}

/** The signed-in shell shows the user's name; the sign-in page does not. */
async function expectSignedInAs(page: Page, user: TestUser) {
  await expect(page.getByText(user.username, { exact: true })).toBeVisible()
}

test.describe('sign-in', () => {
  let account: TestUser

  test.beforeAll(async ({ baseURL }) => {
    account = newUser()
    await createAccount(baseURL ?? '', account)
  })

  test('a signed-out visitor is sent to sign in, then returned to the page they asked for', async ({
    page,
  }) => {
    await page.goto('/assets')
    await expect(page).toHaveURL(/\/login$/)
    await signInThroughTheForm(page, account.email, account.password)

    await expect(page).toHaveURL(/\/assets$/)
    await expect(page.getByRole('heading', { level: 1, name: 'Assets' })).toBeVisible()
    await expectSignedInAs(page, account)
  })

  test('a failed sign-in gives the generic message, keeps the email and clears the password', async ({
    page,
  }) => {
    await page.goto('/login')
    await signInThroughTheForm(page, account.email, 'a wrong passphrase entirely')
    await expect(page.getByRole('alert')).toHaveText('The email address or password is incorrect.')
    await expect(page.getByLabel('Email address')).toHaveValue(account.email)
    await expect(page.getByLabel('Password', { exact: true })).toHaveValue('')

    // An unknown account gets exactly the same message.
    await signInThroughTheForm(page, `nobody-${account.username}@example.test`, account.password)
    await expect(page.getByRole('alert')).toHaveText('The email address or password is incorrect.')
  })

  test('the session survives a page reload', async ({ page }) => {
    await page.goto('/login')
    await signInThroughTheForm(page, account.email, account.password)
    await expect(page).toHaveURL(/\/$/)

    await page.reload()

    await expect(page).toHaveURL(/\/$/)
    await expectSignedInAs(page, account)
  })

  test('sign-out ends the session on the server, not only in the browser', async ({ page }) => {
    await page.goto('/login')
    await signInThroughTheForm(page, account.email, account.password)
    await expect(page.getByRole('button', { name: 'Sign out' })).toBeVisible()

    await page.getByRole('button', { name: 'Sign out' }).click()

    await expect(page.getByText('You have been signed out.')).toBeVisible()
    // The browser's own cookies are sent: the server now refuses the session they hold.
    const me = await page.request.get('/api/v1/auth/me')
    expect(me.status()).toBe(401)
  })
})

test.describe('protected routes', () => {
  for (const path of ['/', '/findings', '/settings']) {
    test(`${path} redirects a signed-out visitor to sign in`, async ({ page }) => {
      await page.goto(path)
      await expect(page).toHaveURL(/\/login$/)
    })
  }
})

/*
 * Diagnostics for a failed registration test, written to the job log. Only the
 * status of the options request, a boolean, the URL path, whether the form is
 * shown, the application's own alert text and the first line of the failure are
 * printed. Never a password, email address, cookie, token or CSRF value.
 */
let optionsReport = 'not requested'

function recordOptionsRequest(page: Page): void {
  optionsReport = 'not requested'
  page.on('response', (response) => {
    if (!new URL(response.url()).pathname.endsWith('/api/v1/auth/options')) {
      return
    }
    optionsReport = `status ${response.status()}`
    response.json().then(
      (body: unknown) => {
        const enabled =
          typeof body === 'object' && body !== null && 'registration_enabled' in body
            ? String(body.registration_enabled)
            : 'missing'
        optionsReport += `, registration_enabled ${enabled}`
      },
      () => {
        optionsReport += ', body unreadable'
      },
    )
  })
}

async function reportRegistrationFailure(page: Page, testInfo: TestInfo): Promise<void> {
  if (testInfo.status === 'passed') {
    return
  }
  const formShown = (await page.getByRole('button', { name: 'Create account' }).count()) > 0
  const alerts = await page.getByRole('alert').allInnerTexts()
  const failure = testInfo.error?.message ?? ''
  const waiting = failure
    .split('\n')
    .filter((line) => line.includes('waiting for'))
    .slice(0, 3)
  const lines = [
    `[registration diagnostics] ${testInfo.title}`,
    `  test status: ${testInfo.status}`,
    `  failure: ${failure.split('\n')[0] ?? 'none'}`,
    ...waiting.map((line) => `  ${line.trim()}`),
    `  /auth/options: ${optionsReport}`,
    `  current path: ${new URL(page.url()).pathname}`,
    `  registration form shown: ${formShown}`,
    `  visible alerts: ${alerts.length > 0 ? alerts.join(' | ') : 'none'}`,
  ]
  process.stdout.write(`${lines.join('\n')}\n`)
}

test.describe('registration', () => {
  test.beforeEach(({ page }) => {
    recordOptionsRequest(page)
  })

  test.afterEach(async ({ page }, testInfo) => {
    await reportRegistrationFailure(page, testInfo)
  })

  test('registration is closed by default: the page says so and offers no account', async ({
    page,
    baseURL,
  }) => {
    const api = await administratorApi(baseURL ?? '')
    try {
      await setRegistration(api, false)
    } finally {
      await api.dispose()
    }

    await page.goto('/register')
    await expect(page.getByText('Open registration is turned off')).toBeVisible()
    await expect(page.getByLabel('Username')).toHaveCount(0)

    await page.goto('/login')
    await expect(page.getByRole('link', { name: 'Create one' })).toHaveCount(0)
  })

  test('when an administrator enables it, a visitor can register and is signed in', async ({
    page,
    baseURL,
  }) => {
    const user = newUser()
    const api = await administratorApi(baseURL ?? '')
    try {
      await setRegistration(api, true)
      await page.goto('/login')
      await page.getByRole('link', { name: 'Create one' }).click()
      await expect(page).toHaveURL(/\/register$/)

      await page.getByLabel('Email address').fill(user.email)
      await page.getByLabel('Username').fill(user.username)
      await page.getByLabel('Password', { exact: true }).fill(user.password)
      await page.getByLabel('Confirm password').fill(user.password)
      await page.getByRole('button', { name: 'Create account' }).click()

      await expect(page).toHaveURL(/\/$/)
      await expectSignedInAs(page, user)
    } finally {
      await setRegistration(api, false)
      await api.dispose()
    }
  })

  test('mismatched passwords are caught before anything is sent', async ({ page, baseURL }) => {
    const user = newUser()
    const api = await administratorApi(baseURL ?? '')
    try {
      await setRegistration(api, true)
      await page.goto('/register')
      await page.getByLabel('Email address').fill(user.email)
      await page.getByLabel('Username').fill(user.username)
      await page.getByLabel('Password', { exact: true }).fill(user.password)
      await page.getByLabel('Confirm password').fill(`${user.password} extra`)
      await page.getByRole('button', { name: 'Create account' }).click()
      await expect(page.getByLabel('Confirm password')).toHaveAccessibleDescription(
        'The passwords do not match.',
      )
      await expect(page).toHaveURL(/\/register$/)
    } finally {
      await setRegistration(api, false)
      await api.dispose()
    }
  })
})

test.describe('password reset and sessions', () => {
  // The three tests below share one account and change its password in turn.
  let account: TestUser
  let password: string

  test.beforeAll(async ({ baseURL }) => {
    account = newUser()
    password = account.password
    await createAccount(baseURL ?? '', account)
  })

  async function resetWithLink(page: Page, path: string, newPassword: string) {
    await page.goto(path)
    await expect(page.getByRole('heading', { level: 1, name: 'Reset your password' })).toBeVisible()
    await page.getByLabel('New password', { exact: true }).fill(newPassword)
    await page.getByLabel('Confirm new password').fill(newPassword)
    await page.getByRole('button', { name: 'Set new password' }).click()
    await expect(page.getByText(/all your sessions have been signed out/)).toBeVisible()
  }

  test('an administrator link lets the user choose a new password; the old one stops working', async ({
    page,
    browser,
    baseURL,
  }) => {
    const path = await issueResetLink(baseURL ?? '', account.email)
    await page.goto(path)
    // The token has been removed from the address bar (the router does this just after the form appears).
    await expect(page).toHaveURL(/\/reset-password$/)
    const renewed = `${password} renewed`
    await page.getByLabel('New password', { exact: true }).fill(renewed)
    await page.getByLabel('Confirm new password').fill(renewed)
    await page.getByRole('button', { name: 'Set new password' }).click()
    await expect(page.getByText(/all your sessions have been signed out/)).toBeVisible()

    const fresh = await browser.newContext({ baseURL })
    try {
      const other = await fresh.newPage()
      await other.goto('/login')
      await signInThroughTheForm(other, account.email, password)
      await expect(other.getByRole('alert')).toHaveText(
        'The email address or password is incorrect.',
      )
      await signInThroughTheForm(other, account.email, renewed)
      await expectSignedInAs(other, account)
    } finally {
      await fresh.close()
    }
    password = renewed
  })

  test('a reset link cannot be used twice', async ({ page, baseURL }) => {
    const path = await issueResetLink(baseURL ?? '', account.email)
    const first = `${password} first`
    await resetWithLink(page, path, first)
    password = first

    // Leave the page first: a link to the same page would only change its fragment.
    await page.goto('/login')
    await page.goto(path)
    await page.getByLabel('New password', { exact: true }).fill(`${password} second`)
    await page.getByLabel('Confirm new password').fill(`${password} second`)
    await page.getByRole('button', { name: 'Set new password' }).click()
    await expect(page.getByRole('alert')).toContainText('invalid or has expired')
  })

  test('a password reset signs out a session that is still open in a browser', async ({
    page,
    browser,
    baseURL,
  }) => {
    await page.goto('/login')
    await signInThroughTheForm(page, account.email, password)
    await expect(page.getByRole('button', { name: 'Sign out' })).toBeVisible()

    const resetter = await browser.newContext({ baseURL })
    try {
      const path = await issueResetLink(baseURL ?? '', account.email)
      await resetWithLink(await resetter.newPage(), path, `${password} changed`)
      password = `${password} changed`
    } finally {
      await resetter.close()
    }

    await page.reload()
    await expect(page).toHaveURL(/\/login$/)
    expect((await page.request.get('/api/v1/auth/me')).status()).toBe(401)
  })
})
