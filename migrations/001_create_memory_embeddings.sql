-- Memory Embeddings Table for Custom Semantic Search
-- Uses pgvector extension (already enabled: azure.extensions = 'btree_gin,vector,pg_trgm,uuid-ossp')
-- 
-- Run this migration against engram database on staging-env-db:
-- psql -h staging-env-db.postgres.database.azure.com -U cogadmin -d engram -f migrations/001_create_memory_embeddings.sql

-- Ensure vector extension is created in the database
CREATE EXTENSION IF NOT EXISTS vector;

-- Memory embeddings table
-- Links to Zep sessions and stores vector embeddings for semantic search
CREATE TABLE IF NOT EXISTS memory_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Reference to Zep session (session_id matches Zep's session table)
    session_id VARCHAR(255) NOT NULL,
    
    -- Optional reference to specific message within session
    message_uuid UUID NULL,
    
    -- The text content that was embedded (for debugging/display)
    content TEXT NOT NULL,
    
    -- The embedding vector (1536 dimensions for text-embedding-ada-002)
    embedding vector(1536) NOT NULL,
    
    -- Metadata for filtering and boosting
    title VARCHAR(500),
    topics TEXT[],
    source_type VARCHAR(50) DEFAULT 'episode',  -- 'wiki', 'document', 'episode', 'conversation'
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for vector similarity search (cosine distance)
-- ivfflat is faster than hnsw for small datasets, switch to hnsw at scale
CREATE INDEX IF NOT EXISTS idx_memory_embeddings_vector 
ON memory_embeddings 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Index for session lookups
CREATE INDEX IF NOT EXISTS idx_memory_embeddings_session 
ON memory_embeddings (session_id);

-- Index for source type filtering
CREATE INDEX IF NOT EXISTS idx_memory_embeddings_source_type 
ON memory_embeddings (source_type);

-- GIN index for topics array search
CREATE INDEX IF NOT EXISTS idx_memory_embeddings_topics
ON memory_embeddings USING GIN (topics);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_memory_embeddings_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update updated_at
DROP TRIGGER IF EXISTS trg_memory_embeddings_updated_at ON memory_embeddings;
CREATE TRIGGER trg_memory_embeddings_updated_at
    BEFORE UPDATE ON memory_embeddings
    FOR EACH ROW
    EXECUTE FUNCTION update_memory_embeddings_updated_at();

-- Add helpful comments
COMMENT ON TABLE memory_embeddings IS 'Stores vector embeddings for semantic search, bypassing Zep OSS limitations';
COMMENT ON COLUMN memory_embeddings.embedding IS 'text-embedding-ada-002 vector (1536 dimensions)';
COMMENT ON COLUMN memory_embeddings.session_id IS 'References Zep session_id for linking back to full content';
