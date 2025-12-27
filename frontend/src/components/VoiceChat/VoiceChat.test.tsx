import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import VoiceChat from './VoiceChat';
import * as api from '../../services/api';

// Mock API
vi.mock('../../services/api', () => ({
  getVoiceToken: vi.fn(),
  persistTurn: vi.fn(),
}));

describe('VoiceChat Component', () => {
  const defaultProps = {
    agentId: 'elena',
  };

  // Mock WebSocket
  const mockWs: any = {
    send: vi.fn(),
    close: vi.fn(),
    readyState: WebSocket.OPEN,
    onopen: null,
    onmessage: null,
    onerror: null,
    onclose: null,
  };

  const MockWebSocket = vi.fn(() => mockWs) as any;
  MockWebSocket.OPEN = WebSocket.OPEN;

  beforeEach(() => {
    vi.clearAllMocks();
    vi.stubGlobal('WebSocket', MockWebSocket);

    // Reset mock callbacks
    mockWs.onopen = null;
    mockWs.onmessage = null;
    mockWs.onerror = null;
    mockWs.onclose = null;

    // Mock getVoiceToken response
    (api.getVoiceToken as any).mockResolvedValue({
      token: 'fake-token',
      endpoint: 'https://fake-azure.com/'
    });

    // Mock AudioContext and MediaDevices
    global.AudioContext = vi.fn().mockImplementation(() => ({
      createBuffer: vi.fn(() => ({
        getChannelData: vi.fn(() => new Float32Array(1024)),
        duration: 1
      })),
      createBufferSource: vi.fn(() => ({
        connect: vi.fn(),
        start: vi.fn(),
        onended: null
      })),
      createMediaStreamSource: vi.fn(() => ({
        connect: vi.fn()
      })),
      createAnalyser: vi.fn(() => ({
        connect: vi.fn(),
        frequencyBinCount: 128,
        getByteFrequencyData: vi.fn()
      })),
      createScriptProcessor: vi.fn(() => ({
        connect: vi.fn(),
        disconnect: vi.fn(),
        onaudioprocess: null
      })),
      destination: {},
      close: vi.fn().mockResolvedValue(undefined),
      currentTime: 0,
      state: 'running'
    }));

    Object.defineProperty(window.navigator, 'mediaDevices', {
      value: {
        getUserMedia: vi.fn().mockResolvedValue({
          getTracks: () => [{ stop: vi.fn() }],
        }),
      },
      writable: true,
    });

    // Mock requestAnimationFrame
    global.requestAnimationFrame = vi.fn();
    global.cancelAnimationFrame = vi.fn();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('should render and initiate connection', async () => {
    render(<VoiceChat {...defaultProps} />);
    expect(screen.getByRole('button')).toBeInTheDocument();

    // Should call API to get token
    await waitFor(() => {
      expect(api.getVoiceToken).toHaveBeenCalledWith('elena', expect.stringMatching(/^voice-/));
    });

    // Should create WebSocket
    await waitFor(() => {
      expect(MockWebSocket).toHaveBeenCalledWith(
        expect.stringContaining('wss://fake-azure.com/openai/realtime'),
        'realtime-openai-v1-beta'
      );
    });
  });

  it('should handle incoming assistant transcript', async () => {
    const onMessage = vi.fn();
    render(<VoiceChat {...defaultProps} onMessage={onMessage} />);

    await waitFor(() => expect(MockWebSocket).toHaveBeenCalled());

    // Simulate WebSocket open
    mockWs.onopen();

    // Simulate incoming transcript delta
    mockWs.onmessage({
      data: JSON.stringify({
        type: 'response.audio_transcript.delta',
        delta: 'Hello '
      })
    });

    // Simulate transcript done
    mockWs.onmessage({
      data: JSON.stringify({
        type: 'response.audio_transcript.done',
        transcript: 'Hello world'
      })
    });

    // Should call onMessage with final text
    await waitFor(() => {
      expect(onMessage).toHaveBeenCalledWith(expect.objectContaining({
        text: 'Hello world',
        type: 'agent'
      }));
    });

    // Should persist turn
    expect(api.persistTurn).toHaveBeenCalledWith(expect.objectContaining({
      content: 'Hello world',
      role: 'assistant'
    }));
  });

  it('should handle user speech recognition', async () => {
    const onMessage = vi.fn();
    render(<VoiceChat {...defaultProps} onMessage={onMessage} />);

    await waitFor(() => expect(MockWebSocket).toHaveBeenCalled());
    mockWs.onopen();

    // Simulate user transcript completion
    mockWs.onmessage({
      data: JSON.stringify({
        type: 'conversation.item.input_audio_transcription.completed',
        transcript: 'Hello Elena'
      })
    });

    await waitFor(() => {
      expect(onMessage).toHaveBeenCalledWith(expect.objectContaining({
        text: 'Hello Elena',
        type: 'user'
      }));
    });

    // Should persist turn
    expect(api.persistTurn).toHaveBeenCalledWith(expect.objectContaining({
      content: 'Hello Elena',
      role: 'user'
    }));
  });

  it('should handle connection errors', async () => {
    const onStatusChange = vi.fn();
    (api.getVoiceToken as any).mockRejectedValue(new Error('Auth failed'));

    render(<VoiceChat {...defaultProps} onStatusChange={onStatusChange} />);

    await waitFor(() => {
      expect(onStatusChange).toHaveBeenCalledWith('error');
    });

    expect(screen.getByText('Auth failed')).toBeInTheDocument();
  });
});
