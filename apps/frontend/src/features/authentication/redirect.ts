import type { Location } from 'react-router'
import { paths } from '../../app/router/paths'
import { isRecord } from '../../lib/api'

/**
 * Where to go after sign-in: the in-app page that required it, or the
 * overview. Only local paths are accepted, never another site.
 */
export function redirectTarget(location: Location): string {
  const state: unknown = location.state
  const from = isRecord(state) && isRecord(state['from']) ? state['from'] : undefined
  const pathname = from?.['pathname']
  if (typeof pathname !== 'string' || !pathname.startsWith('/') || pathname.startsWith('//')) {
    return paths.overview
  }
  const search = typeof from?.['search'] === 'string' ? from['search'] : ''
  const hash = typeof from?.['hash'] === 'string' ? from['hash'] : ''
  return `${pathname}${search}${hash}`
}
