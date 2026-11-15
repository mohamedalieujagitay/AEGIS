import type { ReactNode } from 'react'
import { cx } from '../../lib/cx'
import { formatDocumentTitle } from '../../lib/documentTitle'
import { Heading } from '../ui'

export interface PageContainerProps {
  /** Page title, rendered as the page's single level-1 heading. */
  title: string
  /** Browser tab title. Defaults to the page title. */
  documentTitle?: string
  description?: string
  /** Optional page-level controls shown alongside the title. */
  actions?: ReactNode
  children?: ReactNode
  className?: string
}

/**
 * Page padding, page header and document title (React 19 hoists the <title>
 * element into <head>). Sections inside are spaced 26px apart, as in the
 * AEGIS design.
 *
 * It renders a plain container, not a <main> landmark: the application
 * layout provides the single <main> element for the whole page.
 */
export function PageContainer({
  title,
  documentTitle,
  description,
  actions,
  children,
  className,
}: PageContainerProps) {
  return (
    <div
      className={cx(
        'mx-auto flex w-full max-w-content flex-col gap-6.5 px-4 pt-6 pb-8 sm:pr-6 sm:pl-6.5',
        className,
      )}
    >
      <title>{formatDocumentTitle(documentTitle ?? title)}</title>
      <header className="flex flex-col items-start justify-between gap-5 sm:flex-row">
        <div>
          <Heading level={1}>{title}</Heading>
          {description && <p className="mt-1 text-[0.96875rem] text-fg-muted">{description}</p>}
        </div>
        {actions && <div className="flex flex-wrap items-center gap-4">{actions}</div>}
      </header>
      {children}
    </div>
  )
}
