export interface SkipLinkProps {
  /** id of the element that receives focus, normally the <main> landmark. */
  targetId: string
}

/**
 * First focusable element on the page. Hidden until it receives keyboard
 * focus, then lets keyboard users jump past the navigation.
 */
export function SkipLink({ targetId }: SkipLinkProps) {
  return (
    <a
      href={`#${targetId}`}
      className="sr-only rounded-control bg-primary px-4 py-2 text-sm font-medium text-primary-fg focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus"
    >
      Skip to main content
    </a>
  )
}
