import { describe, expect, it } from 'vitest'
import { screen } from '@testing-library/react'
import { BAUHub } from './BAUHub'
import { renderWithRouter } from '../../test/testUtils'

describe('BAUHub', () => {
  it('renders flows and recent artifacts', async () => {
    renderWithRouter(<BAUHub />, { route: '/bau' })

    expect(screen.getByRole('heading', { name: /bau hub/i })).toBeInTheDocument()

    expect(await screen.findByText(/intake & triage/i)).toBeInTheDocument()
    expect(screen.getByText(/policy q&a/i)).toBeInTheDocument()
    expect(screen.getByText(/decision log search/i)).toBeInTheDocument()

    expect(screen.getByText(/meeting notes/i)).toBeInTheDocument()
    expect(screen.getByText(/policy update/i)).toBeInTheDocument()
  })
})
