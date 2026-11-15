export interface ResultsFooterProps {
  /** Number of results shown. */
  shown: number
  /** Total number of matching results. */
  total: number
  /** Plural noun, for example "assets". */
  noun: string
}

/**
 * Result count below a list. Hidden while the list is empty, because the
 * empty state already says so. Pagination is added when lists hold real data.
 */
export function ResultsFooter({ shown, total, noun }: ResultsFooterProps) {
  if (total === 0) {
    return null
  }
  return (
    <footer className="flex items-center justify-between px-6 py-5.5 text-body text-fg">
      <span aria-live="polite">
        Showing {shown} of {total} {noun}
      </span>
    </footer>
  )
}
