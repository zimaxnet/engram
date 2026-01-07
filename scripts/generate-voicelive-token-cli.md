# VoiceLive Token Generation CLI

CLI tool to generate VoiceLive tokens using Azure Managed Identity (DefaultAzureCredential).

## Usage

### Basic Usage

```bash
# Generate token for Elena with video
python scripts/generate-voicelive-token-cli.py --agent elena --modalities video,text

# Generate token for audio only
python scripts/generate-voicelive-token-cli.py --agent elena --modalities audio,text

# Output as JSON (for scripting)
python scripts/generate-voicelive-token-cli.py --agent elena --output json
```

### Options

- `--agent`: Agent ID (`elena`, `marcus`, `sage`) - default: `elena`
- `--modalities`: Comma-separated list of modalities (`audio`, `text`, `video`) - default: `video,text`
- `--output`: Output format (`human` or `json`) - default: `human`

## Authentication

The script uses Azure Managed Identity via `DefaultAzureCredential`, which tries multiple authentication methods in order:

1. **Environment variables** (`AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_TENANT_ID`)
2. **Workload Identity** (AKS)
3. **Managed Identity** (Azure Container Apps, VMs)
4. **Azure CLI** (`az login`)
5. **Azure PowerShell**
6. **Interactive browser** (if enabled)

### For Local Development

If Managed Identity is not available locally, use Azure CLI:

```bash
# Login to Azure
az login

# Set subscription (if needed)
az account set --subscription <subscription-id>

# Run the script
python scripts/generate-voicelive-token-cli.py --agent elena
```

### For Azure Container Apps / VMs

The script will automatically use the Managed Identity assigned to the resource. Ensure the Managed Identity has the `Cognitive Services Speech User` role on the VoiceLive resource.

## Token Generation Strategy

The script uses the same failsafe token generation logic as the API:

1. **Strategy 1**: Managed Identity with current API version
2. **Strategy 2**: Managed Identity with fallback API versions
3. **Strategy 3**: API key with current API version (if available)
4. **Strategy 4**: REST token endpoint for direct endpoints
5. **Strategy 5**: REST token endpoint with fallback API versions

## Output

### Human-readable format (default)

```
======================================================================
✅ Token Generated Successfully
======================================================================

Token Details:
  Token (first 50 chars): eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6...
  Token length: 1234 characters
  Endpoint: wss://zimax.services.ai.azure.com/api/projects/zimax/voice-live/realtime?api-version=2025-10-01&model=gpt-realtime
  Expires at: 2026-01-07T04:00:00Z

Usage:
  Use this token in the 'Authorization: Bearer <token>' header
  Or as 'api-key: <token>' header for WebSocket connections
```

### JSON format

```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6...",
  "endpoint": "wss://zimax.services.ai.azure.com/api/projects/zimax/voice-live/realtime?api-version=2025-10-01&model=gpt-realtime",
  "expires_at": "2026-01-07T04:00:00Z",
  "agent_id": "elena",
  "modalities": ["video", "text"],
  "voice": "en-US-Ava:DragonHDLatestNeural"
}
```

## Troubleshooting

### Error: "Failed to authenticate with Managed Identity"

**Solutions:**
1. Run `az login` for local development
2. Ensure you're in an Azure environment (Container App, VM, etc.)
3. Set environment variables: `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_TENANT_ID`

### Error: "All token generation strategies failed"

**Solutions:**
1. Check Managed Identity has `Cognitive Services Speech User` role
2. Verify endpoint is correct and accessible
3. Check API version compatibility
4. For local testing, set `AZURE_VOICELIVE_KEY`

### Error: "Invalid agent ID"

**Solutions:**
- Use one of: `elena`, `marcus`, `sage`

### Error: "Invalid modality"

**Solutions:**
- Use one of: `audio`, `text`, `video`
- Separate multiple modalities with commas: `video,text`

## Examples

### Generate video token for Elena

```bash
python scripts/generate-voicelive-token-cli.py --agent elena --modalities video,text
```

### Generate audio token for Marcus

```bash
python scripts/generate-voicelive-token-cli.py --agent marcus --modalities audio,text
```

### Get token as JSON for scripting

```bash
TOKEN=$(python scripts/generate-voicelive-token-cli.py --agent elena --output json | jq -r '.token')
echo "Token: $TOKEN"
```

### Test token with curl

```bash
# Get token
TOKEN=$(python scripts/generate-voicelive-token-cli.py --agent elena --output json | jq -r '.token')
ENDPOINT=$(python scripts/generate-voicelive-token-cli.py --agent elena --output json | jq -r '.endpoint')

# Use token (example)
curl -H "Authorization: Bearer $TOKEN" "$ENDPOINT"
```

## Integration with Testing

This CLI tool is useful for:
- Testing token generation locally
- Debugging authentication issues
- Verifying Managed Identity configuration
- Generating tokens for manual testing
- CI/CD pipeline testing

