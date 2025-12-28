#!/usr/bin/env python3
"""
Run SQL migrations against Azure Postgres.

Usage:
    python scripts/run_migration.py migrations/001_create_memory_embeddings.sql
"""

import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path.parent))

import asyncpg


async def run_migration(sql_file: str):
    """Run a SQL migration file against the Postgres database."""
    
    # Database connection settings
    host = os.environ.get("POSTGRES_HOST", "staging-env-db.postgres.database.azure.com")
    port = int(os.environ.get("POSTGRES_PORT", "5432"))
    user = os.environ.get("POSTGRES_USER", "cogadmin")
    password = os.environ.get("POSTGRES_PASSWORD", "")
    database = os.environ.get("POSTGRES_DB", "engram")
    
    if not password:
        print("ERROR: POSTGRES_PASSWORD environment variable required")
        print("Get it from Azure Key Vault: az keyvault secret show --vault-name stagingenvkvysoxm5 --name postgres-password --query value -o tsv")
        sys.exit(1)
    
    # Read SQL file
    sql_path = Path(sql_file)
    if not sql_path.exists():
        print(f"ERROR: SQL file not found: {sql_file}")
        sys.exit(1)
    
    sql_content = sql_path.read_text()
    
    print(f"🚀 Running migration: {sql_file}")
    print(f"   Target: {host}:{port}/{database}")
    print("-" * 50)
    
    try:
        conn = await asyncpg.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            ssl="require",
        )
        
        # Execute the SQL
        await conn.execute(sql_content)
        
        await conn.close()
        
        print("✅ Migration completed successfully!")
        
    except asyncpg.PostgresError as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/run_migration.py <sql_file>")
        print("Example: python scripts/run_migration.py migrations/001_create_memory_embeddings.sql")
        sys.exit(1)
    
    asyncio.run(run_migration(sys.argv[1]))
