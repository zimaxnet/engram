@description('Location for all resources.')
param location string = resourceGroup().location

@description('Name of the environment (used for resource naming).')
param envName string = 'engram-env'

@description('Environment type: staging, dev, test, uat, or prod.')
@allowed(['staging', 'dev', 'test', 'uat', 'prod'])
param environment string = 'staging'

var isProd = environment == 'prod'
@description('Enable authentication requirement for API endpoints.')
param authRequired bool = false  // Disabled for POC testing - enable for UAT/prod later

@description('Enable Azure AD authentication for Postgres (recommended for uat/prod).')
param enablePostgresAad bool = false

@description('Object ID of the AAD admin for Postgres (user or group).')
param postgresAadAdminObjectId string = ''

@description('Tenant ID for AAD admin (defaults to current tenant).')
param postgresAadAdminTenantId string = tenant().tenantId

@description('Enable Private Link for Blob, Postgres, Key Vault (off for staging POC).')
param enablePrivateLink bool = false

@description('Postgres Admin Password')
@secure()
param postgresPassword string

// param adminObjectId string

@description('Container image for backend API.')
param backendImage string = 'ghcr.io/zimaxnet/engram/backend:latest'

@description('Container image for worker.')
param workerImage string = 'ghcr.io/zimaxnet/engram/worker:latest'

@description('Container image for Zep (memory).')
param zepImage string = 'ghcr.io/getzep/zep:latest'

@description('AKS node size (prod).')
param aksNodeSize string = 'Standard_D4s_v3'

@description('AKS node count (prod).')
param aksNodeCount int = 3

@description('AKS min node count (prod).')
param aksNodeMinCount int = 3

@description('AKS max node count (prod).')
param aksNodeMaxCount int = 10

@description('Enable private cluster for AKS (prod).')
param enableAksPrivateCluster bool = true
// param azureOpenAiKey removed
// param azureSpeechKey removed

@description('Azure AI Services unified endpoint (base URL).')
param azureAiEndpoint string = ''



@description('Azure AI Services project name.')
param azureAiProjectName string = ''

@description('Azure AI Model Router deployment name (optional, for intelligent routing).')
param azureAiModelRouter string = ''

@description('Azure AI Services API key for Foundry.')
@secure()
param azureAiKey string = ''

@description('Registry username.')
param registryUsername string

@description('Registry password.')
@secure()
param registryPassword string

@description('Zep API key (stored in Key Vault and used by backend/worker).')
@secure()
param zepApiKey string = ''

// Enhanced tagging schema for enterprise data-plane split
var baseTags = {
  Project: 'Engram'
  Environment: environment
  Component: ''  // Set per resource
  Plane: ''  // record (Blob) or recall (Zep/Postgres)
  Owner: 'zimax-engram-team'
  CostCenter: 'engram-platform'
  DataClass: 'internal'  // internal, confidential, restricted (set per resource)
}

@description('Tags to apply to all resources.')
param tags object = {}

// Merge base tags with overrides
var mergedTags = union(baseTags, tags)

// =============================================================================
// Log Analytics
// =============================================================================
var logAnalyticsTags = union(mergedTags, {
  Component: 'LogAnalytics'
  DataClass: 'internal'
})

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2021-06-01' = {
  name: '${envName}-logs'
  location: location
  tags: logAnalyticsTags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

// =============================================================================
// Container Apps Environment
// =============================================================================
var acaEnvTags = union(mergedTags, {
  Component: 'ContainerAppsEnvironment'
  DataClass: 'internal'
})

resource acaEnv 'Microsoft.App/managedEnvironments@2022-03-01' = {
  name: '${envName}-aca'
  location: location
  tags: acaEnvTags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
  }
}

// =============================================================================
// AKS (Prod only)
// =============================================================================
module aksCluster 'modules/aks.bicep' = if (isProd) {
  name: 'aksCluster'
  params: {
    location: location
    aksName: '${envName}-aks'
    dnsPrefix: '${envName}-aks'
    nodeSize: aksNodeSize
    nodeCount: aksNodeCount
    nodeMinCount: aksNodeMinCount
    nodeMaxCount: aksNodeMaxCount
    enablePrivateCluster: enableAksPrivateCluster
    enableAzurePolicy: true
    tags: union(mergedTags, { Component: 'AKS' })
  }
}

