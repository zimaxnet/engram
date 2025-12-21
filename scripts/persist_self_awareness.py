import asyncio
import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend.memory.client import memory_client
from zep_python.memory import Session, Memory, Message

async def persist_troubleshooting_memory():
    session_id = "sess-recursion-001"
    
    print(f"Creating Session: {session_id}...")
    
    # 1. Create the Session
    try:
        await memory_client.client.memory.add_session(
            Session(
                session_id=session_id,
                user_id="derek",
                metadata={
                    "type": "recursive_debugging",
                    "topic": "sage_elena_troubleshooting",
                    "status": "resolved"
                }
            )
        )
        print("✅ Session Created")
    except Exception as e:
        print(f"⚠️ Session creation note (might exist): {e}")

    # 2. Construct the Memory (Dialogue History)
    history = [
        {"role": "user", "content": "We are experiencing 401 errors with Sage and Elena agents. Sage returns a generic apology."},
        {"role": "assistant", "content": "Investigating. Sage's logs show `401 PermissionDenied` from Azure AI. It seems Sage is defaulting to the FoundryChatClient instead of Anthropic."},
        {"role": "user", "content": "How do we fix Sage?"},
        {"role": "assistant", "content": "I implemented `ClaudeLangChainAdapter` to force Sage to use the ANTHROPIC_API_KEY. This bypasses the failing Azure AI endpoint. Sage is now VERIFIED working via CLI."},
        {"role": "user", "content": "What about Elena and Marcus? They are also giving 401s."},
        {"role": "assistant", "content": "Diagnosis: The `AZURE_AI_KEY` in Key Vault corresponds to the APIM Gateway (`https://zimax-gw...`), but the environment was using the direct Foundry endpoint (`https://zimax.services...`). This mismatch caused the 401."},
        {"role": "user", "content": "Fixing the endpoint secret resolved it. Now, what about VoiceLive?"},
        {"role": "assistant", "content": "VoiceLive was also trying to connect directly to Foundry. I updated the `AZURE_VOICELIVE_ENDPOINT` to route through the APIM Gateway as well. Audio tests passed."},
        {"role": "user", "content": "Summary of resolutions?"},
        {"role": "assistant", "content": "1. SWA Auth: Disabled Platform Auth.\n2. Sage: Switched to Claude/Gemini adapters.\n3. Elena/Marcus: Aligned AZURE_AI_ENDPOINT with APIM Key.\n4. Voice: Aligned AZURE_VOICELIVE_ENDPOINT with APIM Key.\n5. Documentation: Updated SOPs and Memory Architecture."}
    ]

    messages = [Message(role=msg["role"], content=msg["content"]) for msg in history]
    memory = Memory(messages=messages)

    # 3. Add Memory to Session
    print("Persisting Memory Terms...")
    try:
        await memory_client.client.memory.add_memory(session_id, memory)
        print("✅ Memory Persisted")
    except Exception as e:
        print(f"❌ Failed to persist memory: {e}")
        return

    # 4. Verify & Check Type
    print("\n--- Verifying Ingestion ---")
    try:
        retrieved_session = await memory_client.client.memory.get_session(session_id)
        print(f"Retrieved Session ID: {retrieved_session.session_id}")
        print(f"Class Type: {type(retrieved_session)}")
        
        # Check for Episodes (might be empty initially as Zep processes async)
        episodes = await memory_client.client.memory.get_session_episodes(session_id)
        print(f"Episodes Found: {len(episodes)}")
        if episodes:
             print(f"Episode 1 Summary: {episodes[0].content}")
        else:
            print("(Zep is likely still processing the episodes asynchronously)")

    except Exception as e:
        print(f"Verification Info: {e}")

if __name__ == "__main__":
    asyncio.run(persist_troubleshooting_memory())
