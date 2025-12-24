
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { ChatPanel } from './ChatPanel'

// Mock VoiceChat because it uses WebSocket
vi.mock('../VoiceChat/VoiceChat', () => ({
    default: () => <div data-testid="voice-chat-mock">Voice Chat Active</div>
}))

const mockAgent = {
    id: 'elena',
    name: 'Elena',
    role: 'BA',
    title: 'Business Analyst',
    avatarUrl: 'elena.png',
    accentColor: 'blue'
}

describe('ChatPanel', () => {
    it('toggles VoiceLive overlay when mic button is clicked', () => {
        render(
            <ChatPanel
                agent={mockAgent}
                onMetricsUpdate={() => { }}
            />
        )

        // Verify mic button exists (using the mic icon text or title)
        const micButton = screen.getByTitle(/Tap to talk/i)
        expect(micButton).toBeInTheDocument()

        // Overlay should not be visible initially
        expect(screen.queryByTestId('voice-chat-mock')).not.toBeInTheDocument()

        // Click mic
        fireEvent.click(micButton)

        // Overlay should be visible
        expect(screen.getByTestId('voice-chat-mock')).toBeInTheDocument()
        expect(screen.getByText(/Speaking with Elena/i)).toBeInTheDocument()

        // Click close button
        const closeButton = screen.getByLabelText('Close voice chat')
        fireEvent.click(closeButton)

        // Overlay should be gone
        expect(screen.queryByTestId('voice-chat-mock')).not.toBeInTheDocument()
    })
})