// =============================================================================
// PostgreSQL Flexible Server (Temporal + Zep storage)
// =============================================================================
var postgresTags = union(mergedTags, {
  Component: 'PostgreSQL'
  Plane: 'recall'  // System of recall (memory/knowledge graph)
  DataClass: 'internal'
})

// Postgres SKU selection based on environment
var postgresSku = environment == 'prod' || environment == 'uat' 
  ? { name: 'Standard_D2s_v3', tier: 'GeneralPurpose' }  // HA for uat/prod
  : { name: 'Standard_B2s', tier: 'Burstable' }  // Upgraded for extension performance

var enableAadForEnv = enablePostgresAad || environment == 'prod' || environment == 'uat'

var postgresBackupDays = environment == 'prod' ? 35 : (environment == 'uat' ? 14 : 7)
var postgresGeoRedundant = environment == 'prod' ? 'Enabled' : 'Disabled'

resource postgres 'Microsoft.DBforPostgreSQL/flexibleServers@2022-12-01' = {
  name: '${envName}-db'
  location: location
  tags: postgresTags
  sku: postgresSku
  properties: {
    administratorLogin: 'cogadmin'
    administratorLoginPassword: postgresPassword
    version: '16'  // Use PG16 for pgvector support
    storage: {
      storageSizeGB: environment == 'prod' ? 128 : (environment == 'uat' ? 64 : 32)
    }
    authConfig: {
      activeDirectoryAuth: enableAadForEnv ? 'Enabled' : 'Disabled'
      passwordAuth: 'Enabled'
      tenantId: postgresAadAdminTenantId
    }
    backup: {
      backupRetentionDays: postgresBackupDays
      geoRedundantBackup: postgresGeoRedundant
    }
    highAvailability: {
      mode: (environment == 'prod' || environment == 'uat') ? 'ZoneRedundant' : 'Disabled'
    }
  }

  resource allowAzureServices 'firewallRules' = {
    name: 'AllowAzureServices'
    properties: {
      startIpAddress: '0.0.0.0'
      endIpAddress: '0.0.0.0'
    }
  }

  // Enable required PostgreSQL extensions for Temporal and Zep
  resource azureExtensions 'configurations' = {
    name: 'azure.extensions'
    properties: {
      value: 'btree_gin,vector,pg_trgm,uuid-ossp'
      source: 'user-override'
    }
  }
}

resource postgresAadAdmin 'Microsoft.DBforPostgreSQL/flexibleServers/administrators@2022-12-01' = if (enableAadForEnv && !empty(postgresAadAdminObjectId)) {
  parent: postgres
  name: 'ActiveDirectory'
  properties: {
    principalName: 'aad-admin'
    principalType: 'User'
    tenantId: postgresAadAdminTenantId
  }
}

// =============================================================================
// Storage Account (System of Record - raw artifacts)
// =============================================================================
var storageTags = union(mergedTags, {
  Component: 'BlobStorage'
  Plane: 'record'  // System of record (raw docs, artifacts, provenance)
  DataClass: 'internal'
})

resource storage 'Microsoft.Storage/storageAccounts@2021-09-01' = {
  name: replace('${envName}store', '-', '')
  location: location
  tags: storageTags
  kind: 'StorageV2'
  sku: {
    name: environment == 'prod' ? 'Standard_GRS' : 'Standard_LRS'  // Geo-redundant for prod
  }
  properties: {
    supportsHttpsTrafficOnly: true
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
    networkAcls: {
      defaultAction: enablePrivateLink ? 'Deny' : 'Allow'  // Deny public access when Private Link enabled
      bypass: 'AzureServices'
    }
  }
}

// RBAC: grant blob contributor to backend/worker identities
// RBAC: grant blob contributor to backend/worker identities
resource storageBlobContributorBackend 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storage.id, backendIdentity.name, 'blob-contrib-backend')
  scope: storage
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe') // Storage Blob Data Contributor
    principalId: backendIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

resource storageBlobContributorWorker 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storage.id, workerIdentity.name, 'blob-contrib-worker')
  scope: storage
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')
    principalId: workerIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

// =============================================================================
// Managed Identities (User Assigned)
// =============================================================================
var identityTags = union(mergedTags, {
  Component: 'ManagedIdentity'
  DataClass: 'internal'
})

resource backendIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2018-11-30' = {
  name: '${envName}-backend-identity'
  location: location
  tags: union(identityTags, { Component: 'ManagedIdentity-Backend' })
}

