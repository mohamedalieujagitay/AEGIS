import type { ComponentType } from 'react'
import { cx } from '../../lib/cx'
import { ArrowDownIcon, ArrowUpIcon } from '../icons/icons'
import { Sparkline } from './Sparkline'
import { toneGraphicClasses, toneSurfaceClasses, type DataTone } from './tones'

export interface StatDelta {
  /** Display text, for example "+4 (20%)". */
  change: string
  direction: 'up' | 'down'
  /** Whether the change is good news (for findings, "down" is an improvement). */
  isImprovement: boolean
  /** Comparison period, for example "from last 30 days". */
  period: string
}

export interface StatCardProps {
  label: string
  /** The metric value. null means no data exists yet, shown as an empty state. */
  value: number | null
  icon: ComponentType<{ className?: string }>
  tone: DataTone
  /** Compact cards (used on list pages) have no sparkline or delta row. */
  compact?: boolean
  delta?: StatDelta
  /** Recent values for the sparkline, in chronological order. */
  trend?: readonly number[]
  /** Text shown when value is null. */
  emptyText?: string
}

const numberFormat = new Intl.NumberFormat()

export function StatCard({
  label,
  value,
  icon: StatIcon,
  tone,
  compact = false,
  delta,
  trend,
  emptyText = 'No data yet',
}: StatCardProps) {
  const hasValue = value !== null

  return (
    <article
      className={cx(
        'relative flex flex-col justify-center overflow-hidden rounded-card border border-line bg-linear-to-b from-surface-raised to-surface px-4 py-3.5',
        compact ? 'min-h-23' : 'min-h-33',
      )}
    >
      <div className="flex items-center gap-3.5">
        <span
          className={cx(
            'flex size-14.5 shrink-0 items-center justify-center rounded-xl',
            toneSurfaceClasses[tone],
          )}
        >
          <StatIcon className="size-6.5" />
        </span>
        <div className="flex min-w-0 flex-col">
          <h2 className="truncate text-body text-fg">{label}</h2>
          <p className="text-display font-extrabold text-fg-heading">
            {hasValue ? (
              numberFormat.format(value)
            ) : (
              <>
                <span aria-hidden="true">—</span>
                <span className="sr-only">{emptyText}</span>
              </>
            )}
          </p>
        </div>
      </div>

      {!compact && hasValue && trend && (
        <Sparkline
          values={trend}
          className={cx('absolute top-8.5 right-0 h-11 w-1/2', toneGraphicClasses[tone])}
        />
      )}

      {!compact && hasValue && delta && (
        <p className="mt-3.5 flex items-center gap-1 text-sm text-fg-muted">
          <span
            className={cx(
              'inline-flex items-center gap-1 font-medium',
              delta.isImprovement ? 'text-success' : 'text-danger',
            )}
          >
            {delta.direction === 'up' ? (
              <ArrowUpIcon className="size-3.5" />
            ) : (
              <ArrowDownIcon className="size-3.5" />
            )}
            <span className="sr-only">
              {delta.direction === 'up' ? 'Increased by' : 'Decreased by'}
            </span>
            {delta.change}
          </span>
          {delta.period}
        </p>
      )}
      {!compact && !hasValue && (
        // Visible hint; screen readers already hear emptyText with the value.
        <p aria-hidden="true" className="mt-3.5 text-sm text-fg-subtle">
          {emptyText}
        </p>
      )}
    </article>
  )
}
