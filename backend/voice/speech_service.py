"""
Azure Speech Service Integration

Provides:
- Speech-to-Text (STT) for voice input
- Text-to-Speech (TTS) for voice output
- Viseme data for lip-sync animation
- Real-time streaming support

Uses Azure Cognitive Services Speech SDK.
"""

import asyncio
import base64
import io
import logging
from dataclasses import dataclass
from enum import Enum
from typing import AsyncGenerator, Callable, Optional

from backend.core import get_settings

logger = logging.getLogger(__name__)


class VoiceId(str, Enum):
    """Available voice identities for agents"""
    ELENA = "elena"
    MARCUS = "marcus"


# Voice configuration mapping
VOICE_CONFIG = {
    VoiceId.ELENA: {
        "name": "en-US-JennyNeural",  # Warm, professional female voice
        "style": "friendly",
        "pitch": "+0%",
        "rate": "0%",
    },
    VoiceId.MARCUS: {
        "name": "en-US-GuyNeural",  # Confident male voice
        "style": "professional",
        "pitch": "-5%",
        "rate": "+5%",
    },
}


@dataclass
class SpeechRecognitionResult:
    """Result from speech recognition"""
    text: str
    confidence: float
    duration_ms: int
    is_final: bool


@dataclass
class SpeechSynthesisResult:
    """Result from speech synthesis"""
    audio_data: bytes
    audio_format: str
    duration_ms: int
    visemes: list[dict]  # List of {time_ms, viseme_id}


@dataclass
class VisemeEvent:
    """A viseme event for lip-sync"""
    time_ms: int
    viseme_id: int  # 0-21 standard viseme IDs


class AzureSpeechService:
    """
    Azure Speech Service client for STT and TTS.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self._speech_config = None
        self._initialized = False
    
    @property
    def speech_config(self):
        """Lazy-load speech config"""
        if self._speech_config is None:
            try:
                import azure.cognitiveservices.speech as speechsdk
                
                if not self.settings.azure_speech_key:
                    logger.warning("Azure Speech key not configured")
                    return None
                
                self._speech_config = speechsdk.SpeechConfig(
                    subscription=self.settings.azure_speech_key,
                    region=self.settings.azure_speech_region
                )
                self._initialized = True
                logger.info(f"Azure Speech initialized: {self.settings.azure_speech_region}")
                
            except ImportError:
                logger.warning("azure-cognitiveservices-speech not installed")
                return None
            except Exception as e:
                logger.error(f"Failed to initialize Azure Speech: {e}")
                return None
        
        return self._speech_config
    
    async def recognize_speech(
        self,
        audio_data: bytes,
        language: str = "en-US"
    ) -> SpeechRecognitionResult:
        """
        Recognize speech from audio data.
        
        Args:
            audio_data: Raw audio bytes (WAV format)
            language: Language code (default: en-US)
            
        Returns:
            SpeechRecognitionResult with transcribed text
        """
        if not self.speech_config:
            return SpeechRecognitionResult(
                text="[Speech recognition not configured]",
                confidence=0.0,
                duration_ms=0,
                is_final=True
            )
        
        try:
            import azure.cognitiveservices.speech as speechsdk
            
            # Configure for the specific language
            self.speech_config.speech_recognition_language = language
            
            # Create audio stream from bytes
            stream = speechsdk.audio.PushAudioInputStream()
            audio_config = speechsdk.audio.AudioConfig(stream=stream)
            
            # Create recognizer
            recognizer = speechsdk.SpeechRecognizer(
                speech_config=self.speech_config,
                audio_config=audio_config
            )
            
            # Push audio data
            stream.write(audio_data)
            stream.close()
            
            # Recognize
            result = await asyncio.to_thread(recognizer.recognize_once)
            
            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                return SpeechRecognitionResult(
                    text=result.text,
                    confidence=0.95,  # SDK doesn't expose confidence directly
                    duration_ms=int(result.duration / 10000),  # Convert from ticks
                    is_final=True
                )
            elif result.reason == speechsdk.ResultReason.NoMatch:
                return SpeechRecognitionResult(
                    text="",
                    confidence=0.0,
                    duration_ms=0,
                    is_final=True
                )
            else:
                logger.warning(f"Speech recognition failed: {result.reason}")
                return SpeechRecognitionResult(
                    text="",
                    confidence=0.0,
                    duration_ms=0,
                    is_final=True
                )
                
        except Exception as e:
            logger.error(f"Speech recognition error: {e}")
            return SpeechRecognitionResult(
                text="[Recognition error]",
                confidence=0.0,
                duration_ms=0,
                is_final=True
            )
    
    async def synthesize_speech(
        self,
        text: str,
        voice_id: VoiceId = VoiceId.ELENA,
        include_visemes: bool = True
    ) -> SpeechSynthesisResult:
        """
        Synthesize speech from text.
        
        Args:
            text: Text to synthesize
            voice_id: Which agent voice to use
            include_visemes: Whether to include viseme data for lip-sync
            
        Returns:
            SpeechSynthesisResult with audio and visemes
        """
        if not self.speech_config:
            # Return mock result for development
            return SpeechSynthesisResult(
                audio_data=b"",
                audio_format="audio/wav",
                duration_ms=len(text) * 50,  # Rough estimate
                visemes=[]
            )
        
        try:
            import azure.cognitiveservices.speech as speechsdk
            
            # Get voice configuration
            voice_config = VOICE_CONFIG.get(voice_id, VOICE_CONFIG[VoiceId.ELENA])
            
            # Set output format
            self.speech_config.set_speech_synthesis_output_format(
                speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3
            )
            
            # Create synthesizer
            synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=self.speech_config,
                audio_config=None  # We'll capture to memory
            )
            
            # Collect visemes
            visemes: list[VisemeEvent] = []
            
            if include_visemes:
                def viseme_callback(evt):
                    visemes.append(VisemeEvent(
                        time_ms=int(evt.audio_offset / 10000),
                        viseme_id=evt.viseme_id
                    ))
                
                synthesizer.viseme_received.connect(viseme_callback)
            
            # Build SSML for better control
            ssml = self._build_ssml(text, voice_config)
            
            # Synthesize
            result = await asyncio.to_thread(
                synthesizer.speak_ssml_async(ssml).get
            )
            
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                return SpeechSynthesisResult(
                    audio_data=result.audio_data,
                    audio_format="audio/mp3",
                    duration_ms=int(result.audio_duration / 10000),
                    visemes=[{"time_ms": v.time_ms, "viseme_id": v.viseme_id} for v in visemes]
                )
            else:
                logger.warning(f"Speech synthesis failed: {result.reason}")
                return SpeechSynthesisResult(
                    audio_data=b"",
                    audio_format="audio/mp3",
                    duration_ms=0,
                    visemes=[]
                )
                
        except Exception as e:
            logger.error(f"Speech synthesis error: {e}")
            return SpeechSynthesisResult(
                audio_data=b"",
                audio_format="audio/mp3",
                duration_ms=0,
                visemes=[]
            )
    
    def _build_ssml(self, text: str, voice_config: dict) -> str:
        """Build SSML for speech synthesis with voice styling"""
        return f"""
