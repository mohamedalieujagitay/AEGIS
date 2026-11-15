import { useEffect, useId, useRef, useState } from 'react'
import { Link, Outlet, ScrollRestoration, useLocation } from 'react-router'
import {
  BellIcon,
  ChevronsLeftIcon,
  CloseIcon,
  HelpIcon,
  MenuIcon,
  SearchIcon,
  ShieldLogo,
} from '../../components/icons/icons'
import { SideNav } from '../../components/layout/SideNav'
import { SkipLink } from '../../components/layout/SkipLink'
import { cx } from '../../lib/cx'
import { APP_NAME } from '../../lib/documentTitle'
import { primaryNavigation } from '../navigation/navigation'
import { paths } from '../router/paths'

export const MAIN_CONTENT_ID = 'main-content'

const focusRing =
  'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus'

const iconButton = cx(
  'grid place-items-center rounded-lg p-1 text-fg transition-colors',
  'enabled:hover:text-fg-heading disabled:cursor-not-allowed disabled:opacity-50',
  focusRing,
)

function Brand({ collapsed = false }: { collapsed?: boolean }) {
  return (
    <Link
      to={paths.overview}
      className={cx('flex min-w-0 flex-1 items-center gap-3 rounded-control', focusRing)}
    >
      <ShieldLogo className={cx('h-11.5 w-10.5 shrink-0', collapsed && 'sr-only')} />
      <span className={cx('flex min-w-0 flex-col leading-[1.1]', collapsed && 'sr-only')}>
        <span className="text-[1.5625rem] font-extrabold tracking-[0.5px] text-fg-heading">
          {APP_NAME}
        </span>
        <span className="mt-0.75 truncate text-[0.78125rem] text-fg-muted">
          Cybersecurity Platform
        </span>
      </span>
    </Link>
  )
}

/**
 * Workspace area. Workspaces arrive with authentication (Phase 02), so this
 * shows an honest empty state rather than a sample workspace.
 */
function WorkspaceStatus({ collapsed = false }: { collapsed?: boolean }) {
  return (
    <div
      title={collapsed ? 'No workspace: available after sign-in' : undefined}
      className={cx(
        'flex items-center gap-3 rounded-xl border border-line bg-surface',
        collapsed ? 'justify-center p-2.5' : 'px-4 py-3.5',
      )}
    >
      <span
        aria-hidden="true"
        className="grid size-10 shrink-0 place-items-center rounded-[9px] bg-surface-muted text-lg font-bold text-fg-muted"
      >
        —
      </span>
      <span className={cx('flex min-w-0 flex-col leading-tight', collapsed && 'sr-only')}>
        <strong className="truncate text-[0.90625rem] text-fg-heading">No workspace</strong>
        <small className="truncate text-[0.78125rem] text-fg-subtle">Available after sign-in</small>
      </span>
    </div>
  )
}

/**
 * Application shell: skip link, collapsible sidebar (desktop), top bar with
 * search and utility actions, navigation strip (small screens) and the single
 * <main> landmark.
 *
 * Search, notifications and help are shown disabled until the features
 * behind them exist; they never pretend to work.
 */
