#!/usr/bin/env python3
"""
Bulk Ingest Wiki Pages into Zep Memory.

Crawls wiki.engram.work and ingests each page as a Zep session,
making the content searchable by agents.
"""

import asyncio
import os
import sys
import httpx
from pathlib import Path
from datetime import datetime, timezone

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path.parent))

from backend.core import get_settings
from backend.memory.client import ZepMemoryClient

# Azure Zep URL
ZEP_URL = "https://staging-env-zep.gentleriver-dd0de193.eastus2.azurecontainerapps.io"

# All Wiki Pages to Ingest
WIKI_PAGES = [
    ("home", "https://wiki.engram.work/"),
    ("architecture", "https://wiki.engram.work/architecture.html"),
    ("agents", "https://wiki.engram.work/agents.html"),
    ("system-navigator", "https://wiki.engram.work/system-navigator.html"),
    ("connectors", "https://wiki.engram.work/connectors.html"),
    ("storage-strategy", "https://wiki.engram.work/storage-strategy.html"),
    ("deployment", "https://wiki.engram.work/deployment.html"),
    ("pricing", "https://wiki.engram.work/pricing.html"),
    ("poc-vs-enterprise", "https://wiki.engram.work/poc-vs-enterprise.html"),
    ("enterprise-env-model", "https://wiki.engram.work/enterprise-env-model.html"),
    ("finops", "https://wiki.engram.work/finops.html"),
    ("temporal-enterprise-deployment", "https://wiki.engram.work/temporal-enterprise-deployment.html"),
    ("zep-enterprise-deployment", "https://wiki.engram.work/zep-enterprise-deployment.html"),
    ("postgresql-blob-storage", "https://wiki.engram.work/postgresql-blob-storage-enterprise-deployment.html"),
    ("unstructured-enterprise-deployment", "https://wiki.engram.work/unstructured-enterprise-deployment.html"),
    ("testing-guide", "https://wiki.engram.work/TESTING-GUIDE.html"),
    ("local-testing-guide", "https://wiki.engram.work/LOCAL-TESTING-GUIDE.html"),
    ("app-insights-guide", "https://wiki.engram.work/app-insights-guide.html"),
    ("visual-development", "https://wiki.engram.work/visual-development.html"),
]


async def fetch_page_content(url: str) -> str:
    """Fetch page content and extract text (simplified HTML to text)."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
            
            # Simple HTML to text conversion (remove tags)
            import re
            html = response.text
            
            # Remove script and style elements
            html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
            html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
            
            # Remove HTML tags but keep newlines for structure
            html = re.sub(r'<br\s*/?>', '\n', html, flags=re.IGNORECASE)
            html = re.sub(r'</p>', '\n\n', html, flags=re.IGNORECASE)
            html = re.sub(r'</div>', '\n', html, flags=re.IGNORECASE)
            html = re.sub(r'</h[1-6]>', '\n\n', html, flags=re.IGNORECASE)
            html = re.sub(r'<[^>]+>', '', html)
            
            # Decode HTML entities
            import html as html_module
            text = html_module.unescape(html)
            
            # Clean up whitespace
            text = re.sub(r'\n{3,}', '\n\n', text)
            text = text.strip()
            
            return text
        except Exception as e:
            print(f"  ❌ Failed to fetch {url}: {e}")
            return ""


async def ingest_wiki_page(memory_client: ZepMemoryClient, slug: str, url: str) -> bool:
    """Ingest a single Wiki page into Zep."""
    session_id = f"doc-wiki-{slug}"
    user_id = "system"
    
    print(f"📄 Ingesting: {slug} ({url})")
    
    # Fetch content
    content = await fetch_page_content(url)
    if not content:
        return False
    
    # Truncate if too long (Zep has limits)
    max_content_length = 50000
    if len(content) > max_content_length:
        content = content[:max_content_length] + "\n\n[Content truncated...]"
    
    # Extract title from slug
    title = slug.replace("-", " ").title()
    
    # Create/Update session
    try:
        await memory_client.get_or_create_session(
            session_id=session_id,
            user_id=user_id,
            metadata={
                "type": "wiki_page",
                "source": url,
                "title": title,
                "topics": ["wiki", "documentation", slug],
                "summary": f"Wiki page: {title} from wiki.engram.work",
                "ingested_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        
        # Add content as a message
        messages = [
            {
                "role": "system",
                "content": f"# {title}\n\nSource: {url}\n\n{content}"
            }
        ]
        
        await memory_client.add_memory(
            session_id=session_id,
            messages=messages,
            metadata={"source": url}
        )
        
        print(f"  ✅ Ingested {len(content)} characters")
        return True
        
    except Exception as e:
        print(f"  ❌ Failed to ingest: {e}")
        return False


async def main():
    print("🚀 Bulk Wiki Ingestion Script")
    print(f"Target: {ZEP_URL}")
    print(f"Pages: {len(WIKI_PAGES)}")
    print("-" * 50)
    
    # Configure Zep URL
    settings = get_settings()
    settings.zep_api_url = ZEP_URL
    os.environ["ZEP_API_URL"] = ZEP_URL
    
    memory_client = ZepMemoryClient()
    
    # Ensure system user exists
    try:
        user_payload = {
            "user_id": "system",
            "metadata": {"role": "system", "name": "System Ingestion"}
        }
        await memory_client._request("POST", "/api/v1/users", json=user_payload)
        print("✅ System user confirmed")
    except Exception as e:
        print(f"ℹ️  User creation note: {e}")
    
    # Ingest all pages
    success_count = 0
    for slug, url in WIKI_PAGES:
        result = await ingest_wiki_page(memory_client, slug, url)
        if result:
            success_count += 1
        await asyncio.sleep(0.5)  # Rate limiting
    
    print("-" * 50)
    print(f"✅ Ingestion Complete: {success_count}/{len(WIKI_PAGES)} pages")


if __name__ == "__main__":
    asyncio.run(main())
