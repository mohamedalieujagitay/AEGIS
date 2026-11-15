import { cx } from '../../lib/cx'

/** Shared field styling for inputs, selects and search fields. */
export const fieldClasses = cx(
  'h-10.5 w-full rounded-control border border-field-border bg-canvas px-3.5 text-body text-fg-heading placeholder:text-fg-muted',
  'focus:border-chart-blue focus:ring-3 focus:ring-chart-blue/18 focus:outline-none',
  'disabled:cursor-not-allowed disabled:opacity-60',
)
