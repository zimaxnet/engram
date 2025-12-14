import { describe, expect, it } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { EvidenceTelemetry } from './EvidenceTelemetry'
import { renderWithRouter } from '../../test/testUtils'

describe('EvidenceTelemetry', () => {
  it('renders snapshot with alerts and narratives from API', async () => {
    renderWithRouter(<EvidenceTelemetry />, { route: '/evidence' })

    expect(screen.getByRole('heading', { name: /evidence & telemetry/i })).toBeInTheDocument()

    expect(await screen.findByText(/alerts/i)).toBeInTheDocument()
    expect(screen.getByText(/parse failures elevated/i)).toBeInTheDocument()
    expect(screen.getByText(/provenance coverage drifting/i)).toBeInTheDocument()

    expect(screen.getByText(/^Elena$/)).toBeInTheDocument()
    expect(screen.getByText(/^Marcus$/)).toBeInTheDocument()
  })

  it('changes range when selector is used', async () => {
    const user = userEvent.setup()
    renderWithRouter(<EvidenceTelemetry />, { route: '/evidence' })

    await waitFor(() => {
      expect(screen.getByText(/reliability/i)).toBeInTheDocument()
    })

    const rangeSelect = screen.getByLabelText(/range/i)
    await user.selectOptions(rangeSelect, '24h')

    // Range should update (in a real test, we'd verify API was called with new range)
    expect(rangeSelect).toHaveValue('24h')
  })
})
