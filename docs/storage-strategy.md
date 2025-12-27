# Storage Strategy & Scale: Postgres/pgvector for Zep

## Overview

Engram's self-hosted Zep deployment uses **PostgreSQL with the pgvector extension** for storing:
- **Episodic memory** (conversation sessions, message transcripts)
- **Semantic memory** (knowledge graph facts, entities, relationships)
- **Vector embeddings** (for similarity search)

This document outlines the storage strategy, tuning, retention, backups, and RPO/RTO targets per environment.

## Postgres Configuration per Environment

### Staging (POC)

- **SKU**: `Standard_B1ms` (Burstable, 1 vCore, 2GB RAM)
- **Version**: PostgreSQL 16
- **Storage**: 32GB
- **High Availability**: Disabled
- **Backup Retention**: 7 days
- **Geo-redundant Backup**: Disabled
- **Cost**: Minimum (scale-to-zero friendly)

### Dev/Test

- **SKU**: `Standard_B1ms` (Burstable)
- **Version**: PostgreSQL 16
- **Storage**: 32GB
- **High Availability**: Disabled
- **Backup Retention**: 7 days
- **Geo-redundant Backup**: Disabled

### UAT

- **SKU**: `Standard_D2s_v3` (General Purpose, 2 vCores, 8GB RAM)
- **Version**: PostgreSQL 16
- **Storage**: 64GB
- **High Availability**: Zone-redundant
- **Backup Retention**: 14 days
- **Geo-redundant Backup**: Enabled
- **PITR**: Point-in-time restore enabled

### Production

- **SKU**: `Standard_D2s_v3` or higher (General Purpose, HA-capable)
- **Version**: PostgreSQL 16
- **Storage**: 128GB+ (scales with data volume)
- **High Availability**: Zone-redundant
- **Backup Retention**: 35 days
- **Geo-redundant Backup**: Enabled
- **PITR**: Point-in-time restore enabled

## pgvector Extension Setup

### Enable pgvector on Azure Postgres Flexible Server

1. **Add extension to allowed list**:
   - Azure Portal → Postgres server → **Server parameters**
   - Search for `azure.extensions`
   - Add `vector` to the comma-separated list
   - Save

2. **Create extension in Zep database**:
   ```sql
   -- Connect to 'zep' database
   \c zep

   -- Create pgvector extension
   CREATE EXTENSION IF NOT EXISTS vector;

   -- Verify
   SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';
   ```

### pgvector Index Strategy

Zep uses vector similarity search. Recommended indexes:

1. **HNSW (Hierarchical Navigable Small World)** - Best for high-dimensional vectors (>100 dims)
   ```sql
   CREATE INDEX ON zep_embeddings 
   USING hnsw (embedding vector_cosine_ops)
   WITH (m = 16, ef_construction = 64);
   ```

2. **IVFFlat** - Alternative for smaller datasets or when memory is constrained
   ```sql
   CREATE INDEX ON zep_embeddings 
   USING ivfflat (embedding vector_cosine_ops)
   WITH (lists = 100);
   ```

**Recommendation**: Start with HNSW for uat/prod; IVFFlat for dev/test if memory constrained.

## Connection Pooling

- **Recommendation**: Use PgBouncer or Azure Postgres connection pooler for production workloads
- **Pool size**: 20-50 connections per app instance (backend/worker)
- **Idle timeout**: 10 minutes
- **Max lifetime**: 1 hour

## Vacuum & Maintenance

### Autovacuum Configuration

Postgres autovacuum should run regularly to maintain index health:

```sql
-- Check autovacuum status
SELECT schemaname, tablename, last_vacuum, last_autovacuum, last_analyze, last_autoanalyze
FROM pg_stat_user_tables
WHERE schemaname = 'public';
```

### Manual Vacuum (if needed)

```sql
-- Analyze table statistics
ANALYZE zep_facts;

-- Vacuum (reclaim space, update statistics)
VACUUM ANALYZE zep_facts;
```

