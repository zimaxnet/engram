
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.core import get_settings
from backend.memory.client import ZepMemoryClient

DOC_PATH = Path("docs/troubleshooting/authentication-guide.md")
# Use Staging Zep specific for memory persistence
ZEP_URL = "https://staging-env-zep.gentleriver-dd0de193.eastus2.azurecontainerapps.io"

async def ingest_troubleshooting():
    print(f"📄 Ingesting troubleshooting guide: {DOC_PATH}")
    
    if not DOC_PATH.exists():
        print(f"❌ File not found: {DOC_PATH}")
        return

    content = DOC_PATH.read_text()
    title = "Authentication Troubleshooting Guide"
    slug = "auth-troubleshooting-guide"
    
    try:
        settings = get_settings()
        # Override with Staging URL
        settings.zep_api_url = ZEP_URL
        client = ZepMemoryClient()
        
        # Ensure system user exists
        try:
            user_payload = {
                "user_id": "system",
                "metadata": {"role": "system", "name": "System Ingestion"}
            }
            await client._request("POST", "/api/v1/users", json=user_payload)
            print("  ✅ System user confirmed")
        except Exception as e:
            print(f"  ℹ️  User creation note: {e}")
        
        session_id = f"doc-troubleshooting-{slug}"
        print(f"  🧠 Sending to Zep (Session: {session_id})...")
        
        # Create/Update Session
        await client.get_or_create_session(
            session_id=session_id,
            user_id="system",
            metadata={
                "type": "documentation",
                "title": title,
                "category": "troubleshooting",
                "tags": ["authentication", "azure", "ciam", "google", "docker"],
                "ingested_at": datetime.now(timezone.utc).isoformat()
            }
        )
        
        # Add Memory
        await client.add_memory(
            session_id=session_id,
            messages=[{"role": "system", "content": content}],
            metadata={"source": "local_file", "file_path": str(DOC_PATH)}
        )
        print("  ✅ Zep Ingestion Complete")

        # Ingest JSON Artifact
        JSON_PATH = Path("docs/architecture/auth-flow.json")
        if JSON_PATH.exists():
            print(f"📄 Ingesting Architecture JSON: {JSON_PATH}")
            json_content = JSON_PATH.read_text()
            json_session_id = f"doc-architecture-auth-flow"
            
            await client.get_or_create_session(
                session_id=json_session_id,
                user_id="system",
                metadata={
                    "type": "architecture_diagram",
                    "title": "Authentication Architecture Flow",
                    "category": "architecture",
                    "tags": ["auth", "json", "diagram", "hybrid"],
                    "ingested_at": datetime.now(timezone.utc).isoformat()
                }
            )
            
            await client.add_memory(
                session_id=json_session_id,
                messages=[{"role": "system", "content": json_content}],
                metadata={"source": "local_file", "file_path": str(JSON_PATH)}
            )
            print("  ✅ JSON Ingestion Complete")

        # 2. Ingest to Graphlete
        
    except Exception as e:
        print(f"  ❌ Zep Ingestion Failed: {e}")

if __name__ == "__main__":
    asyncio.run(ingest_troubleshooting())
