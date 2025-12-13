import { describe, expect, it } from 'vitest'
import { screen } from '@testing-library/react'
import { EvidenceTelemetry } from './EvidenceTelemetry'
import { renderWithRouter } from '../../test/testUtils'

describe('EvidenceTelemetry', () => {
  it('renders snapshot with alerts and narratives', async () => {
    renderWithRouter(<EvidenceTelemetry />, { route: '/evidence' })

    expect(screen.getByRole('heading', { name: /evidence & telemetry/i })).toBeInTheDocument()

    expect(await screen.findByText(/alerts/i)).toBeInTheDocument()
    expect(screen.getByText(/parse failures elevated/i)).toBeInTheDocument()
    expect(screen.getByText(/provenance coverage drifting/i)).toBeInTheDocument()

    expect(screen.getByText(/^Elena$/)).toBeInTheDocument()
    expect(screen.getByText(/^Marcus$/)).toBeInTheDocument()
  })
})