resource workerIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2018-11-30' = {
  name: '${envName}-worker-identity'
  location: location
  tags: union(identityTags, { Component: 'ManagedIdentity-Worker' })
}

// =============================================================================
// Key Vault
// =============================================================================
module keyVaultModule 'modules/keyvault.bicep' = {
  name: 'keyVault'
  params: {
    location: location
    // Key Vault names must be 3-24 alphanumeric only; strip hyphens from envName and suffix a short unique string
    keyVaultName: '${toLower(replace(envName, '-', ''))}kvy${take(uniqueString(resourceGroup().id), 5)}'
    enableSoftDelete: true
    enablePurgeProtection: isProd || environment == 'uat'
    enablePrivateLink: enablePrivateLink
    tags: union(mergedTags, { Component: 'KeyVault', DataClass: 'confidential' })
  }
}

// Seed required secrets (postgres, zep, azure-ai)
module keyVaultSecrets 'modules/keyvault-secrets.bicep' = {
  name: 'keyVaultSecrets'
  params: {
    keyVaultName: keyVaultModule.outputs.keyVaultName
    postgresPassword: postgresPassword
    zepApiKey: zepApiKey
    azureAiKey: azureAiKey
  }
}

// =============================================================================
// Role Assignments (Key Vault Access for Managed Identities)
// =============================================================================
// Key Vault Secrets User (4633458b-17de-408a-b874-0445c86b69e6)
var keyVaultSecretsUserRole = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6')

module backendKvRole 'modules/role-assignment.bicep' = {
  name: 'backend-kv-role'
  params: {
    principalId: backendIdentity.properties.principalId
    roleDefinitionId: keyVaultSecretsUserRole
    nameSeed: 'backend-kv'
  }
}

module workerKvRole 'modules/role-assignment.bicep' = {
  name: 'worker-kv-role'
  params: {
    principalId: workerIdentity.properties.principalId
    roleDefinitionId: keyVaultSecretsUserRole
    nameSeed: 'worker-kv'
  }
}

// =============================================================================
// Temporal Container App
// =============================================================================
module temporalModule 'modules/temporal-aca.bicep' = {
  name: 'temporal'
  params: {
    location: location
    acaEnvId: acaEnv.id
    acaEnvName: acaEnv.name
    // Include environment in app name to avoid cross-environment collisions
    appName: '${envName}-temporal'
    enableCustomDomain: false
    postgresFqdn: postgres.properties.fullyQualifiedDomainName
    postgresUser: 'cogadmin'
    postgresPassword: postgresPassword
    postgresDb: 'temporal'
    tags: union(mergedTags, { Component: 'Temporal' })
  }
}

// =============================================================================
// Zep Self-hosted Deployment
// =============================================================================
// Create Zep database on Postgres
resource zepDb 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2021-06-01' = {
  parent: postgres
  name: 'zep'
  properties: {
    charset: 'UTF8'
    collation: 'en_US.utf8'
  }
}

// Create Temporal database on Postgres
resource temporalDb 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2021-06-01' = {
  parent: postgres
  name: 'temporal'
  properties: {
    charset: 'UTF8'
    collation: 'en_US.utf8'
  }
}

// Create Temporal visibility database on Postgres
resource temporalVisibilityDb 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2021-06-01' = {
  parent: postgres
  name: 'temporal_visibility'
  properties: {
    charset: 'UTF8'
    collation: 'en_US.utf8'
  }
}

// Enable pgvector extension on Zep database
// Note: This requires azure.extensions parameter to include 'vector' in Postgres server config
// The extension is created via init script or manual setup after deployment

var zepTags = union(mergedTags, {
  Component: 'Zep'
  Plane: 'recall'  // System of recall (memory/knowledge graph)
  DataClass: 'internal'
})

module zepModule 'modules/zep-aca.bicep' = {
  name: 'zep'
  params: {
    location: location
    acaEnvId: acaEnv.id
    acaEnvName: acaEnv.name
    enableCustomDomain: true  // Using existing certificate reference
    customDomainName: 'zep.engram.work'
    appName: '${envName}-zep'
    zepPostgresFqdn: postgres.properties.fullyQualifiedDomainName
    zepPostgresUser: 'cogadmin'
    zepPostgresPassword: postgresPassword
    zepPostgresDb: 'zep'
    zepApiKey: zepApiKey
    zepImage: zepImage
    registryServer: 'ghcr.io'
    registryUsername: registryUsername
    registryPassword: registryPassword
    azureAiKey: azureAiKey
    azureAiEndpoint: azureAiEndpoint
    tags: zepTags
  }
}

