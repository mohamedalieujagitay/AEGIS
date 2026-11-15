import type { ComponentPropsWithRef } from 'react'
import { cx } from '../../lib/cx'
import { buttonStyles, type ButtonStyleOptions } from './buttonStyles'

export interface ButtonProps extends ComponentPropsWithRef<'button'>, ButtonStyleOptions {}

/** Button that defaults to type="button" so it never submits a form by accident. */
export function Button({ variant, size, type = 'button', className, ...props }: ButtonProps) {
  return (
    <button type={type} className={cx(buttonStyles({ variant, size }), className)} {...props} />
  )
}
