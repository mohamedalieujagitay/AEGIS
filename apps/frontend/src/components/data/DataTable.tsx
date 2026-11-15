import type { ReactNode } from 'react'
import { cx } from '../../lib/cx'

export interface DataTableColumn<Row> {
  key: string
  header: ReactNode
  /** Renders the cell. Optional while a page has no data to show yet. */
  cell?: (row: Row) => ReactNode
  /** Classes for both the header and data cells of this column, e.g. a width. */
  className?: string
}

export interface DataTableProps<Row> {
  /** Describes the table for assistive technology. Visually hidden. */
  caption: string
  columns: readonly DataTableColumn<Row>[]
  rows: readonly Row[]
  getRowKey: (row: Row) => string
  /** Shown in a single full-width row when there are no rows. */
  empty: ReactNode
  /** Compact rows for summary tables (Overview); full rows for list pages. */
  density?: 'compact' | 'comfortable'
  /** Minimum table width before it scrolls horizontally. */
  minWidthClass?: string
}

/**
 * Accessible data table with column headers and a caption. The header row is
 * always shown, so the structure of the data is visible even when empty.
 */
export function DataTable<Row>({
  caption,
  columns,
  rows,
  getRowKey,
  empty,
  density = 'comfortable',
  minWidthClass = 'min-w-[60rem]',
}: DataTableProps<Row>) {
  const compact = density === 'compact'

  return (
    <div className="overflow-x-auto">
      <table
        className={cx(
          'w-full border-collapse text-left',
          compact ? 'text-body' : cx('text-body', minWidthClass),
        )}
      >
        <caption className="sr-only">{caption}</caption>
        <thead>
          <tr className="border-b border-line">
            {columns.map((column) => (
              <th
                key={column.key}
                scope="col"
                className={cx(
                  'font-medium',
                  compact ? 'pb-3 text-sm text-fg-muted' : 'h-12 px-2 text-fg first:pl-5.5',
                  column.className,
                )}
              >
                {column.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="px-4 text-center text-fg-muted">
                {empty}
              </td>
            </tr>
          ) : (
            rows.map((row) => (
              <tr
                key={getRowKey(row)}
                className="border-b border-line-soft last:border-b-0 hover:bg-chart-blue/5"
              >
                {columns.map((column) => (
                  <td
                    key={column.key}
                    className={cx(
                      'text-fg',
                      compact ? 'h-11.25' : 'h-15.5 px-2 first:pl-5.5',
                      column.className,
                    )}
                  >
                    {column.cell?.(row)}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  )
}
