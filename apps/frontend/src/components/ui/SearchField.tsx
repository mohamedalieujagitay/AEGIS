import type { ComponentPropsWithRef } from 'react'
import { cx } from '../../lib/cx'
import { SearchIcon } from '../icons/icons'

export interface SearchFieldProps extends Omit<ComponentPropsWithRef<'input'>, 'type'> {
  /** Accessible name of the search input. */
  label: string
  className?: string
}

export function SearchField({ label, className, ...props }: SearchFieldProps) {
  return (
    <label
      className={cx(
        'flex h-10.5 items-center gap-3 rounded-control border border-line-strong bg-canvas px-3.5 text-fg-muted',
        'focus-within:border-chart-blue focus-within:ring-3 focus-within:ring-chart-blue/18',
        'has-disabled:cursor-not-allowed has-disabled:opacity-60',
        className,
      )}
    >
      <span className="sr-only">{label}</span>
      <SearchIcon className="size-5 shrink-0" />
      <input
        type="search"
        className="min-w-0 flex-1 bg-transparent text-body text-fg-heading outline-none placeholder:text-fg-muted disabled:cursor-not-allowed"
        {...props}
      />
    </label>
  )
}
