#!/usr/bin/env python3
"""
Ingest Startup Troubleshooting Episode (Dec 28, 2025).

Documents the recurring auth (401) and Zep connectivity issues,
their root causes, and permanent fixes applied to Bicep.
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path.parent))

from backend.core import get_settings
from backend.memory.client import ZepMemoryClient

# Azure Zep URL
ZEP_URL = "https://staging-env-zep.gentleriver-dd0de193.eastus2.azurecontainerapps.io"

SESSION_ID = "finding-startup-auth-zep-url-fix"
USER_ID = "system"

EPISODE_CONTENT = """
# Startup Troubleshooting: Recurring 401 and Zep Connectivity (Dec 28, 2025)

## Problem Summary
After every deployment, two issues would recur:
1. **401 Unauthorized** on api.engram.work (Platform Authentication re-enabling)
2. **Zep connectivity failures** (backend using internal HTTP instead of external HTTPS)

## Root Causes Identified

### Issue 1: Platform Authentication
- **Symptom**: `curl https://api.engram.work/health` returns 401
- **Root Cause**: Azure Static Web Apps identity provider was being detected
- **Location**: `infra/modules/backend-aca.bicep` line 357-374
- **Fix**: Removed commented `identityProviders` section, kept only:
  ```bicep
  platform: { enabled: false }
  globalValidation: { unauthenticatedClientAction: 'AllowAnonymous' }
  ```

### Issue 2: Zep URL Configuration
- **Symptom**: Backend couldn't reach Zep, memory operations failed
- **Root Cause**: `zep-aca.bicep` line 250 was outputting:
  `http://{fqdn}:8000` (internal HTTP with port)
- **Correct URL**: `https://zep.engram.work` (external HTTPS)
- **Fix**: Changed output to use custom domain when enabled:
  ```bicep
  output zepApiUrl string = enableCustomDomain 
    ? 'https://${customDomainName}' 
    : 'https://${zepApp.properties.configuration.ingress.fqdn}'
  ```

## Manual Workaround (Until Bicep Fix Deploys)
```bash
az containerapp auth update --name staging-env-api --resource-group engram-rg --enabled false
```

## Verification Commands
```bash
# Check health (should return 200)
curl -s -o /dev/null -w "%{http_code}" https://api.engram.work/health

# Test chat
curl -s https://api.engram.work/api/v1/chat -X POST \\
  -H "Content-Type: application/json" \\
  -d '{"agent_id":"elena","content":"Hello","session_id":"test"}' | jq .content
```

## Files Modified
1. `infra/modules/zep-aca.bicep` - Fixed zepApiUrl output
2. `infra/modules/backend-aca.bicep` - Cleaned up auth config

## Key Takeaways
- Bicep `authConfig` resource defines auth settings, but must be clean (no commented code)
- Zep URL must use external HTTPS for cross-container communication
- The `:8000` port is internal only - external ingress uses standard HTTPS (443)

## Related Sessions
- `sess-startup-recovery-001`: Initial Azure startup troubleshooting
- `finding-zep-connectivity-fix`: Zep ingress/connectivity fix
- `doc-enterprise-auth-strategy`: Enterprise auth documentation
"""

METADATA = {
    "type": "troubleshooting_finding",
    "date": "2025-12-28",
    "topics": ["Azure", "authentication", "Zep", "Bicep", "401 error", "connectivity", "startup"],
    "summary": "Permanent fix for recurring 401 auth errors and Zep connectivity issues after deployments",
    "severity": "high",
    "resolution": "Bicep updated to use external HTTPS URLs and clean auth config",
}


async def main():
    print("🚀 Ingesting Startup Troubleshooting Episode")
    print(f"Target: {ZEP_URL}")
    print(f"Session: {SESSION_ID}")
    print("-" * 50)
    
    # Configure Zep URL
    settings = get_settings()
    settings.zep_api_url = ZEP_URL
    os.environ["ZEP_API_URL"] = ZEP_URL
    
    memory_client = ZepMemoryClient()
    
    # Ensure system user exists
    try:
        user_payload = {
            "user_id": USER_ID,
            "metadata": {"role": "system", "name": "System Ingestion"}
        }
        await memory_client._request("POST", "/api/v1/users", json=user_payload)
        print("✅ System user confirmed")
    except Exception as e:
        print(f"ℹ️  User note: {e}")
    
    # Create/update session with metadata
    try:
        await memory_client.get_or_create_session(
            session_id=SESSION_ID,
            user_id=USER_ID,
            metadata=METADATA
        )
        print(f"✅ Session created/updated: {SESSION_ID}")
    except Exception as e:
        print(f"⚠️  Session creation note: {e}")
    
    # Add the episode content
    messages = [
        {
            "role": "system",
            "content": EPISODE_CONTENT
        }
    ]
    
    try:
        await memory_client.add_memory(
            session_id=SESSION_ID,
            messages=messages,
            metadata=METADATA
        )
        print(f"✅ Episode ingested ({len(EPISODE_CONTENT)} characters)")
    except Exception as e:
        print(f"❌ Failed to ingest: {e}")
    
    print("-" * 50)
    print("✅ Memory enrichment complete")


if __name__ == "__main__":
    asyncio.run(main())
