#!/usr/bin/env python3
"""
Ingest auth robustness discussion episode into Zep (Azure deployment).
Run this script in Azure or with proper ZEP_API_URL configured.
"""

import asyncio
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path.parent))

from backend.core import get_settings
from backend.memory.client import ZepMemoryClient


async def ingest_episode():
    """Ingest auth robustness discussion into Zep"""
    
    settings = get_settings()
    
    if not settings.zep_api_url:
        print("❌ ZEP_API_URL not configured. Set it to your Zep endpoint.")
        return
    
    memory_client = ZepMemoryClient()
    
    session_id = "auth-robustness-discussion-001"
    user_id = "system"
    
    print(f"📝 Creating Zep episode: {session_id}")
    print(f"   Zep URL: {settings.zep_api_url}")
    
    # Create session
    try:
        session = await memory_client.get_or_create_session(
            session_id=session_id,
            user_id=user_id,
            metadata={
                "topic": "authentication",
                "type": "technical_discussion",
                "participants": ["elena", "markus"],
                "priority": "high",
                "status": "open_for_discussion",
                "created_by": "system",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        )
        print(f"✅ Session created/retrieved: {session.get('session_id', session_id)}")
    except Exception as e:
        print(f"⚠️  Session creation warning: {e}")
        print("   Continuing with episode creation...")
    
    # Episode content - discussion between Elena and Markus
    messages = [
        {
            "role": "user",
            "content": """Elena and Markus, I need your input on a critical authentication robustness issue we discovered during POC deployment.

**Problem**: The authentication system is fragile - when AUTH_REQUIRED=false is set, all API endpoints still return 401 Unauthorized errors. This blocks Chat, VoiceLive, and Episodes functionality.

**Root Causes Identified**:
1. Settings caching may prevent environment variable updates from taking effect
2. Environment variable parsing (string "false" to boolean) may fail silently
3. No validation or logging to diagnose auth configuration issues
4. Single point of failure - one boolean flag controls everything

**Impact**: 
- POC deployments fail silently
- Difficult to diagnose auth issues
- Enterprise deployment risk

**Proposed Solutions**:
1. Enhanced settings validation with explicit type checking
2. Defensive auth bypass with logging
3. Health check endpoint to verify auth configuration
4. Multi-level auth configuration (not just on/off)
5. Configuration service integration for dynamic updates

**Questions for Discussion**:
1. Should we implement multi-level auth configuration now, or keep it simple for POC?
2. How should we handle auth configuration in production vs staging?
3. What monitoring/alerting do we need for auth health?
4. Should auth bypass be tenant-specific or global?

Please review the plan in `docs/enterprise-auth-robustness-plan.md` and let me know your thoughts."""
        },
        {
            "role": "assistant",
            "content": """This is an excellent analysis of the authentication robustness issue. Let me break down the key concerns and recommendations:

**Immediate Actions (POC Readiness)**:
- ✅ Fix the auth bypass logic with explicit boolean checks
- ✅ Add comprehensive logging for auth decisions
- ✅ Create a health check endpoint to verify configuration
- ✅ Test all components after fixes

**Architecture Considerations**:
- The single boolean flag is indeed fragile. A multi-level configuration would be more robust.
- Settings caching is a performance optimization but can cause issues. We need a refresh mechanism.
- Configuration should be environment-aware (dev/staging/prod).

**Enterprise Readiness**:
- Auth configuration should be in Azure App Configuration or Key Vault
- Need tenant-specific auth policies for multi-tenant scenarios
- Monitoring and alerting are critical - we should alert if auth bypass is active in production

**Recommendation**:
1. Fix the immediate issue for POC (Phase 1)
2. Implement multi-level auth config in next sprint (Phase 2)
3. Move to configuration service for enterprise deployment (Phase 3)

This phased approach balances POC needs with enterprise requirements."""
        },
        {
            "role": "user",
            "content": """Markus, from a security and operations perspective, what are your concerns about the current approach and the proposed solutions?"""
        },
        {
            "role": "assistant",
            "content": """From a security operations perspective, I have several concerns:

**Security Concerns**:
1. **Silent Failures**: If auth bypass fails silently, we could have unauthenticated access in production without knowing it
2. **Configuration Drift**: Environment variables can be changed accidentally or maliciously
3. **No Audit Trail**: We need to log every auth decision for compliance

**Operational Concerns**:
1. **Debugging Difficulty**: Without proper logging, diagnosing auth issues takes too long
2. **Deployment Risk**: Configuration errors can break entire deployments
3. **Monitoring Gap**: We can't see auth health in real-time

**Recommendations**:
1. **Defense in Depth**: Don't rely on a single boolean - use multiple checks
2. **Fail Secure**: Default to auth enabled if configuration is unclear
3. **Audit Everything**: Log all auth decisions with request IDs
4. **Health Monitoring**: Real-time dashboard showing auth status
5. **Automated Testing**: Test auth in all modes before deployment

**For POC**:
- Auth bypass is acceptable for demos, but we MUST have:
  - Clear logging when bypass is active
  - Health check endpoint to verify state
  - Alert if bypass is active in production-like environments

**For Enterprise**:
- Move to Azure App Configuration for centralized management
- Implement tenant-specific policies
- Add automated compliance checks
- Regular security audits of auth configuration"""
        },
        {
            "role": "user",
            "content": """Based on this discussion, what's our action plan?"""
        },
        {
            "role": "assistant",
            "content": """**Immediate Action Plan (This Week)**:

1. **Fix Auth Bypass Logic** ✅
   - Enhanced boolean checks with explicit type validation
   - Added debug logging for auth configuration
   - Fail-safe defaults

2. **Create Health Check Endpoint**
   - `/api/v1/auth/status` to verify auth configuration
   - Returns current auth mode, user context, settings state
   - Helps diagnose issues without affecting other endpoints

3. **Test All Components**
   - Verify Chat, VoiceLive, and Episodes work with auth bypass
   - Test with auth enabled to ensure it still works
   - Document test results

4. **Documentation**
   - Enterprise auth robustness plan created
   - This episode for Elena/Markus discussion
   - Update deployment docs with auth configuration

**Next Sprint (Phase 2)**:
- Multi-level auth configuration
- Settings refresh mechanism
- Comprehensive logging
- Health monitoring dashboard

**Enterprise (Phase 3)**:
- Azure App Configuration integration
- Multi-tenant auth policies
- Automated compliance checks
- Security audit integration

**Success Criteria**:
- ✅ All endpoints work with AUTH_REQUIRED=false
- ✅ Auth configuration visible in logs
- ✅ Health check endpoint functional
- ✅ No silent failures
- ✅ Easy to diagnose auth issues"""
        }
    ]
    
    # Add messages to session
    try:
        await memory_client.add_memory(
            session_id=session_id,
            messages=messages,
            metadata={
                "topic": "authentication_robustness",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "participants": ["elena", "markus"],
                "status": "open_for_discussion",
                "priority": "high",
                "episode_type": "technical_discussion"
            }
        )
        print(f"✅ Added {len(messages)} messages to episode")
    except Exception as e:
        print(f"⚠️  Memory ingestion warning: {e}")
        print("   Episode may have been partially created")
    
    print(f"\n📋 Episode Summary:")
    print(f"   - Session ID: {session_id}")
    print(f"   - Topic: Authentication Robustness")
    print(f"   - Participants: Elena, Markus")
    print(f"   - Status: Open for discussion")
    print(f"   - Priority: High")
    print(f"   - Messages: {len(messages)}")
    print(f"\n🔗 View episode at: {settings.zep_api_url}/api/v1/sessions/{session_id}")
    
    return session_id


if __name__ == "__main__":
    asyncio.run(ingest_episode())

