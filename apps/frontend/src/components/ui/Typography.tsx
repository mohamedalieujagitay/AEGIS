import type { ComponentPropsWithRef } from 'react'
import { cx } from '../../lib/cx'

export type HeadingLevel = 1 | 2 | 3
export type HeadingSize = 'lg' | 'md' | 'sm'

const headingSizeClasses: Record<HeadingSize, string> = {
  lg: 'text-display font-extrabold tracking-tight',
  md: 'text-title font-bold',
  sm: 'text-body font-semibold',
}

const defaultSizeForLevel: Record<HeadingLevel, HeadingSize> = {
  1: 'lg',
  2: 'md',
  3: 'sm',
}

export interface HeadingProps extends ComponentPropsWithRef<'h1'> {
  /** Semantic heading level. Choose it from the document outline, not the look. */
  level: HeadingLevel
  /** Visual size. Defaults to the size matching the level. */
  size?: HeadingSize
}

export function Heading({ level, size, className, ...props }: HeadingProps) {
  const Element = `h${level}` as const
  return (
    <Element
      className={cx(
        'text-fg-heading',
        headingSizeClasses[size ?? defaultSizeForLevel[level]],
        className,
      )}
      {...props}
    />
  )
}

export type TextTone = 'default' | 'muted'

const textToneClasses: Record<TextTone, string> = {
  default: 'text-fg',
  muted: 'text-fg-muted',
}

export interface TextProps extends ComponentPropsWithRef<'p'> {
  tone?: TextTone
}

export function Text({ tone = 'default', className, ...props }: TextProps) {
  return <p className={cx('text-body', textToneClasses[tone], className)} {...props} />
}
