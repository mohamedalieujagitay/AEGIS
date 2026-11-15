import {
  useId,
  useRef,
  useState,
  type ComponentType,
  type KeyboardEvent,
  type ReactNode,
} from 'react'
import { Link } from 'react-router'
import { paths } from '../../../app/router/paths'
import {
  BellIcon,
  CheckIcon,
  CrownIcon,
  FileIcon,
  GlobeIcon,
  LayersIcon,
  LinkIcon,
  ResetIcon,
  SaveIcon,
  ShieldCheckIcon,
  ShieldLogo,
  UsersIcon,
} from '../../../components/icons/icons'
import { PageContainer } from '../../../components/layout/PageContainer'
import {
  Badge,
  Button,
  EmptyState,
  Input,
  Select,
  buttonStyles,
  fieldClasses,
} from '../../../components/ui'
import { notAvailableYet } from '../../../lib/availability'
import { cx } from '../../../lib/cx'

type TabId = 'workspace' | 'members' | 'security' | 'integrations' | 'notifications' | 'audit'

const tabs: readonly { id: TabId; label: string; icon: ComponentType<{ className?: string }> }[] = [
  { id: 'workspace', label: 'Workspace', icon: LayersIcon },
  { id: 'members', label: 'Members', icon: UsersIcon },
  { id: 'security', label: 'Security', icon: ShieldCheckIcon },
  { id: 'integrations', label: 'Integrations', icon: LinkIcon },
  { id: 'notifications', label: 'Notifications', icon: BellIcon },
  { id: 'audit', label: 'Audit & Logs', icon: FileIcon },
]

const panelClasses =
  'rounded-card border border-line bg-linear-to-b from-surface-raised to-surface p-6'

function PanelHeader({
  icon: HeaderIcon,
  title,
  description,
  extra,
}: {
  icon: ComponentType<{ className?: string }>
  title: string
  description?: string
  extra?: ReactNode
}) {
  return (
    <header className="mb-5.5 flex items-center gap-4">
      <span className="grid size-11.5 shrink-0 place-items-center rounded-xl bg-chart-gray/14 text-fg">
        <HeaderIcon className="size-6.5" />
      </span>
      <div className="flex-1">
        <h2 className="text-[1.3125rem] font-bold text-fg-heading">{title}</h2>
        {description && <p className="mt-0.5 text-body text-fg-muted">{description}</p>}
      </div>
      {extra}
    </header>
  )
}

function SettingRow({
  title,
  description,
  children,
}: {
  title: string
  description: string
  children: ReactNode
}) {
  return (
    <li className="flex items-center gap-4 border-b border-line-soft py-4 last:border-b-0">
      <div className="flex flex-1 flex-col gap-0.75">
        <strong className="font-semibold text-fg-heading">{title}</strong>
        <small className="text-sm text-fg-muted">{description}</small>
      </div>
      {children}
    </li>
  )
}

