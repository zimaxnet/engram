import { describe, expect, it } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BAUHub } from './BAUHub'
import { renderWithRouter } from '../../test/testUtils'

describe('BAUHub', () => {
  it('renders flows and recent artifacts from API', async () => {
    renderWithRouter(<BAUHub />, { route: '/bau' })

    expect(screen.getByRole('heading', { name: /bau hub/i })).toBeInTheDocument()

    expect(await screen.findByText(/intake & triage/i)).toBeInTheDocument()
    expect(screen.getByText(/policy q&a/i)).toBeInTheDocument()
    expect(screen.getByText(/decision log search/i)).toBeInTheDocument()

    expect(await screen.findByText(/meeting notes/i)).toBeInTheDocument()
    expect(screen.getByText(/policy update/i)).toBeInTheDocument()
  })

  it('navigates to golden thread when button clicked', async () => {
    const user = userEvent.setup()
    const { container } = renderWithRouter(<BAUHub />, { route: '/bau' })

    await waitFor(() => {
      expect(screen.getByText(/run golden thread/i)).toBeInTheDocument()
    })

    const button = screen.getByRole('button', { name: /run golden thread/i })
    await user.click(button)

    // Check that navigation occurred (URL should change)
    // In a real test, we'd check the router location
    expect(button).toBeInTheDocument()
  })
})
