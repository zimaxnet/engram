# VoiceLive v2 Architecture Diagram

## Overview

This diagram shows the decoupled VoiceLive v2 architecture where audio flows directly browser↔Azure while memory enrichment happens asynchronously.

## Architecture Flow

```mermaid
graph LR
    subgraph Browser ["🖥️ Browser"]
        VC[VoiceChatV2]
        Hook[useAzureRealtime Hook]
        WebRTC[WebRTC PeerConnection]
    end

    subgraph Azure ["☁️ Azure Cognitive Services"]
        RT[gpt-realtime Model]
        VAD[Voice Activity Detection]
        TTS[Text-to-Speech]
    end

    subgraph Backend ["🔧 Backend API"]
        Token[/realtime/token]
        Enrich[/memory/enrich]
    end

    subgraph Memory ["💾 Zep Memory"]
        Sessions[Sessions]
        Facts[Facts]
    end

    %% Realtime path
    VC --> Hook
    Hook --> WebRTC
    WebRTC <-->|"🎤 Audio Stream (WebRTC)"| RT
    RT --> VAD
    VAD --> TTS

    %% Token acquisition
    Hook -.->|"1. Get Token"| Token
    Token -.->|"Ephemeral Key"| Hook

    %% Memory enrichment (async)
    Hook -->|"📝 Transcripts"| Enrich
    Enrich --> Sessions
    Enrich --> Facts

    %% Styling
    classDef browser fill:#3B82F6,stroke:#1E40AF,color:white
    classDef azure fill:#0078D4,stroke:#005A9E,color:white
    classDef backend fill:#8B5CF6,stroke:#6D28D9,color:white
    classDef memory fill:#10B981,stroke:#059669,color:white

    class VC,Hook,WebRTC browser
    class RT,VAD,TTS azure
    class Token,Enrich backend
    class Sessions,Facts memory
```

## Data Flow

| Path | Description | Latency |
|------|-------------|---------|
| **Audio** | Browser ↔ Azure (direct WebRTC) | ~50ms |
| **Token** | Browser → Backend → Azure | One-time, ~200ms |
| **Transcripts** | Browser → Backend → Zep | Async, non-blocking |

## Key Benefits

1. **Lower Latency**: Audio bypasses backend entirely
2. **Simpler Backend**: No audio processing, just token + text
3. **Resilient**: Memory failures don't affect voice
4. **Scalable**: Audio load on Azure, not our backend