export function AppLayout() {
  const [mobileNavOpen, setMobileNavOpen] = useState(false)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const mobileNavId = useId()
  const sidebarId = useId()
  const searchId = useId()
  const searchNoteId = useId()
  const menuButtonRef = useRef<HTMLButtonElement>(null)
  const mainRef = useRef<HTMLElement>(null)
  const { pathname } = useLocation()
  const previousPathname = useRef(pathname)

  // Move focus to the main content after client-side navigation, so screen
  // reader and keyboard users start at the new page instead of the old link.
  // The initial page load is skipped: focus stays at the top of the document.
  useEffect(() => {
    if (previousPathname.current !== pathname) {
      previousPathname.current = pathname
      mainRef.current?.focus({ preventScroll: true })
    }
  }, [pathname])

  // Close the mobile navigation with Escape and return focus to its button.
  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        setMobileNavOpen(false)
        menuButtonRef.current?.focus()
      }
    }
    if (mobileNavOpen) {
      document.addEventListener('keydown', handleKeyDown)
    }
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [mobileNavOpen])

  const closeMobileNav = () => setMobileNavOpen(false)

  return (
    <div className="min-h-screen lg:flex">
      <SkipLink targetId={MAIN_CONTENT_ID} />

      {/* Desktop sidebar */}
      <aside
        id={sidebarId}
        aria-label="Sidebar"
        className={cx(
          'sticky top-0 hidden h-dvh shrink-0 flex-col border-r border-line-soft bg-sidebar px-3.75 pb-4 transition-[width] duration-200 lg:flex',
          sidebarCollapsed ? 'w-19' : 'w-72',
        )}
      >
        <div
          className={cx(
            '-mx-3.75 mb-5 flex h-16.5 items-center gap-3 border-b border-line-soft',
            sidebarCollapsed ? 'justify-center px-0' : 'pr-5 pl-5.5',
          )}
        >
          <Brand collapsed={sidebarCollapsed} />
          <button
            type="button"
            className={iconButton}
            aria-controls={sidebarId}
            aria-expanded={!sidebarCollapsed}
            onClick={() => setSidebarCollapsed((collapsed) => !collapsed)}
          >
            <ChevronsLeftIcon
              className={cx('size-5.5 text-fg-muted', sidebarCollapsed && 'rotate-180')}
            />
            <span className="sr-only">
              {sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            </span>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto">
          <SideNav items={primaryNavigation} label="Primary" collapsed={sidebarCollapsed} />
        </div>

        <WorkspaceStatus collapsed={sidebarCollapsed} />
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-30 flex h-16.5 items-center justify-between gap-5 border-b border-line-soft bg-sidebar pr-6 pl-4 sm:pl-6.5">
          <div className="flex min-w-0 flex-1 items-center gap-3">
            <button
              ref={menuButtonRef}
              type="button"
              className={cx(iconButton, 'lg:hidden')}
              aria-expanded={mobileNavOpen}
              aria-controls={mobileNavId}
              onClick={() => setMobileNavOpen((open) => !open)}
            >
              {mobileNavOpen ? <CloseIcon className="size-6" /> : <MenuIcon className="size-6" />}
              <span className="sr-only">
                {mobileNavOpen ? 'Close navigation' : 'Open navigation'}
              </span>
            </button>

            <div className="lg:hidden">
              <Link
                to={paths.overview}
                className={cx('flex items-center gap-2 rounded-control', focusRing)}
              >
                <ShieldLogo className="h-9 w-8 shrink-0" />
                <span className="text-xl font-extrabold text-fg-heading">{APP_NAME}</span>
              </Link>
            </div>

            <search className="hidden w-full max-w-131.75 md:block">
              <label
                htmlFor={searchId}
                className="flex h-10.5 cursor-not-allowed items-center gap-3 rounded-control border border-line-strong bg-canvas pr-3 pl-3.5 text-fg-muted"
              >
                <span className="sr-only">Search</span>
                <SearchIcon className="size-5.5 shrink-0" />
                <input
                  id={searchId}
                  type="search"
                  disabled
                  aria-describedby={searchNoteId}
                  placeholder="Search assets, assessments, findings..."
                  className="min-w-0 flex-1 cursor-not-allowed bg-transparent text-[0.90625rem] text-fg-heading outline-none placeholder:text-fg-muted"
                />
                <kbd
                  aria-hidden="true"
                  className="rounded-md border border-line-emphasis bg-surface-raised px-2.25 py-0.5 font-sans text-[0.8125rem] text-fg-muted"
                >
                  /
                </kbd>
              </label>
              <span id={searchNoteId} className="sr-only">
                Search is not available yet.
              </span>
            </search>
          </div>

          <div className="flex items-center gap-4.5">
            <button type="button" className={iconButton} disabled>
              <BellIcon className="size-6.5" />
              <span className="sr-only">Notifications (not available yet)</span>
            </button>
            <button type="button" className={iconButton} disabled>
              <HelpIcon className="size-6.5" />
              <span className="sr-only">Help (not available yet)</span>
            </button>
          </div>
        </header>

        {mobileNavOpen && (
          <div
            id={mobileNavId}
            className="flex flex-col gap-3 border-b border-line-soft bg-sidebar p-3 lg:hidden"
          >
            <SideNav items={primaryNavigation} label="Primary" onNavigate={closeMobileNav} />
            <WorkspaceStatus />
          </div>
        )}

        <main
          id={MAIN_CONTENT_ID}
          ref={mainRef}
          tabIndex={-1}
          className="flex-1 focus:outline-none"
        >
          <Outlet />
        </main>
      </div>

      <ScrollRestoration />
    </div>
  )
}
