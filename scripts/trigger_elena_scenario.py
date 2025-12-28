#!/usr/bin/env python3
"""
Trigger Elena to analyze the Startup Recovery episode and delegate to Sage.
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
import httpx

# API URL (Azure POC)
API_URL = "https://staging-env-api.gentleriver-dd0de193.eastus2.azurecontainerapps.io/api/v1/chat"

async def trigger_elena():
    print(f"🚀 Triggering Elena on {API_URL}...")
    
    # Prompt derived from user request
    prompt = (
        "Elena, please review the 'system_recovery_troubleshooting' episode we just experienced (sess-startup-recovery-20251228). "
        "1. Write a comprehensive Business Analysis of what it takes to get the system ready for customers, establishing the business value of this reliability work. "
        "2. Then, DELEGATE to Sage (using your tools) to create a visual 'Success Story' and image for the navigation UI that represents this 'Road to Reliability'. "
        "3. Confirm when the delegation is complete."
    )
    
    payload = {
        "content": prompt,
        "agent_id": "elena",
        "user_id": "derek", 
        "session_id": f"chat-demo-{datetime.now().strftime('%H%M%S')}" # New chat session for this interaction
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            # Streaming response handling
            async with client.stream("POST", API_URL, json=payload) as response:
                if response.status_code != 200:
                    print(f"❌ API Error: {response.status_code}")
                    print(await response.aread())
                    return

                print("\n💬 Elena's Response:\n" + "-"*40)
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            # Parse SSE JSON
                            data = json.loads(data_str)
                            # Checking for content or tool calls
                            if "choices" in data:
                                delta = data["choices"][0]["delta"]
                                content = delta.get("content", "")
                                if content:
                                    print(content, end="", flush=True)
                        except:
                            pass
                print("\n" + "-"*40 + "\n✅ Stream finished.")
                
        except Exception as e:
            print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    asyncio.run(trigger_elena())
