import { randomBytes } from 'node:crypto'
import {
  request as playwrightRequest,
  type APIRequestContext,
  type Browser,
  type BrowserContext,
  expect,
} from '@playwright/test'
import { createAccountWithCli, disposableStack } from './stack'

export const DEVICE_COOKIE = '__Host-aegis_device'
export const SESSION_COOKIE = '__Host-aegis_session'

/** The instance administrator the tests use to manage accounts (from the environment). */
export function administrator(): { email: string; password: string } {
  const email = process.env['AEGIS_E2E_ADMIN_EMAIL']
  const password = process.env['AEGIS_E2E_ADMIN_PASSWORD']
  if (!email || !password) {
    throw new Error('Set AEGIS_E2E_ADMIN_EMAIL and AEGIS_E2E_ADMIN_PASSWORD to run these tests.')
  }
  return { email, password }
}

export interface TestUser {
  email: string
  username: string
  password: string
}

/** A new account with unique names and a passphrase that passes the password policy. */
export function newUser(): TestUser {
  const id = randomBytes(4).toString('hex')
  return {
    email: `e2e-${id}@example.test`,
    username: `e2e${id}`,
    password: `blue harbour kettle ${id}`,
  }
}

/** A request context signed in as the administrator (separate from any browser). */
export async function administratorApi(baseURL: string): Promise<APIRequestContext> {
  const context = await playwrightRequest.newContext({ baseURL })
  const admin = administrator()
  const csrf = await csrfToken(context)
  const login = await context.post('/api/v1/auth/login', {
    data: { email: admin.email, password: admin.password },
    headers: { 'X-CSRF-Token': csrf },
  })
  expect(login.status(), 'administrator sign-in').toBe(200)
  return context
}

/** A string field of a JSON response body. Throws if the field is missing. */
export function stringField(body: unknown, field: string): string {
  if (typeof body === 'object' && body !== null && field in body) {
    const value: unknown = Reflect.get(body, field)
    if (typeof value === 'string') {
      return value
    }
  }
  throw new Error(`the response has no string field "${field}"`)
}

async function csrfToken(context: APIRequestContext): Promise<string> {
  const response = await context.get('/api/v1/auth/csrf')
  expect(response.status()).toBe(200)
  return stringField(await response.json(), 'csrf_token')
}

/** Send a state-changing request with a fresh CSRF token for this context. */
export async function unsafe(
  context: APIRequestContext,
  method: 'post' | 'put',
  path: string,
  data: object,
) {
  const headers = { 'X-CSRF-Token': await csrfToken(context) }
  return method === 'post'
    ? context.post(path, { data, headers })
    : context.put(path, { data, headers })
}

export async function setRegistration(api: APIRequestContext, enabled: boolean): Promise<void> {
  const response = await unsafe(api, 'put', '/api/v1/admin/settings/registration', { enabled })
  expect(response.status()).toBe(200)
}

/**
 * Create an account. On a disposable stack the administration CLI creates it
 * (public registration allows five attempts per address per hour, which the
 * trusted-device tests exceed); otherwise it is created through registration,
 * which switches open registration on briefly.
 */
export async function createAccount(baseURL: string, user: TestUser): Promise<void> {
  const stack = disposableStack()
  if (stack) {
    await createAccountWithCli(stack, user)
    return
  }
  const api = await administratorApi(baseURL)
  try {
    await setRegistration(api, true)
    const anonymous = await playwrightRequest.newContext({ baseURL })
    try {
      const response = await unsafe(anonymous, 'post', '/api/v1/auth/register', user)
      expect(response.status(), 'registration').toBe(201)
    } finally {
      await anonymous.dispose()
    }
  } finally {
    // Registration goes back to closed even if the registration request failed.
    await setRegistration(api, false)
    await api.dispose()
  }
}

/** The value of a cookie in a browser context, or undefined. Values are never printed. */
export async function cookieValue(
  context: BrowserContext,
  name: string,
): Promise<string | undefined> {
  const cookies = await context.cookies()
  return cookies.find((cookie) => cookie.name === name)?.value
}

/**
 * A new browser context that holds only the named cookie of ``source`` (for
 * example the device cookie without the session), with its attributes intact.
 */
export async function contextWithOnlyCookie(
  browser: Browser,
  baseURL: string | undefined,
  source: BrowserContext,
  name: string,
): Promise<BrowserContext> {
  const state = await source.storageState()
  return browser.newContext({
    baseURL,
    storageState: { cookies: state.cookies.filter((cookie) => cookie.name === name), origins: [] },
  })
}

/** Issue a reset link for ``email`` as the administrator; returns its path with the token fragment. */
export async function issueResetLink(baseURL: string, email: string): Promise<string> {
  const api = await administratorApi(baseURL)
  try {
    const response = await unsafe(api, 'post', '/api/v1/admin/password-resets', { email })
    expect(response.status(), 'reset link').toBe(201)
    return stringField(await response.json(), 'reset_path')
  } finally {
    await api.dispose()
  }
}
