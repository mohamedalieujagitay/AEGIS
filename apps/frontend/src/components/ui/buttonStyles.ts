import { cx } from '../../lib/cx'

export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger'
export type ButtonSize = 'sm' | 'md'

export interface ButtonStyleOptions {
  variant?: ButtonVariant
  size?: ButtonSize
}

const baseClasses = cx(
  'inline-flex items-center justify-center gap-2 font-semibold whitespace-nowrap transition',
  'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus',
  'disabled:cursor-not-allowed disabled:opacity-50 disabled:shadow-none',
)

const variantClasses: Record<ButtonVariant, string> = {
  primary: cx(
    'bg-linear-to-b from-primary-from to-primary-to text-primary-fg shadow-primary',
    'enabled:hover:from-primary-hover-from enabled:hover:to-primary-hover-to',
  ),
  secondary:
    'border border-line-emphasis bg-sidebar text-fg-heading enabled:hover:border-chart-blue',
  ghost: 'text-fg-muted enabled:hover:bg-surface-hover enabled:hover:text-fg-heading',
  danger: 'border border-chart-red/50 bg-chart-red/8 text-danger enabled:hover:bg-chart-red/16',
}

const sizeClasses: Record<ButtonSize, string> = {
  sm: 'h-8.5 rounded-lg px-3.5 text-sm',
  md: 'h-11 rounded-control px-5.5 text-body',
}

/**
 * Button styles, exported so that links which must look like buttons
 * (for example, router links) can share them without nesting elements.
 */
export function buttonStyles({
  variant = 'primary',
  size = 'md',
}: ButtonStyleOptions = {}): string {
  return cx(baseClasses, variantClasses[variant], sizeClasses[size])
}
