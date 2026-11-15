import { useId } from 'react'

export interface TrendPoint {
  /** Axis label, for example "Nov 13". */
  label: string
  value: number
}

export interface TrendChartProps {
  points: readonly TrendPoint[]
  /** Describes the series, for example "Open findings per day". */
  description: string
  /** Shown when there are fewer than two points. */
  emptyText: string
}

const WIDTH = 600
const HEIGHT = 160
const TICKS = 4
const MAX_X_LABELS = 8

function niceMaximum(value: number): number {
  if (value <= 0) {
    return TICKS
  }
  const magnitude = 10 ** Math.floor(Math.log10(value))
  return Math.ceil(value / magnitude) * magnitude
}

/**
 * Line and area chart for a single series.
 *
 * Accessibility: the drawing is hidden from assistive technology and the
 * same data is provided in a visually hidden table.
 */
export function TrendChart({ points, description, emptyText }: TrendChartProps) {
  const gradientId = useId()

  if (points.length < 2) {
    return (
      <div className="mt-3.5 flex h-50 items-center justify-center rounded-control border border-dashed border-line text-body text-fg-muted">
        {emptyText}
      </div>
    )
  }

  const max = niceMaximum(Math.max(...points.map((p) => p.value)))
  const ticks = Array.from({ length: TICKS + 1 }, (_, i) => Math.round((max / TICKS) * (TICKS - i)))
  const coordinates = points.map((point, index) => ({
    x: (index / (points.length - 1)) * WIDTH,
    y: HEIGHT - (point.value / max) * HEIGHT,
  }))
  const line = coordinates.map(({ x, y }) => `${x.toFixed(1)},${y.toFixed(1)}`).join(' ')
  const labelStep = Math.max(1, Math.ceil(points.length / MAX_X_LABELS))
  const xLabels = points.filter((_, index) => index % labelStep === 0)

  return (
    <figure className="mt-3.5 grid grid-cols-[38px_1fr] gap-x-2">
      <ul
        aria-hidden="true"
        className="flex h-40 flex-col justify-between text-right text-sm leading-none text-fg-muted"
      >
        {ticks.map((tick) => (
          <li key={tick}>{tick}</li>
        ))}
      </ul>
      <div className="relative mr-2 h-40" aria-hidden="true">
        <svg
          viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
          preserveAspectRatio="none"
          className="absolute inset-0 size-full overflow-visible text-chart-blue"
          focusable="false"
        >
          <defs>
            <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0" stopColor="currentColor" stopOpacity="0.45" />
              <stop offset="1" stopColor="currentColor" stopOpacity="0.02" />
            </linearGradient>
          </defs>
          <g stroke="var(--color-chart-grid)" strokeWidth="1">
            {ticks.map((_, i) => {
              const y = (HEIGHT / TICKS) * i
              return (
                <line key={y} x1="0" x2={WIDTH} y1={y} y2={y} vectorEffect="non-scaling-stroke" />
              )
            })}
          </g>
          <polygon points={`0,${HEIGHT} ${line} ${WIDTH},${HEIGHT}`} fill={`url(#${gradientId})`} />
          <polyline
            points={line}
            fill="none"
            stroke="currentColor"
            strokeWidth="2.5"
            strokeLinejoin="round"
            vectorEffect="non-scaling-stroke"
          />
        </svg>
        {coordinates.map(({ x, y }, index) => (
          <span
            key={points[index]?.label ?? index}
            className="absolute size-2.25 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-canvas bg-chart-blue ring-1 ring-chart-blue/60"
            style={{ left: `${(x / WIDTH) * 100}%`, top: `${(y / HEIGHT) * 100}%` }}
          />
        ))}
      </div>
      <ul
        aria-hidden="true"
        className="col-start-2 mt-3 flex justify-between text-sm text-fg-muted"
      >
        {xLabels.map((point) => (
          <li key={point.label}>{point.label}</li>
        ))}
      </ul>

      <table className="sr-only">
        <caption>{description}</caption>
        <thead>
          <tr>
            <th scope="col">Date</th>
            <th scope="col">Value</th>
          </tr>
        </thead>
        <tbody>
          {points.map((point) => (
            <tr key={point.label}>
              <td>{point.label}</td>
              <td>{point.value}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </figure>
  )
}
