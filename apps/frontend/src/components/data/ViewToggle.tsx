import { cx } from '../../lib/cx'
import { GridIcon, ListIcon } from '../icons/icons'

export type ViewMode = 'list' | 'grid'

export interface ViewToggleProps {
  value: ViewMode
  onChange: (value: ViewMode) => void
  disabled?: boolean
}

const modes = [
  { value: 'list', label: 'List view', icon: ListIcon },
  { value: 'grid', label: 'Grid view', icon: GridIcon },
] as const

/** List or grid switch for collection pages. */
export function ViewToggle({ value, onChange, disabled = false }: ViewToggleProps) {
  return (
    <fieldset className="flex min-w-0 rounded-control border border-line-strong bg-canvas p-0.75">
      <legend className="sr-only">View</legend>
      {modes.map(({ value: mode, label, icon: ModeIcon }) => {
        const active = value === mode
        return (
          <button
            key={mode}
            type="button"
            aria-pressed={active}
            disabled={disabled}
            onClick={() => onChange(mode)}
            className={cx(
              'grid h-8.5 w-12 place-items-center rounded-lg',
              'focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-focus',
              'disabled:cursor-not-allowed disabled:opacity-60',
              active ? 'bg-toggle-active text-fg-heading' : 'text-fg-muted',
            )}
          >
            <ModeIcon className="size-5.5" />
            <span className="sr-only">{label}</span>
          </button>
        )
      })}
    </fieldset>
  )
}
