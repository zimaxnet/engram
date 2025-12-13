@description('Location for all resources.')
param location string = resourceGroup().location

@description('Name of the environment (used for resource naming).')
param envName string = 'engram-env'

@description('Environment type: staging, dev, test, uat, or prod.')
@allowed(['staging', 'dev', 'test', 'uat', 'prod'])
param environment string = 'staging'

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

// param azureOpenAiKey removed
// param azureSpeechKey removed

@description('Azure AI Services unified endpoint (base URL).')
param azureAiEndpoint string = ''



@description('Azure AI Services project name.')
param azureAiProjectName string = ''

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
  : { name: 'Standard_B1ms', tier: 'Burstable' }  // Cost-optimized for staging/dev/test

var postgresBackupDays = environment == 'prod' ? 35 : (environment == 'uat' ? 14 : 7)
var postgresGeoRedundant = environment == 'prod' ? 'Enabled' : 'Disabled'

resource postgres 'Microsoft.DBforPostgreSQL/flexibleServers@2021-06-01' = {
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
    // The prior name is stuck in soft-deleted state; add a static differentiator to avoid the collision
    keyVaultName: '${toLower(replace(envName, '-', ''))}kvy${take(uniqueString(resourceGroup().id), 5)}'
    tags: union(mergedTags, { Component: 'KeyVault', DataClass: 'confidential' })
  }
}

// Seed required secrets (Zep API key)
module keyVaultSecrets 'modules/keyvault-secrets.bicep' = {
  name: 'keyVaultSecrets'
  params: {
    keyVaultName: keyVaultModule.outputs.keyVaultName
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
    postgresDb: 'engram'
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
    containerImage: backendImage
    postgresFqdn: postgres.properties.fullyQualifiedDomainName
    postgresPassword: postgresPassword
    temporalHost: temporalModule.outputs.temporalHost

    zepApiUrl: zepApiUrl

    azureAiEndpoint: azureAiEndpoint
    azureAiProjectName: azureAiProjectName
    registryUsername: registryUsername
    registryPassword: registryPassword
    keyVaultUri: keyVaultModule.outputs.keyVaultUri
    identityResourceId: backendIdentity.id
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
    postgresPassword: postgresPassword
    temporalHost: temporalModule.outputs.temporalHost

    zepApiUrl: zepApiUrl

    azureAiEndpoint: azureAiEndpoint
    azureAiProjectName: azureAiProjectName
    registryUsername: registryUsername
    registryPassword: registryPassword
    keyVaultUri: keyVaultModule.outputs.keyVaultUri
    identityResourceId: workerIdentity.id
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
output openAiEndpoint string = azureAiEndpoint
output storageAccountName string = storage.name
