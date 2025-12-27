# VoiceLive Voice Configuration Update

**Date**: 2025-12-27  
**Status**: ✅ Complete

## Summary

Updated VoiceLive voice configurations for all three agents to use Dragon HD Latest voices:

- **Elena**: `en-US-Seraphina:DragonHDLatestNeural`
- **Marcus**: `en-US-Ollie:DragonHDLatestNeural`
- **Sage**: `en-US-Brian:DragonHDLatestNeural` (newly added)

## Changes Made

### 1. `backend/core/config.py`

Added new configuration setting for Sage voice:
```python
sage_voicelive_voice: str = Field("en-US-Brian:DragonHDLatestNeural", alias="SAGE_VOICELIVE_VOICE")
```

Updated default values:
- `azure_voicelive_voice`: Changed from `en-US-Ava:DragonHDLatestNeural` to `en-US-Seraphina:DragonHDLatestNeural`
- `marcus_voicelive_voice`: Changed from `en-US-GuyNeural` to `en-US-Ollie:DragonHDLatestNeural`

### 2. `backend/voice/voicelive_service.py`

- Added Sage to `_agent_voices` dictionary with:
  - Voice: `en-US-Brian:DragonHDLatestNeural`
  - Instructions: Comprehensive storytelling and visualization instructions
  - Personality: "eloquent, visual, empathetic, synthesizing storyteller"

- Added `_get_sage_instructions()` method with detailed system instructions for Sage's voice interactions

- Updated comments to reflect new voice names

### 3. `backend/api/routers/voice.py`

- Added Sage to the `/api/v1/voice/status` endpoint response
- Now returns voice configuration for all three agents: elena, marcus, and sage

## Voice Details

### Elena (Seraphina Dragon HD Latest)
- **Voice ID**: `en-US-Seraphina:DragonHDLatestNeural`
- **Personality**: Warm, measured, professional with Miami accent
- **Use Case**: Business analysis, requirements gathering, stakeholder communication

### Marcus (Ollie Dragon HD Latest)
- **Voice ID**: `en-US-Ollie:DragonHDLatestNeural`
- **Personality**: Confident, energetic, Pacific Northwest professional
- **Use Case**: Project management, risk assessment, team coordination

### Sage (Brian Dragon HD Latest)
- **Voice ID**: `en-US-Brian:DragonHDLatestNeural`
- **Personality**: Eloquent, visual, empathetic, synthesizing storyteller
- **Use Case**: Technical storytelling, architecture visualization, documentation narratives

## Environment Variables

The voice configurations can be overridden via environment variables:

```bash
AZURE_VOICELIVE_VOICE=en-US-Seraphina:DragonHDLatestNeural  # Elena
MARCUS_VOICELIVE_VOICE=en-US-Ollie:DragonHDLatestNeural      # Marcus
SAGE_VOICELIVE_VOICE=en-US-Brian:DragonHDLatestNeural        # Sage
```

## Testing

To verify the voice configurations:

1. **Check status endpoint**:
   ```bash
   curl https://staging-env-api.gentleriver-dd0de193.eastus2.azurecontainerapps.io/api/v1/voice/status | jq '.agents'
   ```

2. **Expected response**:
   ```json
   {
     "agents": {
       "elena": {
         "voice": "en-US-Seraphina:DragonHDLatestNeural"
       },
       "marcus": {
         "voice": "en-US-Ollie:DragonHDLatestNeural"
       },
       "sage": {
         "voice": "en-US-Brian:DragonHDLatestNeural"
       }
     }
   }
   ```

3. **Test VoiceLive from frontend**:
   - Switch between agents (Elena, Marcus, Sage)
   - Verify each agent uses the correct Dragon HD voice
   - Confirm voice quality and characteristics match expectations

## Next Steps

1. ✅ Code changes complete
2. ⏳ Deploy to Azure (backend will automatically use new voices)
3. ⏳ Test VoiceLive with each agent from frontend
4. ⏳ Verify voice quality and characteristics

## Notes

- Dragon HD Latest voices provide enhanced quality and expressiveness
- All three agents now have distinct, high-quality voices
- Sage voice configuration is new - previously inherited Elena's voice
- Changes are backward compatible - existing sessions will use new voices on next connection

