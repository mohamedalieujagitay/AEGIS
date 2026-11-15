import { cx } from '../../lib/cx'

export interface FilterTabsProps<Value extends string> {
  /** Accessible name of the group, for example "Assessment status". */
  label: string
  options: readonly { value: Value; label: string }[]
  value: Value
  onChange: (value: Value) => void
}

/**
 * Underlined status filters above a list. They filter the list below rather
 * than switching panels, so they are toggle buttons (aria-pressed), not tabs.
 */
export function FilterTabs<Value extends string>({
  label,
  options,
  value,
  onChange,
}: FilterTabsProps<Value>) {
  return (
    <fieldset className="-my-1.5 flex min-w-0 gap-2 overflow-x-auto border-b border-line-soft">
      <legend className="sr-only">{label}</legend>
      {options.map((option) => {
        const active = option.value === value
        return (
          <button
            key={option.value}
            type="button"
            aria-pressed={active}
            onClick={() => onChange(option.value)}
            className={cx(
              '-mb-px rounded-t-md border-b-3 px-4 py-3.5 text-body whitespace-nowrap',
              'focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-focus',
              active
                ? 'border-chart-blue font-medium text-info'
                : 'border-transparent text-fg hover:text-fg-heading',
            )}
          >
            {option.label}
          </button>
        )
      })}
    </fieldset>
  )
}
