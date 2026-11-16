import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach, beforeEach, vi } from 'vitest'

beforeEach(() => {
  // jsdom does not implement scrolling. React Router's <ScrollRestoration>
  // calls window.scrollTo after navigation, so it is replaced with a no-op
  // here (test environment only). Restored after each test (unstubGlobals).
  vi.stubGlobal('scrollTo', () => undefined)
})

afterEach(() => {
  cleanup()
})
