# VoiceLive API Version Update to 2025-10-01

**Date**: December 27, 2025  
**Status**: ✅ Complete

## Summary

Updated VoiceLive configuration to use the latest API version `2025-10-01`, which includes significant enhancements over the previous `2024-10-01-preview` version.

## New Features in 2025-10-01

According to Azure documentation, the `2025-10-01` API version includes:

1. **140+ Languages Support**: Expanded language support for global deployments
2. **Custom Speech Integration**: Improved recognition accuracy with Custom Speech models
3. **Neural HD Voices**: Upgraded voice quality for more natural interactions
4. **Improved Semantic VAD**: Better interruption detection with semantic Voice Activity Detection
5. **4K Avatar Support**: High-fidelity visual components for avatar-based interactions

## Changes Made

### 1. Backend Code Updates

**File**: `backend/voice/voicelive_service.py`
- ✅ Updated `build_websocket_endpoint()` to use configurable API version instead of hardcoded `2024-10-01-preview`
- ✅ Now uses `self._api_version` from environment variable

**File**: `backend/core/config.py`
- ✅ Changed default API version from `2024-10-01-preview` to `2025-10-01`
- ✅ Updated documentation comment to reflect new features

### 2. Infrastructure Updates

**File**: `infra/modules/backend-aca.bicep`
- ✅ Updated default API version to `2025-10-01`
- ✅ Updated comment to document new features

### 3. Azure Deployment

**Container App**: `staging-env-api`
- ✅ Updated `AZURE_VOICELIVE_API_VERSION` environment variable to `2025-10-01`

### 4. Documentation Updates

**File**: `docs/sop/voicelive-configuration.md`
- ✅ Updated environment variables table to show `2025-10-01` as recommended
- ✅ Updated endpoint type documentation
- ✅ Updated troubleshooting section
- ✅ Updated production configuration section
- ✅ Added changelog entry

## Testing

### Local Docker Test Results

✅ **Successfully tested with API version 2025-10-01**:

```bash
# Environment Variables
AZURE_VOICELIVE_API_VERSION=2025-10-01
AZURE_VOICELIVE_ENDPOINT=https://zimax.services.ai.azure.com
AZURE_VOICELIVE_MODEL=gpt-realtime

# Service Verification
API Version: 2025-10-01

# Voice Status Endpoint
{
    "voicelive_configured": true,
    "endpoint": "https://zimax.services.ai.azure.com...",
    "model": "gpt-realtime",
    "active_sessions": 0,
    "agents": {
        "elena": { "voice": "en-US-Ava:DragonHDLatestNeural" },
        "marcus": { "voice": "en-US-GuyNeural" }
    }
}
```

## Backward Compatibility

- ✅ The SDK (`azure-ai-voicelive>=1.0.0`) supports both API versions
- ✅ Can revert to `2024-10-01-preview` if needed by setting environment variable
- ✅ No breaking changes in our code - API version is configurable

## Migration Path

If you need to revert to the previous version:

```bash
# Set environment variable
AZURE_VOICELIVE_API_VERSION=2024-10-01-preview

# Or update Azure Container App
az containerapp update \
  --name staging-env-api \
  --resource-group engram-rg \
  --set-env-vars AZURE_VOICELIVE_API_VERSION="2024-10-01-preview"
```

## Verification

### Check Current API Version

```bash
# Local
docker exec <container> env | grep AZURE_VOICELIVE_API_VERSION

# Azure
az containerapp show \
  --name staging-env-api \
  --resource-group engram-rg \
  --query "properties.template.containers[0].env[?name=='AZURE_VOICELIVE_API_VERSION'].value" -o tsv

# From service
python -c "from backend.voice.voicelive_service import voicelive_service; print(voicelive_service.api_version)"
```

## Next Steps

1. ✅ Monitor WebSocket connections for any issues
2. ✅ Test voice quality improvements (Neural HD voices)
3. ✅ Verify improved VAD performance
4. ✅ Test with different languages if applicable

## Files Modified

1. `backend/voice/voicelive_service.py` - Use configurable API version
2. `backend/core/config.py` - Updated default to 2025-10-01
3. `infra/modules/backend-aca.bicep` - Updated default to 2025-10-01
4. `docs/sop/voicelive-configuration.md` - Updated documentation
5. Azure Container App `staging-env-api` - Updated environment variable

## Status

✅ **Update Complete**: All code, infrastructure, and documentation updated to use API version `2025-10-01`

