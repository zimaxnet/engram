import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { WorkflowDetail } from './WorkflowDetail'

describe('WorkflowDetail', () => {
  it('renders mock workflow details for route param', async () => {
    const route = '/workflows/temporal-agent-execution-001'
    
    // Need Routes for useParams
    const ui = (
      <MemoryRouter initialEntries={[route]}>
        <Routes>
          <Route path="/workflows/:workflowId" element={<WorkflowDetail />} />
        </Routes>
      </MemoryRouter>
    )

    render(ui)

    expect(await screen.findByText(/temporal-agent-execution-001/i)).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /context snapshot \(redacted\)/i })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /signals/i })).toBeInTheDocument()
  })
})
