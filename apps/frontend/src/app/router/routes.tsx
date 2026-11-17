import type { RouteObject } from 'react-router'
import { ActivityPage } from '../../features/activity/pages/ActivityPage'
import { AssessmentsPage } from '../../features/assessments/pages/AssessmentsPage'
import { AssetsPage } from '../../features/assets/pages/AssetsPage'
import {
  AuthRoot,
  PublicOnly,
  RequireAuth,
} from '../../features/authentication/components/RouteGuards'
import { LoginPage } from '../../features/authentication/pages/LoginPage'
import { RegisterPage } from '../../features/authentication/pages/RegisterPage'
import { ResetPasswordPage } from '../../features/authentication/pages/ResetPasswordPage'
import { OverviewPage } from '../../features/dashboard/pages/OverviewPage'
import { ReportsPage } from '../../features/reports/pages/ReportsPage'
import { SettingsPage } from '../../features/settings/pages/SettingsPage'
import { FindingsPage } from '../../features/vulnerabilities/pages/FindingsPage'
import { AppLayout } from '../layout/AppLayout'
import { NotFoundPage } from '../pages/NotFoundPage'
import { RootErrorPage, RouteErrorPage } from '../pages/RouteErrorPage'
import { paths } from './paths'

/**
 * Central route configuration.
 *
 * Kept separate from router creation so that the same routes can be used
 * with a memory router in tests.
 *
 * - AuthRoot provides the authentication state to every route.
 * - Sign-in and registration are only for signed-out visitors. The reset
 *   page is always reachable: the link comes from the administrator.
 * - Every application page requires a session (RequireAuth). The backend
 *   enforces authentication on its own; these guards only decide what to show.
 * - The layout route renders the application shell. If the shell itself
 *   fails, RootErrorPage replaces it.
 * - The pathless child route catches errors from pages, so RouteErrorPage
 *   is shown inside the shell and navigation stays available.
 */
export const routes: RouteObject[] = [
  {
    Component: AuthRoot,
    ErrorBoundary: RootErrorPage,
    children: [
      {
        Component: PublicOnly,
        children: [
          { path: paths.login, Component: LoginPage },
          { path: paths.register, Component: RegisterPage },
        ],
      },
      { path: paths.resetPassword, Component: ResetPasswordPage },
      {
        Component: RequireAuth,
        children: [
          {
            Component: AppLayout,
            ErrorBoundary: RootErrorPage,
            children: [
              {
                ErrorBoundary: RouteErrorPage,
                children: [
                  { path: paths.overview, Component: OverviewPage },
                  { path: paths.assets, Component: AssetsPage },
                  { path: paths.assessments, Component: AssessmentsPage },
                  { path: paths.findings, Component: FindingsPage },
                  { path: paths.reports, Component: ReportsPage },
                  { path: paths.activity, Component: ActivityPage },
                  { path: paths.settings, Component: SettingsPage },
                  { path: '*', Component: NotFoundPage },
                ],
              },
            ],
          },
        ],
      },
    ],
  },
]
