import { useState, type FormEvent } from 'react'
import { Button, Input } from '../../../components/ui'
import { ApiError } from '../../../lib/api'
import { accountApi } from '../account'
import { errorMessage, fieldErrors, PASSWORD_MIN_LENGTH, passwordProblem } from '../errors'

const SUCCESS =
  'Your password was changed. Other browsers and trusted devices were signed out. This browser stays signed in.'

/**
 * Change the password of the signed-in user. The current password is verified
 * by the server; the new password follows the same policy as registration.
 */
export function PasswordChange() {
  const [current, setCurrent] = useState('')
  const [next, setNext] = useState('')
  const [confirmation, setConfirmation] = useState('')
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [formError, setFormError] = useState<string>()
  const [saved, setSaved] = useState<string>()
  const [saving, setSaving] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSaved(undefined)
    setFormError(undefined)
    const problems: Record<string, string> = {}
    if (current.length === 0) {
      problems['current'] = 'Enter your current password.'
    }
    const newProblem = passwordProblem(next, confirmation)
    if (newProblem !== undefined) {
      problems[newProblem.includes('match') ? 'confirmation' : 'next'] = newProblem
    }
    if (Object.keys(problems).length > 0) {
      setErrors(problems)
      return
    }
    setErrors({})
    setSaving(true)
    try {
      await accountApi.changePassword(current, next)
      setSaved(SUCCESS)
      setCurrent('')
      setNext('')
      setConfirmation('')
    } catch (caught) {
      if (caught instanceof ApiError && caught.code === 'current_password_incorrect') {
        setErrors({ current: caught.message })
      } else if (
        caught instanceof ApiError &&
        (caught.code === 'password_rejected' || caught.code === 'password_unchanged')
      ) {
        setErrors({ next: caught.message })
      } else {
        const byField = fieldErrors(caught)
        if (byField['current_password'] || byField['new_password']) {
          setErrors({
            ...(byField['current_password'] ? { current: byField['current_password'] } : {}),
            ...(byField['new_password'] ? { next: byField['new_password'] } : {}),
          })
        } else {
          setFormError(errorMessage(caught))
        }
      }
      setCurrent('')
    } finally {
      setSaving(false)
    }
  }

  return (
    <form className="flex flex-col gap-4" onSubmit={(event) => void handleSubmit(event)} noValidate>
      <Input
        label="Current password"
        type="password"
        autoComplete="current-password"
        value={current}
        error={errors['current']}
        onChange={(event) => setCurrent(event.target.value)}
      />
      <Input
        label="New password"
        type="password"
        autoComplete="new-password"
        hint={`At least ${PASSWORD_MIN_LENGTH} characters. A passphrase of several words works well.`}
        value={next}
        error={errors['next']}
        onChange={(event) => setNext(event.target.value)}
      />
      <Input
        label="Confirm new password"
        type="password"
        autoComplete="new-password"
        value={confirmation}
        error={errors['confirmation']}
        onChange={(event) => setConfirmation(event.target.value)}
      />
      {formError !== undefined && (
        <p role="alert" className="text-sm text-danger">
          {formError}
        </p>
      )}
      {saved !== undefined && <output className="block text-sm text-success">{saved}</output>}
      <div>
        <Button type="submit" disabled={saving || next.length === 0 || confirmation.length === 0}>
          {saving ? 'Changing password…' : 'Change password'}
        </Button>
      </div>
    </form>
  )
}
