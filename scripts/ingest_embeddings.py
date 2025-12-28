#!/usr/bin/env python3
"""
Ingest Existing Zep Sessions with Embeddings.

Fetches all sessions from Zep, generates embeddings via Azure OpenAI,
and stores them in the memory_embeddings table for semantic search.

Usage:
    python scripts/ingest_embeddings.py

Environment Variables (or set via .env):
    POSTGRES_PASSWORD - Azure Postgres password
    AZURE_AI_KEY - Azure OpenAI API key
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path.parent))

import httpx
import asyncpg
from typing import Optional

# Configuration
ZEP_URL = os.environ.get("ZEP_API_URL", "https://staging-env-zep.gentleriver-dd0de193.eastus2.azurecontainerapps.io")
POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "staging-env-db.postgres.database.azure.com")
POSTGRES_PORT = int(os.environ.get("POSTGRES_PORT", "5432"))
POSTGRES_USER = os.environ.get("POSTGRES_USER", "cogadmin")
POSTGRES_DB = os.environ.get("POSTGRES_DB", "zep")

# Azure OpenAI settings
AZURE_AI_ENDPOINT = os.environ.get("AZURE_AI_ENDPOINT", "https://zimax-gw.azure-api.net/zimax/openai/v1")
EMBEDDING_MODEL = "text-embedding-3-small"  # Available on zimax-gw (ada-002 not deployed)


async def generate_embedding(text: str, api_key: str) -> Optional[list[float]]:
    """Generate embedding for text via Azure OpenAI."""
    url = f"{AZURE_AI_ENDPOINT}/embeddings"
    headers = {
        "Content-Type": "application/json",
        "api-key": api_key,
        "Ocp-Apim-Subscription-Key": api_key,
    }
    payload = {
        "input": text[:8000],  # Truncate to max tokens
        "model": EMBEDDING_MODEL,
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["data"][0]["embedding"]
        except Exception as e:
            print(f"   ⚠️  Embedding generation failed: {e}")
            return None


async def fetch_zep_sessions() -> list[dict]:
    """Fetch all sessions from Zep."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{ZEP_URL}/api/v1/sessions")
        response.raise_for_status()
        return response.json()


async def fetch_session_memory(session_id: str) -> dict:
    """Fetch memory for a specific session."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(f"{ZEP_URL}/api/v1/sessions/{session_id}/memory")
            response.raise_for_status()
            return response.json()
        except:
            return {}


async def main():
    print("🚀 Ingesting Zep Sessions with Embeddings")
    print(f"Zep: {ZEP_URL}")
    print(f"Postgres: {POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}")
    print("-" * 60)
    
    # Get credentials
    postgres_password = os.environ.get("POSTGRES_PASSWORD", "")
    azure_ai_key = os.environ.get("AZURE_AI_KEY", "")
    
    if not postgres_password:
        print("ERROR: POSTGRES_PASSWORD required")
        print("Run: export POSTGRES_PASSWORD=$(az keyvault secret show --vault-name stagingenvkvysoxm5 --name postgres-password --query value -o tsv)")
        sys.exit(1)
    
    if not azure_ai_key:
        print("ERROR: AZURE_AI_KEY required")
        print("Run: export AZURE_AI_KEY=$(az keyvault secret show --vault-name stagingenvkvysoxm5 --name azure-ai-key --query value -o tsv)")
        sys.exit(1)
    
    # Connect to Postgres
    print("📊 Connecting to Postgres...")
    conn = await asyncpg.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        user=POSTGRES_USER,
        password=postgres_password,
        database=POSTGRES_DB,
        ssl="require",
    )
    
    # Fetch all sessions from Zep
    print("📥 Fetching sessions from Zep...")
    sessions = await fetch_zep_sessions()
    print(f"   Found {len(sessions)} sessions")
    
    # Check existing embeddings
    existing = await conn.fetch("SELECT DISTINCT session_id FROM memory_embeddings")
    existing_ids = {r["session_id"] for r in existing}
    print(f"   {len(existing_ids)} already have embeddings")
    
    # Process each session
    ingested = 0
    skipped = 0
    failed = 0
    
    for i, sess in enumerate(sessions, 1):
        session_id = sess.get("session_id", "")
        if not session_id:
            continue
        
        # Skip if already has embedding
        if session_id in existing_ids:
            skipped += 1
            continue
        
        # Get session metadata
        metadata = sess.get("metadata", {}) or {}
        title = metadata.get("title", session_id)
        topics = metadata.get("topics", []) or []
        summary = metadata.get("summary", "")
        
        # Determine source type
        if session_id.startswith("doc-wiki-"):
            source_type = "wiki"
        elif session_id.startswith("doc-"):
            source_type = "document"
        elif session_id.startswith("sess-"):
            source_type = "episode"
        elif session_id.startswith("finding-"):
            source_type = "finding"
        else:
            source_type = "conversation"
        
        # Fetch session content
        memory = await fetch_session_memory(session_id)
        messages = memory.get("messages", [])
        
        if not messages:
            # Use summary as content if no messages
            content = summary or title
        else:
            # Combine all message content
            content = "\n\n".join([
                m.get("content", "") for m in messages if m.get("content")
            ])
        
        if not content or len(content) < 10:
            print(f"   [{i}/{len(sessions)}] ⏭️  {session_id}: No content")
            skipped += 1
            continue
        
        # Generate embedding
        print(f"   [{i}/{len(sessions)}] 🔄 {session_id}... ", end="", flush=True)
        embedding = await generate_embedding(content, azure_ai_key)
        
        if not embedding:
            failed += 1
            continue
        
        # Store in database
        embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"
        
        try:
            await conn.execute(
                """
                INSERT INTO memory_embeddings 
                    (session_id, content, embedding, title, topics, source_type)
                VALUES ($1, $2, $3::vector, $4, $5, $6)
                ON CONFLICT DO NOTHING
                """,
                session_id,
                content[:10000],
                embedding_str,
                title,
                topics if topics else None,
                source_type,
            )
            print(f"✅ ({len(content)} chars, {source_type})")
            ingested += 1
        except Exception as e:
            print(f"❌ {e}")
            failed += 1
        
        # Rate limiting (avoid 429s)
        if ingested % 10 == 0:
            await asyncio.sleep(1)
    
    await conn.close()
    
    print("-" * 60)
    print(f"✅ Complete!")
    print(f"   Ingested: {ingested}")
    print(f"   Skipped: {skipped}")
    print(f"   Failed: {failed}")
    print(f"   Total embeddings: {len(existing_ids) + ingested}")


if __name__ == "__main__":
    asyncio.run(main())
