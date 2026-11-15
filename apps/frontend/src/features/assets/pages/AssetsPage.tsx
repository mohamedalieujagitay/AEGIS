import { useState } from 'react'
import { DataTable, type DataTableColumn } from '../../../components/data/DataTable'
import { ResultsFooter } from '../../../components/data/ResultsFooter'
import { StatCard } from '../../../components/data/StatCard'
import { ViewToggle, type ViewMode } from '../../../components/data/ViewToggle'
import {
  CubeIcon,
  DownloadIcon,
  GlobeIcon,
  LayersIcon,
  NetworkIcon,
  PlusIcon,
} from '../../../components/icons/icons'
import { PageContainer } from '../../../components/layout/PageContainer'
import { Button, Card, EmptyState, SearchField, Select } from '../../../components/ui'
import { notAvailableYet } from '../../../lib/availability'

/** Asset types and statuses from PRODUCT_REQUIREMENTS.md FR-ASSET-001 and FR-ASSET-003. */
const typeOptions = [
  { value: '', label: 'All Types' },
  { value: 'domain', label: 'Domain' },
  { value: 'ip_address', label: 'IP address' },
  { value: 'cidr_range', label: 'CIDR range' },
  { value: 'service', label: 'Service' },
] as const

const statusOptions = [
  { value: '', label: 'All Statuses' },
  { value: 'authorized', label: 'Authorized' },
  { value: 'pending', label: 'Pending verification' },
  { value: 'expired', label: 'Authorization expired' },
] as const

const columns: readonly DataTableColumn<never>[] = [
  { key: 'asset', header: 'Asset', className: 'w-[28%]' },
  { key: 'type', header: 'Type' },
  { key: 'scope', header: 'Scope' },
  { key: 'status', header: 'Status' },
  { key: 'added', header: 'Added' },
  { key: 'actions', header: <span className="sr-only">Actions</span>, className: 'w-25' },
]

export function AssetsPage() {
  const [view, setView] = useState<ViewMode>('list')

  return (
    <PageContainer
      title="Assets"
      description="Manage your authorized assets for security assessments."
      actions={
        <>
          <Button variant="secondary" disabled title={notAvailableYet}>
            <DownloadIcon className="size-5.5" />
            Import Assets
          </Button>
          <Button disabled title={notAvailableYet}>
            <PlusIcon className="size-5.5" />
            Add Asset
          </Button>
        </>
      }
    >
      <section aria-label="Asset totals" className="grid gap-6.5 sm:grid-cols-2 stats4:grid-cols-4">
        <StatCard compact label="Total Assets" value={null} icon={CubeIcon} tone="blue" />
        <StatCard compact label="Domains" value={null} icon={GlobeIcon} tone="green" />
        <StatCard compact label="IP Addresses" value={null} icon={LayersIcon} tone="violet" />
        <StatCard compact label="CIDR Ranges" value={null} icon={NetworkIcon} tone="indigo" />
      </section>

      <hr className="-my-0.5 border-line-soft" />

      <div className="flex flex-wrap items-end gap-5.5">
        <SearchField
          label="Search assets"
          placeholder="Search assets..."
          disabled
          className="w-full sm:w-86.5"
        />
        <Select label="Filter by type" options={typeOptions} disabled />
        <Select label="Filter by status" options={statusOptions} disabled />
        <div className="ml-auto">
          <ViewToggle value={view} onChange={setView} disabled />
        </div>
      </div>

      <Card flush className="overflow-hidden">
        <DataTable<never>
          caption="Assets"
          columns={columns}
          rows={[]}
          getRowKey={() => ''}
          empty={
            <EmptyState
              icon={LayersIcon}
              title="No assets yet"
              description="Register the domains, IP addresses and CIDR ranges you are authorized to assess. Only assets verified through DNS, HTTP or administrative attestation can be assessed."
            />
          }
        />
        <ResultsFooter shown={0} total={0} noun="assets" />
      </Card>
    </PageContainer>
  )
}
