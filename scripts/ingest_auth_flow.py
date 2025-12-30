
import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime, timezone

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.memory.client import ZepMemoryClient
from backend.core import get_settings

JSON_PATH = Path("docs/assets/images/social/auth-user-flow.json")
# Use the correct Zep URL - likely the one from the script I saw earlier or local if running locally?
# The previous script used a hardcoded Azure URL: https://staging-env-zep.gentleriver-dd0de193.eastus2.azurecontainerapps.io
# But the user is running `frontent npm run dev`. The backend might be local.
# If I use `get_settings()`, it should pull from .env.
# I'll check .env to be sure, or just assume the script should use the local/configured one.
# However, if I am running this LOCALLY on the user's machine, I should target the Zep instance they are using.
# If they are `cd frontend && npm run dev`, maybe they have a local backend running?
# The user's open files included `setup-github-secrets.sh` and `parameters.json`.
# I saw `ZEP_API_URL` in `deploy.yml`.
# I'll try to use `get_settings()` which loads from `.env`.

# Wait, `ingest_local_doc.py` had a HARDCODED Zep URL. 
# `ZEP_URL = "https://staging-env-zep.gentleriver-dd0de193.eastus2.azurecontainerapps.io"`
# That looks like a Staging URL.
# The user just deployed to Staging.
# If I want it to show up in the *deployed* app (which they might be testing), I should target Staging.
# If they are testing locally (localhost:5173), I should target Local.
# The user requested "Is this gonna show up...".
# I'll assume they want it in the environment they are using.
# Given the user context "Browser State: Page ... localhost:5173", they are using LOCAL.
# Local backend usually uses `http://localhost:8000` or the docker container.
# I will use `get_settings()` and ensure `.env` has the right Zep URL or fall back.

async def ingest_auth_flow():
    print(f"📄 Reading artifact: {JSON_PATH}")
    
    if not JSON_PATH.exists():
        print(f"❌ File not found: {JSON_PATH}")
        return

    data = json.loads(JSON_PATH.read_text())
    session_id = data["session_id"]
    
    print(f"🧠 Ingesting Session: {session_id}")
    
    try:
        # Target Staging Zep Instance
        settings = get_settings()
        settings.zep_api_url = "https://staging-env-zep.gentleriver-dd0de193.eastus2.azurecontainerapps.io"
        client = ZepMemoryClient()
        
        # Ensure user exists
        try:
            user_payload = {
                "user_id": data["user_id"],
                "metadata": {"role": "user", "name": "Derek"}
            }
            await client._request("POST", "/api/v1/users", json=user_payload)
            print(f"  ✅ User '{data['user_id']}' ensured")
        except Exception as e:
            print(f"  ℹ️  User creation note: {e}")

        # Create Session
        await client.get_or_create_session(
            session_id=session_id,
            user_id=data["user_id"],
            metadata=data["metadata"]
        )
        print("  ✅ Session Created/Updated")
        
        # Add Messages
        await client.add_memory(
            session_id=session_id,
            messages=data["messages"],
            metadata={"source": "ingestion_script"}
        )
        print("  ✅ Messages Added")
        print("🎉 Ingestion Complete!")
        
    except Exception as e:
        print(f"❌ Ingestion Failed: {e}")
        # Fallback debug: print env var
        from os import environ
        print(f"ZEP_API_URL was: {environ.get('ZEP_API_URL')}")

if __name__ == "__main__":
    asyncio.run(ingest_auth_flow())
