
from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any
from backend.core.graph_client import graph_client
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/search", response_model=List[Dict[str, Any]])
async def search_graph(query: str = Query(..., min_length=1)):
    """
    Search the knowledge graph for entities matching the query.
    Returns nodes and their immediate neighbors.
    """
    try:
        results = graph_client.search(query)
        return results
    except Exception as e:
        logger.error(f"Graph search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dump", response_model=Dict[str, Any])
async def dump_graph():
    """
    Return the entire graph as a node-link JSON.
    Useful for full visualization.
    """
    try:
        import networkx as nx
        return nx.node_link_data(graph_client.graph)
    except Exception as e:
        logger.error(f"Graph dump error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
