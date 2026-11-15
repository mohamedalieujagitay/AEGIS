export const APP_NAME = 'AEGIS'

/** Builds a document title such as "Overview · AEGIS". */
export function formatDocumentTitle(pageTitle: string): string {
  return `${pageTitle} · ${APP_NAME}`
}
