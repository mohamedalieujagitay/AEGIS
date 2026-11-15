import type { ComponentPropsWithRef } from 'react'
import { cx } from '../../lib/cx'

export type BadgeTone =
  | 'neutral'
  | 'info'
  | 'success'
  | 'warning'
  | 'danger'
  | 'violet'
  | 'critical'
  | 'high'
  | 'medium'
  | 'low'

const toneClasses: Record<BadgeTone, string> = {
  neutral: 'border border-line bg-surface-muted text-fg',
  info: 'bg-chart-blue/16 text-info',
  success: 'bg-chart-green/16 text-success',
  warning: 'bg-chart-orange/16 text-warning',
  danger: 'bg-chart-red/16 text-danger',
  violet: 'bg-chart-violet/20 text-violet',
  critical: 'bg-severity-critical/16 text-severity-critical-text',
  high: 'bg-chart-orange/16 text-severity-high-text',
  medium: 'bg-chart-yellow/16 text-severity-medium-text',
  low: 'bg-chart-blue/16 text-severity-low-text',
}

export interface BadgeProps extends ComponentPropsWithRef<'span'> {
  /**
   * Visual tone. Colour must never be the only carrier of meaning: the badge
   * text itself must state what it represents.
   */
  tone?: BadgeTone
}

export function Badge({ tone = 'neutral', className, ...props }: BadgeProps) {
  return (
    <span
      className={cx(
        'inline-flex h-7 items-center gap-1.5 rounded-badge px-3 text-sm font-semibold whitespace-nowrap',
        toneClasses[tone],
        className,
      )}
      {...props}
    />
  )
}
