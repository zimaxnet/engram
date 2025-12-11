# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
# -------------------------------------------------------------------------
import asyncio
import base64
import logging
import pyaudio
from typing import Optional

from openai import AsyncAzureOpenAI

logger = logging.getLogger(__name__)


class RealtimeClient:
    def __init__(
        self,
        endpoint: str,
        api_key: str,
        deployment_name: str,
        system_message: str,
        voice: str,
    ):
        self.endpoint = endpoint
        self.api_key = api_key
        self.deployment_name = deployment_name
        self.system_message = system_message
        self.voice = voice
        self.client: Optional[AsyncAzureOpenAI] = None

        # Audio settings
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 24000
        self.chunk_size = 2400  # 100ms
        self.audio = pyaudio.PyAudio()
        self.input_stream = None
        self.output_stream = None

        self.stop_event = asyncio.Event()

    async def run(self):
        print("\n✨ Connecting to Azure OpenAI Realtime API...")
        print(f"   Endpoint: {self.endpoint}")
        print(f"   Model: {self.deployment_name}")
        print(f"   Voice: {self.voice}")

        self.client = AsyncAzureOpenAI(
            azure_endpoint=self.endpoint,
            api_key=self.api_key,
            api_version="2024-10-01-preview",  # Check for latest version
        )

        # Build WebSocket URL - handled by SDK usually but let's see MS sample
        # MS sample uses AsyncOpenAI with base_url modification.
        # But AsyncAzureOpenAI might support it natively now?
        # The MS Quickstart shows:
        # client = AsyncOpenAI(websocket_base_url=...)
        # Let's stick to the sample pattern exactly for reliability.

        # NOTE: Using protocol from MS Quickstart
        # NOTE: Using protocol from MS Quickstart
        # base_url = f"{self.endpoint.rstrip('/')}/openai/realtime"
        # Actually MS sample says: base_url = endpoint.replace("https://", "wss://").rstrip("/") + "/openai/realtime"
        # But `AsyncAzureOpenAI` is the modern way if supported.
        # Let's use the exact MS Quickstart code structure for safety.

        from openai import AsyncOpenAI

        # Construct wss URL
        wss_url = (
            self.endpoint.replace("https://", "wss://").rstrip("/") + "/openai/realtime"
        )

        client = AsyncOpenAI(base_url=wss_url, api_key=self.api_key)

        print("🎤 Starting audio session... (Press Ctrl+C to stop)")

        async with client.beta.realtime.connect(
            model=self.deployment_name
        ) as connection:
            await connection.session.update(
                session={
                    "modalities": ["audio", "text"],
                    "instructions": self.system_message,
                    "voice": self.voice,
                    "input_audio_format": "pcm16",
                    "output_audio_format": "pcm16",
                    "turn_detection": {
                        "type": "server_vad",
                        "threshold": 0.5,
                        "prefix_padding_ms": 300,
                        "silence_duration_ms": 200,
                    },
                }
            )

            # Start audio tasks
            send_task = asyncio.create_task(self.send_audio(connection))
            receive_task = asyncio.create_task(self.receive_audio(connection))

            try:
                await asyncio.gather(send_task, receive_task)
            except asyncio.CancelledError:
                pass
            finally:
                self.cleanup()

    async def send_audio(self, connection):
        self.input_stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk_size,
        )

        try:
            while not self.stop_event.is_set():
                data = await asyncio.to_thread(
                    self.input_stream.read, self.chunk_size, exception_on_overflow=False
                )
                base64_audio = base64.b64encode(data).decode("utf-8")
                await connection.input_audio_buffer.append(audio=base64_audio)
                await asyncio.sleep(0)  # Yield
        except Exception as e:
            logger.error(f"Error sending audio: {e}")

    async def receive_audio(self, connection):
        self.output_stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            output=True,
            frames_per_buffer=self.chunk_size,
        )

        print("🗣️  Assistant is listening...")

        async for event in connection:
            if event.type == "response.audio.delta":
                audio_bytes = base64.b64decode(event.delta)
                await asyncio.to_thread(self.output_stream.write, audio_bytes)
            elif event.type == "response.audio_transcript.done":
                print(f"\n🤖 Assistant: {event.transcript}")
            elif event.type == "conversation.item.input_audio_transcription.completed":
                print(f"\n👤 User: {event.transcript}")
            elif event.type == "error":
                print(f"Error: {event.error}")

    def cleanup(self):
        if self.input_stream:
            self.input_stream.stop_stream()
            self.input_stream.close()
        if self.output_stream:
            self.output_stream.stop_stream()
            self.output_stream.close()
        self.audio.terminate()
