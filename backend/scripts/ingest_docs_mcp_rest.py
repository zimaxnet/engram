#!/usr/bin/env python3
"""
MCP Document Ingestion via Direct Zep REST API

This script ingests project documentation into Zep using the same interface
as the MCP `ingest_document` tool, but via direct REST calls to production Zep.

This demonstrates recursive self-awareness: the system enriches its own
memory through its own architecture patterns (MCP tool interface + Zep storage).

Usage:
    python -m backend.scripts.ingest_docs_mcp_rest --dry-run
    python -m backend.scripts.ingest_docs_mcp_rest
"""

import argparse
import asyncio
import logging
import re
import uuid
from pathlib import Path
from typing import Optional

import httpx

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Production Zep endpoint
ZEP_URL = 'https://zep.engram.work'

# Agent mapping based on topics
AGENT_MAPPING = {
    "architecture": "elena",
    "schema": "elena",
    "context": "elena",
    "memory": "elena",
    "zep": "elena",
    "security": "elena",
    "postgresql": "elena",
    "database": "elena",
    "deployment": "marcus",
    "finops": "marcus",
    "pricing": "marcus",
    "enterprise": "marcus",
    "azure": "marcus",
    "ci": "marcus",
    "testing": "marcus",
    "frontend": "marcus",
    "ui": "marcus",
    "visual": "marcus",
    "temporal": "marcus",
    "sop": "marcus",
    "voice": "marcus",
}


def determine_agent(filepath: Path, content: str) -> str:
    """Determine which agent should own this document."""
    path_lower = str(filepath).lower()
    content_lower = content.lower()[:2000]
    
    for keyword, agent in AGENT_MAPPING.items():
        if keyword in path_lower or keyword in content_lower:
            return agent
    
    return "elena"


def extract_title(content: str, filepath: Path) -> str:
    """Extract title from markdown content or use filename."""
    h1_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    if h1_match:
        return h1_match.group(1).strip()
    
    frontmatter_match = re.search(r'^---\s*\ntitle:\s*["\']?(.+?)["\']?\s*\n', content, re.MULTILINE)
    if frontmatter_match:
        return frontmatter_match.group(1).strip()
    
    return filepath.stem.replace('-', ' ').replace('_', ' ').title()


def extract_topics(content: str, filepath: Path) -> list[str]:
    """Extract topics from content and filepath."""
    topics = set()
    
    for part in filepath.parts:
        if part not in ['docs', '.', '..'] and not part.endswith('.md') and not part.endswith('.html'):
            topics.add(part.capitalize())
    
    content_lower = content.lower()
    keyword_topics = {
        "architecture": "Architecture",
        "deployment": "Deployment",
        "testing": "Testing",
        "security": "Security",
        "finops": "FinOps",
        "postgres": "PostgreSQL",
        "zep": "Zep",
        "temporal": "Temporal",
        "azure": "Azure",
        "mcp": "MCP",
        "voice": "Voice",
        "agent": "Agents",
        "self-awareness": "SelfAwareness",
    }
    
    for keyword, topic in keyword_topics.items():
        if keyword in content_lower:
            topics.add(topic)
    
    return list(topics)[:5]


def get_doc_type(filepath: Path) -> str:
    """Determine document type from file extension."""
    suffix = filepath.suffix.lower()
    return {
        ".md": "markdown",
        ".html": "html",
        ".txt": "text",
    }.get(suffix, "text")


