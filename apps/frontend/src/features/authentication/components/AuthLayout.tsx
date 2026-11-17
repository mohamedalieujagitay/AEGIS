import type { ReactNode } from 'react'
import { ShieldLogo } from '../../../components/icons/icons'
import { Heading } from '../../../components/ui'
import { APP_NAME, formatDocumentTitle } from '../../../lib/documentTitle'

export const AUTH_MAIN_ID = 'main-content'

/** Centered card for the pages shown before sign-in. Provides the <main> landmark. */
export function AuthLayout({
  title,
  description,
  children,
}: {
  title: string
  description?: string
  children: ReactNode
}) {
  return (
    <main
      id={AUTH_MAIN_ID}
      className="grid min-h-dvh place-items-center bg-canvas px-4 py-10"
      tabIndex={-1}
    >
      <title>{formatDocumentTitle(title)}</title>
      <div className="w-full max-w-md">
        <div className="mb-7 flex items-center justify-center gap-3">
          <ShieldLogo className="h-11.5 w-10.5" />
          <span className="text-[1.5625rem] font-extrabold tracking-[0.5px] text-fg-heading">
            {APP_NAME}
          </span>
        </div>
        <div className="rounded-card border border-line bg-linear-to-b from-surface-raised to-surface p-7">
          <Heading level={1} size="md">
            {title}
          </Heading>
          {description && <p className="mt-1.5 text-body text-fg-muted">{description}</p>}
          <div className="mt-6">{children}</div>
        </div>
      </div>
    </main>
  )
}

/** A message at the top of an authentication form. */
export function FormAlert({
  tone,
  children,
}: {
  tone: 'error' | 'info' | 'success'
  children: ReactNode
}) {
  const classes = {
    error: 'border-chart-red/40 bg-chart-red/8 text-danger',
    info: 'border-chart-blue/30 bg-chart-blue/8 text-fg',
    success: 'border-chart-green/35 bg-chart-green/8 text-success',
  }[tone]
  const className = `mb-5 block rounded-control border p-3.5 text-sm ${classes}`
  if (tone === 'error') {
    return (
      <div role="alert" className={className}>
        {children}
      </div>
    )
  }
  return <output className={className}>{children}</output>
}
