import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { Input } from './Input'

describe('Input', () => {
  it('is labelled by its visible label', () => {
    render(<Input label="Asset name" />)
    expect(screen.getByRole('textbox', { name: 'Asset name' })).toBeInTheDocument()
  })

  it('is described by its hint and is not marked invalid without an error', () => {
    render(<Input label="Asset name" hint="Use the fully qualified domain name." />)
    const input = screen.getByRole('textbox', { name: 'Asset name' })

    expect(input).toHaveAccessibleDescription('Use the fully qualified domain name.')
    expect(input).not.toHaveAttribute('aria-invalid')
  })

  it('announces the error together with the hint and is marked invalid', () => {
    render(
      <Input
        label="Asset name"
        hint="Use the fully qualified domain name."
        error="Enter a valid domain name."
      />,
    )
    const input = screen.getByRole('textbox', { name: 'Asset name' })

    expect(input).toBeInvalid()
    expect(input).toHaveAccessibleDescription(
      'Use the fully qualified domain name. Enter a valid domain name.',
    )
  })

  it('uses an explicit id for the label and description references', () => {
    render(<Input id="asset-name" label="Asset name" error="Required." />)
    const input = screen.getByRole('textbox', { name: 'Asset name' })

    expect(input).toHaveAttribute('id', 'asset-name')
    expect(input).toHaveAttribute('aria-describedby', 'asset-name-error')
  })

  it('accepts typed input', async () => {
    const user = userEvent.setup()
    render(<Input label="Asset name" />)
    const input = screen.getByRole('textbox', { name: 'Asset name' })

    await user.type(input, 'example.com')

    expect(input).toHaveValue('example.com')
  })
})
