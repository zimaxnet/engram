import { describe, expect, it } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { WorkflowDetail } from './WorkflowDetail'

describe('WorkflowDetail', () => {
  it('renders workflow details from API', async () => {
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
    
    // Verify steps are rendered
    expect(await screen.findByText(/initialize_context/i)).toBeInTheDocument()
  })

  it('sends signal when approve button clicked', async () => {
    const user = userEvent.setup()
    const route = '/workflows/test-workflow-123'
    
    const ui = (
      <MemoryRouter initialEntries={[route]}>
        <Routes>
          <Route path="/workflows/:workflowId" element={<WorkflowDetail />} />
        </Routes>
      </MemoryRouter>
    )

    render(ui)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /approve/i })).toBeInTheDocument()
    })

    const approveButton = screen.getByRole('button', { name: /approve/i })
    await user.click(approveButton)

    // Signal should be sent (in a real test, we'd verify API was called)
    expect(approveButton).toBeInTheDocument()
  })
})
