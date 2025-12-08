# Infrastructure

This folder contains the Bicep templates for the Cognitive Enterprise Architecture.

## Resources Deployed
- **Azure Container Apps Environment**: For hosting Zep, Temporal, and Agents.
- **Postgres Flexible Server (B1ms)**: Shared database for Zep and Temporal.
- **Storage Account**: For Unstructured.io data ingestion (Data Lake).
- **Log Analytics**: Observability.

## Deployment

```bash
az group create --name cogai-rg --location eastus
az deployment group create --resource-group cogai-rg --template-file main.bicep --parameters postgresPassword='<YOUR_SECURE_PASSWORD>'
```
