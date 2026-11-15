import { useId, type ReactNode } from 'react'
import { cx } from '../../lib/cx'
import { Heading } from './Typography'

export interface CardProps {
  /** Optional title. When present, the card becomes a labelled section. */
  title?: string
  description?: string
  /** Optional controls shown alongside the title, such as a button or link. */
  actions?: ReactNode
  children?: ReactNode
  /** Remove the inner padding, for edge-to-edge content such as tables. */
  flush?: boolean
  className?: string
}

/** Panel with the AEGIS card surface: subtle vertical gradient and border. */
export function Card({
  title,
  description,
  actions,
  children,
  flush = false,
  className,
}: CardProps) {
  const titleId = useId()
  const hasHeader = Boolean(title || description || actions)
  const Element = title ? 'section' : 'div'

  return (
    <Element
      aria-labelledby={title ? titleId : undefined}
      className={cx(
        'rounded-card border border-line bg-linear-to-b from-surface-raised to-surface',
        !flush && 'px-5.5 py-5',
        className,
      )}
    >
      {hasHeader && (
        <div
          className={cx('flex items-center justify-between gap-4', flush ? 'px-5.5 pt-5' : 'mb-4')}
        >
          <div className="flex flex-col gap-1">
            {title && (
              <Heading level={2} id={titleId}>
                {title}
              </Heading>
            )}
            {description && <p className="text-body text-fg-muted">{description}</p>}
          </div>
          {actions && <div className="flex shrink-0 items-center gap-3">{actions}</div>}
        </div>
      )}
      {children}
    </Element>
  )
}
