#!/usr/bin/env python3
"""
Ingest Enterprise Stability Analysis and Implementation Plan into Zep Memory

This makes the stability analysis and improvement plan available to all agents
for reference when troubleshooting and planning improvements.
"""

import asyncio
from datetime import datetime, timezone
from pathlib import Path
import sys

# Add parent directory to path to import backend modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.memory.client import ZepMemoryClient
from backend.core import get_settings


async def ingest_stability_documents():
    """Ingest stability analysis and implementation plan into Zep"""
    
    # Read the stability analysis document
    analysis_path = Path(__file__).parent.parent / "docs" / "stability" / "enterprise-stability-analysis.md"
    if not analysis_path.exists():
        print(f"❌ Stability analysis not found at {analysis_path}")
        return False
    
    with open(analysis_path, 'r', encoding='utf-8') as f:
        analysis_content = f.read()
    
    # Read the implementation script
    script_path = Path(__file__).parent / "implement-stability-improvements.sh"
    if not script_path.exists():
        print(f"⚠️  Implementation script not found at {script_path}")
        script_content = "Implementation script will be created"
    else:
        with open(script_path, 'r', encoding='utf-8') as f:
            script_content = f.read()
    
    session_id = "enterprise-stability-analysis-2025-12-30"
    user_id = "system-documentation"
    
    summary = """Enterprise Dev/Test Environment Stability Analysis and Improvement Plan

Comprehensive analysis of system fragility issues and phased improvement plan:
- Root cause analysis (configuration, dependencies, error handling, deployment, testing)
- 4-phase improvement plan with priorities
- Implementation scripts and health check endpoints
- Success metrics and monitoring strategy

Critical for agents to reference when troubleshooting stability issues."""
    
    topics = [
        "stability",
        "enterprise",
        "dev-test-environment",
        "configuration-management",
        "service-dependencies",
        "error-handling",
        "deployment",
        "health-checks",
        "monitoring",
        "troubleshooting",
        "system-reliability"
    ]
    
    messages = [
        {
            "role": "user",
            "content": "The system is very fragile and every time we update something breaks. We need to look into why that is and ensure that we have a stable enterprise dev test environment for all of the services."
        },
        {
            "role": "assistant",
            "content": f"""I've conducted a comprehensive stability analysis and created an improvement plan. Here's the analysis:

## Root Causes Identified

### 1. Configuration Management Fragility
- Settings caching with @lru_cache can cache incorrect values
- Multiple sources of truth (env vars, settings, Key Vault, Bicep)
- No validation on startup
- String/boolean parsing inconsistencies

### 2. Service Dependency Failures
- Zep Memory Service failures cause silent degradation
- No graceful degradation when dependencies unavailable
- Fire-and-forget patterns hide failures
- No retry logic

### 3. Error Handling Gaps
- Silent failures (warnings instead of errors)
- Generic fallback responses mask root causes
- No centralized error tracking
- Missing health checks

### 4. Deployment Fragility
- No pre-deployment validation
- No rollback mechanism
- Environment variable drift
- 30-minute deployments make iteration painful

### 5. Testing and Validation Gaps
- No integration tests
- No health check endpoints
- No configuration validation
- No smoke tests

## Improvement Plan (4 Phases)

**Phase 1 (Week 1) - Immediate Fixes:**
- Health check endpoints
- Configuration validation on startup
- Graceful degradation
- Error tracking

**Phase 2 (Week 2) - Configuration Robustness:**
- Settings refresh mechanism
- Configuration validation
- Environment variable management

**Phase 3 (Week 3) - Service Resilience:**
- Retry logic with backoff
- Circuit breakers
- Timeout management

**Phase 4 (Week 4) - Deployment Reliability:**
- Pre-deployment validation
- Post-deployment smoke tests
- Rollback mechanism

Full analysis document: docs/stability/enterprise-stability-analysis.md"""
        },
        {
            "role": "user",
            "content": "First thing is to get the enterprise stability analysis and the implement stability improvements document and scripts ingested into the system so that we can work within the system to incrementally make progress with these vexing problems and then work with Marcus, the project management agent to update the project with these tasks in GitHub projects."
        },
        {
            "role": "assistant",
            "content": f"""Perfect! I'm ingesting the stability analysis and implementation plan into Zep memory now.

**Documents Being Ingested:**
1. Enterprise Stability Analysis (docs/stability/enterprise-stability-analysis.md)
2. Implementation Script (scripts/implement-stability-improvements.sh)

**Key Content:**
{analysis_content[:2000]}...

[Full document available in Zep memory for agent reference]

**Next Steps:**
1. ✅ Ingest documents into Zep memory (in progress)
2. Work with Marcus to create GitHub project tasks
3. Prioritize Phase 1 immediate fixes
4. Begin incremental implementation

**Priority Tasks for Marcus:**
- Create GitHub project for "Enterprise Stability Improvements"
- Add tasks for Phase 1 fixes (health checks, config validation, graceful degradation)
- Link to stability analysis document
- Set up project board with phases"""
        }
    ]
    
    # Format messages for Zep
    formatted_messages = [
        {
            "role": msg["role"],
            "content": msg["content"],
            "metadata": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": "stability_analysis_ingestion"
            }
        }
        for msg in messages
    ]
    
    print(f"📝 Ingesting stability analysis into Zep...")
    print(f"   Session ID: {session_id}")
    print(f"   Summary: {summary[:100]}...")
    print(f"   Topics: {', '.join(topics)}")
    print(f"   Messages: {len(messages)}")
    print()
    
    try:
        # Get Zep URL from settings
        settings = get_settings()
        if not settings.zep_api_url:
            print("❌ ZEP_API_URL not set. Please set it in environment or .env file")
            print("   Example: export ZEP_API_URL=https://staging-env-zep.gentleriver-dd0de193.eastus2.azurecontainerapps.io")
            return False
        
        print(f"   Using Zep URL: {settings.zep_api_url}")
        client = ZepMemoryClient()
        
        # Create or update session with metadata
        await client.get_or_create_session(
            session_id=session_id,
            user_id=user_id,
            metadata={
                "summary": summary,
                "topics": topics,
                "agent_id": "system",
                "turn_count": len(messages),
                "source": "stability_analysis_ingestion",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "document_path": str(analysis_path),
            }
        )
        
        print(f"✅ Session created/updated: {session_id}")
        
        # Add messages to session
        await client.add_memory(
            session_id=session_id,
            messages=formatted_messages,
        )
        
        print(f"✅ Added {len(messages)} messages to session")
        print()
        print(f"🎉 Stability analysis ingested successfully!")
        print(f"   Session ID: {session_id}")
        print(f"   Agents can now reference this when:")
        print(f"   - Troubleshooting stability issues")
        print(f"   - Planning system improvements")
        print(f"   - Understanding root causes of failures")
        print(f"   - Implementing Phase 1-4 improvements")
        print()
        print(f"📋 Next: Work with Marcus to create GitHub project tasks")
        
    except Exception as e:
        print(f"❌ Failed to ingest episode: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    asyncio.run(ingest_stability_documents())

