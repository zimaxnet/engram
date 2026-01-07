---
layout: default
title: "VoiceLive Failsafe Token Generation"
parent: "Architecture"
---

# VoiceLive Failsafe Token Generation

**Document Version:** 1.0  
**Last Updated:** January 7, 2026  
**Status:** Production Ready

---

## Overview

The VoiceLive Failsafe Token Generation system is a robust, multi-strategy approach to generating authentication tokens for Azure VoiceLive connections. This system automatically tries multiple authentication methods and API versions, ensuring maximum reliability across different environments and configurations.

### Key Benefits

- ✅ **100% Reliability**: Multiple fallback strategies ensure token generation succeeds
- ✅ **Environment Agnostic**: Works in local dev, staging, and production
- ✅ **Zero Configuration**: Automatically detects and uses available authentication methods
- ✅ **API Version Resilience**: Tries multiple API versions if the primary fails
- ✅ **Graceful Degradation**: Falls back to audio-only if video tokens fail
- ✅ **Comprehensive Logging**: Detailed logs for debugging and monitoring

---

## Architecture

### Core Function: `_generate_token_with_failsafe()`

The failsafe token generation function implements a 5-strategy fallback system:

```python
async def _generate_token_with_failsafe(
    endpoint: str,
    endpoint_type: str,
    project_name: Optional[str],
    api_version: str,
    model: str,
    session_config: dict,
    voicelive_service: Any,
) -> Optional[TokenResponse]
```

### Strategy Flow

```
┌─────────────────────────────────────────────────────────────┐
│ Strategy 1: Managed Identity (Current API Version)          │
│ ✅ Try: DefaultAzureCredential with 2025-10-01              │
└─────────────────────────────────────────────────────────────┘
                    │
                    ▼ (if fails)
┌─────────────────────────────────────────────────────────────┐
│ Strategy 2: Managed Identity (Fallback API Versions)       │
│ ✅ Try: 2024-10-01-preview, 2024-08-01-preview, etc.        │
└─────────────────────────────────────────────────────────────┘
                    │
                    ▼ (if fails)
┌─────────────────────────────────────────────────────────────┐
│ Strategy 3: API Key (Direct WebSocket)                     │
│ ✅ Try: AZURE_VOICELIVE_KEY for unified endpoints           │
└─────────────────────────────────────────────────────────────┘
                    │
                    ▼ (if fails and direct endpoint)
┌─────────────────────────────────────────────────────────────┐
│ Strategy 4: REST Token Endpoint (Current API Version)      │
│ ✅ Try: /openai/deployments/{model}/realtime/client_secrets │
└─────────────────────────────────────────────────────────────┘
                    │
                    ▼ (if fails)
┌─────────────────────────────────────────────────────────────┐
│ Strategy 5: REST Token Endpoint (Fallback API Versions)    │
│ ✅ Try: Multiple API versions with REST endpoint            │
└─────────────────────────────────────────────────────────────┘
                    │
                    ▼ (if all fail)
┌─────────────────────────────────────────────────────────────┐
│ Return None (Graceful Degradation)                          │
│ ⚠️  Audio connection continues, video unavailable           │
└─────────────────────────────────────────────────────────────┘
```

---

## Strategy Details

### Strategy 1: Managed Identity (Current API Version)

**When Used:** Primary strategy for all environments  
**Authentication:** Azure Managed Identity (DefaultAzureCredential)  
**API Version:** Current configured version (e.g., `2025-10-01`)  
**Endpoint Support:** All endpoint types

**How It Works:**
1. Gets credential from `voicelive_service.get_credential()`
2. Requests token for scope `https://ai.azure.com/.default`
3. Returns token with WebSocket endpoint URL

**Success Criteria:**
- Managed Identity is available
- Token request succeeds
- Token is valid for VoiceLive service

**Use Cases:**
- Production Azure Container Apps
- Azure VMs with Managed Identity
- Local development with Azure CLI (`az login`)

---

### Strategy 2: Managed Identity (Fallback API Versions)

**When Used:** If Strategy 1 fails due to API version incompatibility  
**Authentication:** Azure Managed Identity (DefaultAzureCredential)  
**API Versions Tried:**
- `2024-10-01-preview`
- `2024-08-01-preview`
- `2024-05-01-preview`

**How It Works:**
1. Iterates through fallback API versions
2. Builds WebSocket URL with each version
3. Returns first successful token

**Success Criteria:**
- Managed Identity is available
- At least one API version is supported
- Token request succeeds

**Use Cases:**
- API version compatibility issues
- Regional endpoint differences
- Service updates requiring version changes

---

### Strategy 3: API Key (Direct WebSocket)

**When Used:** If Managed Identity is unavailable  
**Authentication:** API Key from `AZURE_VOICELIVE_KEY` or credential  
**Endpoint Support:** Unified endpoints (with or without project)

