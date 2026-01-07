import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import VoiceChat from './VoiceChat';
import * as authConfig from '../../auth/authConfig';

// Mock auth config
vi.mock('../../auth/authConfig', () => ({
  getAccessToken: vi.fn().mockResolvedValue('fake-access-token'),
}));

describe('VoiceChat Component', () => {
  const defaultProps = {
    agentId: 'elena',
  };

  // Mock WebSocket with proper handler storage
  let mockWs: any;
  
  const createMockWebSocket = () => {
    const handlers: any = {
      onopen: null,
      onmessage: null,
      onerror: null,
      onclose: null,
    };
    
    mockWs = {
      send: vi.fn(),
      close: vi.fn(),
      readyState: WebSocket.CONNECTING,
      get onopen() { return handlers.onopen; },
      set onopen(fn) { handlers.onopen = fn; },
      get onmessage() { return handlers.onmessage; },
      set onmessage(fn) { handlers.onmessage = fn; },
      get onerror() { return handlers.onerror; },
      set onerror(fn) { handlers.onerror = fn; },
      get onclose() { return handlers.onclose; },
      set onclose(fn) { handlers.onclose = fn; },
    };
    
    return mockWs;
  };

  const MockWebSocket = vi.fn(() => createMockWebSocket()) as any;
  MockWebSocket.OPEN = WebSocket.OPEN;
  MockWebSocket.CONNECTING = WebSocket.CONNECTING;
  MockWebSocket.CLOSED = WebSocket.CLOSED;

  beforeEach(() => {
    vi.clearAllMocks();
    vi.stubGlobal('WebSocket', MockWebSocket);

    // Mock environment variable
    import.meta.env = { VITE_API_URL: 'http://localhost:8082' };

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

    // Should create WebSocket connection to backend proxy (with optional token query param)
    await waitFor(() => {
      expect(MockWebSocket).toHaveBeenCalledWith(
        expect.stringMatching(/^ws:\/\/localhost:8082\/api\/v1\/voice\/voicelive\/voice-.*(\?token=.*)?$/),
        undefined
      );
    });

    // Should get access token
    await waitFor(() => {
      expect(authConfig.getAccessToken).toHaveBeenCalled();
    });
  });

  it('should handle incoming assistant transcript', async () => {
    const onMessage = vi.fn();
    render(<VoiceChat {...defaultProps} onMessage={onMessage} />);

    await waitFor(() => {
      expect(MockWebSocket).toHaveBeenCalled();
      expect(mockWs).toBeDefined();
    });

    // Wait for handlers to be set
    await waitFor(() => {
      expect(mockWs.onopen).toBeDefined();
    });

    // Simulate WebSocket open
    mockWs.readyState = WebSocket.OPEN;
    if (mockWs.onopen) {
      mockWs.onopen();
    }

    // Wait a bit for state updates
    await waitFor(() => {
      expect(mockWs.onmessage).toBeDefined();
    });

    // Simulate incoming transcript from backend proxy
    if (mockWs.onmessage) {
      mockWs.onmessage({
        data: JSON.stringify({
          type: 'transcription',
          speaker: 'assistant',
          status: 'complete',
          text: 'Hello world'
        })
      });
    }

    // Should call onMessage with final text
    await waitFor(() => {
      expect(onMessage).toHaveBeenCalledWith(expect.objectContaining({
        text: 'Hello world',
        type: 'agent'
      }));
    }, { timeout: 3000 });
  });

  it('should handle user speech recognition', async () => {
    const onMessage = vi.fn();
    render(<VoiceChat {...defaultProps} onMessage={onMessage} />);

    await waitFor(() => {
      expect(MockWebSocket).toHaveBeenCalled();
      expect(mockWs).toBeDefined();
    });

    // Wait for handlers to be set
    await waitFor(() => {
      expect(mockWs.onopen).toBeDefined();
    });
    
    // Simulate WebSocket open
    mockWs.readyState = WebSocket.OPEN;
    if (mockWs.onopen) {
      mockWs.onopen();
    }

    // Wait for message handler
    await waitFor(() => {
      expect(mockWs.onmessage).toBeDefined();
    });

    // Simulate user transcript completion from backend proxy
    if (mockWs.onmessage) {
      mockWs.onmessage({
        data: JSON.stringify({
          type: 'transcription',
          speaker: 'user',
          status: 'complete',
          text: 'Hello Elena'
        })
      });
    }

    await waitFor(() => {
      expect(onMessage).toHaveBeenCalledWith(expect.objectContaining({
        text: 'Hello Elena',
        type: 'user'
      }));
    }, { timeout: 3000 });
  });

  it('should handle connection errors', async () => {
    const onStatusChange = vi.fn();
    
    render(<VoiceChat {...defaultProps} onStatusChange={onStatusChange} />);

    await waitFor(() => {
      expect(MockWebSocket).toHaveBeenCalled();
      expect(mockWs).toBeDefined();
    });

    // Wait for error handler to be set
    await waitFor(() => {
      expect(mockWs.onerror).toBeDefined();
    });

    // Simulate WebSocket error
    if (mockWs.onerror) {
      mockWs.onerror(new Event('error'));
    }

    await waitFor(() => {
      expect(onStatusChange).toHaveBeenCalledWith('error');
    }, { timeout: 3000 });

    // Check for error message (use getAllByText since there may be multiple elements)
    const errorElements = screen.getAllByText(/Voice connection error/i);
    expect(errorElements.length).toBeGreaterThan(0);
  });
});
