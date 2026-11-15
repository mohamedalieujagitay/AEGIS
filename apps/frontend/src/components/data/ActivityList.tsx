import type { ComponentType, ReactNode } from 'react'
import { cx } from '../../lib/cx'
import { toneSurfaceClasses, type DataTone } from './tones'

export interface ActivityItem {
  id: string
  text: string
  icon: ComponentType<{ className?: string }>
  tone: DataTone
  /** Machine-readable timestamp (ISO 8601). */
  dateTime: string
  /** Human-readable time, for example "2 hours ago". */
  timeLabel: string
}

export interface ActivityListProps {
  items: readonly ActivityItem[]
  /** Shown instead of the list when there are no items. */
  empty: ReactNode
}

export function ActivityList({ items, empty }: ActivityListProps) {
  if (items.length === 0) {
    return <>{empty}</>
  }

  return (
    <ul className="mt-2 flex flex-col">
      {items.map(({ id, text, icon: ItemIcon, tone, dateTime, timeLabel }) => (
        <li
          key={id}
          className="grid grid-cols-[44px_1fr_auto] items-center gap-4 border-b border-line-soft py-2.25 last:border-b-0"
        >
          <span
            className={cx(
              'flex size-11 items-center justify-center rounded-[11px]',
              toneSurfaceClasses[tone],
            )}
          >
            <ItemIcon className="size-5.5" />
          </span>
          <span className="min-w-0 truncate text-body text-fg-heading">{text}</span>
          <time dateTime={dateTime} className="text-sm whitespace-nowrap text-fg-muted">
            {timeLabel}
          </time>
        </li>
      ))}
    </ul>
  )
}
