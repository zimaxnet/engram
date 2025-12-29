
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.core.graph_client import graph_client
from backend.memory.client import ZepMemoryClient
from backend.core import get_settings

DOC_PATH = Path("docs/knowledge-graph-implementation.md")
ZEP_URL = "https://staging-env-zep.gentleriver-dd0de193.eastus2.azurecontainerapps.io"

async def ingest_local_doc():
    print(f"📄 Ingesting local doc: {DOC_PATH}")
    
    if not DOC_PATH.exists():
        print(f"❌ File not found: {DOC_PATH}")
        return

    content = DOC_PATH.read_text()
    title = "Knowledge Graph Implementation"
    slug = "knowledge-graph-implementation"
    
    # 1. Ingest to Zep
    try:
        settings = get_settings()
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
        
        session_id = f"doc-local-{slug}"
        print(f"  🧠 Sending to Zep (Session: {session_id})...")
        
        await client.get_or_create_session(
            session_id=session_id,
            user_id="system",
            metadata={
                "type": "documentation",
                "title": title,
                "source": "local_file",
                "ingested_at": datetime.now(timezone.utc).isoformat()
            }
        )
        
        await client.add_memory(
            session_id=session_id,
            messages=[{"role": "system", "content": content}],
            metadata={"source": "local"}
        )
        print("  ✅ Zep Ingestion Complete")
    except Exception as e:
        print(f"  ❌ Zep Ingestion Failed: {e}")

    # 2. Ingest to Graph
    try:
        print("  🕸️  Updating Knowledge Graph...")
        graph_client.graph.add_node(title, type="documentation", source="local")
        
        # Add manual edges based on content
        topics = ["Knowledge Graph", "NetworkX", "Graphiti", "React", "Frontend", "Backend"]
        for topic in topics:
            graph_client.add_triplet(title, "has_topic", topic)
            
        print("  ✅ Graph Update Complete")
    except Exception as e:
        print(f"  ❌ Graph Update Failed: {e}")

if __name__ == "__main__":
    asyncio.run(ingest_local_doc())
