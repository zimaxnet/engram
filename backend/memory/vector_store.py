"""
Vector Store Client for Custom Semantic Search.

Provides CRUD operations for the memory_embeddings table using pgvector.
Bypasses Zep OSS limitations by storing embeddings directly in Postgres.
"""

import logging
from typing import Optional
import asyncpg

from backend.core import get_settings
from backend.memory.embedding_client import get_embedding_client

logger = logging.getLogger(__name__)


class VectorStore:
    """
    Custom vector store using pgvector in Postgres.
    
    Connects to the engram database and provides:
    - Store embeddings for session content
    - Semantic search using cosine similarity
    - Hybrid search combining vector + keyword scores
    """
    
    def __init__(self):
        self.settings = get_settings()
        self._pool: Optional[asyncpg.Pool] = None
    
    async def _get_pool(self) -> asyncpg.Pool:
        """Get or create the database connection pool."""
        if self._pool is None:
            # Build connection string from settings
            host = self.settings.postgres_host or "localhost"
            port = int(self.settings.postgres_port or 5432)
            user = self.settings.postgres_user or "cogadmin"
            password = self.settings.postgres_password or ""
            database = self.settings.postgres_db or "engram"
            
            self._pool = await asyncpg.create_pool(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database,
                ssl="require",
                min_size=1,
                max_size=10,
            )
            logger.info(f"VectorStore connected to {host}:{port}/{database}")
        return self._pool
    
    async def store_embedding(
        self,
        session_id: str,
        content: str,
        embedding: list[float],
        title: Optional[str] = None,
        topics: Optional[list[str]] = None,
        source_type: str = "episode",
        message_uuid: Optional[str] = None,
    ) -> str:
        """
        Store an embedding for a session/message.
        
        Args:
            session_id: Zep session ID
            content: The text that was embedded
            embedding: The embedding vector (1536 dimensions)
            title: Optional title for display
            topics: Optional list of topics for filtering
            source_type: 'wiki', 'document', 'episode', 'conversation'
            message_uuid: Optional specific message UUID
            
        Returns:
            The UUID of the stored embedding
        """
        pool = await self._get_pool()
        
        # Convert embedding to pgvector format
        embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"
        
        query = """
            INSERT INTO memory_embeddings 
                (session_id, content, embedding, title, topics, source_type, message_uuid)
            VALUES 
                ($1, $2, $3::vector, $4, $5, $6, $7)
            RETURNING id
        """
        
        async with pool.acquire() as conn:
            result = await conn.fetchval(
                query,
                session_id,
                content[:10000],  # Truncate very long content
                embedding_str,
                title,
                topics,
                source_type,
                message_uuid,
            )
            logger.debug(f"Stored embedding for session {session_id}: {result}")
            return str(result)
    
    async def search_similar(
        self,
        query_embedding: list[float],
        limit: int = 10,
        source_types: Optional[list[str]] = None,
        min_score: float = 0.5,
    ) -> list[dict]:
        """
        Search for similar embeddings using cosine similarity.
        
        Args:
            query_embedding: The query vector
            limit: Maximum results to return
            source_types: Optional filter by source types
            min_score: Minimum similarity score (0-1)
            
        Returns:
            List of matches with session_id, content, score, metadata
        """
        pool = await self._get_pool()
        
        # Convert embedding to pgvector format
        embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"
        
        # Build query with optional source type filter
        if source_types:
            query = """
                SELECT 
                    session_id,
                    content,
                    title,
                    topics,
                    source_type,
                    1 - (embedding <=> $1::vector) as score
                FROM memory_embeddings
                WHERE source_type = ANY($4)
                ORDER BY embedding <=> $1::vector
                LIMIT $2
            """
            params = [embedding_str, limit, min_score, source_types]
        else:
            query = """
                SELECT 
                    session_id,
                    content,
                    title,
                    topics,
                    source_type,
                    1 - (embedding <=> $1::vector) as score
                FROM memory_embeddings
                ORDER BY embedding <=> $1::vector
                LIMIT $2
            """
            params = [embedding_str, limit]
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            
        results = []
        for row in rows:
            score = float(row["score"])
            if score >= min_score:
                results.append({
                    "session_id": row["session_id"],
                    "content": row["content"],
                    "title": row["title"],
                    "topics": row["topics"] or [],
                    "source_type": row["source_type"],
                    "score": score,
                })
        
        logger.info(f"Vector search found {len(results)} results with min_score {min_score}")
        return results
    
    async def delete_session_embeddings(self, session_id: str) -> int:
        """Delete all embeddings for a session."""
        pool = await self._get_pool()
        
        query = "DELETE FROM memory_embeddings WHERE session_id = $1"
        async with pool.acquire() as conn:
            result = await conn.execute(query, session_id)
            count = int(result.split()[-1])
            logger.info(f"Deleted {count} embeddings for session {session_id}")
            return count
    
    async def get_embedding_count(self) -> int:
        """Get total number of stored embeddings."""
        pool = await self._get_pool()
        
        async with pool.acquire() as conn:
            count = await conn.fetchval("SELECT COUNT(*) FROM memory_embeddings")
            return count or 0
    
    async def close(self):
        """Close the connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None


# Singleton instance
_vector_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    """Get or create the vector store singleton."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store


async def store_with_embedding(
    session_id: str,
    content: str,
    title: Optional[str] = None,
    topics: Optional[list[str]] = None,
    source_type: str = "episode",
) -> str:
    """
    Convenience function to generate embedding and store in one call.
    
    Args:
        session_id: Zep session ID
        content: Text content to embed and store
        title: Optional title
        topics: Optional topics list
        source_type: Type of content
        
    Returns:
        UUID of stored embedding
    """
    embedding_client = get_embedding_client()
    embedding = await embedding_client.generate_embedding(content)
    
    store = get_vector_store()
    return await store.store_embedding(
        session_id=session_id,
        content=content,
        embedding=embedding,
        title=title,
        topics=topics,
        source_type=source_type,
    )


async def semantic_search(
    query: str,
    limit: int = 10,
    source_types: Optional[list[str]] = None,
    min_score: float = 0.5,
) -> list[dict]:
    """
    Convenience function for semantic search.
    
    Args:
        query: Search query text
        limit: Max results
        source_types: Optional filter
        min_score: Minimum similarity
        
    Returns:
        List of matching results with scores
    """
    embedding_client = get_embedding_client()
    query_embedding = await embedding_client.generate_embedding(query)
    
    store = get_vector_store()
    return await store.search_similar(
        query_embedding=query_embedding,
        limit=limit,
        source_types=source_types,
        min_score=min_score,
    )
