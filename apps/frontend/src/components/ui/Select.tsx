import type { ComponentPropsWithRef, ComponentType } from 'react'
import { cx } from '../../lib/cx'
import { ChevronDownIcon } from '../icons/icons'

export interface SelectOption {
  value: string
  label: string
}

export interface SelectProps extends Omit<ComponentPropsWithRef<'select'>, 'children'> {
  /** Accessible name. Shown visually only when visibleLabel is set. */
  label: string
  visibleLabel?: boolean
  options: readonly SelectOption[]
  /** Optional leading icon, for example a calendar for date ranges. */
  icon?: ComponentType<{ className?: string }>
  className?: string
}

/** Styled native select. Native elements keep keyboard and screen reader support. */
export function Select({
  label,
  visibleLabel = false,
  options,
  icon: LeadingIcon,
  className,
  id,
  ...props
}: SelectProps) {
  return (
    <label className={cx('flex flex-col gap-1.5', className)} htmlFor={id}>
      <span className={visibleLabel ? 'text-sm font-medium text-fg-muted' : 'sr-only'}>
        {label}
      </span>
      <span className="relative flex items-center">
        {LeadingIcon && (
          <LeadingIcon className="pointer-events-none absolute left-3 size-4 text-fg-muted" />
        )}
        <select
          id={id}
          className={cx(
            'h-10.5 w-full cursor-pointer appearance-none rounded-control border border-field-border bg-canvas pr-10 text-body text-fg',
            'hover:border-chart-blue focus:border-chart-blue focus:ring-3 focus:ring-chart-blue/18 focus:outline-none',
            'disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:border-field-border',
            LeadingIcon ? 'pl-9.5' : 'pl-4',
          )}
          {...props}
        >
          {options.map((option) => (
            <option key={option.value} value={option.value} className="bg-surface-raised">
              {option.label}
            </option>
          ))}
        </select>
        <ChevronDownIcon className="pointer-events-none absolute right-3.5 size-4 text-fg-muted" />
      </span>
    </label>
  )
}
