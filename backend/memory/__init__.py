"""
Engram Memory Module

Zep integration for knowledge graph and episodic memory.
Implements the Memory layer of the Brain + Spine architecture.
"""

from .client import (
    ZepMemoryClient,
    enrich_context,
    get_facts,
    memory_client,
    persist_conversation,
    search_memory,
)

__all__ = [
    "ZepMemoryClient",
    "memory_client",
    "enrich_context",
    "persist_conversation",
    "search_memory",
    "get_facts",
]
