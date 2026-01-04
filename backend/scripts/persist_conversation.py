#!/usr/bin/env python3
"""
Persist Antigravity Conversations - Capture AI session artifacts to Memory Graph.

Scans the Antigravity brain directory for implementation plans and walkthroughs,
then ingests them into Zep for future agent reference.

Usage:
    # Ingest all recent conversations
    python -m backend.scripts.persist_conversation --env azure
    
    # Ingest a specific conversation
    python -m backend.scripts.persist_conversation --env azure \
        --conversation-id "4f30db73-befb-4a21-bb04-1f20dce67f5f"
    
    # Dry run (show what would be ingested)
    python -m backend.scripts.persist_conversation --env azure --dry-run
"""

import argparse
import asyncio
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Default Antigravity brain directory
DEFAULT_BRAIN_DIR = Path.home() / ".gemini" / "antigravity" / "brain"

# Environment presets
ENVIRONMENT_PRESETS = {
    "local": {"ZEP_API_URL": "http://localhost:8000"},
    "azure": {"ZEP_API_URL": "https://zep.engram.work"},
    "staging": {"ZEP_API_URL": "https://zep-staging.engram.work"},
}


def apply_environment(env_name: str) -> str:
    """Apply environment preset and return the Zep URL."""
    if env_name not in ENVIRONMENT_PRESETS:
        return ENVIRONMENT_PRESETS["azure"]["ZEP_API_URL"]
    
    zep_url = ENVIRONMENT_PRESETS[env_name]["ZEP_API_URL"]
    os.environ["ZEP_API_URL"] = zep_url
    return zep_url


def find_conversation_artifacts(brain_dir: Path, conversation_id: str = None) -> list[dict]:
    """Find all ingestable artifacts in the brain directory."""
    artifacts = []
    
    if not brain_dir.exists():
        print(f"⚠️  Brain directory not found: {brain_dir}")
        return artifacts
    
    # Find conversation directories
    if conversation_id:
        conv_dirs = [brain_dir / conversation_id]
    else:
        conv_dirs = [d for d in brain_dir.iterdir() if d.is_dir()]
    
    for conv_dir in conv_dirs:
        if not conv_dir.exists():
            continue
            
        conv_id = conv_dir.name
        
        # Look for ingestable files
        for artifact_name in ["implementation_plan.md", "walkthrough.md", "task.md"]:
            artifact_path = conv_dir / artifact_name
            if artifact_path.exists():
                # Get modification time
                mtime = datetime.fromtimestamp(artifact_path.stat().st_mtime, tz=timezone.utc)
                
                # Read content
                content = artifact_path.read_text()
                if len(content.strip()) < 50:  # Skip nearly empty files
                    continue
                
                artifacts.append({
                    "conversation_id": conv_id,
                    "artifact_type": artifact_name.replace(".md", ""),
                    "path": artifact_path,
                    "content": content,
                    "modified": mtime,
                })
    
    return artifacts


def extract_title_from_content(content: str, artifact_type: str) -> str:
    """Extract a title from the markdown content."""
    lines = content.strip().split("\n")
    for line in lines[:5]:
        if line.startswith("# "):
            return line[2:].strip()
    return f"Antigravity {artifact_type.replace('_', ' ').title()}"


