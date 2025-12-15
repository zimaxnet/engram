import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { VoiceInteractionPage } from './VoiceInteractionPage';

// Mock the VoiceChat component
vi.mock('../../components/VoiceChat/VoiceChat', () => ({
  default: ({ agentId }: { agentId: string }) => (
    <div data-testid="voice-chat-mock">VoiceChat Component for {agentId}</div>
  ),
}));

describe('VoiceInteractionPage', () => {
  it('should render voice interaction page with heading', () => {
    render(<VoiceInteractionPage activeAgent="elena" />);
    expect(screen.getByRole('heading', { name: /voice interaction/i })).toBeInTheDocument();
  });

  it('should display agent name in subtitle for Elena', () => {
    render(<VoiceInteractionPage activeAgent="elena" />);
    expect(screen.getByText(/interact with elena/i)).toBeInTheDocument();
  });

  it('should display agent name in subtitle for Marcus', () => {
    render(<VoiceInteractionPage activeAgent="marcus" />);
    expect(screen.getByText(/interact with marcus/i)).toBeInTheDocument();
  });

  it('should render VoiceChat component', () => {
    render(<VoiceInteractionPage activeAgent="elena" />);
    expect(screen.getByTestId('voice-chat-mock')).toBeInTheDocument();
  });

  it('should display connection status section', () => {
    render(<VoiceInteractionPage activeAgent="elena" />);
    expect(screen.getByText(/connection status:/i)).toBeInTheDocument();
  });

  it('should show connecting status initially', () => {
    render(<VoiceInteractionPage activeAgent="elena" />);
    expect(screen.getByText(/🟡 connecting to voice service/i)).toBeInTheDocument();
  });

  it('should pass correct agent ID to VoiceChat', () => {
    render(<VoiceInteractionPage activeAgent="marcus" />);
    expect(screen.getByText(/voicechat component for marcus/i)).toBeInTheDocument();
  });

  it('should handle instructions correctly', () => {
    render(<VoiceInteractionPage activeAgent="elena" />);
    expect(screen.getByText(/press and hold to speak/i)).toBeInTheDocument();
  });
});
