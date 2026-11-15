import { useId } from 'react'
import { cx } from '../../lib/cx'

export interface SparklineProps {
  /** Data points in chronological order. At least two are needed to draw a line. */
  values: readonly number[]
  className?: string
}

const WIDTH = 120
const HEIGHT = 50
const PADDING = 4

/**
 * Small decorative trend line. It uses the current text colour, so set the
 * colour with a text-* token class. It is hidden from assistive technology:
 * the value it accompanies must be presented as text.
 */
export function Sparkline({ values, className }: SparklineProps) {
  const gradientId = useId()
  if (values.length < 2) {
    return null
  }

  const min = Math.min(...values)
  const max = Math.max(...values)
  const range = max - min || 1
  const step = WIDTH / (values.length - 1)
  const points = values.map((value, index) => {
    const x = index * step
    const y = HEIGHT - PADDING - ((value - min) / range) * (HEIGHT - PADDING * 2)
    return `${x.toFixed(1)},${y.toFixed(1)}`
  })
  const line = points.join(' ')

  return (
    <svg
      viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
      preserveAspectRatio="none"
      aria-hidden="true"
      focusable="false"
      className={cx('h-12 w-28', className)}
    >
      <defs>
        <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="currentColor" stopOpacity="0.35" />
          <stop offset="1" stopColor="currentColor" stopOpacity="0" />
        </linearGradient>
      </defs>
      <polygon points={`0,${HEIGHT} ${line} ${WIDTH},${HEIGHT}`} fill={`url(#${gradientId})`} />
      <polyline
        points={line}
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinejoin="round"
        vectorEffect="non-scaling-stroke"
      />
    </svg>
  )
}
