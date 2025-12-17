import asyncio
import logging
from backend.memory.client import list_episodes, memory_client
from backend.core import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    print("Settings Zep URL:", get_settings().zep_api_url)
    print("Memory Client Type:", type(memory_client._client))
    
    print("Calling list_episodes...")
    try:
        # User ID usually 'user-derek' based on other contexts
        sessions = await list_episodes(user_id="user-derek", limit=5)
        print(f"Successfully retrieved {len(sessions)} sessions.")
        for s in sessions:
            print(f"- {s.get('session_id')}: {s.get('created_at')}")
    except Exception as e:
        print(f"Error calling list_episodes: {e}")

if __name__ == "__main__":
    asyncio.run(main())
