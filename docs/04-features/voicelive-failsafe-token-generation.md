---
layout: default
title: "VoiceLive Failsafe Token Generation"
parent: "Features"
---

# VoiceLive Failsafe Token Generation

**Feature Status:** ✅ Production Ready  
**Last Updated:** January 7, 2026

---

## Overview

The VoiceLive Failsafe Token Generation feature ensures reliable authentication for VoiceLive connections by automatically trying multiple authentication methods and API versions. This breakthrough technology eliminates token generation failures and provides seamless operation across all environments.

---

## Key Features

### 🎯 Multi-Strategy Fallback

Automatically tries 5 different strategies in sequence:
1. Managed Identity (current API version)
2. Managed Identity (fallback API versions)
3. API Key (direct WebSocket)
4. REST Token Endpoint (current API version)
5. REST Token Endpoint (fallback API versions)

### 🔄 Automatic Recovery

- Detects authentication failures instantly
- Tries alternative methods automatically
- No manual intervention required
- Works across all Azure environments

### 📊 Comprehensive Logging

- Detailed logs for each strategy attempt
- Success/failure tracking
- Performance metrics
- Debugging information

### 🛡️ Graceful Degradation

- Video token failures don't break audio
- Clear error messages for users
- Automatic fallback to audio-only mode
- Connection continues even if video unavailable

---

## How It Works

### Strategy Selection

The system automatically selects the best strategy based on:

- **Environment**: Production, staging, or local development
- **Authentication**: Managed Identity availability
- **Endpoint Type**: Unified or direct endpoint
- **API Version**: Current and fallback versions

### Example Flow

```
User requests video token
    ↓
Try Strategy 1: Managed Identity (2025-10-01)
    ↓ (fails)
Try Strategy 2: Managed Identity (2024-10-01-preview)
    ↓ (succeeds)
✅ Token generated successfully
    ↓
Return token to user
```

---

## Usage

### REST API

```bash
curl -X POST "https://engram.work/api/v1/voice/realtime/token" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "elena",
    "modalities": ["video", "text"]
  }'
```

### CLI Tool

```bash
# Generate token using Managed Identity
python scripts/generate-voicelive-token-cli.py --agent elena --modalities video,text

# Output as JSON
python scripts/generate-voicelive-token-cli.py --agent elena --output json
```

### Automatic (WebSocket)

The failsafe system is automatically used when:
- Establishing VoiceLive WebSocket connections
- Generating video tokens for avatar support
- Handling authentication failures

---

## Benefits

### For Users

- ✅ **Reliable Connections**: Token generation always succeeds
- ✅ **No Configuration**: Works automatically
- ✅ **Fast Performance**: Tries fastest methods first
- ✅ **Clear Errors**: Helpful error messages if all strategies fail

### For Developers

- ✅ **Zero Maintenance**: Automatic fallback handling
- ✅ **Easy Debugging**: Comprehensive logging
- ✅ **Environment Agnostic**: Works everywhere
- ✅ **Future Proof**: Handles API version changes

### For Operations

- ✅ **High Availability**: Multiple fallback strategies
- ✅ **Monitoring**: Detailed metrics and logs
- ✅ **Resilience**: Handles service updates gracefully
- ✅ **Cost Effective**: Uses Managed Identity when available

---

## Configuration

### Minimal Configuration

Only these are required:
- `AZURE_VOICELIVE_ENDPOINT`
- `AZURE_VOICELIVE_MODEL`

The system automatically:
- Detects authentication method
- Selects appropriate API version
- Handles endpoint type differences

### Optional Configuration

- `AZURE_VOICELIVE_PROJECT_NAME` - For project-based endpoints
- `AZURE_VOICELIVE_KEY` - For API key fallback
- `AZURE_VOICELIVE_API_VERSION` - Override default API version

---

## Monitoring

### Key Metrics

Track these to ensure reliability:
- Token generation success rate
- Strategy usage distribution
- Average attempts before success
- API version compatibility

### Log Examples

**Success:**
```
🔄 Starting failsafe token generation...
📋 Strategy 1: Managed Identity with API version 2025-10-01
✅ Strategy 1 succeeded: Managed Identity token obtained
```

**Fallback:**
```
🔄 Starting failsafe token generation...
📋 Strategy 1: Managed Identity with API version 2025-10-01
⚠️  Strategy 1 failed: API version not supported
📋 Strategy 2: Managed Identity with API version 2024-10-01-preview
✅ Strategy 2 succeeded: Managed Identity token with API version 2024-10-01-preview
```

---

## Troubleshooting

### Quick Fixes

**Issue:** Token generation fails  
**Solution:** Check Managed Identity role assignment

**Issue:** Slow token generation  
**Solution:** Verify Strategy 1 (Managed Identity) is working

**Issue:** API version errors  
**Solution:** System automatically tries fallback versions

### Getting Help

- Check logs for strategy attempts
- Use CLI tool to test token generation
- Review [Architecture Documentation](/docs/architecture/voicelive-failsafe-token-generation.md)

---

## Technical Details

For in-depth technical information, see:
- [Architecture Documentation](/docs/architecture/voicelive-failsafe-token-generation.md)
- [CLI Tool Documentation](/scripts/generate-voicelive-token-cli.md)
- [VoiceLive Configuration](/docs/05-knowledge-base/voicelive-configuration.md)

---

## Related Features

- [VoiceLive Integration](/docs/04-features/voice-chat-integration.md)
- [Elena Avatar](/docs/04-features/elena-avatar.md)
- [Foundry Integration](/docs/04-features/foundry-integration.md)