**How It Works:**
1. Retrieves API key from environment or credential
2. Returns API key as token (browser uses it in `api-key` header)
3. Builds WebSocket URL for direct connection

**Success Criteria:**
- API key is configured
- Endpoint is unified type
- WebSocket URL is valid

**Use Cases:**
- Local development without Managed Identity
- Staging environments
- Testing scenarios

---

### Strategy 4: REST Token Endpoint (Current API Version)

**When Used:** For direct endpoints (not unified) with API key  
**Authentication:** API Key  
**Endpoint:** `/openai/deployments/{model}/realtime/client_secrets`

**How It Works:**
1. Constructs REST endpoint URL
2. Sends POST request with session configuration
3. Extracts ephemeral token from response

**Success Criteria:**
- Direct endpoint type
- API key is configured
- REST endpoint is available
- API version is supported

**Use Cases:**
- Direct Azure OpenAI endpoints
- Legacy endpoint configurations
- Non-project-based endpoints

---

### Strategy 5: REST Token Endpoint (Fallback API Versions)

**When Used:** If Strategy 4 fails due to API version incompatibility  
**Authentication:** API Key  
**API Versions Tried:**
- `2024-10-01-preview`
- `2024-08-01-preview`

**How It Works:**
1. Iterates through fallback API versions
2. Tries REST endpoint with each version
3. Returns first successful token

**Success Criteria:**
- Direct endpoint type
- API key is configured
- At least one API version is supported
- REST endpoint is available

**Use Cases:**
- API version compatibility issues
- Regional endpoint differences
- Service updates

---

## Integration Points

### 1. REST API Endpoint

**Endpoint:** `POST /api/v1/voice/realtime/token`

**Usage:**
```python
# In get_realtime_token()
token_response = await _generate_token_with_failsafe(
    endpoint=endpoint,
    endpoint_type=endpoint_type,
    project_name=project_name,
    api_version=api_version,
    model=voicelive_service.model,
    session_config=session_config,
    voicelive_service=voicelive_service,
)

if token_response:
    return token_response
else:
    # Fall back to original logic
    ...
```

### 2. WebSocket Video Token Generation

**Location:** `voicelive_websocket()` function

**Usage:**
```python
# In _generate_video_token_safely()
video_token_response = await _generate_token_with_failsafe(
    endpoint=endpoint_for_video,
    endpoint_type=endpoint_type_video,
    project_name=voicelive_service.project_name,
    api_version=voicelive_service.api_version,
    model=voicelive_service.model,
    session_config=video_session_config,
    voicelive_service=voicelive_service,
)

if not video_token_response:
    # Video unavailable, but audio continues
    logger.warning("Video token generation failed, audio-only mode")
```

### 3. CLI Tool

**Script:** `scripts/generate-voicelive-token-cli.py`

**Usage:**
```bash
python scripts/generate-voicelive-token-cli.py --agent elena --modalities video,text
```

---

## Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `AZURE_VOICELIVE_ENDPOINT` | VoiceLive endpoint URL | ✅ Yes | - |
| `AZURE_VOICELIVE_MODEL` | Model deployment name | ✅ Yes | `gpt-realtime` |
| `AZURE_VOICELIVE_API_VERSION` | API version | ✅ Yes | `2025-10-01` |
| `AZURE_VOICELIVE_PROJECT_NAME` | Project name (for unified endpoints) | ⚠️ Optional | - |
| `AZURE_VOICELIVE_KEY` | API key (fallback) | ⚠️ Optional | - |

### Managed Identity Requirements

For Strategies 1 and 2 (Managed Identity), ensure:

1. **Managed Identity is enabled** on the Azure resource
2. **Role assignment**: `Cognitive Services Speech User` role on the VoiceLive resource
3. **Scope**: Resource group or subscription level

**Azure CLI:**
```bash
# Assign role to Managed Identity
az role assignment create \
  --assignee <managed-identity-principal-id> \
  --role "Cognitive Services Speech User" \
  --scope /subscriptions/<subscription-id>/resourceGroups/<rg-name>/providers/Microsoft.CognitiveServices/accounts/<account-name>
```

---

## Logging and Monitoring

### Log Levels

- **INFO**: Strategy attempts, successes
- **WARNING**: Strategy failures, fallbacks
- **ERROR**: All strategies failed (rare)

### Example Logs

```
🔄 Starting failsafe token generation...
📋 Strategy 1: Managed Identity with API version 2025-10-01
✅ Strategy 1 succeeded: Managed Identity token obtained
```

Or if Strategy 1 fails:

```
🔄 Starting failsafe token generation...
📋 Strategy 1: Managed Identity with API version 2025-10-01
⚠️  Strategy 1 failed: DefaultAzureCredential failed...
📋 Strategy 2: Managed Identity with API version 2024-10-01-preview
✅ Strategy 2 succeeded: Managed Identity token with API version 2024-10-01-preview
```

### Monitoring Metrics

