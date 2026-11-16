import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { createMemoryRouter, RouterProvider, type RouteObject } from 'react-router'
import { describe, expect, it, vi } from 'vitest'
import { AppLayout } from '../layout/AppLayout'
import { RouteErrorPage } from '../pages/RouteErrorPage'
import { paths } from './paths'
import { routes } from './routes'

function renderAt(path: string, routeList: RouteObject[] = routes) {
  const user = userEvent.setup()
  const router = createMemoryRouter(routeList, { initialEntries: [path] })
  render(<RouterProvider router={router} />)
  return { user, router }
}

/** The primary navigation in the desktop sidebar (always rendered). */
function primaryNav() {
  const sidebar = screen.getByRole('complementary', { name: 'Sidebar' })
  return within(sidebar).getByRole('navigation', { name: 'Primary' })
}

describe('application routes', () => {
  it('renders the overview page inside the application shell', async () => {
    renderAt(paths.overview)

    expect(await screen.findByRole('heading', { level: 1, name: 'Overview' })).toBeInTheDocument()
    expect(screen.getByRole('main')).toContainElement(screen.getByRole('heading', { level: 1 }))
    expect(within(primaryNav()).getByRole('link', { name: 'Overview' })).toHaveAttribute(
      'aria-current',
      'page',
    )
  })

  it('shows the not-found page for unknown paths, with navigation still available', async () => {
    const { user, router } = renderAt('/does-not-exist')

    expect(
      await screen.findByRole('heading', { level: 1, name: 'Page not found' }),
    ).toBeInTheDocument()
    expect(primaryNav()).toBeInTheDocument()

    await user.click(screen.getByRole('link', { name: 'Return to overview' }))

    expect(await screen.findByRole('heading', { level: 1, name: 'Overview' })).toBeInTheDocument()
    expect(router.state.location.pathname).toBe(paths.overview)
  })

  it('navigates with the primary navigation and moves focus to the main content', async () => {
    const { user } = renderAt(paths.overview)
    await screen.findByRole('heading', { level: 1, name: 'Overview' })

    await user.click(within(primaryNav()).getByRole('link', { name: 'Assets' }))

    expect(await screen.findByRole('heading', { level: 1, name: 'Assets' })).toBeInTheDocument()
    expect(within(primaryNav()).getByRole('link', { name: 'Assets' })).toHaveAttribute(
      'aria-current',
      'page',
    )
    expect(screen.getByRole('main')).toHaveFocus()
  })

  it('shows page errors inside the shell without exposing them as a crash', async () => {
    // React reports the thrown error to the console; that output is expected here.
    vi.spyOn(console, 'error').mockImplementation(() => undefined)
    function BrokenPage(): never {
      throw new Error('page failed')
    }
    const failingRoutes: RouteObject[] = [
      {
        Component: AppLayout,
        children: [
          { ErrorBoundary: RouteErrorPage, children: [{ path: '/', Component: BrokenPage }] },
        ],
      },
    ]

    renderAt('/', failingRoutes)

    expect(
      await screen.findByRole('heading', { level: 1, name: 'Something went wrong' }),
    ).toBeInTheDocument()
    expect(primaryNav()).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Return to overview' })).toBeInTheDocument()
  })

  it('closes the mobile navigation with Escape and returns focus to its button', async () => {
    const { user } = renderAt(paths.overview)
    await screen.findByRole('heading', { level: 1, name: 'Overview' })
    expect(screen.getAllByRole('navigation', { name: 'Primary' })).toHaveLength(1)

    await user.click(screen.getByRole('button', { name: 'Open navigation' }))
    expect(screen.getAllByRole('navigation', { name: 'Primary' })).toHaveLength(2)

    await user.keyboard('{Escape}')

    expect(screen.getAllByRole('navigation', { name: 'Primary' })).toHaveLength(1)
    expect(screen.getByRole('button', { name: 'Open navigation' })).toHaveFocus()
  })
})
