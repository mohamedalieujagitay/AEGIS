import { ApiError } from '../../lib/api'

/** A message for the user, from an error thrown by the API client. */
export function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 429 && error.retryAfter) {
      return `${error.message} You can try again in about ${formatSeconds(error.retryAfter)}.`
    }
    return error.message
  }
  return 'Something went wrong. Try again.'
}

function formatSeconds(seconds: number): string {
  if (seconds < 60) {
    return `${seconds} second${seconds === 1 ? '' : 's'}`
  }
  const minutes = Math.ceil(seconds / 60)
  return `${minutes} minute${minutes === 1 ? '' : 's'}`
}

/** Validation messages by request field, for example `{ email: '...' }`. */
export function fieldErrors(error: unknown): Record<string, string> {
  const result: Record<string, string> = {}
  if (error instanceof ApiError) {
    for (const detail of error.details) {
      const field = detail.location[detail.location.length - 1]
      if (detail.location[0] === 'body' && typeof field === 'string' && !(field in result)) {
        result[field] = detail.message
      }
    }
  }
  return result
}

/** Client-side password checks, mirroring the server's policy (DECISIONS.md D-063). */
export const PASSWORD_MIN_LENGTH = 12
export const PASSWORD_MAX_LENGTH = 128

export function passwordProblem(password: string, confirmation: string): string | undefined {
  if (password.length < PASSWORD_MIN_LENGTH) {
    return `Use at least ${PASSWORD_MIN_LENGTH} characters.`
  }
  if (password.length > PASSWORD_MAX_LENGTH) {
    return `Use at most ${PASSWORD_MAX_LENGTH} characters.`
  }
  if (password !== confirmation) {
    return 'The passwords do not match.'
  }
  return undefined
}
