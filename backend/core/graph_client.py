
import logging
from typing import List, Optional
import networkx as nx
import json
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class SimpleGraphClient:
    """
    A lightweight Knowledge Graph client using NetworkX.
    Persists to a JSON file in the docs directory.
    """
    
    def __init__(self, persistence_path: str = "docs/knowledge_graph.json"):
        self.persistence_path = persistence_path
        self.graph = nx.MultiDiGraph()
        self._load()
        logger.info(f"SimpleGraphClient initialized. Nodes: {self.graph.number_of_nodes()}, Edges: {self.graph.number_of_edges()}")

    def _load(self):
        """Load graph from JSON file if exists."""
        if os.path.exists(self.persistence_path):
            try:
                with open(self.persistence_path, 'r') as f:
                    data = json.load(f)
                    self.graph = nx.node_link_graph(data)
            except Exception as e:
                logger.error(f"Failed to load graph: {e}")
                self.graph = nx.MultiDiGraph()

    def _save(self):
        """Save graph to JSON file."""
        try:
            os.makedirs(os.path.dirname(self.persistence_path), exist_ok=True)
            data = nx.node_link_data(self.graph)
            with open(self.persistence_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save graph: {e}")

    def add_triplet(self, source: str, edge: str, target: str, metadata: dict = None):
        """Add a semantic triplet (Source)-[Edge]->(Target)."""
        self.graph.add_node(source, type="entity")
        self.graph.add_node(target, type="entity")
        self.graph.add_edge(source, target, relationship=edge, metadata=metadata or {}, created_at=datetime.utcnow().isoformat())
        self._save()

    def add_document_facts(self, doc_name: str, facts: List[str]):
        """Add facts extracted from a document."""
        # Simple heuristic: link document to facts
        self.graph.add_node(doc_name, type="document")
        for fact in facts:
            # Create a 'Fact' node
            fact_id = f"fact_{hash(fact)}"
            self.graph.add_node(fact_id, type="fact", content=fact)
            self.graph.add_edge(doc_name, fact_id, relationship="asserts")
        self._save()
        
    def search(self, query: str) -> List[dict]:
        """
        Simple graph search: find nodes matching query and their neighbors.
        """
        results = []
        query_lower = query.lower()
        
        for node in self.graph.nodes(data=True):
            node_id, data = node
            if query_lower in str(node_id).lower() or query_lower in str(data.get("content", "")).lower():
                # Found a match, get neighbors
                neighbors = []
                for neighbor in self.graph.neighbors(node_id):
                    edges = self.graph.get_edge_data(node_id, neighbor)
                    for edge_key, edge_data in edges.items():
                        neighbors.append({
                            "node": neighbor,
                            "relationship": edge_data.get("relationship", "related_to")
                        })
                
                results.append({
                    "node": node_id,
                    "data": data,
                    "neighbors": neighbors
                })
        return results

# Singleton
graph_client = SimpleGraphClient()
