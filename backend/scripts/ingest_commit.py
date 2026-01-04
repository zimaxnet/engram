#!/usr/bin/env python3
"""
Ingest Git Commit - Capture commit context into Memory Graph.

Called by the post-commit hook to enrich memory with development context.
Runs in background to not block git operations.

Usage (typically called by hook, not manually):
    python -m backend.scripts.ingest_commit \
        --sha abc123 \
        --message "fix: VoiceLive timeout" \
        --author "Derek" \
        --branch "main" \
        --files "voice.py,config.py" \
        --env azure
"""

import argparse
import asyncio
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

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


def extract_topics_from_commit(message: str, files: str) -> list[str]:
    """Extract topic tags from commit message and files."""
    topics = ["commit", "development"]
    
    # Conventional commit prefixes
    prefixes = {
        "fix": ["fix", "bugfix"],
        "feat": ["feature", "enhancement"],
        "docs": ["documentation"],
        "refactor": ["refactor"],
        "test": ["testing"],
        "chore": ["maintenance"],
        "perf": ["performance"],
        "style": ["style", "formatting"],
    }
    
    msg_lower = message.lower()
    for prefix, tags in prefixes.items():
        if msg_lower.startswith(f"{prefix}:") or msg_lower.startswith(f"{prefix}("):
            topics.extend(tags)
            break
    
    # Extract component from files
    file_list = [f.strip() for f in files.split(",") if f.strip()]
    for f in file_list:
        if "voice" in f.lower():
            topics.append("voicelive")
        if "auth" in f.lower():
            topics.append("authentication")
        if "memory" in f.lower() or "zep" in f.lower():
            topics.append("memory")
        if "temporal" in f.lower():
            topics.append("temporal")
        if "frontend" in f.lower() or ".tsx" in f or ".css" in f:
            topics.append("frontend")
        if "backend" in f.lower() or ".py" in f:
            topics.append("backend")
        if "infra" in f.lower() or ".bicep" in f:
            topics.append("infrastructure")
    
    return list(set(topics))


async def ingest_commit(
    sha: str,
    message: str,
    author: str,
    branch: str,
    files: str,
    env_name: str = "azure"
):
    """Ingest commit context into the Memory Graph."""
    zep_url = apply_environment(env_name)
    
    # Import after environment is set
    from backend.memory.client import ZepMemoryClient
    
    client = ZepMemoryClient()
    client.zep_url = zep_url
    
    # Generate session ID using short SHA
    short_sha = sha[:7] if len(sha) >= 7 else sha
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    session_id = f"commit-{timestamp}-{short_sha}"
    
    # Extract topics
    topics = extract_topics_from_commit(message, files)
    
    # Build content
    files_list = [f.strip() for f in files.split(",") if f.strip()]
    files_display = "\n".join([f"  - {f}" for f in files_list[:10]])
    if len(files_list) > 10:
        files_display += f"\n  - ... and {len(files_list) - 10} more"
    
    content = f"""# Git Commit: {short_sha}

**Branch:** {branch}
**Author:** {author}
**Date:** {datetime.now(timezone.utc).isoformat()}

## Message
{message}

## Files Changed
{files_display if files_display else "  (no files recorded)"}

## Topics
{', '.join(topics)}
"""
    
    try:
        # Ensure user exists
        await client.get_or_create_user(
            user_id="developer",
            metadata={"role": "developer", "source": "git_commit"}
        )
        
        # Create session with metadata
        await client.get_or_create_session(
            session_id=session_id,
            user_id="developer",
            metadata={
                "type": "commit",
                "sha": sha,
                "short_sha": short_sha,
                "branch": branch,
                "author": author,
                "topics": topics,
                "summary": message[:200],
                "files_changed": files_list[:10],
                "source": "post_commit_hook",
                "ingested_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        
        # Add content as a message
        await client.add_memory(
            session_id=session_id,
            messages=[{
                "role": "assistant",
                "content": content,
                "metadata": {"source": "git_commit", "sha": sha}
            }],
            metadata={"source": "post_commit_hook"}
        )
        
        # Silent success (running in background)
        
    except Exception:
        # Silent failure (don't disrupt git operations)
        pass


def main():
    parser = argparse.ArgumentParser(description="Ingest git commit to memory")
    parser.add_argument("--sha", required=True, help="Commit SHA")
    parser.add_argument("--message", required=True, help="Commit message")
    parser.add_argument("--author", default="unknown", help="Commit author")
    parser.add_argument("--branch", default="unknown", help="Branch name")
    parser.add_argument("--files", default="", help="Comma-separated changed files")
    parser.add_argument("--env", default="azure", help="Environment: local, azure, staging")
    
    args = parser.parse_args()
    
    asyncio.run(ingest_commit(
        sha=args.sha,
        message=args.message,
        author=args.author,
        branch=args.branch,
        files=args.files,
        env_name=args.env
    ))


if __name__ == "__main__":
    main()
