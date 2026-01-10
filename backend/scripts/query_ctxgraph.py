#!/usr/bin/env python3
"""
Query CtxGraph - Alias for query_memory.py

This is a convenience alias that forwards to query_memory.py.
Use this to query the CtxGraph (Engram's temporal knowledge graph).

Usage:
    python -m backend.scripts.query_ctxgraph -q "voice live config"
    python -m backend.scripts.query_ctxgraph --env azure --episodes
"""

from backend.scripts.query_memory import main

if __name__ == "__main__":
    main()
