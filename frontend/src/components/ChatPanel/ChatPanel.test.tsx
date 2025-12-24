
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { ChatPanel } from './ChatPanel'

// Mock react-markdown and remark-gfm to avoid ESM issues in tests
vi.mock('react-markdown', () => ({
    default: ({ children }: { children: React.ReactNode }) => <div data-testid="markdown">{children}</div>,
}))

vi.mock('remark-gfm', () => ({
    default: () => 'remark-gfm-plugin',
}))

// Mock scrollIntoView unavailable in JSDOM
window.HTMLElement.prototype.scrollIntoView = vi.fn()

// Mock VoiceChat because we aren't testing voice logic heavily here.
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
        // Verify mic button exists (using title because role match failed)
        const micButton = screen.getByTitle('Tap to talk (Voice Live)')
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
