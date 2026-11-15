import { useId, type ComponentPropsWithRef } from 'react'
import { cx } from '../../lib/cx'
import { fieldClasses } from './fieldStyles'

export interface InputProps extends Omit<ComponentPropsWithRef<'input'>, 'children'> {
  /** Visible label. Required so that every input has an accessible name. */
  label: string
  /** Optional help text shown below the input. */
  hint?: string
  /** Validation message. When present, the input is marked invalid. */
  error?: string
}

export function Input({ label, hint, error, id, className, ...props }: InputProps) {
  const generatedId = useId()
  const inputId = id ?? generatedId
  const hintId = hint ? `${inputId}-hint` : undefined
  const errorId = error ? `${inputId}-error` : undefined
  const describedBy = [hintId, errorId].filter(Boolean).join(' ') || undefined

  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={inputId} className="text-sm font-medium text-fg-muted">
        {label}
      </label>
      <input
        id={inputId}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy}
        className={cx(fieldClasses, error && 'border-chart-red', className)}
        {...props}
      />
      {hint && (
        <p id={hintId} className="text-sm text-fg-muted">
          {hint}
        </p>
      )}
      {error && (
        <p id={errorId} className="text-sm text-danger">
          {error}
        </p>
      )}
    </div>
  )
}
