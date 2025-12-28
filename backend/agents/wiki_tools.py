"""
Wiki Tools for AI Agents.

Provides tools for agents to query and fetch content from wiki.engram.work.
This enables live Wiki access beyond cached memory ingestion.
"""

import logging
import re
from typing import Optional
import httpx

logger = logging.getLogger(__name__)

WIKI_BASE_URL = "https://wiki.engram.work"

# All known Wiki pages
WIKI_PAGES = {
    "home": "/",
    "architecture": "/architecture.html",
    "agents": "/agents.html",
    "system-navigator": "/system-navigator.html",
    "connectors": "/connectors.html",
    "storage-strategy": "/storage-strategy.html",
    "deployment": "/deployment.html",
    "pricing": "/pricing.html",
    "poc-vs-enterprise": "/poc-vs-enterprise.html",
    "enterprise-env-model": "/enterprise-env-model.html",
    "finops": "/finops.html",
    "temporal": "/temporal-enterprise-deployment.html",
    "zep": "/zep-enterprise-deployment.html",
    "postgresql": "/postgresql-blob-storage-enterprise-deployment.html",
    "unstructured": "/unstructured-enterprise-deployment.html",
    "testing-guide": "/TESTING-GUIDE.html",
    "local-setup": "/LOCAL-TESTING-GUIDE.html",
    "observability": "/app-insights-guide.html",
    "visual-dev": "/visual-development.html",
}


def _html_to_text(html: str) -> str:
    """Convert HTML to plain text."""
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


async def list_wiki_pages() -> list[dict]:
    """
    List all available Wiki pages.
    
    Returns:
        List of dicts with 'slug' and 'url' keys.
    """
    return [
        {"slug": slug, "url": f"{WIKI_BASE_URL}{path}"}
        for slug, path in WIKI_PAGES.items()
    ]


async def get_wiki_page(slug: str, max_length: int = 10000) -> dict:
    """
    Fetch a specific Wiki page by slug.
    
    Args:
        slug: Page identifier (e.g., 'architecture', 'deployment')
        max_length: Maximum content length to return
        
    Returns:
        Dict with 'slug', 'url', 'title', 'content', and 'success' keys.
    """
    if slug not in WIKI_PAGES:
        return {
            "slug": slug,
            "url": "",
            "title": "",
            "content": f"Page '{slug}' not found. Available pages: {', '.join(WIKI_PAGES.keys())}",
            "success": False,
        }
    
    url = f"{WIKI_BASE_URL}{WIKI_PAGES[slug]}"
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            
            html = response.text
            
            # Extract title
            title_match = re.search(r'<title>([^<]+)</title>', html, re.IGNORECASE)
            title = title_match.group(1) if title_match else slug.replace("-", " ").title()
            
            # Convert to text
            content = _html_to_text(html)
            
            # Truncate if needed
            if len(content) > max_length:
                content = content[:max_length] + "\n\n[Content truncated...]"
            
            return {
                "slug": slug,
                "url": url,
                "title": title,
                "content": content,
                "success": True,
            }
            
    except Exception as e:
        logger.error(f"Failed to fetch Wiki page {slug}: {e}")
        return {
            "slug": slug,
            "url": url,
            "title": "",
            "content": f"Error fetching page: {str(e)}",
            "success": False,
        }


async def search_wiki(query: str, max_results: int = 5) -> list[dict]:
    """
    Search Wiki pages for content matching the query.
    
    This is a simple keyword-based search across all pages.
    For production, consider using ingested memory or embeddings.
    
    Args:
        query: Search query
        max_results: Maximum number of results to return
        
    Returns:
        List of matching page dicts with scores.
    """
    query_lower = query.lower()
    query_words = set(query_lower.split())
    
    # Remove stop words
    stop_words = {"the", "a", "an", "is", "are", "was", "were", "what", "how", "why", 
                  "when", "where", "which", "who", "and", "or", "but", "in", "on", "at", 
                  "to", "for", "of", "with", "by", "from", "as", "about"}
    query_words = query_words - stop_words
    
    if not query_words:
        query_words = set(query_lower.split())
    
    results = []
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for slug, path in WIKI_PAGES.items():
            try:
                url = f"{WIKI_BASE_URL}{path}"
                response = await client.get(url)
                response.raise_for_status()
                
                content = _html_to_text(response.text).lower()
                
                # Score based on word matches
                matches = sum(1 for w in query_words if w in content)
                
                if matches > 0:
                    score = min(1.0, 0.3 + (matches * 0.15))
                    
                    # Boost for slug match
                    if any(w in slug for w in query_words):
                        score = min(1.0, score + 0.2)
                    
                    # Extract snippet
                    snippet_start = 0
                    for word in query_words:
                        idx = content.find(word)
                        if idx != -1:
                            snippet_start = max(0, idx - 100)
                            break
                    
                    snippet = content[snippet_start:snippet_start + 300]
                    
                    results.append({
                        "slug": slug,
                        "url": url,
                        "score": score,
                        "snippet": snippet + "...",
                    })
                    
            except Exception as e:
                logger.warning(f"Failed to search Wiki page {slug}: {e}")
                continue
    
    # Sort by score descending
    results.sort(key=lambda x: x["score"], reverse=True)
    
    return results[:max_results]


# Tool definitions for agent use
WIKI_TOOLS = [
    {
        "name": "list_wiki_pages",
        "description": "List all available pages on wiki.engram.work",
        "function": list_wiki_pages,
    },
    {
        "name": "get_wiki_page",
        "description": "Fetch the full content of a specific Wiki page by slug (e.g., 'architecture', 'deployment')",
        "function": get_wiki_page,
    },
    {
        "name": "search_wiki",
        "description": "Search Wiki pages for content matching a query",
        "function": search_wiki,
    },
]
