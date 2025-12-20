#!/usr/bin/env python3
"""
MCP Client Document Ingestion

Ingests all project documentation via the production MCP server's
`ingest_document` tool. This demonstrates recursive self-awareness:
the system enriches its own memory through its own MCP interface.

Usage:
    python -m backend.scripts.ingest_docs_mcp --dry-run
    python -m backend.scripts.ingest_docs_mcp
"""

import argparse
import asyncio
import json
import logging
import re
from pathlib import Path
from typing import Optional

from mcp import ClientSession
from mcp.client.sse import sse_client

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Production MCP endpoint
MCP_SSE_URL = "https://engram.work/api/v1/mcp/sse"

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
    
    return "elena"  # Default to Elena for technical docs


def extract_title_from_markdown(content: str, filepath: Path) -> str:
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
        ".yaml": "yaml",
        ".yml": "yaml",
        ".json": "json",
    }.get(suffix, "text")


async def ingest_via_mcp(
    session: ClientSession,
    content: str,
    title: str,
    doc_type: str,
    topics: list[str],
    agent_id: str,
    dry_run: bool = False,
) -> bool:
    """Ingest a document via the MCP ingest_document tool."""
    
    if dry_run:
        logger.info(f"  [DRY RUN] Would ingest: {title} ({doc_type}, {len(content)} chars)")
        logger.info(f"            Agent: {agent_id}, Topics: {topics}")
        return True
    
    try:
        result = await session.call_tool(
            "ingest_document",
            arguments={
                "content": content,
                "title": title,
                "doc_type": doc_type,
                "topics": ",".join(topics),
                "agent_id": agent_id,
            }
        )
        
        result_text = result.content[0].text if result.content else ""
        
        if "✅" in result_text:
            logger.info(f"  ✅ {result_text}")
            return True
        else:
            logger.error(f"  ❌ {result_text}")
            return False
            
    except Exception as e:
        logger.error(f"  ❌ Error ingesting {title}: {e}")
        return False


async def ingest_all_docs(docs_dir: Path, mcp_url: str, dry_run: bool = False):
    """Connect to MCP server and ingest all documents."""
    
    logger.info("=" * 60)
    logger.info("ENGRAM MCP DOCUMENT INGESTION")
    logger.info(f"Source: {docs_dir}")
    logger.info(f"MCP Endpoint: {mcp_url}")
    logger.info(f"Mode: {'DRY RUN' if dry_run else 'LIVE INGESTION'}")
    logger.info("=" * 60)
    
    # Find all documents
    docs = list(docs_dir.rglob("*.md")) + list(docs_dir.rglob("*.html"))
    
    # Filter out files we don't want
    skip_patterns = ['.old.', 'CNAME', '_config.yml']
    docs = [d for d in docs if not any(p in str(d) for p in skip_patterns)]
    
    logger.info(f"\nFound {len(docs)} documents to process\n")
    
    stats = {"success": 0, "failed": 0, "skipped": 0}
    
    if dry_run:
        # Dry run doesn't need MCP connection
        for doc_path in sorted(docs):
            relative_path = doc_path.relative_to(docs_dir)
            logger.info(f"\n📄 Processing: {relative_path}")
            
            try:
                content = doc_path.read_text()
                
                if len(content) < 100:
                    logger.info(f"  ⏭️ Skipped (too small)")
                    stats["skipped"] += 1
                    continue
                
                title = extract_title_from_markdown(content, doc_path)
                topics = extract_topics(content, doc_path)
                agent_id = determine_agent(doc_path, content)
                doc_type = get_doc_type(doc_path)
                
                await ingest_via_mcp(None, content, title, doc_type, topics, agent_id, dry_run=True)
                stats["success"] += 1
                
            except Exception as e:
                logger.error(f"  ❌ Error processing: {e}")
                stats["failed"] += 1
    else:
        # Live ingestion via MCP SSE
        async with sse_client(mcp_url) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # List available tools to confirm connection
                tools = await session.list_tools()
                logger.info(f"Connected! Available MCP tools: {[t.name for t in tools.tools]}")
                
                for doc_path in sorted(docs):
                    relative_path = doc_path.relative_to(docs_dir)
                    logger.info(f"\n📄 Processing: {relative_path}")
                    
                    try:
                        content = doc_path.read_text()
                        
                        if len(content) < 100:
                            logger.info(f"  ⏭️ Skipped (too small)")
                            stats["skipped"] += 1
                            continue
                        
                        title = extract_title_from_markdown(content, doc_path)
                        topics = extract_topics(content, doc_path)
                        agent_id = determine_agent(doc_path, content)
                        doc_type = get_doc_type(doc_path)
                        
                        success = await ingest_via_mcp(
                            session, content, title, doc_type, topics, agent_id
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
    parser = argparse.ArgumentParser(description="Ingest docs via MCP ingest_document tool")
    parser.add_argument("--dry-run", action="store_true", help="Preview without ingesting")
    parser.add_argument("--docs-dir", default=None, help="Path to docs folder")
    parser.add_argument("--mcp-url", default=MCP_SSE_URL, help="MCP SSE endpoint URL")
    
    args = parser.parse_args()
    
    mcp_url = args.mcp_url
    
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
    
    asyncio.run(ingest_all_docs(docs_dir, mcp_url, args.dry_run))


if __name__ == "__main__":
    main()
