import { isRouteErrorResponse, Link, useRouteError } from 'react-router'
import { PageContainer } from '../../components/layout/PageContainer'
import { buttonStyles, Text } from '../../components/ui'
import { MAIN_CONTENT_ID } from '../layout/AppLayout'
import { paths } from '../router/paths'

interface ErrorDescription {
  title: string
  message: string
  /** Technical detail, shown only in development builds. */
  detail?: string
}

function describeError(error: unknown): ErrorDescription {
  if (isRouteErrorResponse(error)) {
    return {
      title: `Error ${error.status}`,
      message: error.statusText || 'The request could not be completed.',
    }
  }
  return {
    title: 'Something went wrong',
    message: 'An unexpected error occurred while displaying this page.',
    detail: error instanceof Error ? error.message : undefined,
  }
}

/**
 * Error page for failures inside a page. Rendered inside the application
 * layout, so the navigation remains available.
 *
 * Technical details are shown only in development builds, so internal
 * errors are never exposed to users of a production deployment.
 */
export function RouteErrorPage() {
  const { title, message, detail } = describeError(useRouteError())

  return (
    <PageContainer title={title} description={message}>
      {import.meta.env.DEV && detail && (
        <Text className="mb-6 font-mono text-danger">Development detail: {detail}</Text>
      )}
      <Link to={paths.overview} className={buttonStyles({ variant: 'secondary' })}>
        Return to overview
      </Link>
    </PageContainer>
  )
}

/**
 * Last-resort error page for failures in the application layout itself.
 * The layout is unavailable, so this page provides its own <main> landmark.
 */
export function RootErrorPage() {
  return (
    <main id={MAIN_CONTENT_ID}>
      <RouteErrorPage />
    </main>
  )
}
