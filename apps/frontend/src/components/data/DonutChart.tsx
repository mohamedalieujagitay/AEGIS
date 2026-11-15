import { chartColorVar, type ChartColor } from './tones'

export interface DonutSegment {
  label: string
  value: number
  color: ChartColor
}

export interface DonutChartProps {
  segments: readonly DonutSegment[]
  /** Label under the total in the centre, for example "Findings". */
  totalLabel: string
  /** Shown when there is no data. */
  emptyText: string
}

const percentFormat = new Intl.NumberFormat(undefined, { style: 'percent' })

/** Running totals as percentages of the total, for example [14, 46, 76, 100]. */
function cumulativePercentages(values: readonly number[], total: number): number[] {
  const result: number[] = []
  let sum = 0
  for (const value of values) {
    sum += value
    result.push((sum / total) * 100)
  }
  return result
}

/**
 * Donut chart with a legend. The drawing is hidden from assistive technology;
 * a visually hidden figure caption summarises the data, and the legend lists
 * every value as text.
 */
export function DonutChart({ segments, totalLabel, emptyText }: DonutChartProps) {
  const total = segments.reduce((sum, segment) => sum + segment.value, 0)
  const isEmpty = total === 0

  const boundaries = isEmpty
    ? []
    : cumulativePercentages(
        segments.map((segment) => segment.value),
        total,
      )
  const stops = segments.map(
    (segment, index) =>
      `${chartColorVar(segment.color)} ${boundaries[index - 1] ?? 0}% ${boundaries[index] ?? 0}%`,
  )
  const background = isEmpty ? 'var(--color-chart-grid)' : `conic-gradient(${stops.join(', ')})`
  const summary = isEmpty
    ? `${totalLabel}: ${emptyText}`
    : `${total} ${totalLabel}: ${segments.map((s) => `${s.label} ${s.value}`).join(', ')}`

  return (
    <figure className="flex flex-1 flex-col items-start gap-6 sm:flex-row sm:items-center sm:gap-8.5 sm:pl-3.5">
      <figcaption className="sr-only">{summary}</figcaption>
      <div
        aria-hidden="true"
        className="relative size-44 shrink-0 rounded-full"
        style={{ background }}
      >
        <div className="absolute inset-8 flex flex-col items-center justify-center rounded-full bg-surface text-center">
          <span className="text-[1.625rem] leading-tight font-bold text-fg-heading">
            {isEmpty ? '—' : total}
          </span>
          <span className="text-body text-fg-muted">{totalLabel}</span>
        </div>
      </div>

      {isEmpty ? (
        <p className="text-body text-fg-muted">{emptyText}</p>
      ) : (
        <ul className="flex w-full max-w-68 flex-col gap-1.5 text-body">
          {segments.map((segment) => (
            <li
              key={segment.label}
              className="grid h-6.5 grid-cols-[18px_1fr_40px_52px] items-center"
            >
              <span
                aria-hidden="true"
                className="size-3.5 rounded-full"
                style={{ background: chartColorVar(segment.color) }}
              />
              <span className="text-fg">{segment.label}</span>
              <span className="text-right font-medium text-fg-heading">{segment.value}</span>
              <span className="text-right text-fg-muted">
                {percentFormat.format(segment.value / total)}
              </span>
            </li>
          ))}
        </ul>
      )}
    </figure>
  )
}
