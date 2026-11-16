import { describe, expect, it } from 'vitest'
import type { RouteObject } from 'react-router'
import { paths } from '../router/paths'
import { routes } from '../router/routes'
import { primaryNavigation } from './navigation'

function routePaths(routeList: readonly RouteObject[]): string[] {
  return routeList.flatMap((route) => [
    ...(route.path === undefined ? [] : [route.path]),
    ...routePaths(route.children ?? []),
  ])
}

describe('primary navigation', () => {
  it('links only to routes that exist (D-031)', () => {
    const configured = new Set(routePaths(routes))
    for (const item of primaryNavigation) {
      if (item.status === 'available') {
        expect(configured, `no route for ${item.label}`).toContain(item.to)
      }
    }
  })

  it('lists every page exactly once, in the approved order', () => {
    const targets = primaryNavigation.flatMap((item) =>
      item.status === 'available' ? [item.to] : [],
    )
    expect(targets).toEqual([
      paths.overview,
      paths.assets,
      paths.assessments,
      paths.findings,
      paths.reports,
      paths.activity,
      paths.settings,
    ])
  })
})
