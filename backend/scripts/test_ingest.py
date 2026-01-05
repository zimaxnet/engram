import asyncio
import logging
import sys
from datetime import datetime
import os
from dotenv import load_dotenv

# Load Azure config for verification
load_dotenv(".env.azure")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_ingest")

# Mock BackgroundTasks to run properly in script
from fastapi import BackgroundTasks

class CaptureBackgroundTasks(BackgroundTasks):
    def __init__(self):
        super().__init__()
        self.tasks = []
    
    def add_task(self, func, *args, **kwargs):
        import asyncio
        if asyncio.iscoroutinefunction(func):
            self.tasks.append(func(*args, **kwargs))
        else:
            # Sync functions run immediately
            func(*args, **kwargs)

    async def await_all(self):
        for t in self.tasks:
            await t
        self.tasks = []

async def test_wiki():
    print("\n--- Testing Wiki Connector ---")
    from backend.etl.connectors.wiki import wiki_connector
    
    bg = CaptureBackgroundTasks()
    try:
        url = "https://wiki.engram.work" # Use internal wiki or external safe URL
        # Accessing publicly available page for test
        url = "https://example.com" 
        
        await wiki_connector.ingest_url(url, "test-user", bg)
        await bg.await_all()
        print("✅ Wiki Ingest Success")
    except Exception as e:
        print(f"❌ Wiki Ingest Failed: {e}")

async def test_ticket():
    print("\n--- Testing Ticket Connector ---")
    from backend.etl.connectors.ticket import ticket_connector
    mock_ticket = {
        "id": "INC-12345",
        "title": "VoiceLive Connection Timeout",
        "status": "Resolved",
        "priority": "High",
        "created_at": datetime.now().isoformat(),
        "description": "Users are reporting timeouts when connecting to VoiceLive socket.",
        "comments": [
            {"author": "Support", "timestamp": datetime.now().isoformat(), "body": "Investigating logs."},
            {"author": "Dev", "timestamp": datetime.now().isoformat(), "body": "Fixed by increasing timeout to 10s."}
        ]
    }
    try:
        bg = CaptureBackgroundTasks()
        await ticket_connector.ingest_ticket(mock_ticket, "test-user", bg)
        await bg.await_all()
        print("✅ Ticket Ingest Success")
    except Exception as e:
        print(f"❌ Ticket Ingest Failed: {e}")

async def test_code():
    print("\n--- Testing Code Connector ---")
    from backend.etl.connectors.git_repo import git_repo_connector
    import os
    
    # Test on the connectors directory itself
    repo_path = os.path.dirname(os.path.abspath(__file__)) + "/../etl/connectors"
    
    try:
        bg = CaptureBackgroundTasks()
        await git_repo_connector.ingest_repository(repo_path, "test-user", bg, max_files=5)
        await bg.await_all()
        print("✅ Code Ingest Success")
    except Exception as e:
        print(f"❌ Code Ingest Failed: {e}")

async def test_file_upload():
    print("\n--- Testing File Upload (Policy/PDF) path ---")
    from backend.etl.ingestion_service import ingestion_service
    
    # Mock file content
    content = b"This is a test policy document. All embeddings must be 1536 dimensions."
    try:
        bg = CaptureBackgroundTasks()
        await ingestion_service.ingest_document(
            content, "policy_test.txt", "text/plain", "test-user", bg
        )
        await bg.await_all()
        print("✅ File Ingest Success")
    except Exception as e:
        print(f"❌ File Ingest Failed: {e}")

async def main():
    print("🚀 Starting MVP Ingestion Verification")
    
    await test_wiki()
    await test_ticket()
    await test_code()
    await test_file_upload()
    
    print("\n🏁 Verification Complete")

if __name__ == "__main__":
    asyncio.run(main())
