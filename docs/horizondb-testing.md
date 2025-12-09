# Azure HorizonDB Testing Plan

## What is Azure HorizonDB?

**Azure HorizonDB** is Microsoft's **next-generation, fully managed, cloud-native PostgreSQL database service** currently in **preview**. It's designed as a high-performance replacement for traditional PostgreSQL deployments, built on the latest Azure infrastructure.

## Key Capabilities We'll Test

### 1. **Performance & Scalability**
- **Up to 3,072 vCores** across primary nodes and replicas
- **Up to 3x throughput** compared to open-source PostgreSQL for transactional workloads
- **Multi-zone commit latency under 1 millisecond**
- Test how Engram's agent workflows and memory operations perform under high load

### 2. **Storage & Auto-Scaling**
- **Shared storage with auto-scaling** supporting databases up to **128 TB**
- Test storage scaling behavior as Zep memory graph grows
- Validate cost efficiency of auto-scaling vs. fixed storage

### 3. **High Availability**
- Multi-zone architecture for enterprise-grade reliability
- Test failover scenarios for Temporal workflows
- Validate zero-downtime maintenance windows

### 4. **PostgreSQL Compatibility**
- Full PostgreSQL compatibility (same as Flexible Server)
- Test existing Zep and Temporal PostgreSQL integrations
- Validate all PostgreSQL extensions work correctly

## What We'll Test with Engram Platform

### Test Scenarios

#### 1. **Memory Layer (Zep) Performance**
- **Test**: High-volume memory operations (episodic and semantic memory writes)
- **Measure**: Write throughput, query latency for knowledge graph operations
- **Goal**: Validate HorizonDB handles Zep's temporal knowledge graph efficiently

#### 2. **Orchestration Layer (Temporal) Durability**
- **Test**: Long-running workflow persistence and recovery
- **Measure**: Workflow state write/read performance, failover recovery time
- **Goal**: Ensure Temporal's PostgreSQL backend benefits from HorizonDB's performance

#### 3. **Agent Brain Operations**
- **Test**: Concurrent agent reasoning sessions with database queries
- **Measure**: Query latency under load, connection pool efficiency
- **Goal**: Validate agent response times improve with HorizonDB's performance

#### 4. **Cost Optimization**
- **Test**: Auto-scaling behavior during peak vs. idle periods
- **Measure**: Storage costs, compute costs, total cost vs. Flexible Server
- **Goal**: Validate FinOps-first approach with HorizonDB's shared storage model

#### 5. **Migration & Compatibility**
- **Test**: Migrate from Flexible Server to HorizonDB
- **Measure**: Migration time, data integrity, application compatibility
- **Goal**: Ensure seamless migration path for production deployment

## Testing Environment

### Current Setup (Flexible Server)
- **SKU**: Burstable B1ms
- **Storage**: 32GB fixed
- **Version**: PostgreSQL 13
- **Use Case**: Zep memory + Temporal workflows

### HorizonDB Preview Setup
- **Region**: Central US, West US3, UK South, or Australia East (preview availability)
- **Configuration**: TBD based on preview access
- **Migration**: From Flexible Server using standard PostgreSQL tools

## Success Criteria

✅ **Performance**: 2-3x improvement in query throughput  
✅ **Scalability**: Handle 10x memory graph growth without manual intervention  
✅ **Reliability**: 99.99% uptime with sub-millisecond commit latency  
✅ **Cost**: Equal or lower TCO compared to Flexible Server  
✅ **Compatibility**: Zero application code changes required  

## Testing Timeline

1. **Week 1**: Preview access, environment setup, baseline measurements
2. **Week 2**: Migration testing, compatibility validation
3. **Week 3**: Performance testing under load
4. **Week 4**: Cost analysis, documentation, recommendations

## Expected Benefits for Engram

- **Faster agent responses** from improved database performance
- **Better scalability** for growing memory graphs
- **Lower operational overhead** with auto-scaling storage
- **Enterprise readiness** with multi-zone high availability
- **Future-proof** with next-generation Azure infrastructure

## Next Steps

1. Apply for HorizonDB preview access
2. Set up test environment in preview region
3. Create test plan with specific benchmarks
4. Execute migration and performance testing
5. Document findings and recommendations

---

**Note**: HorizonDB is currently in **preview** and available in select regions. This testing will help evaluate it as a potential upgrade path from Azure Database for PostgreSQL Flexible Server.

