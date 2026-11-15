import type { ComponentType, ReactNode } from 'react'
import { cx } from '../../lib/cx'

export interface EmptyStateProps {
  title: string
  description?: string
  icon?: ComponentType<{ className?: string }>
  /** Optional follow-up action, such as a button or link. */
  action?: ReactNode
  className?: string
}

/** Shown in place of data that does not exist yet. Never substitute sample data. */
export function EmptyState({
  title,
  description,
  icon: EmptyIcon,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cx(
        'flex flex-col items-center justify-center gap-2 px-6 py-12 text-center',
        className,
      )}
    >
      {EmptyIcon && (
        <span className="mb-1 flex size-11 items-center justify-center rounded-xl bg-surface-muted text-fg-muted">
          <EmptyIcon className="size-5.5" />
        </span>
      )}
      <p className="text-body font-semibold text-fg-heading">{title}</p>
      {description && <p className="max-w-md text-body text-fg-muted">{description}</p>}
      {action && <div className="mt-2">{action}</div>}
    </div>
  )
}
