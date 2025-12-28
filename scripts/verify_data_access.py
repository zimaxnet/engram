#!/usr/bin/env python3
"""
Verify Agent Data Access (GitHub & Wiki) via Azure API.
"""

import asyncio
import sys
import json
import httpx
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path.parent))

# Azure API URL - User requested custom domain
API_URL = "https://api.engram.work/api/v1/chat"

PROMPTS = [
    {
        "name": "GitHub Access",
        "content": "Use your tools to check the status of the 'Production-Grade System Implementation' project on GitHub. What is the current progress?"
    },
    {
        "name": "Wiki/Doc Access",
        "content": "What are the key points of the 'Enterprise Auth Strategy' document currently in your memory?"
    }
]

async def trigger_verification(prompt_name, content):
    print(f"\n🚀 Testing {prompt_name}...")
    print(f"Prompt: {content}")
    
    payload = {
        "content": content,
        "session_id": f"verify-access-{prompt_name.lower().replace(' ', '-')}",
        "user_id": "derek", 
        "agent_id": "elena",
        "stream": True
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            async with client.stream("POST", API_URL, json=payload) as response:
                if response.status_code != 200:
                    print(f"❌ Error: {response.status_code}")
                    print(await response.aread())
                    return

                print(f"💬 Elena's Response:")
                print("-" * 40)
                async for chunk in response.aiter_bytes():
                    if chunk:
                        print(chunk.decode("utf-8"), end="", flush=True)
                print("\n" + "-" * 40)
                print("✅ Stream finished.")
        except Exception as e:
            print(f"❌ Failed to connect: {e}")

async def main():
    print(f"TARGET: {API_URL}")
    for prompt in PROMPTS:
        await trigger_verification(prompt["name"], prompt["content"])
        await asyncio.sleep(2) # Brief pause

if __name__ == "__main__":
    asyncio.run(main())
