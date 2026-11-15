import { useState } from 'react'
import { DataTable, type DataTableColumn } from '../../../components/data/DataTable'
import { ResultsFooter } from '../../../components/data/ResultsFooter'
import { StatCard } from '../../../components/data/StatCard'
import { ViewToggle, type ViewMode } from '../../../components/data/ViewToggle'
import {
  CalendarIcon,
  HistoryIcon,
  SettingsIcon,
  ShieldCheckIcon,
  UsersIcon,
} from '../../../components/icons/icons'
import { PageContainer } from '../../../components/layout/PageContainer'
import { Card, EmptyState, SearchField, Select } from '../../../components/ui'

/** Audit event categories (SYSTEM_ARCHITECTURE.md §13.2). */
const typeOptions = [
  { value: '', label: 'All Event Types' },
  { value: 'assessment', label: 'Assessment' },
  { value: 'finding', label: 'Finding' },
  { value: 'asset', label: 'Asset' },
  { value: 'report', label: 'Report' },
  { value: 'user', label: 'User' },
  { value: 'security', label: 'Security' },
  { value: 'system', label: 'System' },
] as const

const rangeOptions = [
  { value: '24h', label: 'Last 24 hours' },
  { value: '7', label: 'Last 7 days' },
  { value: '30', label: 'Last 30 days' },
  { value: 'all', label: 'All time' },
] as const

const columns: readonly DataTableColumn<never>[] = [
  { key: 'time', header: 'Time', className: 'w-[19%]' },
  { key: 'icon', header: <span className="sr-only">Icon</span>, className: 'w-14' },
  { key: 'event', header: 'Event' },
  { key: 'details', header: 'Details' },
  { key: 'user', header: 'User' },
  { key: 'type', header: 'Type' },
]

export function ActivityPage() {
  const [view, setView] = useState<ViewMode>('list')

  return (
    <PageContainer
      title="Activity"
      description="Audit log of security-relevant events across your workspace."
    >
      <section aria-label="Event totals" className="grid gap-5 sm:grid-cols-2 split:grid-cols-4">
        <StatCard compact label="Total Events" value={null} icon={HistoryIcon} tone="blue" />
        <StatCard
          compact
          label="Security Events"
          value={null}
          icon={ShieldCheckIcon}
          tone="green"
        />
        <StatCard compact label="User Actions" value={null} icon={UsersIcon} tone="violet" />
        <StatCard compact label="System Events" value={null} icon={SettingsIcon} tone="gray" />
      </section>

      <div className="flex flex-wrap items-end gap-5.5">
        <SearchField
          label="Search events"
          placeholder="Search events..."
          disabled
          className="w-full sm:w-86.5"
        />
        <Select label="Filter by event type" options={typeOptions} disabled />
        <Select label="Filter by user" options={[{ value: '', label: 'All Users' }]} disabled />
        <Select
          label="Date range"
          icon={CalendarIcon}
          options={rangeOptions}
          defaultValue="7"
          disabled
        />
        <div className="ml-auto">
          <ViewToggle value={view} onChange={setView} disabled />
        </div>
      </div>

      <div className="grid items-start gap-5.5 split:grid-cols-[minmax(0,1fr)_340px]">
        <Card flush className="overflow-hidden">
          <DataTable<never>
            caption="Audit events"
            columns={columns}
            rows={[]}
            getRowKey={() => ''}
            minWidthClass="min-w-[45rem]"
            empty={
              <EmptyState
                icon={HistoryIcon}
                title="No events recorded yet"
                description="Sign-ins, permission changes, asset authorization, scope changes, assessments, finding changes and report generation are recorded here."
              />
            }
          />
          <ResultsFooter shown={0} total={0} noun="events" />
        </Card>

        <Card title="Event Details" className="split:sticky split:top-21">
          <p className="text-body text-fg-muted">Select an event to see its details.</p>
        </Card>
      </div>
    </PageContainer>
  )
}