// Self-hosted Zep API URL (internal to ACA environment)
var zepApiUrl = zepModule.outputs.zepApiUrl

// =============================================================================
// Backend API Container App
// =============================================================================
module backendModule 'modules/backend-aca.bicep' = {
  name: 'backend'
  params: {
    location: location
    acaEnvName: acaEnv.name
    appName: '${envName}-api'
    enableCustomDomain: true  // Using existing certificate reference
    customDomainName: 'api.engram.work'
    containerImage: backendImage
    postgresFqdn: postgres.properties.fullyQualifiedDomainName
    temporalHost: temporalModule.outputs.temporalHost

    zepApiUrl: zepApiUrl

    azureAiEndpoint: azureAiEndpoint
    azureAiProjectName: azureAiProjectName
    azureVoiceLiveEndpoint: 'https://zimax.services.ai.azure.com'
    registryUsername: registryUsername
    registryPassword: registryPassword
    keyVaultUri: keyVaultModule.outputs.keyVaultUri
    identityResourceId: backendIdentity.id
    identityClientId: backendIdentity.properties.clientId
    authRequired: authRequired
    tags: union(mergedTags, { Component: 'BackendAPI' })
  }
}

// =============================================================================
// Worker Container App
// =============================================================================
module workerModule 'modules/worker-aca.bicep' = {
  name: 'worker'
  params: {
    location: location
    acaEnvId: acaEnv.id
    appName: '${envName}-worker'
    containerImage: workerImage
    postgresFqdn: postgres.properties.fullyQualifiedDomainName
    temporalHost: temporalModule.outputs.temporalHost

    zepApiUrl: zepApiUrl

    azureAiEndpoint: azureAiEndpoint
    azureAiProjectName: azureAiProjectName
    registryUsername: registryUsername
    registryPassword: registryPassword
    keyVaultUri: keyVaultModule.outputs.keyVaultUri
    identityResourceId: workerIdentity.id
    identityClientId: workerIdentity.properties.clientId
    tags: union(mergedTags, { Component: 'Worker' })
  }
}

// =============================================================================
// Static Web App
// =============================================================================
module swaModule 'static-webapp.bicep' = {
  name: 'staticWebApp'
  params: {
    location: location
    // Use the default SWA name so certificates remain bound to the intended environment
    swaName: '${envName}-web'
    enableCustomDomain: false
    backendResourceId: backendModule.outputs.backendId
  }
}

// =============================================================================
// DNS Records
// =============================================================================
// Note: Frontend uses apex domain (engram.work) which is configured separately
// Deploy DNS records to the dns-rg resource group where the DNS zone exists
// module dnsModule 'modules/dns.bicep' = {
//   name: 'dns'
//   scope: resourceGroup('dns-rg')
//   params: {
//     dnsZoneName: 'engram.work'
//     backendFqdn: backendModule.outputs.backendDefaultFqdn
//     temporalUIFqdn: temporalModule.outputs.temporalUIDefaultFqdn
//   }
// }

// =============================================================================
// Outputs
// =============================================================================
output acaEnvId string = acaEnv.id
output postgresFqdn string = postgres.properties.fullyQualifiedDomainName
output keyVaultUri string = keyVaultModule.outputs.keyVaultUri
output backendUrl string = backendModule.outputs.backendUrl
output swaDefaultHostname string = swaModule.outputs.swaDefaultHostname
output temporalUIFqdn string = temporalModule.outputs.temporalUIDefaultFqdn
output zepApiUrl string = zepApiUrl

output storageAccountName string = storage.name
// Output SWA Identity Principal ID for debugging/verification
output swaIdentityPrincipalId string = swaModule.outputs.swaIdentityPrincipalId

// Grant SWA Identity 'Reader' access to the Resource Group (or specific resources)
// Role: Reader (acdd72a7-3385-48ef-bd42-f606fba81ae7)
resource swaReaderRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, 'swa-reader-role')
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'acdd72a7-3385-48ef-bd42-f606fba81ae7')
    principalId: swaModule.outputs.swaIdentityPrincipalId
    principalType: 'ServicePrincipal'
  }
}

