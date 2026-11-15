import { useState } from 'react'
import { DataTable, type DataTableColumn } from '../../../components/data/DataTable'
import { FilterTabs } from '../../../components/data/FilterTabs'
import { ResultsFooter } from '../../../components/data/ResultsFooter'
import { StatCard } from '../../../components/data/StatCard'
import { ViewToggle, type ViewMode } from '../../../components/data/ViewToggle'
import {
  AlertCircleIcon,
  DownloadIcon,
  FlagIcon,
  InfoIcon,
  ShieldAlertIcon,
  WarningIcon,
} from '../../../components/icons/icons'
import { PageContainer } from '../../../components/layout/PageContainer'
import { Button, Card, EmptyState, SearchField, Select } from '../../../components/ui'
import { notAvailableYet } from '../../../lib/availability'

type StatusFilter = 'all' | 'open' | 'in_progress' | 'resolved'

const statusTabs = [
  { value: 'all', label: 'All Findings' },
  { value: 'open', label: 'Open' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'resolved', label: 'Resolved' },
] as const satisfies readonly { value: StatusFilter; label: string }[]

/** Severities from PRODUCT_REQUIREMENTS.md FR-VULN-002. */
const severityOptions = [
  { value: '', label: 'All Severities' },
  { value: 'critical', label: 'Critical' },
  { value: 'high', label: 'High' },
  { value: 'medium', label: 'Medium' },
  { value: 'low', label: 'Low' },
  { value: 'informational', label: 'Informational' },
] as const

/** Lifecycle statuses from PRODUCT_REQUIREMENTS.md FR-VULN-004. */
const lifecycleOptions = [
  { value: '', label: 'All Statuses' },
  { value: 'open', label: 'Open' },
  { value: 'acknowledged', label: 'Acknowledged' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'resolved', label: 'Resolved' },
  { value: 'accepted_risk', label: 'Accepted Risk' },
  { value: 'false_positive', label: 'False Positive' },
] as const

const columns: readonly DataTableColumn<never>[] = [
  { key: 'finding', header: 'Finding', className: 'w-[27%]' },
  { key: 'severity', header: 'Severity' },
  { key: 'asset', header: 'Asset' },
  { key: 'assessment', header: 'Assessment' },
  { key: 'status', header: 'Status' },
  { key: 'discovered', header: 'Discovered' },
  { key: 'actions', header: <span className="sr-only">Actions</span>, className: 'w-25' },
]

export function FindingsPage() {
  const [status, setStatus] = useState<StatusFilter>('all')
  const [view, setView] = useState<ViewMode>('list')

  return (
    <PageContainer
      title="Findings"
      description="Review, triage and track security findings across your assets."
      actions={
        <Button variant="secondary" disabled title={notAvailableYet}>
          <DownloadIcon className="size-5.5" />
          Export Findings
        </Button>
      }
    >
      <section
        aria-label="Findings by severity"
        className="grid gap-5.5 sm:grid-cols-2 lg:grid-cols-3 stats5:grid-cols-5"
      >
        <StatCard compact label="Total Findings" value={null} icon={WarningIcon} tone="blue" />
        <StatCard compact label="Critical" value={null} icon={ShieldAlertIcon} tone="red" />
        <StatCard compact label="High" value={null} icon={AlertCircleIcon} tone="orange" />
        <StatCard compact label="Medium" value={null} icon={InfoIcon} tone="yellow" />
        <StatCard compact label="Low" value={null} icon={FlagIcon} tone="gray" />
      </section>

      <FilterTabs label="Finding status" options={statusTabs} value={status} onChange={setStatus} />

      <div className="flex flex-wrap items-end gap-5.5">
        <SearchField
          label="Search findings"
          placeholder="Search findings..."
          disabled
          className="w-full sm:w-86.5"
        />
        <Select label="Filter by severity" options={severityOptions} disabled />
        <Select label="Filter by status" options={lifecycleOptions} disabled />
        <Select label="Filter by asset" options={[{ value: '', label: 'All Assets' }]} disabled />
        <div className="ml-auto">
          <ViewToggle value={view} onChange={setView} disabled />
        </div>
      </div>

      <Card flush className="overflow-hidden">
        <DataTable<never>
          caption="Findings"
          columns={columns}
          rows={[]}
          getRowKey={() => ''}
          empty={
            <EmptyState
              icon={WarningIcon}
              title="No findings yet"
              description="Findings are created from assessment results. Each finding keeps its evidence, source and history."
            />
          }
        />
        <ResultsFooter shown={0} total={0} noun="findings" />
      </Card>
    </PageContainer>
  )
}
