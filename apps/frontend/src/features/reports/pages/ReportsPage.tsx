import { useState } from 'react'
import { DataTable, type DataTableColumn } from '../../../components/data/DataTable'
import { FilterTabs } from '../../../components/data/FilterTabs'
import { ResultsFooter } from '../../../components/data/ResultsFooter'
import { StatCard } from '../../../components/data/StatCard'
import {
  CheckCircleIcon,
  ClockIcon,
  FileIcon,
  FilePlusIcon,
  InfoIcon,
  XCircleIcon,
} from '../../../components/icons/icons'
import { PageContainer } from '../../../components/layout/PageContainer'
import { Button, Card, EmptyState, Heading, SearchField, Select } from '../../../components/ui'
import { notAvailableYet } from '../../../lib/availability'

type StatusFilter = 'all' | 'completed' | 'generating' | 'failed'

const statusTabs = [
  { value: 'all', label: 'All Reports' },
  { value: 'completed', label: 'Completed' },
  { value: 'generating', label: 'Generating' },
  { value: 'failed', label: 'Failed' },
] as const satisfies readonly { value: StatusFilter; label: string }[]

/** Report formats from PRODUCT_REQUIREMENTS.md FR-REPORT-001 and FR-REPORT-002. */
const formatOptions = [
  { value: 'pdf', label: 'PDF' },
  { value: 'json', label: 'JSON' },
] as const

const columns: readonly DataTableColumn<never>[] = [
  { key: 'report', header: 'Report', className: 'w-[31%]' },
  { key: 'format', header: 'Format' },
  { key: 'assessment', header: 'Assessment' },
  { key: 'status', header: 'Status' },
  { key: 'generated', header: 'Generated' },
  { key: 'actions', header: <span className="sr-only">Actions</span>, className: 'w-25' },
]

function CreateReportPanel() {
  return (
    <section
      aria-labelledby="create-report-title"
      className="flex flex-col gap-3.5 rounded-card border border-line bg-linear-to-b from-surface-raised to-surface p-5.5"
    >
      <Heading level={2} id="create-report-title">
        Create Report
      </Heading>
      <p className="-mt-2 text-body text-fg-muted">
        Generate a new report from a completed assessment.
      </p>
      <form className="flex flex-col gap-4" onSubmit={(event) => event.preventDefault()}>
        <Select
          label="Assessment"
          visibleLabel
          options={[{ value: '', label: 'No completed assessments' }]}
          disabled
        />
        <Select label="Format" visibleLabel options={formatOptions} disabled />
        <div className="flex gap-2.5 rounded-control border border-chart-blue/25 bg-chart-blue/8 p-3.5 text-sm text-fg-muted">
          <InfoIcon className="mt-0.5 size-5 shrink-0 text-chart-blue" />
          <p>
            Reports include the assessment details, authorized scope, an executive summary, the
            asset inventory, findings with evidence and remediation recommendations. Observed
            results are kept separate from inferred risk.
          </p>
        </div>
        <Button type="submit" disabled title={notAvailableYet} className="w-full">
          <FilePlusIcon className="size-5.5" />
          Generate Report
        </Button>
      </form>
    </section>
  )
}

export function ReportsPage() {
  const [status, setStatus] = useState<StatusFilter>('all')

  return (
    <PageContainer
      title="Reports"
      description="Generate, view and download security reports from completed assessments."
    >
      <section aria-label="Report totals" className="grid gap-5 sm:grid-cols-2 split:grid-cols-4">
        <StatCard compact label="Total Reports" value={null} icon={FileIcon} tone="violet" />
        <StatCard compact label="Completed" value={null} icon={CheckCircleIcon} tone="green" />
        <StatCard compact label="Generating" value={null} icon={ClockIcon} tone="blue" />
        <StatCard compact label="Failed" value={null} icon={XCircleIcon} tone="red" />
      </section>

      <div className="grid items-start gap-5.5 split:grid-cols-[minmax(0,1fr)_340px]">
        <Card flush className="overflow-hidden">
          <div className="px-3">
            <FilterTabs
              label="Report status"
              options={statusTabs}
              value={status}
              onChange={setStatus}
            />
          </div>
          <div className="flex flex-wrap gap-3 p-4">
            <SearchField
              label="Search reports"
              placeholder="Search reports..."
              disabled
              className="min-w-50 flex-1"
            />
            <Select
              label="Filter by format"
              options={[{ value: '', label: 'All Formats' }, ...formatOptions]}
              disabled
            />
          </div>
          <DataTable<never>
            caption="Reports"
            columns={columns}
            rows={[]}
            getRowKey={() => ''}
            minWidthClass="min-w-[45rem]"
            empty={
              <EmptyState
                icon={FileIcon}
                title="No reports yet"
                description="Reports can be generated once an assessment has completed."
              />
            }
          />
          <ResultsFooter shown={0} total={0} noun="reports" />
        </Card>

        <CreateReportPanel />
      </div>
    </PageContainer>
  )
}
