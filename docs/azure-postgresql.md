# Azure Database for PostgreSQL

## Overview

**Azure Database for PostgreSQL** is Microsoft Azure's fully managed, native PostgreSQL database service. It's the direct equivalent to self-hosted PostgreSQL, providing enterprise-grade features with minimal operational overhead.

## Service Tiers

### 1. Flexible Server (Recommended - Currently Used)
- **What it is**: Modern deployment option with maximum control and flexibility
- **Best for**: Production workloads, development, and testing
- **Features**:
  - Zone-redundant high availability (99.99% SLA)
  - Independent compute and storage scaling
  - Better cost optimization with stop/start capability
  - More control over maintenance windows
  - Support for PostgreSQL 11, 12, 13, 14, 15, 16

### 2. Single Server (Legacy)
- **What it is**: Original managed PostgreSQL offering
- **Status**: Being phased out in favor of Flexible Server
- **Best for**: Simple applications (not recommended for new deployments)

## Current Implementation

The Engram platform uses **Azure Database for PostgreSQL Flexible Server** as configured in `infra/main.bicep`:

```bicep
resource postgres 'Microsoft.DBforPostgreSQL/flexibleServers@2021-06-01' = {
  name: '${envName}-db'
  sku: {
    name: 'Standard_B1ms'  // Burstable tier - cost-optimized
    tier: 'Burstable'
  }
  properties: {
    version: '13'
    storage: {
      storageSizeGB: 32
    }
  }
}
```

## Key Features

### 1. AI Integration
- **Native vector search**: Built-in support for AI/ML workloads
- **Azure AI extension**: Direct integration with Azure AI services
- **Local embeddings**: Process embeddings within the database

### 2. High Availability
- **99.99% uptime SLA** with zone-redundant configuration
- Automatic failover for mission-critical applications
- Built-in backup and point-in-time restore

### 3. Cost Optimization
- **Scale-to-zero**: Stop server when not in use (dev/test)
- **Burstable SKUs**: Cost-effective for variable workloads
- **Up to 58% cost reduction** vs on-premises

### 4. Security & Compliance
- **Azure AD authentication**: Integrated with Entra ID
- **Private endpoints**: Isolated network connectivity
- **Encryption at rest**: Automatic data encryption
- **Compliance**: SOC, ISO, HIPAA, PCI-DSS certified

### 5. PostgreSQL Compatibility
- **Latest versions**: Support for PostgreSQL 11-16
- **Extensions**: Full support for PostgreSQL extensions
- **Migration**: Easy migration from on-premises PostgreSQL

## SKU Tiers

### Burstable (B-series) - Current Choice
- **Best for**: Development, testing, low-traffic applications
- **Examples**: `Standard_B1ms`, `Standard_B2s`
- **Cost**: ~$12-25/month (varies by region)
- **Features**: Can burst CPU when needed

### General Purpose
- **Best for**: Most production workloads
- **Examples**: `Standard_D2s_v3`, `Standard_D4s_v3`
- **Cost**: ~$100-400/month
- **Features**: Predictable performance, balanced compute/memory

### Memory Optimized
- **Best for**: High-performance, memory-intensive workloads
- **Examples**: `Standard_E2s_v3`, `Standard_E4s_v3`
- **Cost**: ~$200-800/month
- **Features**: High memory-to-vCPU ratio

## Comparison with Alternatives

| Service | Use Case | Pros | Cons |
|---------|----------|------|------|
| **Azure Database for PostgreSQL** | PostgreSQL workloads | Native PostgreSQL, managed, AI-ready | PostgreSQL-specific |
| **Azure SQL Database** | SQL Server workloads | Microsoft ecosystem, advanced features | Not PostgreSQL |
| **Azure Cosmos DB** | NoSQL, global scale | Multi-model, global distribution | Different data model |
| **Self-hosted PostgreSQL on VM** | Full control | Complete control | Operational overhead |

## Connection Configuration

### Current Setup (from `backend/core/config.py`)

```python
postgres_host: str = Field("localhost", alias="POSTGRES_HOST")
postgres_port: int = Field(5432, alias="POSTGRES_PORT")
postgres_user: str = Field("postgres", alias="POSTGRES_USER")
postgres_password: str = Field("password", alias="POSTGRES_PASSWORD")
postgres_db: str = Field("engram", alias="POSTGRES_DB")
```

### Azure Flexible Server Connection String

```
postgresql://<admin-user>:<password>@<server-name>.postgres.database.azure.com:5432/<database-name>?sslmode=require
```

## Best Practices

1. **Use Flexible Server** for all new deployments
2. **Enable private endpoints** for production (network isolation)
3. **Use Azure AD authentication** when possible (better security)
4. **Configure automated backups** (7-35 day retention)
5. **Monitor with Azure Monitor** (built-in metrics and alerts)
6. **Use connection pooling** (PgBouncer recommended)
7. **Scale compute independently** from storage

## Cost Optimization Tips

1. **Use Burstable SKUs** for dev/test (can stop/start)
2. **Right-size storage** (32GB minimum, pay for what you use)
3. **Enable auto-grow** to avoid over-provisioning
4. **Use reserved capacity** for predictable workloads (up to 55% savings)
5. **Stop servers** during non-business hours (dev/test)

## Migration Path

### From Self-Hosted PostgreSQL
1. Use `pg_dump` to export data
2. Create Azure Database for PostgreSQL Flexible Server
3. Use `pg_restore` to import data
4. Update connection strings
5. Test and validate

### From Single Server (Legacy)
1. Use Azure Database Migration Service
2. Or manual migration with `pg_dump`/`pg_restore`
3. Update application connection strings

## Resources

- [Azure Database for PostgreSQL Documentation](https://learn.microsoft.com/azure/postgresql/)
- [Flexible Server Documentation](https://learn.microsoft.com/azure/postgresql/flexible-server/)
- [Pricing Calculator](https://azure.microsoft.com/pricing/details/postgresql/)
- [Migration Guide](https://learn.microsoft.com/azure/postgresql/flexible-server/how-to-migrate)

## Summary

Azure Database for PostgreSQL Flexible Server is the **native, fully managed PostgreSQL service** on Azure. It provides:

✅ **100% PostgreSQL compatibility**  
✅ **Enterprise-grade availability** (99.99% SLA)  
✅ **AI-ready features** (vector search, embeddings)  
✅ **Cost-effective** (scale-to-zero, burstable SKUs)  
✅ **Secure by default** (encryption, private endpoints, Azure AD)  
✅ **Fully managed** (patching, backups, monitoring)

The Engram platform is already configured to use this service, making it the ideal choice for production deployments.