async def ingest_artifact(
    client,
    artifact: dict,
    env_name: str
):
    """Ingest a single artifact into the Memory Graph."""
    conv_id = artifact["conversation_id"]
    artifact_type = artifact["artifact_type"]
    content = artifact["content"]
    modified = artifact["modified"]
    
    # Generate session ID
    short_conv_id = conv_id[:8]
    session_id = f"antigravity-{artifact_type}-{short_conv_id}"
    
    # Extract title
    title = extract_title_from_content(content, artifact_type)
    
    # Build topics
    topics = ["antigravity", "ai-session", artifact_type.replace("_", "-")]
    
    # Add topics from content keywords
    content_lower = content.lower()
    if "azure" in content_lower:
        topics.append("azure")
    if "voice" in content_lower:
        topics.append("voicelive")
    if "memory" in content_lower or "zep" in content_lower:
        topics.append("memory")
    if "authentication" in content_lower or "auth" in content_lower:
        topics.append("authentication")
    
    topics = list(set(topics))
    
    try:
        # Ensure user exists
        await client.get_or_create_user(
            user_id="antigravity",
            metadata={"role": "ai_agent", "source": "antigravity_session"}
        )
        
        # Create/update session
        await client.get_or_create_session(
            session_id=session_id,
            user_id="antigravity",
            metadata={
                "type": "antigravity_artifact",
                "artifact_type": artifact_type,
                "conversation_id": conv_id,
                "title": title,
                "topics": topics,
                "summary": title,
                "source": "persist_conversation",
                "modified_at": modified.isoformat(),
                "ingested_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        
        # Add content
        await client.add_memory(
            session_id=session_id,
            messages=[{
                "role": "assistant",
                "content": f"# {title}\n\n{content}",
                "metadata": {
                    "source": "antigravity",
                    "artifact_type": artifact_type,
                    "conversation_id": conv_id,
                }
            }],
            metadata={"source": "persist_conversation"}
        )
        
        print(f"  ✅ {artifact_type}: {title[:50]}...")
        return True
        
    except Exception as e:
        print(f"  ❌ {artifact_type}: {e}")
        return False


async def persist_conversations(
    env_name: str = "azure",
    brain_dir: Path = DEFAULT_BRAIN_DIR,
    conversation_id: str = None,
    dry_run: bool = False
):
    """Persist Antigravity conversations to Memory Graph."""
    zep_url = apply_environment(env_name)
    
    print(f"🧠 Persist Antigravity Conversations")
    print(f"   Environment: {env_name.upper()}")
    print(f"   URL: {zep_url}")
    print(f"   Brain Dir: {brain_dir}")
    print("-" * 60)
    
    # Find artifacts
    artifacts = find_conversation_artifacts(brain_dir, conversation_id)
    
    if not artifacts:
        print("No artifacts found to ingest.")
        return
    
    print(f"Found {len(artifacts)} artifacts:\n")
    
    if dry_run:
        for artifact in artifacts:
            title = extract_title_from_content(artifact["content"], artifact["artifact_type"])
            print(f"  📄 {artifact['artifact_type']}: {title[:50]}...")
            print(f"     Conversation: {artifact['conversation_id'][:8]}...")
            print(f"     Modified: {artifact['modified'].isoformat()}")
            print()
        print("(Dry run - no ingestion performed)")
        return
    
    # Import and create client
    from backend.memory.client import ZepMemoryClient
    client = ZepMemoryClient()
    client.zep_url = zep_url
    
    # Ingest each artifact
    success_count = 0
    for artifact in artifacts:
        if await ingest_artifact(client, artifact, env_name):
            success_count += 1
    
    print("-" * 60)
    print(f"✅ Ingested {success_count}/{len(artifacts)} artifacts")
    print(f"   Query with: python -m backend.scripts.query_memory --env {env_name} -q 'antigravity sessions'")


def main():
    parser = argparse.ArgumentParser(
        description="Persist Antigravity conversations to Memory Graph",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Ingest all recent conversations
  python -m backend.scripts.persist_conversation --env azure
  
  # Dry run to see what would be ingested
  python -m backend.scripts.persist_conversation --env azure --dry-run
  
  # Ingest specific conversation
  python -m backend.scripts.persist_conversation --env azure \\
    --conversation-id "4f30db73-befb-4a21-bb04-1f20dce67f5f"
"""
    )
    parser.add_argument("-e", "--env", default="azure",
                        help="Environment: local, azure, staging")
    parser.add_argument("--brain-dir", type=Path, default=DEFAULT_BRAIN_DIR,
                        help="Path to Antigravity brain directory")
    parser.add_argument("--conversation-id",
                        help="Specific conversation ID to ingest")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be ingested without ingesting")
    
    args = parser.parse_args()
    
    asyncio.run(persist_conversations(
        env_name=args.env,
        brain_dir=args.brain_dir,
        conversation_id=args.conversation_id,
        dry_run=args.dry_run
    ))


if __name__ == "__main__":
    main()
