#!/usr/bin/env python3
"""
Ingest Sage SOP into Zep for Agent Awareness.
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

async def ingest_sage_sop():
    """Ingest the Sage Nano Banana SOP as a document session"""
    
    settings = get_settings()
    zep_url = os.environ.get("ZEP_API_URL", settings.zep_api_url)
    
    if not zep_url:
        print("❌ ZEP_API_URL not set.")
        return

    memory_client = ZepMemoryClient()
    
    # Session ID convention for docs: doc-[type]-[slug]
    session_id = "doc-sop-sage-nano-banana"
    
    # Read the SOP content
    sop_path = Path(__file__).parent.parent / "docs/sop/sage_nano_banana.md"
    try:
        with open(sop_path, "r") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"❌ SOP file not found at {sop_path}")
        return

    print(f"📝 Ingesting Sage SOP: {session_id}")
    
    # 1. Create/Update Session with rich metadata for search
    try:
        session = await memory_client.get_or_create_session(
            session_id=session_id,
            user_id="system", # Owned by system
            metadata={
                "title": "SOP: Sage Visual & Memory Capabilities",
                "summary": "Standard Operating Procedure for using Nano Banana Pro (Gemini 3) image generation and understanding Memory Enrichment protocols.",
                "topics": ["sage", "nano banana pro", "gemini 3", "image generation", "memory enrichment", "sop", "documentation"],
                "type": "documentation",
                "source": "docs/sop/sage_nano_banana.md",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        )
        print(f"✅ Session metadata updated")
    except Exception as e:
        print(f"⚠️  Session update warning: {e}")

    # 2. Add content as a system message
    # We chunk it slightly for better readability if needed, but Zep handles large messages reasonably well for search.
    # We'll ingest it as a single coherent document message.
    messages = [
        {
            "role": "system", 
            "content": content,
            "metadata": {"type": "document_content"}
        }
    ]
    
    try:
        await memory_client.add_memory(
            session_id=session_id,
            messages=messages,
            metadata={
                "ingested_at": datetime.now(timezone.utc).isoformat()
            }
        )
        print(f"✅ Content ingested into Zep")
    except Exception as e:
        print(f"❌ Failed to ingest content: {e}")

if __name__ == "__main__":
    asyncio.run(ingest_sage_sop())
