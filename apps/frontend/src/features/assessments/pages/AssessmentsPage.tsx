import { useState } from 'react'
import { DataTable, type DataTableColumn } from '../../../components/data/DataTable'
import { FilterTabs } from '../../../components/data/FilterTabs'
import { ResultsFooter } from '../../../components/data/ResultsFooter'
import { StatCard } from '../../../components/data/StatCard'
import { ViewToggle, type ViewMode } from '../../../components/data/ViewToggle'
import {
  AssessmentIcon,
  CheckCircleIcon,
  ClockIcon,
  PlayIcon,
  PlusIcon,
  TargetIcon,
  XCircleIcon,
} from '../../../components/icons/icons'
import { PageContainer } from '../../../components/layout/PageContainer'
import { Button, Card, EmptyState, SearchField, Select } from '../../../components/ui'
import { notAvailableYet } from '../../../lib/availability'

/** Job statuses from PRODUCT_REQUIREMENTS.md FR-JOB-002. */
type StatusFilter = 'all' | 'running' | 'queued' | 'completed' | 'failed'

const statusTabs = [
  { value: 'all', label: 'All Assessments' },
  { value: 'running', label: 'Running' },
  { value: 'queued', label: 'Queued' },
  { value: 'completed', label: 'Completed' },
  { value: 'failed', label: 'Failed' },
] as const satisfies readonly { value: StatusFilter; label: string }[]

/** Assessment engines in the v0.1.0 scope (SYSTEM_ARCHITECTURE.md §7.2). */
const typeOptions = [
  { value: '', label: 'All Types' },
  { value: 'dns', label: 'DNS analysis' },
  { value: 'subdomains', label: 'Subdomain discovery' },
  { value: 'tcp', label: 'TCP port assessment' },
  { value: 'tls', label: 'TLS assessment' },
] as const

const columns: readonly DataTableColumn<never>[] = [
  { key: 'assessment', header: 'Assessment', className: 'w-[25%]' },
  { key: 'target', header: 'Target (Asset)' },
  { key: 'type', header: 'Type' },
  { key: 'status', header: 'Status' },
  { key: 'progress', header: 'Progress' },
  { key: 'started', header: 'Started' },
  { key: 'actions', header: <span className="sr-only">Actions</span>, className: 'w-22.5' },
]

export function AssessmentsPage() {
  const [status, setStatus] = useState<StatusFilter>('all')
  const [view, setView] = useState<ViewMode>('list')

  return (
    <PageContainer
      title="Assessments"
      description="Create, run and manage security assessments for your assets."
      actions={
        <Button disabled title={notAvailableYet}>
          <PlusIcon className="size-5.5" />
          New Assessment
        </Button>
      }
    >
      <section
        aria-label="Assessment totals"
        className="grid gap-5.5 sm:grid-cols-2 lg:grid-cols-3 stats5:grid-cols-5"
      >
        <StatCard compact label="Total Assessments" value={null} icon={TargetIcon} tone="blue" />
        <StatCard compact label="Completed" value={null} icon={CheckCircleIcon} tone="green" />
        <StatCard compact label="Running" value={null} icon={PlayIcon} tone="blue" />
        <StatCard compact label="Queued" value={null} icon={ClockIcon} tone="violet" />
        <StatCard compact label="Failed" value={null} icon={XCircleIcon} tone="red" />
      </section>

      <FilterTabs
        label="Assessment status"
        options={statusTabs}
        value={status}
        onChange={setStatus}
      />

      <div className="flex flex-wrap items-end gap-5.5">
        <SearchField
          label="Search assessments"
          placeholder="Search assessments..."
          disabled
          className="w-full sm:w-86.5"
        />
        <Select label="Filter by target" options={[{ value: '', label: 'All Targets' }]} disabled />
        <Select label="Filter by type" options={typeOptions} disabled />
        <div className="ml-auto">
          <ViewToggle value={view} onChange={setView} disabled />
        </div>
      </div>

      <Card flush className="overflow-hidden">
        <DataTable<never>
          caption="Assessments"
          columns={columns}
          rows={[]}
          getRowKey={() => ''}
          empty={
            <EmptyState
              icon={AssessmentIcon}
              title="No assessments yet"
              description="Assessments run non-destructive checks against authorized assets. Targets are checked against your approved scope again when an assessment runs."
            />
          }
        />
        <ResultsFooter shown={0} total={0} noun="assessments" />
      </Card>
    </PageContainer>
  )
}
