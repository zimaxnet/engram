#!/usr/bin/env python3
"""
Quick Ingest - Capture learnings to Memory Graph instantly.

Use this during development to persist insights, bug fixes, and discoveries
that should be available to AI agents in future sessions.

Usage:
    # Ingest a learning
    python -m backend.scripts.quick_ingest --env azure \
        --topic "voicelive-timeout" \
        --content "Fixed VoiceLive timeout by wrapping connect() in asyncio.wait_for()"
    
    # Ingest from stdin (pipe from clipboard)
    pbpaste | python -m backend.scripts.quick_ingest --env azure --topic "my-topic"
    
    # Ingest with tags
    python -m backend.scripts.quick_ingest --env azure \
        --topic "authentication" \
        --tags "fix,ciam,entra" \
        --content "Entra External ID uses GUID issuer, not domain name"
"""

import argparse
import asyncio
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Environment presets (shared with query_memory.py)
ENVIRONMENT_PRESETS = {
    "local": {
        "ZEP_API_URL": "http://localhost:8000",
        "description": "Local development Zep",
    },
    "azure": {
        "ZEP_API_URL": "https://zep.engram.work",
        "description": "Azure Container Apps (Production)",
    },
    "staging": {
        "ZEP_API_URL": "https://zep-staging.engram.work",
        "description": "Azure Staging Environment",
    },
}


def apply_environment(env_name: str) -> str:
    """Apply environment preset and return the Zep URL."""
    if env_name not in ENVIRONMENT_PRESETS:
        print(f"❌ Unknown environment: {env_name}")
        print(f"   Available: {', '.join(ENVIRONMENT_PRESETS.keys())}")
        sys.exit(1)
    
    preset = ENVIRONMENT_PRESETS[env_name]
    zep_url = preset["ZEP_API_URL"]
    os.environ["ZEP_API_URL"] = zep_url
    return zep_url


async def quick_ingest(
    topic: str,
    content: str,
    tags: list[str],
    env_name: str = "azure",
    user_id: str = "developer"
):
    """Ingest a quick learning into the Memory Graph."""
    zep_url = apply_environment(env_name)
    
    # Import after environment is set
    from backend.memory.client import ZepMemoryClient
    
    client = ZepMemoryClient()
    client.zep_url = zep_url
    
    # Generate session ID
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    session_id = f"learning-{topic}-{timestamp}"
    
    # Combine topic with other tags
    all_tags = list(set([topic, "learning", "vibe-coding"] + tags))
    
    print(f"🧠 Quick Ingest to Memory Graph")
    print(f"   Environment: {env_name.upper()}")
    print(f"   URL: {zep_url}")
    print(f"   Topic: {topic}")
    print(f"   Tags: {', '.join(all_tags)}")
    print(f"   Content: {len(content)} chars")
    print("-" * 60)
    
    try:
        # Ensure user exists
        await client.get_or_create_user(
            user_id=user_id,
            metadata={"role": "developer", "source": "quick_ingest"}
        )
        
        # Create session with metadata
        await client.get_or_create_session(
            session_id=session_id,
            user_id=user_id,
            metadata={
                "type": "learning",
                "topic": topic,
                "topics": all_tags,
                "summary": content[:200] + "..." if len(content) > 200 else content,
                "source": "quick_ingest",
                "ingested_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        
        # Add content as a message
        messages = [
            {
                "role": "assistant",
                "content": f"# Learning: {topic.replace('-', ' ').title()}\n\n{content}",
                "metadata": {
                    "source": "quick_ingest",
                    "topic": topic,
                    "tags": all_tags,
                }
            }
        ]
        
        await client.add_memory(
            session_id=session_id,
            messages=messages,
            metadata={"source": "quick_ingest", "topic": topic}
        )
        
        print(f"✅ Ingested as: {session_id}")
        print(f"   Query with: python -m backend.scripts.query_memory --env {env_name} -q \"{topic}\"")
        
    except Exception as e:
        print(f"❌ Failed to ingest: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Quick ingest learnings into Engram Memory Graph",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Ingest a bug fix
  python -m backend.scripts.quick_ingest --env azure \\
    --topic "voicelive-timeout" \\
    --content "Fixed by wrapping connect() in asyncio.wait_for(10s)"
  
  # Ingest with multiple tags
  python -m backend.scripts.quick_ingest --env azure \\
    --topic "authentication" \\
    --tags "ciam,entra,fix" \\
    --content "Entra External ID uses GUID issuer format"
  
  # Ingest from stdin (clipboard)
  pbpaste | python -m backend.scripts.quick_ingest --env azure --topic "my-discovery"
"""
    )
    parser.add_argument("-e", "--env", default="azure",
                        help="Environment: local, azure, staging (default: azure)")
    parser.add_argument("-t", "--topic", required=True,
                        help="Topic/category for this learning (use-kebab-case)")
    parser.add_argument("-c", "--content", 
                        help="Content to ingest (or pipe from stdin)")
    parser.add_argument("--tags", default="",
                        help="Comma-separated additional tags")
    parser.add_argument("-u", "--user-id", default="developer",
                        help="User ID for the ingestion (default: developer)")
    
    args = parser.parse_args()
    
    # Get content from args or stdin
    content = args.content
    if not content:
        if not sys.stdin.isatty():
            content = sys.stdin.read().strip()
        else:
            print("❌ Error: --content required, or pipe content via stdin")
            sys.exit(1)
    
    # Parse tags
    tags = [t.strip() for t in args.tags.split(",") if t.strip()]
    
    asyncio.run(quick_ingest(
        topic=args.topic,
        content=content,
        tags=tags,
        env_name=args.env,
        user_id=args.user_id
    ))


if __name__ == "__main__":
    main()
