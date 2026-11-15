import {
  AssessmentIcon,
  ChartBarsIcon,
  HistoryIcon,
  HomeIcon,
  LayersIcon,
  SettingsIcon,
  WarningIcon,
} from '../../components/icons/icons'
import type { NavItem } from '../../components/layout/SideNav'
import { paths } from '../router/paths'

/**
 * Primary navigation, in the order of the AEGIS UI design.
 *
 * Every page exists. Pages whose backend is not built yet show honest empty
 * states and disabled actions. An item can be marked "planned" (visible but
 * disabled) if a future module is added before its page exists.
 */
export const primaryNavigation: readonly NavItem[] = [
  { status: 'available', label: 'Overview', to: paths.overview, icon: HomeIcon, end: true },
  { status: 'available', label: 'Assets', to: paths.assets, icon: LayersIcon },
  { status: 'available', label: 'Assessments', to: paths.assessments, icon: AssessmentIcon },
  { status: 'available', label: 'Findings', to: paths.findings, icon: WarningIcon },
  { status: 'available', label: 'Reports', to: paths.reports, icon: ChartBarsIcon },
  { status: 'available', label: 'Activity', to: paths.activity, icon: HistoryIcon },
  { status: 'available', label: 'Settings', to: paths.settings, icon: SettingsIcon },
]
