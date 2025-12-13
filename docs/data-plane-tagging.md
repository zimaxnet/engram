# Enterprise Data Plane Split & Tagging Schema

## Data Plane Architecture

Engram uses a **two-plane storage architecture** to separate concerns and optimize for different access patterns:

### System of Record (Record Plane)

**Purpose**: Store raw artifacts, parsed documents, and provenance metadata.

**Storage**: Azure Blob Storage

**Contents**:
- Original documents (PDF, DOCX, etc.)
- Parsed/chunked artifacts from Unstructured
- Checksums and metadata
- Access control lists (ACLs)
- Retention policies

**Tag**: `Plane=record`

### System of Recall (Recall Plane)

**Purpose**: Store searchable, queryable memory (episodic + semantic).

**Storage**: Zep (PostgreSQL with pgvector)

**Contents**:
- Episodic memory (conversation sessions)
- Semantic memory (knowledge graph facts)
- Vector embeddings
- Entity relationships

**Tag**: `Plane=recall`

## Tagging Schema

All Azure resources use a consistent tagging schema for:
- **Cost allocation** (FinOps)
- **Resource organization** (filtering, grouping)
- **Governance** (policies, compliance)
- **Operations** (alerting, runbooks)

### Standard Tags

| Tag Key | Values | Description | Example |
|---------|--------|-------------|---------|
| `Project` | `Engram` | Project identifier | `Engram` |
| `Environment` | `staging`, `dev`, `test`, `uat`, `prod` | Environment type | `staging` |
| `Component` | Component name | Service/component identifier | `BackendAPI`, `Zep`, `PostgreSQL`, `BlobStorage` |
| `Plane` | `record`, `recall` | Data plane classification | `record` (Blob), `recall` (Zep/Postgres) |
| `Owner` | Team/contact | Resource owner | `zimax-engram-team` |
| `CostCenter` | Cost center code | Financial allocation | `engram-platform` |
| `DataClass` | `internal`, `confidential`, `restricted` | Data classification | `internal`, `confidential` (Key Vault) |

### Tag Examples

#### Blob Storage (Record Plane)
```json
{
  "Project": "Engram",
  "Environment": "staging",
  "Component": "BlobStorage",
  "Plane": "record",
  "Owner": "zimax-engram-team",
  "CostCenter": "engram-platform",
  "DataClass": "internal"
}
```

#### Zep Container App (Recall Plane)
```json
{
  "Project": "Engram",
  "Environment": "staging",
  "Component": "Zep",
  "Plane": "recall",
  "Owner": "zimax-engram-team",
  "CostCenter": "engram-platform",
  "DataClass": "internal"
}
```

#### Postgres (Recall Plane)
```json
{
  "Project": "Engram",
  "Environment": "staging",
  "Component": "PostgreSQL",
  "Plane": "recall",
  "Owner": "zimax-engram-team",
  "CostCenter": "engram-platform",
  "DataClass": "internal"
}
```

#### Key Vault (Confidential)
```json
{
  "Project": "Engram",
  "Environment": "staging",
  "Component": "KeyVault",
  "Plane": "",
  "Owner": "zimax-engram-team",
  "CostCenter": "engram-platform",
  "DataClass": "confidential"
}
```

## Component Naming Convention

Resources follow the pattern: `{org}-engram-{env}-{component}`

Examples:
- `zimax-engram-staging-api` (Backend API)
- `zimax-engram-staging-worker` (Temporal Worker)
- `zimax-engram-staging-zep` (Zep)
- `zimax-engram-staging-temporal-server` (Temporal Server)
- `zimax-engram-staging-db` (PostgreSQL)

## Environment Definitions

| Environment | Purpose | Network Posture | Private Link |
|-------------|---------|-----------------|--------------|
| `staging` | POC, development | Public ingress allowed (limited) | Disabled |
| `dev` | Feature development | Public ingress allowed | Disabled |
| `test` | Integration testing | Public ingress allowed | Disabled |
| `uat` | Customer acceptance | Private ingress preferred | Enabled |
| `prod` | Production workload | Private ingress required | Enabled |

## Data Classification

- **Internal**: Default for most Engram resources (API, workers, Zep, Postgres, Blob)
- **Confidential**: Key Vault (secrets, credentials)
- **Restricted**: Future use for PII/PHI datasets (if applicable)

## Tag Application in IaC

Tags are applied consistently across all resources via Bicep parameters:

```bicep
var baseTags = {
  Project: 'Engram'
  Environment: environment  // staging, dev, test, uat, prod
  Component: ''  // Set per resource
  Plane: ''  // record or recall
  Owner: 'zimax-engram-team'
  CostCenter: 'engram-platform'
  DataClass: 'internal'
}

var storageTags = union(baseTags, {
  Component: 'BlobStorage'
  Plane: 'record'
})

var zepTags = union(baseTags, {
  Component: 'Zep'
  Plane: 'recall'
})
```

## Cost Allocation

Use tags for FinOps reporting:

```bash
# Cost by environment
az costmanagement query --type Usage \
  --timeframe MonthToDate \
  --dataset aggregation='{"totalCost":{"name":"PreTaxCost","function":"Sum"}}' \
  --dataset grouping='[{"name":"TagName","type":"Tag"}]' \
  --query "filter(TagName=='Environment')"

# Cost by data plane
az costmanagement query --type Usage \
  --timeframe MonthToDate \
  --dataset aggregation='{"totalCost":{"name":"PreTaxCost","function":"Sum"}}' \
  --dataset grouping='[{"name":"TagName","type":"Tag"}]' \
  --query "filter(TagName=='Plane')"
```

## Governance Policies

Use Azure Policy to enforce tagging:

```json
{
  "if": {
    "field": "tags['Project']",
    "exists": false
  },
  "then": {
    "effect": "deny"
  }
}
```

## Migration Path

When moving from staging → dev/test/uat/prod:

1. **Update environment parameter** in IaC deployment
2. **Tags automatically applied** per environment
3. **Private Link toggled** based on environment (`enablePrivateLink` param)
4. **Storage/Postgres SKU adjusted** per environment tier