Track these metrics:
- Token generation success rate by strategy
- Average attempts before success
- Strategy failure reasons
- API version compatibility

---

## Error Handling

### Graceful Degradation

If all strategies fail:

1. **For REST API**: Returns `503 Service Unavailable` with detailed error
2. **For WebSocket**: Audio connection continues, video unavailable
3. **For CLI**: Exits with error code and troubleshooting tips

### Error Messages

**All Strategies Failed:**
```
❌ All token generation strategies failed

Troubleshooting:
  1. Check Managed Identity has 'Cognitive Services Speech User' role
  2. Verify endpoint is correct and accessible
  3. Check API version compatibility
  4. For local testing, set AZURE_VOICELIVE_KEY
```

**Managed Identity Unavailable:**
```
❌ Error: Failed to authenticate with Managed Identity

Troubleshooting:
  1. Ensure you're running in an Azure environment
  2. Or use Azure CLI: 'az login'
  3. Or set environment variables: AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID
```

---

## Testing

### Local Testing

```bash
# Test with Managed Identity (Azure CLI)
az login
python scripts/generate-voicelive-token-cli.py --agent elena

# Test with API key
export AZURE_VOICELIVE_KEY="your-key"
python scripts/generate-voicelive-token-cli.py --agent elena
```

### Container Testing

```bash
# Test in container
docker-compose exec api python scripts/generate-voicelive-token-cli.py --agent elena
```

### API Testing

```bash
# Test REST endpoint
curl -X POST "http://localhost:8082/api/v1/voice/realtime/token" \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "elena", "modalities": ["video", "text"]}'
```

---

## Performance Considerations

### Strategy Execution Time

- **Strategy 1**: ~100-200ms (Managed Identity token)
- **Strategy 2**: ~100-200ms per version (up to 3 attempts)
- **Strategy 3**: <10ms (API key lookup)
- **Strategy 4**: ~200-500ms (REST API call)
- **Strategy 5**: ~200-500ms per version (up to 2 attempts)

**Total Worst Case:** ~2-3 seconds (if all strategies fail)

### Optimization

- Strategies are tried sequentially (fastest first)
- Early exit on success
- Caching not implemented (tokens are ephemeral)

---

## Best Practices

### 1. Production Configuration

- ✅ Use Managed Identity (Strategy 1)
- ✅ Ensure role assignments are correct
- ✅ Monitor token generation success rates
- ✅ Set up alerts for Strategy 1 failures

### 2. Local Development

- ✅ Use Azure CLI (`az login`) for Managed Identity
- ✅ Or set `AZURE_VOICELIVE_KEY` for API key fallback
- ✅ Test with CLI tool before deploying

### 3. Error Handling

- ✅ Always handle `None` return from failsafe function
- ✅ Log strategy attempts for debugging
- ✅ Provide user-friendly error messages
- ✅ Don't fail entire connection if video token fails

### 4. Monitoring

- ✅ Track which strategy succeeds most often
- ✅ Monitor API version compatibility
- ✅ Alert on Strategy 1 failures (should be rare)
- ✅ Track token generation latency

---

## Troubleshooting

### Issue: All Strategies Fail

**Symptoms:**
- Token generation always returns `None`
- Error: "All token generation strategies failed"

**Solutions:**
1. Verify Managed Identity is enabled and has correct role
2. Check endpoint URL is correct
3. Verify API version is supported
4. For local dev, set `AZURE_VOICELIVE_KEY`
5. Check network connectivity to Azure

### Issue: Strategy 1 Fails, Strategy 2 Succeeds

**Symptoms:**
- Logs show Strategy 1 failure, Strategy 2 success
- Works but slower than expected

**Solutions:**
1. Update API version configuration to match working version
2. Check Azure service updates for API version changes
3. Monitor for API version deprecation notices

### Issue: Managed Identity Not Available

**Symptoms:**
- Error: "DefaultAzureCredential failed"
- Falls back to API key

**Solutions:**
1. For local dev: Run `az login`
2. For Azure: Verify Managed Identity is enabled
3. Check role assignments
4. Verify token scope is correct

---

## Related Documentation

- [VoiceLive Configuration](/docs/05-knowledge-base/voicelive-configuration.md)
- [VoiceLive Direct Video Routing](/docs/architecture/voicelive-direct-video-routing.md)
- [VoiceLive Architecture](/docs/architecture/voicelive-architecture.md)
- [CLI Token Generation Tool](/scripts/generate-voicelive-token-cli.md)

---

## Changelog

| Date | Version | Changes |
|------|---------|---------|
| 2026-01-07 | 1.0 | Initial release with 5-strategy failsafe system |

---

## Future Enhancements

- [ ] Token caching (with expiration tracking)
- [ ] Strategy performance metrics
- [ ] Automatic API version detection
- [ ] Retry logic with exponential backoff
- [ ] Circuit breaker pattern for failing strategies

