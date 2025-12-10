# DNS Configuration for Engram Platform

**Date**: December 9, 2025  
**DNS Zone**: `engram.work`  
**Resource Group**: `dns-rg`

---

## DNS Records Summary

### ✅ Configured Records

| Subdomain | Type | Target | Purpose | Status |
|-----------|------|--------|---------|--------|
| **@ (apex)** | A/ALIAS | Static Web App | Frontend application | ✅ Configured separately |
| **api** | CNAME | `engram-api.calmgrass-018b2019.eastus2.azurecontainerapps.io` | Backend API | ✅ Active |
| **temporal** | CNAME | `temporal-ui.calmgrass-018b2019.eastus2.azurecontainerapps.io` | Temporal UI | ✅ Active |

---

## Endpoints

### Frontend
- **Apex Domain**: `https://engram.work` (configured separately)
- **Default Hostname**: `calm-smoke-06afc910f.3.azurestaticapps.net`

### Backend API
- **Custom Domain**: `https://api.engram.work`
- **Default FQDN**: `engram-api.calmgrass-018b2019.eastus2.azurecontainerapps.io`

### Temporal UI
- **Custom Domain**: `https://temporal.engram.work`
- **Default FQDN**: `temporal-ui.calmgrass-018b2019.eastus2.azurecontainerapps.io`

---

## Infrastructure as Code

### DNS Module
**File**: `infra/modules/dns.bicep`

The DNS module creates CNAME records for:
- `api.engram.work` → Backend API Container App
- `temporal.engram.work` → Temporal UI Container App

**Note**: The apex domain (`engram.work`) for the Static Web App is configured separately and not managed by this module.

### Integration
**File**: `infra/main.bicep`

The DNS module is integrated into the main Bicep template and automatically creates DNS records during infrastructure deployment.

---

## Verification

To verify DNS records:

```bash
# Check API record
az network dns record-set cname show \
  --resource-group dns-rg \
  --zone-name engram.work \
  --name api

# Check Temporal record
az network dns record-set cname show \
  --resource-group dns-rg \
  --zone-name engram.work \
  --name temporal

# List all CNAME records
az network dns record-set cname list \
  --resource-group dns-rg \
  --zone-name engram.work
```

---

## DNS Propagation

DNS records use a TTL of 3600 seconds (1 hour). Changes may take up to 1 hour to propagate globally.

---

## Custom Domain Configuration

### Static Web App (Apex Domain)
The Static Web App is configured to use the apex domain (`engram.work`) directly. This is managed separately from the Bicep templates.

### Container Apps
Container Apps automatically accept traffic from custom domains when:
1. CNAME record points to the Container App FQDN
2. DNS propagation is complete

No additional configuration is required for Container Apps - they automatically accept traffic from any domain that resolves to their FQDN.

---

## Troubleshooting

### DNS Not Resolving
1. Verify DNS records exist:
   ```bash
   az network dns record-set cname list --resource-group dns-rg --zone-name engram.work
   ```

2. Check DNS propagation:
   ```bash
   nslookup api.engram.work
   nslookup temporal.engram.work
   ```

3. Verify Container App FQDNs match:
   ```bash
   az containerapp show --name engram-api --resource-group engram-rg --query 'properties.configuration.ingress.fqdn'
   az containerapp show --name temporal-ui --resource-group engram-rg --query 'properties.configuration.ingress.fqdn'
   ```

### SSL/TLS Certificates
Container Apps automatically provision SSL certificates for custom domains via Azure-managed certificates. No manual certificate configuration is required.

---

**Last Updated**: December 9, 2025