function WorkspacePanel() {
  return (
    <div className="grid items-start gap-6 split:grid-cols-[minmax(0,1.75fr)_minmax(300px,1fr)]">
      <section className={panelClasses} aria-labelledby="ws-settings-title">
        <PanelHeader
          icon={LayersIcon}
          title="Workspace Settings"
          description="Manage your workspace information and basic configuration."
        />
        <span id="ws-settings-title" className="sr-only">
          Workspace Settings
        </span>
        <p className="mb-5 rounded-control border border-chart-blue/25 bg-chart-blue/8 p-3.5 text-sm text-fg-muted">
          Workspace settings become available after sign-in.
        </p>
        <form className="flex flex-col gap-5" onSubmit={(event) => event.preventDefault()}>
          <div className="grid gap-3.5 sm:grid-cols-2">
            <Input label="Workspace Name" disabled />
            <Input label="Workspace Slug" hint="Used in URLs and API endpoints." disabled />
          </div>
          <label className="flex flex-col gap-1.5">
            <span className="text-sm font-medium text-fg-muted">Description</span>
            <textarea rows={3} disabled className={cx(fieldClasses, 'h-auto min-h-21 py-3')} />
          </label>
          <div className="flex items-center gap-5">
            <div className="grid size-21 place-items-center rounded-xl border border-line-strong bg-canvas">
              <ShieldLogo className="h-11 w-10" />
            </div>
            <div className="flex flex-col gap-1">
              <strong className="text-fg-heading">Workspace Logo</strong>
              <small className="text-sm text-fg-muted">PNG, JPG or SVG. Max 2 MB.</small>
              <div className="mt-2 flex gap-2.5">
                <Button variant="secondary" size="sm" disabled title={notAvailableYet}>
                  Change Logo
                </Button>
                <Button variant="danger" size="sm" disabled title={notAvailableYet}>
                  Remove
                </Button>
              </div>
            </div>
          </div>
          <div className="grid gap-3.5 border-t border-line-soft pt-5 sm:grid-cols-2">
            <Select
              label="Default Timezone"
              visibleLabel
              icon={GlobeIcon}
              options={[{ value: '', label: 'Not set' }]}
              disabled
            />
            <Select
              label="Default Report Format"
              visibleLabel
              options={[
                { value: 'pdf', label: 'PDF' },
                { value: 'json', label: 'JSON' },
              ]}
              disabled
            />
          </div>
          <div className="flex gap-3.5">
            <Button type="submit" disabled title={notAvailableYet}>
              <SaveIcon className="size-5.5" />
              Save Changes
            </Button>
            <Button type="button" variant="secondary" disabled title={notAvailableYet}>
              <ResetIcon className="size-5.5" />
              Reset
            </Button>
          </div>
        </form>
      </section>

      <div className="flex flex-col gap-5.5">
        <section className={panelClasses} aria-label="Workspace Overview">
          <PanelHeader icon={FileIcon} title="Workspace Overview" />
          <dl>
            {[
              'Workspace ID',
              'Created',
              'Owner',
              'Members',
              'Assets',
              'Assessments',
              'Findings',
            ].map((term) => (
              <div
                key={term}
                className="flex items-center justify-between border-b border-line-soft py-2.25 text-body last:border-b-0"
              >
                <dt className="text-fg">{term}</dt>
                <dd className="text-fg-muted">
                  <span aria-hidden="true">—</span>
                  <span className="sr-only">Not available</span>
                </dd>
              </div>
            ))}
          </dl>
        </section>

        <section className={panelClasses} aria-label="Workspace Plan">
          <PanelHeader
            icon={CrownIcon}
            title="Workspace Plan"
            extra={<Badge tone="info">Open Source</Badge>}
          />
          <p className="mb-3 text-fg">Self-hosted deployment with full access to AEGIS features.</p>
          <ul>
            {[
              'Unlimited assets',
              'Unlimited assessments',
              'Full reporting (PDF, JSON)',
              'All core features',
            ].map((item) => (
              <li
                key={item}
                className="flex items-center gap-3.5 border-b border-line-soft py-3 last:border-b-0"
              >
                <span className="grid size-7 shrink-0 place-items-center rounded-full bg-chart-green/18 text-success">
                  <CheckIcon className="size-4" />
                </span>
                {item}
              </li>
            ))}
          </ul>
        </section>
      </div>
    </div>
  )
}

function MembersPanel() {
  return (
    <section className={cx(panelClasses, 'max-w-215')} aria-label="Members">
      <PanelHeader
        icon={UsersIcon}
        title="Members"
        description="People with access to this workspace."
      />
      <EmptyState
        icon={UsersIcon}
        title="No members yet"
        description="Existing users can be invited after sign-in, with one of four roles: Owner, Admin, Analyst or Viewer."
      />
    </section>
  )
}

function SecurityPanel() {
  return (
    <section className={cx(panelClasses, 'max-w-215')} aria-label="Security">
      <PanelHeader
        icon={ShieldCheckIcon}
        title="Security"
        description="Authentication and access controls."
      />
      <ul>
        <SettingRow
          title="Only assess authorized assets"
          description="Always enforced. Targets must be inside a verified or attested scope before any assessment can run."
        >
          <Badge tone="success">Always on</Badge>
        </SettingRow>
        <SettingRow
          title="Session expiration"
          description="Sign users out after a period of inactivity. Configurable once authentication is available."
        >
          <Badge tone="neutral">Not available yet</Badge>
        </SettingRow>
        <SettingRow
          title="Login rate limiting"
          description="Limit repeated sign-in attempts. Part of the authentication system."
        >
          <Badge tone="neutral">Not available yet</Badge>
        </SettingRow>
      </ul>
    </section>
  )
}

