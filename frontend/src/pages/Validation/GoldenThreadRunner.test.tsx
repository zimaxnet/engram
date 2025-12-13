import { describe, expect, it } from 'vitest'
import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { GoldenThreadRunner } from './GoldenThreadRunner'
import { renderWithRouter } from '../../test/testUtils'

describe('GoldenThreadRunner', () => {
  it('renders and can run the suite (mock)', async () => {
    renderWithRouter(<GoldenThreadRunner />, { route: '/validation/golden-thread' })

    expect(screen.getByRole('heading', { name: /golden thread/i })).toBeInTheDocument()

    const runButton = screen.getByRole('button', { name: /run suite/i })
    await userEvent.click(runButton)

    // After run completes, PASS should be visible.
    expect(await screen.findByText('PASS')).toBeInTheDocument()

    // Evidence IDs should appear
    expect(screen.getByText('Workflow ID')).toBeInTheDocument()
    expect(screen.getByText('Session ID')).toBeInTheDocument()
  })
})
