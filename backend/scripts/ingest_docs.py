#!/usr/bin/env python3
"""
Bulk Document Ingestion Script

Ingests all documents from the docs/ folder into the Zep knowledge graph
via the MCP ingest_document tool.

This script can be run as an MCP client to ingest documents without 
redeployment. It reads all markdown and relevant files, extracts metadata,
and calls the ingest_document tool.

Usage:
    # Dry run (preview what would be ingested)
    python -m backend.scripts.ingest_docs --dry-run
    
    # Full ingestion via local API
    python -m backend.scripts.ingest_docs
    
    # Against staging API
    python -m backend.scripts.ingest_docs --api-url https://staging-env-backend.azurecontainerapps.io/api/v1
"""

import argparse
import asyncio
import json
import logging
import os
import re
from pathlib import Path
from typing import Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# Document to agent mapping based on topics
AGENT_MAPPING = {
    "architecture": "elena",
    "schema": "elena", 
    "context": "elena",
    "memory": "elena",
    "zep": "elena",
    "security": "elena",
    "auth": "elena",
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
    "agents": "elena",
    "temporal": "marcus",
    "sop": "marcus",
    "voice": "marcus",
}


def determine_agent(filepath: Path, content: str) -> str:
    """Determine which agent should own this document based on path and content."""
    path_lower = str(filepath).lower()
    content_lower = content.lower()[:2000]  # Check first 2000 chars
    
    for keyword, agent in AGENT_MAPPING.items():
        if keyword in path_lower or keyword in content_lower:
            return agent
    
    return "elena"  # Default to Elena for technical docs


def extract_title_from_markdown(content: str, filepath: Path) -> str:
    """Extract title from markdown content or use filename."""
    # Try to find H1 header
    h1_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    if h1_match:
        return h1_match.group(1).strip()
    
    # Try frontmatter title
    frontmatter_match = re.search(r'^---\s*\ntitle:\s*["\']?(.+?)["\']?\s*\n', content, re.MULTILINE)
    if frontmatter_match:
        return frontmatter_match.group(1).strip()
    
    # Fall back to filename
    return filepath.stem.replace('-', ' ').replace('_', ' ').title()


def extract_topics_from_content(content: str, filepath: Path) -> list[str]:
    """Extract topics from content and filepath."""
    topics = set()
    
    # Add topics from directory path
    for part in filepath.parts:
        if part not in ['docs', '.', '..'] and not part.endswith('.md') and not part.endswith('.html'):
            topics.add(part.capitalize())
    
    # Extract from frontmatter if present
    frontmatter_match = re.search(r'^---\s*\n.*?tags:\s*\[(.+?)\].*?\n---', content, re.MULTILINE | re.DOTALL)
    if frontmatter_match:
        tags = [t.strip().strip('"\'') for t in frontmatter_match.group(1).split(',')]
        topics.update(tags)
    
    # Add common topics based on content keywords
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
        "kubernetes": "Kubernetes",
        "docker": "Docker",
        "mcp": "MCP",
        "voice": "Voice",
        "agent": "Agents",
    }
    
    for keyword, topic in keyword_topics.items():
        if keyword in content_lower:
            topics.add(topic)
    
    return list(topics)[:5]  # Limit to 5 topics


def get_doc_type(filepath: Path) -> str:
    """Determine document type from file extension."""
    suffix = filepath.suffix.lower()
    return {
        ".md": "markdown",
        ".html": "html",
        ".txt": "text",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".json": "json",
    }.get(suffix, "text")


async def ingest_via_local_api(
    content: str,
    title: str,
    doc_type: str,
    topics: list[str],
    agent_id: str,
    api_url: str = "http://localhost:8000",
    dry_run: bool = False,
) -> bool:
    """Ingest document via HTTP API (fallback when MCP client not available)."""
    import httpx
    
    if dry_run:
        logger.info(f"  [DRY RUN] Would ingest: {title} ({doc_type}, {len(content)} chars)")
        logger.info(f"            Agent: {agent_id}, Topics: {topics}")
        return True
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Call the memory enrich endpoint or a dedicated ingestion endpoint
            payload = {
                "content": content,
                "title": title,
                "doc_type": doc_type,
                "topics": ",".join(topics),
                "agent_id": agent_id,
            }
            
            # Use the memory router or MCP SSE interface
            # For now, we'll use direct Zep client in-process
            from backend.api.routers.mcp_server import ingest_document
            result = await ingest_document(
                content=content,
                title=title,
                doc_type=doc_type,
                topics=",".join(topics),
                agent_id=agent_id,
            )
            
            if "✅" in result:
                logger.info(f"  ✅ Ingested: {title}")
                return True
            else:
                logger.error(f"  ❌ Failed: {title} - {result}")
                return False
                
    except Exception as e:
        logger.error(f"  ❌ Error ingesting {title}: {e}")
        return False


