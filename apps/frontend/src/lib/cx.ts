type ClassValue = string | false | null | undefined

/**
 * Joins class names, skipping falsy values.
 *
 * This does not resolve conflicting Tailwind utilities. Components apply
 * caller-supplied classes last, so callers should add classes rather than
 * try to override a component's built-in styles.
 */
export function cx(...classes: ClassValue[]): string {
  return classes.filter(Boolean).join(' ')
}