async def ingest_document_via_zep(
    client: httpx.AsyncClient,
    content: str,
    title: str,
    doc_type: str = "markdown",
    topics: Optional[list[str]] = None,
    agent_id: str = "elena",
    dry_run: bool = False,
) -> bool:
    """
    MCP-compatible document ingestion via Zep REST API.
    
    This mirrors the MCP `ingest_document` tool interface but uses
    direct REST calls to production Zep.
    """
    if dry_run:
        logger.info(f"  [DRY RUN] Would ingest: {title} ({doc_type}, {len(content)} chars)")
        logger.info(f"            Agent: {agent_id}, Topics: {topics}")
        return True
    
    try:
        # Create unique session ID for this document
        doc_session_id = f"doc-{title.lower().replace(' ', '-')[:20]}-{uuid.uuid4().hex[:8]}"
        
        # Chunk content if large
        chunk_size = 4000
        chunks = [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]
        
        # Build messages representing the document
        messages = []
        for i, chunk in enumerate(chunks):
            messages.append({
                "role_type": "user",
                "content": f"[Document: {title} - Part {i+1}/{len(chunks)}]\n\n{chunk}",
                "metadata": {"doc_type": doc_type, "chunk": i+1, "total_chunks": len(chunks)}
            })
            messages.append({
                "role_type": "assistant",
                "content": f"Acknowledged. I've indexed part {i+1} of '{title}' into my knowledge base.",
                "metadata": {"agent_id": agent_id}
            })
        
        # Create session via Zep REST API
        session_response = await client.post(f'{ZEP_URL}/api/v1/sessions', json={
            'session_id': doc_session_id,
            'user_id': 'system-ingestion',
            'metadata': {
                'summary': f"Document ingestion: {title}",
                'topics': topics or [],
                'agent_id': agent_id,
                'doc_type': doc_type,
                'source': 'mcp_ingest_document',
            }
        })
        
        if session_response.status_code not in [200, 201, 400]:  # 400 = already exists
            logger.warning(f"  Session creation returned: {session_response.status_code}")
        
        # Add messages via Zep REST API
        memory_response = await client.post(
            f'{ZEP_URL}/api/v1/sessions/{doc_session_id}/memory',
            json={'messages': messages}
        )
        
        if memory_response.status_code == 200:
            logger.info(f"  ✅ Ingested '{title}' ({len(content)} chars, {len(chunks)} chunks)")
            return True
        else:
            logger.error(f"  ❌ Memory add failed: {memory_response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"  ❌ Error ingesting {title}: {e}")
        return False


async def ingest_all_docs(docs_dir: Path, zep_url: str, dry_run: bool = False):
    """Ingest all documents via MCP-compatible interface to production Zep."""
    
    logger.info("=" * 60)
    logger.info("ENGRAM MCP DOCUMENT INGESTION (via Zep REST)")
    logger.info(f"Source: {docs_dir}")
    logger.info(f"Zep Endpoint: {zep_url}")
    logger.info(f"Mode: {'DRY RUN' if dry_run else 'LIVE INGESTION'}")
    logger.info("=" * 60)
    
    # Find all documents
    docs = list(docs_dir.rglob("*.md")) + list(docs_dir.rglob("*.html"))
    
    # Filter out files we don't want
    skip_patterns = ['.old.', 'CNAME', '_config.yml']
    docs = [d for d in docs if not any(p in str(d) for p in skip_patterns)]
    
    logger.info(f"\nFound {len(docs)} documents to process\n")
    
    stats = {"success": 0, "failed": 0, "skipped": 0}
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Health check
        try:
            health = await client.get(f'{zep_url}/healthz')
            logger.info(f"Zep health: {health.status_code}")
        except Exception as e:
            logger.error(f"Zep health check failed: {e}")
            return stats
        
        for doc_path in sorted(docs):
            relative_path = doc_path.relative_to(docs_dir)
            logger.info(f"\n📄 Processing: {relative_path}")
            
            try:
                content = doc_path.read_text()
                
                if len(content) < 100:
                    logger.info(f"  ⏭️ Skipped (too small)")
                    stats["skipped"] += 1
                    continue
                
                title = extract_title(content, doc_path)
                topics = extract_topics(content, doc_path)
                agent_id = determine_agent(doc_path, content)
                doc_type = get_doc_type(doc_path)
                
                success = await ingest_document_via_zep(
                    client, content, title, doc_type, topics, agent_id, dry_run
                )
                
                if success:
                    stats["success"] += 1
                else:
                    stats["failed"] += 1
                    
            except Exception as e:
                logger.error(f"  ❌ Error processing {relative_path}: {e}")
                stats["failed"] += 1
    
    logger.info("\n" + "=" * 60)
    logger.info("MCP INGESTION COMPLETE")
    logger.info(f"  ✅ Success: {stats['success']}")
    logger.info(f"  ❌ Failed:  {stats['failed']}")
    logger.info(f"  ⏭️ Skipped: {stats['skipped']}")
    logger.info("=" * 60)
    
    return stats


def main():
    parser = argparse.ArgumentParser(description="Ingest docs via MCP ingest_document (Zep REST)")
    parser.add_argument("--dry-run", action="store_true", help="Preview without ingesting")
    parser.add_argument("--docs-dir", default=None, help="Path to docs folder")
    parser.add_argument("--zep-url", default=ZEP_URL, help="Zep API URL")
    
    args = parser.parse_args()
    
    # Find docs directory
    if args.docs_dir:
        docs_dir = Path(args.docs_dir)
    else:
        possible_paths = [
            Path(__file__).parent.parent.parent / "docs",
            Path.cwd() / "docs",
        ]
        docs_dir = None
        for p in possible_paths:
            if p.exists():
                docs_dir = p
                break
        
        if not docs_dir:
            logger.error("Could not find docs folder. Use --docs-dir to specify path.")
            return
    
    asyncio.run(ingest_all_docs(docs_dir, args.zep_url, args.dry_run))


if __name__ == "__main__":
    main()