**Automation**: Azure Postgres Flexible Server handles autovacuum automatically. Monitor via Azure Monitor metrics (`pg_stat_statements` enabled for detailed query stats).

## Retention & Archival

### Episodic Memory (Sessions)

- **Active retention**: 90 days (configurable per tenant)
- **Archive policy**: Move sessions older than 90 days to cold storage (Blob) with metadata preserved
- **Deletion**: GDPR-compliant deletion on request (purge from Postgres + Blob)

### Semantic Memory (Facts)

- **Active retention**: Indefinite (facts don't expire unless explicitly invalidated)
- **Versioning**: Track `valid_from` / `valid_to` timestamps for temporal queries
- **Cleanup**: Periodic job to remove facts with `valid_to < now()` (optional, depends on retention policy)

## Backup Strategy

### RPO (Recovery Point Objective)

- **Staging/Dev/Test**: 24 hours (daily backups)
- **UAT**: 1 hour (hourly snapshots + continuous log backup)
- **Production**: 5 minutes (continuous log backup with PITR)

### RTO (Recovery Time Objective)

- **Staging/Dev/Test**: 4 hours (restore from backup snapshot)
- **UAT**: 1 hour (restore from PITR)
- **Production**: 15 minutes (restore from PITR + HA failover)

### Backup Types

1. **Automated Backups** (Azure Postgres Flexible Server)
   - Full backups: Daily
   - Log backups: Continuous (for PITR)
   - Retention: Per environment (see above)

2. **Manual Snapshots** (before major schema migrations)
   ```bash
   az postgres flexible-server backup create \
     --resource-group engram-rg \
     --server-name <env>-db \
     --backup-name pre-migration-$(date +%Y%m%d)
   ```

3. **Export/Import** (for cross-environment promotion)
   ```bash
   # Export Zep database
   pg_dump -h <source-host> -U cogadmin -d zep -F c -f zep-backup.dump

   # Import to target
   pg_restore -h <target-host> -U cogadmin -d zep zep-backup.dump
   ```

## Encryption

- **Encryption at rest**: Enabled by default (Azure Managed Keys)
- **Encryption in transit**: TLS 1.2+ required (enforced via `sslmode=require` in DSN)
- **Key rotation**: Azure handles key rotation automatically (can use customer-managed keys for prod)

## Monitoring

### Key Metrics

- **Connection pool utilization**: `active_connections / max_connections`
- **Query performance**: `pg_stat_statements` for slow queries
- **Index usage**: `pg_stat_user_indexes` for index hit rates
- **Vacuum activity**: `pg_stat_progress_vacuum` for long-running vacuums
- **Storage growth**: `pg_database_size('zep')` for database size trends

### Alerts

- **High connection count**: >80% of max_connections
- **Slow queries**: >5s execution time
- **Storage >90%**: Approaching storage limit
- **Backup failures**: Automated backup job failures

## Scaling

### Vertical Scaling

- Increase SKU tier (B-series → D-series) for more CPU/RAM
- Increase storage size (32GB → 64GB → 128GB)

### Horizontal Scaling (Future)

- Read replicas for read-heavy workloads (query-only access patterns)
- Sharding (by tenant_id or date range) for very large datasets

## Disaster Recovery

1. **Primary failure**: HA failover (automatic for uat/prod with zone redundancy)
2. **Region failure**: Geo-restore from geo-redundant backups (RTO: 1-4 hours)
3. **Data corruption**: Restore from PITR to point before corruption

## Data Plane Split

- **System of Record**: Raw artifacts stored in **Azure Blob Storage** (see `docs/connectors.md`)
- **System of Recall**: Episodic + semantic memory in **Zep/Postgres** (this document)

The Postgres instance stores Zep's memory data (recall plane). Raw documents and parsed artifacts are stored separately in Blob Storage (record plane) for provenance, reprocessing, and compliance.
