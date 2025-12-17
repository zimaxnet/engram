import '@testing-library/jest-dom/vitest'
import { server } from './mocks/server'

// Simple WebSocket mock to avoid real connections during tests
class MockWebSocket extends EventTarget {
	static CONNECTING = 0
	static OPEN = 1
	static CLOSING = 2
	static CLOSED = 3

	url: string
	readyState = MockWebSocket.OPEN
	onopen: ((event: Event) => void) | null = null
	onmessage: ((event: MessageEvent) => void) | null = null
	onerror: ((event: Event) => void) | null = null
	onclose: ((event: Event) => void) | null = null

	constructor(url: string) {
		super()
		this.url = url
		const evt = new Event('open')
		this.onopen?.(evt)
		this.dispatchEvent(evt)
	}

	send(_data: string) {
		// no-op for tests
	}

	close() {
		this.readyState = MockWebSocket.CLOSED
		const evt = new Event('close')
		this.onclose?.(evt)
		this.dispatchEvent(evt)
	}
}

// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-ignore override global for tests
globalThis.WebSocket = MockWebSocket

// Mock AudioContext for VoiceChat
globalThis.AudioContext = class {
	createAnalyser() { return { frequencyBinCount: 256, getByteFrequencyData: () => { } } as any }
	createScriptProcessor() { return { connect: () => { }, disconnect: () => { }, onaudioprocess: null } as any }
	createMediaStreamSource() { return { connect: () => { } } as any }
	createBufferSource() { return { connect: () => { }, start: () => { }, buffer: null } as any }
	createBuffer() { return { getChannelData: () => new Float32Array(0), duration: 0 } as any }
	destination = {} as any
	currentTime = 0
	close() { return Promise.resolve() }
} as any

// Mock SpeechRecognition for ChatPanel
const MockSpeechRecognition = class {
	continuous = false
	interimResults = false
	lang = ''
	start() { }
	stop() { }
	abort() { }
	onresult: ((event: any) => void) | null = null
	onend: ((event: any) => void) | null = null
	onerror: ((event: any) => void) | null = null
}
globalThis.SpeechRecognition = MockSpeechRecognition as any
globalThis.webkitSpeechRecognition = MockSpeechRecognition as any

// Establish API mocking before all tests
beforeAll(() => server.listen({
	onUnhandledRequest: (req, print) => {
		// Ignore websocket warnings; the WS is mocked above
		if (req.url.protocol === 'ws:' || req.url.protocol === 'wss:') return
		print.warning()
	},
}))

// Reset any request handlers that are declared as a part of our tests
// (i.e. for testing one-time error scenarios)
afterEach(() => server.resetHandlers())

// Clean up after the tests are finished
afterAll(() => server.close())