function IntegrationsPanel() {
  return (
    <section className={cx(panelClasses, 'max-w-215')} aria-label="Integrations">
      <PanelHeader
        icon={LinkIcon}
        title="Integrations"
        description="Connect AEGIS to external services."
      />
      <EmptyState
        icon={LinkIcon}
        title="No integrations available yet"
        description="Third-party lookups such as certificate transparency are configured by the instance administrator and are disabled by default."
      />
    </section>
  )
}

function NotificationsPanel() {
  return (
    <section className={cx(panelClasses, 'max-w-215')} aria-label="Notifications">
      <PanelHeader
        icon={BellIcon}
        title="Notifications"
        description="Choose which events notify you."
      />
      <EmptyState
        icon={BellIcon}
        title="Notifications are not available yet"
        description="In-app and email notifications are planned for continuous monitoring."
      />
    </section>
  )
}

function AuditPanel() {
  return (
    <section className={cx(panelClasses, 'max-w-215')} aria-label="Audit and logs">
      <PanelHeader
        icon={FileIcon}
        title="Audit & Logs"
        description="Every security-relevant action is recorded in the audit log."
      />
      <ul>
        <SettingRow
          title="Audit log"
          description="Browse, search and filter recorded events in Activity."
        >
          <Link to={paths.activity} className={buttonStyles({ variant: 'secondary', size: 'sm' })}>
            Open Activity
          </Link>
        </SettingRow>
        <SettingRow title="Log retention" description="How long audit events are kept.">
          <Badge tone="neutral">Not available yet</Badge>
        </SettingRow>
      </ul>
    </section>
  )
}

const panels: Record<TabId, () => ReactNode> = {
  workspace: WorkspacePanel,
  members: MembersPanel,
  security: SecurityPanel,
  integrations: IntegrationsPanel,
  notifications: NotificationsPanel,
  audit: AuditPanel,
}

export function SettingsPage() {
  const [active, setActive] = useState<TabId>('workspace')
  const baseId = useId()
  const tabRefs = useRef<Partial<Record<TabId, HTMLButtonElement | null>>>({})
  const Panel = panels[active]

  // Arrow keys, Home and End move between tabs (WAI-ARIA tabs pattern).
  function handleKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    const index = tabs.findIndex((tab) => tab.id === active)
    const last = tabs.length - 1
    const nextIndex =
      event.key === 'ArrowRight'
        ? (index + 1) % tabs.length
        : event.key === 'ArrowLeft'
          ? (index - 1 + tabs.length) % tabs.length
          : event.key === 'Home'
            ? 0
            : event.key === 'End'
              ? last
              : null
    const next = nextIndex === null ? undefined : tabs[nextIndex]
    if (next) {
      event.preventDefault()
      setActive(next.id)
      tabRefs.current[next.id]?.focus()
    }
  }

  return (
    <PageContainer
      title="Settings"
      description="Manage your workspace, users, security and platform preferences."
    >
      <div
        role="tablist"
        tabIndex={-1}
        aria-label="Settings sections"
        onKeyDown={handleKeyDown}
        className="-mb-2.5 flex gap-1.5 overflow-x-auto"
      >
        {tabs.map(({ id, label, icon: TabIcon }) => {
          const selected = id === active
          return (
            <button
              key={id}
              ref={(element) => {
                tabRefs.current[id] = element
              }}
              type="button"
              role="tab"
              id={`${baseId}-tab-${id}`}
              aria-selected={selected}
              aria-controls={`${baseId}-panel`}
              tabIndex={selected ? 0 : -1}
              onClick={() => setActive(id)}
              className={cx(
                'mb-2.5 inline-flex items-center gap-2.25 rounded-[9px] px-4.5 py-2.5 text-body whitespace-nowrap',
                'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus',
                selected
                  ? 'bg-primary font-medium text-primary-fg ring-1 ring-fg-heading/10 ring-inset'
                  : 'text-fg hover:text-fg-heading',
              )}
            >
              <TabIcon className="size-5.5" />
              {label}
            </button>
          )
        })}
      </div>

      <div
        role="tabpanel"
        id={`${baseId}-panel`}
        aria-labelledby={`${baseId}-tab-${active}`}
        tabIndex={0}
        className="focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-focus"
      >
        <Panel />
      </div>
    </PageContainer>
  )
}
