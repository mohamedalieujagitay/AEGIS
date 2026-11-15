/** Colour tones for data display. Each maps to design tokens only. */
export type DataTone = 'blue' | 'violet' | 'orange' | 'red' | 'green' | 'yellow' | 'gray' | 'indigo'

/** Icon colour plus a tinted background, as used by stat icons and feed icons. */
export const toneSurfaceClasses: Record<DataTone, string> = {
  blue: 'bg-chart-blue/16 text-chart-blue',
  violet: 'bg-chart-violet/18 text-chart-violet',
  orange: 'bg-chart-orange/16 text-chart-orange',
  red: 'bg-chart-red/16 text-chart-red',
  green: 'bg-chart-green/16 text-chart-green',
  yellow: 'bg-chart-yellow/16 text-chart-yellow',
  gray: 'bg-chart-gray/16 text-chart-gray',
  indigo: 'bg-violet/18 text-violet',
}

/** Graphic colour only (for sparklines). */
export const toneGraphicClasses: Record<DataTone, string> = {
  blue: 'text-chart-blue',
  violet: 'text-chart-violet',
  orange: 'text-chart-orange',
  red: 'text-chart-red',
  green: 'text-chart-green',
  yellow: 'text-chart-yellow',
  gray: 'text-chart-gray',
  indigo: 'text-violet',
}

/** Colours usable in charts, referenced as CSS custom properties. */
export type ChartColor =
  | 'severity-critical'
  | 'severity-high'
  | 'severity-medium'
  | 'severity-low'
  | 'severity-info'
  | 'chart-blue'
  | 'chart-violet'
  | 'chart-green'

export function chartColorVar(color: ChartColor): string {
  return `var(--color-${color})`
}
