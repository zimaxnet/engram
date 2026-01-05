#!/usr/bin/env python3
"""
IDE Memory Enrichment Script

This script pushes context from IDE chat sessions (Cursor, Windsurf, Antigravity, etc.)
to Engram's long-term memory. This enables the "Self-Enriching Workflow" where
knowledge discovered during debugging/development is preserved across all agents.

Usage:
    # Set required environment variables
    export ENGRAM_API_URL="https://engram.work"
    export ENGRAM_API_TOKEN="your-jwt-token"

    # Push a single context item
    python scripts/enrich_from_ide.py --text "We discovered that visuals are generated via Imagen 3.0"

    # Push with session continuity
    python scripts/enrich_from_ide.py --session "ide-debugging-2026-01-04" --text "Root cause: stories created via direct API don't trigger the Temporal workflow"

    # Push as assistant (AI perspective)
    python scripts/enrich_from_ide.py --speaker assistant --text "The visual generation pipeline uses generate_image_activity"
"""

import argparse
import json
import os
import sys
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.error import HTTPError


def enrich_memory(
    text: str,
    session_id: str | None = None,
    speaker: str = "user",
    agent_id: str = "ide-agent",
    channel: str = "ide",
) -> dict:
    """Push context to Engram memory via the /enrich endpoint."""
    
    api_url = os.getenv("ENGRAM_API_URL", "https://engram.work")
    api_token = os.getenv("ENGRAM_API_TOKEN")
    
    if not api_token:
        print("ERROR: ENGRAM_API_TOKEN environment variable required", file=sys.stderr)
        sys.exit(1)
    
    # Generate session ID if not provided
    if not session_id:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        session_id = f"ide-{timestamp}"
    
    url = f"{api_url}/api/v1/memory/enrich"
    
    payload = {
        "text": text,
        "session_id": session_id,
        "speaker": speaker,
        "agent_id": agent_id,
        "channel": channel,
    }
    
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
    }
    
    try:
        request = Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
        with urlopen(request, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result
    except HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else str(e)
        return {"success": False, "error": error_body, "status": e.code}
    except Exception as e:
        return {"success": False, "error": str(e)}


def main():
    parser = argparse.ArgumentParser(
        description="Push IDE context to Engram memory",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--text", "-t", required=True, help="The text/context to enrich")
    parser.add_argument("--session", "-s", help="Session ID for continuity (optional)")
    parser.add_argument("--speaker", choices=["user", "assistant"], default="user", help="Speaker role")
    parser.add_argument("--agent", "-a", default="ide-agent", help="Agent ID (default: ide-agent)")
    parser.add_argument("--channel", "-c", default="ide", help="Channel name (default: ide)")
    
    args = parser.parse_args()
    
    print(f"Enriching memory: {args.text[:80]}...")
    
    result = enrich_memory(
        text=args.text,
        session_id=args.session,
        speaker=args.speaker,
        agent_id=args.agent,
        channel=args.channel,
    )
    
    if result.get("success"):
        print(f"✅ Memory enriched successfully!")
        print(f"   Session ID: {result.get('session_id')}")
        print(f"   Message: {result.get('message')}")
    else:
        print(f"❌ Enrichment failed: {result.get('error', result.get('message', 'Unknown error'))}")
        sys.exit(1)


if __name__ == "__main__":
    main()