<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis"
       xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="en-US">
    <voice name="{voice_config['name']}">
        <mstts:express-as style="{voice_config['style']}">
            <prosody pitch="{voice_config['pitch']}" rate="{voice_config['rate']}">
                {self._escape_ssml(text)}
            </prosody>
        </mstts:express-as>
    </voice>
</speak>
"""
    
    def _escape_ssml(self, text: str) -> str:
        """Escape special characters for SSML"""
        return (
            text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;")
        )
    
    async def stream_recognition(
        self,
        audio_stream: AsyncGenerator[bytes, None],
        language: str = "en-US",
        on_partial: Optional[Callable[[str], None]] = None,
        on_final: Optional[Callable[[str], None]] = None
    ) -> str:
        """
        Stream-based speech recognition for real-time transcription.
        
        Args:
            audio_stream: Async generator yielding audio chunks
            language: Language code
            on_partial: Callback for partial results (live transcription)
            on_final: Callback for final results
            
        Returns:
            Final transcribed text
        """
        if not self.speech_config:
            return "[Speech recognition not configured]"
        
        try:
            import azure.cognitiveservices.speech as speechsdk
            
            self.speech_config.speech_recognition_language = language
            
            # Create push stream
            stream = speechsdk.audio.PushAudioInputStream()
            audio_config = speechsdk.audio.AudioConfig(stream=stream)
            
            recognizer = speechsdk.SpeechRecognizer(
                speech_config=self.speech_config,
                audio_config=audio_config
            )
            
            final_text = ""
            done = asyncio.Event()
            
            def handle_recognizing(evt):
                if on_partial:
                    on_partial(evt.result.text)
            
            def handle_recognized(evt):
                nonlocal final_text
                if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
                    final_text = evt.result.text
                    if on_final:
                        on_final(final_text)
            
            def handle_canceled(evt):
                done.set()
            
            def handle_stopped(evt):
                done.set()
            
            recognizer.recognizing.connect(handle_recognizing)
            recognizer.recognized.connect(handle_recognized)
            recognizer.canceled.connect(handle_canceled)
            recognizer.session_stopped.connect(handle_stopped)
            
            # Start recognition
            recognizer.start_continuous_recognition()
            
            # Stream audio data
            async for chunk in audio_stream:
                stream.write(chunk)
            
            stream.close()
            
            # Wait for completion
            await done.wait()
            recognizer.stop_continuous_recognition()
            
            return final_text
            
        except Exception as e:
            logger.error(f"Stream recognition error: {e}")
            return "[Recognition error]"


# Singleton service
speech_service = AzureSpeechService()


# Convenience functions
async def recognize_speech(audio_data: bytes, language: str = "en-US") -> SpeechRecognitionResult:
    """Recognize speech from audio data"""
    return await speech_service.recognize_speech(audio_data, language)


async def synthesize_speech(
    text: str,
    voice_id: VoiceId = VoiceId.ELENA,
    include_visemes: bool = True
) -> SpeechSynthesisResult:
    """Synthesize speech from text"""
    return await speech_service.synthesize_speech(text, voice_id, include_visemes)


def get_voice_for_agent(agent_id: str) -> VoiceId:
    """Get the voice ID for an agent"""
    if agent_id == "marcus":
        return VoiceId.MARCUS
    return VoiceId.ELENA

