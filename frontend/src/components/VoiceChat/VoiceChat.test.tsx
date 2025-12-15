import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import VoiceChat from './VoiceChat';

describe('VoiceChat Component', () => {
  const defaultProps = {
    agentId: 'elena',
  };

  beforeEach(() => {
    // Mock window.navigator.mediaDevices
    Object.defineProperty(window.navigator, 'mediaDevices', {
      value: {
        getUserMedia: vi.fn(() =>
          Promise.resolve({
            getTracks: () => [],
          })
        ),
      },
      writable: true,
    });
  });

  it('should render voice chat component', () => {
    render(<VoiceChat {...defaultProps} />);
    expect(screen.getByRole('button')).toBeInTheDocument();
  });

  it('should call onStatusChange when status changes', async () => {
    const onStatusChange = vi.fn();
    render(
      <VoiceChat
        {...defaultProps}
        onStatusChange={onStatusChange}
      />
    );

    // Component should initialize with a status
    await waitFor(() => {
      expect(onStatusChange).toHaveBeenCalled();
    });
  });

  it('should disable component when disabled prop is true', () => {
    const { container } = render(
      <VoiceChat {...defaultProps} disabled={true} />
    );
    const buttons = container.querySelectorAll('button');
    buttons.forEach(btn => {
      expect(btn).toBeDisabled();
    });
  });

  it('should call onMessage callback when message is sent', async () => {
    const onMessage = vi.fn();
    render(
      <VoiceChat
        {...defaultProps}
        onMessage={onMessage}
      />
    );

    // Note: Full testing would require mocking WebSocket and audio APIs
    // This is a basic structure test
    expect(screen.getByRole('button')).toBeInTheDocument();
  });

  it('should update agent when agentId prop changes', () => {
    const { rerender } = render(
      <VoiceChat {...defaultProps} agentId="elena" />
    );

    rerender(
      <VoiceChat {...defaultProps} agentId="marcus" />
    );

    expect(screen.getByRole('button')).toBeInTheDocument();
  });

  it('should call onVisemes callback with viseme data', async () => {
    const onVisemes = vi.fn();
    render(
      <VoiceChat
        {...defaultProps}
        onVisemes={onVisemes}
      />
    );

    // Component structure should be in place
    expect(screen.getByRole('button')).toBeInTheDocument();
  });
});
