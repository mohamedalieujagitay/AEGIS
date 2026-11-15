import { Link } from 'react-router'
import { paths } from '../../../app/router/paths'
import { ActivityList } from '../../../components/data/ActivityList'
import { DataTable } from '../../../components/data/DataTable'
import { DonutChart } from '../../../components/data/DonutChart'
import { StatCard } from '../../../components/data/StatCard'
import { TrendChart } from '../../../components/data/TrendChart'
import {
  ArrowRightIcon,
  AssessmentIcon,
  CalendarIcon,
  CubeIcon,
  HistoryIcon,
  PlusIcon,
  ShieldAlertIcon,
  TargetIcon,
  WarningIcon,
} from '../../../components/icons/icons'
import { PageContainer } from '../../../components/layout/PageContainer'
import { Button, Card, EmptyState, Select } from '../../../components/ui'
import { notAvailableYet } from '../../../lib/availability'

const rangeOptions = [
  { value: '7', label: 'Last 7 days' },
  { value: '30', label: 'Last 30 days' },
  { value: '90', label: 'Last 90 days' },
] as const

const linkClasses =
  'inline-flex items-center gap-1.5 rounded text-[0.90625rem] font-semibold text-chart-blue hover:underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus'

function ViewAll({ to, label }: { to: string; label: string }) {
  return (
    <Link to={to} className={linkClasses}>
      View All <span className="sr-only">{label}</span>
      <ArrowRightIcon className="size-3.5" />
    </Link>
  )
}

/**
 * Security overview.
 *
 * The layout follows the AEGIS UI design, but there is no backend data yet,
 * so every metric and list shows an empty state. Each component accepts real
 * data and will render it once the API exists. Sample data must never be used
 * here (PRODUCT_REQUIREMENTS.md §5.3).
 */
export function OverviewPage() {
  return (
    <PageContainer
      title="Overview"
      description="Your security posture, assessments and findings at a glance."
      actions={
        <Button disabled title={notAvailableYet}>
          <PlusIcon className="size-5.5" />
          New Assessment
        </Button>
      }
    >
      <section aria-label="Key metrics" className="grid gap-6.5 sm:grid-cols-2 stats4:grid-cols-4">
        <StatCard label="Total Assets" value={null} icon={CubeIcon} tone="blue" />
        <StatCard label="Assessments" value={null} icon={TargetIcon} tone="violet" />
        <StatCard label="Open Findings" value={null} icon={WarningIcon} tone="orange" />
        <StatCard label="Critical Risks" value={null} icon={ShieldAlertIcon} tone="red" />
      </section>

      <div className="grid gap-6.5 charts:grid-cols-[1.13fr_1.4fr]">
        <Card title="Risk Distribution" className="flex flex-col">
          <DonutChart segments={[]} totalLabel="Findings" emptyText="No findings recorded yet." />
        </Card>

        <Card
          title="Findings Trend"
          actions={
            <Select
              label="Date range"
              icon={CalendarIcon}
              options={rangeOptions}
              defaultValue="30"
              disabled
              className="min-w-38.5"
            />
          }
        >
          <TrendChart
            points={[]}
            description="Open findings per day"
            emptyText="Trends appear after the first assessments complete."
          />
        </Card>
      </div>

      <div className="grid gap-6.5 charts:grid-cols-[1.3fr_1fr]">
        <Card
          title="Recent Assessments"
          actions={<ViewAll to={paths.assessments} label="assessments" />}
        >
          <DataTable<never>
            caption="Recent assessments"
            density="compact"
            columns={[
              { key: 'assessment', header: 'Assessment', className: 'w-[42%]' },
              { key: 'target', header: 'Target' },
              { key: 'status', header: 'Status' },
              { key: 'started', header: 'Started' },
            ]}
            rows={[]}
            getRowKey={() => ''}
            empty={
              <EmptyState
                icon={AssessmentIcon}
                title="No assessments yet"
                description="Assessments you run against authorized assets will be listed here."
              />
            }
          />
        </Card>

        <Card title="Recent Activity" actions={<ViewAll to={paths.activity} label="activity" />}>
          <ActivityList
            items={[]}
            empty={
              <EmptyState
                icon={HistoryIcon}
                title="No activity yet"
                description="Asset, assessment and finding changes will appear here."
              />
            }
          />
        </Card>
      </div>
    </PageContainer>
  )
}