async def ingest_docs_folder(
    docs_dir: Path,
    api_url: str = "http://localhost:8000",
    dry_run: bool = False,
    extensions: list[str] = None,
) -> dict:
    """Ingest all documents from the docs folder."""
    
    if extensions is None:
        extensions = [".md", ".html"]  # Default to markdown and HTML
    
    logger.info("=" * 60)
    logger.info("ENGRAM DOCS INGESTION")
    logger.info(f"Source: {docs_dir}")
    logger.info(f"Mode: {'DRY RUN' if dry_run else 'LIVE INGESTION'}")
    logger.info("=" * 60)
    
    # Find all documents
    docs = []
    for ext in extensions:
        docs.extend(docs_dir.rglob(f"*{ext}"))
    
    # Filter out some files we don't want to ingest
    skip_patterns = ['.old.', 'CNAME', '_config.yml']
    docs = [d for d in docs if not any(p in str(d) for p in skip_patterns)]
    
    logger.info(f"\nFound {len(docs)} documents to process\n")
    
    stats = {"success": 0, "failed": 0, "skipped": 0}
    
    for doc_path in sorted(docs):
        relative_path = doc_path.relative_to(docs_dir)
        logger.info(f"\n📄 Processing: {relative_path}")
        
        try:
            content = doc_path.read_text()
            
            # Skip very small files
            if len(content) < 100:
                logger.info(f"  ⏭️ Skipped (too small: {len(content)} chars)")
                stats["skipped"] += 1
                continue
            
            title = extract_title_from_markdown(content, doc_path)
            topics = extract_topics_from_content(content, doc_path)
            agent_id = determine_agent(doc_path, content)
            doc_type = get_doc_type(doc_path)
            
            success = await ingest_via_local_api(
                content=content,
                title=title,
                doc_type=doc_type,
                topics=topics,
                agent_id=agent_id,
                api_url=api_url,
                dry_run=dry_run,
            )
            
            if success:
                stats["success"] += 1
            else:
                stats["failed"] += 1
                
        except Exception as e:
            logger.error(f"  ❌ Error processing {relative_path}: {e}")
            stats["failed"] += 1
    
    logger.info("\n" + "=" * 60)
    logger.info("INGESTION COMPLETE")
    logger.info(f"  ✅ Success: {stats['success']}")
    logger.info(f"  ❌ Failed:  {stats['failed']}")
    logger.info(f"  ⏭️ Skipped: {stats['skipped']}")
    logger.info("=" * 60)
    
    return stats


def main():
    parser = argparse.ArgumentParser(description="Ingest docs folder into Zep knowledge graph")
    parser.add_argument("--dry-run", action="store_true", help="Preview without ingesting")
    parser.add_argument("--api-url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--docs-dir", default=None, help="Path to docs folder")
    parser.add_argument("--extensions", nargs="+", default=[".md"], help="File extensions to process")
    
    args = parser.parse_args()
    
    # Find docs directory
    if args.docs_dir:
        docs_dir = Path(args.docs_dir)
    else:
        # Try common locations
        possible_paths = [
            Path(__file__).parent.parent.parent.parent / "docs",  # From backend/scripts
            Path.cwd() / "docs",
            Path("/app/docs"),
        ]
        docs_dir = None
        for p in possible_paths:
            if p.exists():
                docs_dir = p
                break
        
        if not docs_dir:
            logger.error("Could not find docs folder. Use --docs-dir to specify path.")
            return
    
    # Run ingestion
    asyncio.run(ingest_docs_folder(
        docs_dir=docs_dir,
        api_url=args.api_url,
        dry_run=args.dry_run,
        extensions=args.extensions,
    ))


if __name__ == "__main__":
    main()
