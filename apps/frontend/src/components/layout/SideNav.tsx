import type { ComponentType } from 'react'
import { NavLink } from 'react-router'
import { cx } from '../../lib/cx'

interface NavItemBase {
  label: string
  icon: ComponentType<{ className?: string }>
}

/** A navigation item whose page exists. */
export interface AvailableNavItem extends NavItemBase {
  status: 'available'
  to: string
  /** Match the path exactly, so that "/" is not active on every page. */
  end?: boolean
}

/** A navigation item for a module that is not built yet. It is shown but not clickable. */
export interface PlannedNavItem extends NavItemBase {
  status: 'planned'
}

export type NavItem = AvailableNavItem | PlannedNavItem

export interface SideNavProps {
  items: readonly NavItem[]
  /** Accessible name of the navigation landmark. */
  label: string
  /** Icon-only mode for a collapsed sidebar. Labels remain available to screen readers. */
  collapsed?: boolean
  /** Called after a link is activated, for example to close a mobile menu. */
  onNavigate?: () => void
}

/**
 * Primary navigation list.
 *
 * - NavLink sets aria-current="page" on the active link, so the current page
 *   is announced and not indicated by colour alone.
 * - Planned items are rendered as disabled entries (aria-disabled, not
 *   focusable) with a visible "Soon" label, so they never lead to
 *   placeholder pages.
 */
export function SideNav({ items, label, collapsed = false, onNavigate }: SideNavProps) {
  const itemBase = cx(
    'flex items-center rounded-control font-semibold transition-colors',
    'h-12.25 gap-4 px-5 text-base',
    collapsed && 'justify-center px-0',
  )

  return (
    <nav aria-label={label}>
      <ul className="flex flex-col gap-1.25">
        {items.map((item) => {
          const ItemIcon = item.icon
          const text = (
            <span className={cx('flex-1 truncate', collapsed && 'sr-only')}>{item.label}</span>
          )

          if (item.status === 'planned') {
            return (
              <li key={item.label}>
                <span
                  aria-disabled="true"
                  title={collapsed ? `${item.label} (coming soon)` : undefined}
                  className={cx(itemBase, 'cursor-not-allowed text-fg-subtle')}
                >
                  <ItemIcon className="size-5.5 shrink-0" />
                  {text}
                  <span
                    className={cx(
                      'rounded-full border border-line px-1.5 py-px text-[0.6875rem] text-fg-subtle',
                      collapsed && 'sr-only',
                    )}
                  >
                    Soon
                  </span>
                </span>
              </li>
            )
          }

          return (
            <li key={item.to}>
              <NavLink
                to={item.to}
                end={item.end}
                onClick={onNavigate}
                title={collapsed ? item.label : undefined}
                className={({ isActive }) =>
                  cx(
                    itemBase,
                    'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus',
                    isActive
                      ? 'bg-linear-to-r from-nav-active-from to-nav-active-to text-fg-heading ring-1 ring-chart-blue/25 ring-inset'
                      : 'text-fg hover:bg-surface-hover',
                  )
                }
              >
                <ItemIcon className="size-5.5 shrink-0" />
                {text}
              </NavLink>
            </li>
          )
        })}
      </ul>
    </nav>
  )
}
