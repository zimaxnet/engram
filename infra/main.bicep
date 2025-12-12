@description('Location for all resources.')
param location string = resourceGroup().location

@description('Name of the environment.')
param envName string = 'engram-env'


@description('Postgres Admin Password')
@secure()
param postgresPassword string

// param adminObjectId string

@description('Container image for backend API.')
param backendImage string = 'ghcr.io/zimaxnet/engram/backend:latest'

@description('Container image for worker.')
param workerImage string = 'ghcr.io/zimaxnet/engram/worker:latest'

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

@description('Tags to apply to all resources.')
param tags object = {
  Project: 'Engram'
  Environment: 'Production'
}

// =============================================================================
// Log Analytics
// =============================================================================
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2021-06-01' = {
  name: '${envName}-logs'
  location: location
  tags: tags
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
resource acaEnv 'Microsoft.App/managedEnvironments@2022-03-01' = {
  name: '${envName}-aca'
  location: location
  tags: tags
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
// PostgreSQL Flexible Server
// =============================================================================
resource postgres 'Microsoft.DBforPostgreSQL/flexibleServers@2021-06-01' = {
  name: '${envName}-db'
  location: location
  tags: tags
  sku: {
    name: 'Standard_B1ms'
    tier: 'Burstable'
  }
  properties: {
    administratorLogin: 'cogadmin'
    administratorLoginPassword: postgresPassword
    version: '13'
    storage: {
      storageSizeGB: 32
    }
    backup: {
      backupRetentionDays: 7
      geoRedundantBackup: 'Disabled'
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
// Storage Account
// =============================================================================
resource storage 'Microsoft.Storage/storageAccounts@2021-09-01' = {
  name: replace('${envName}store', '-', '')
  location: location
  tags: tags
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
}

// =============================================================================
// Managed Identities (User Assigned)
// =============================================================================
resource backendIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2018-11-30' = {
  name: '${envName}-backend-identity'
  location: location
  tags: tags
}

resource workerIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2018-11-30' = {
  name: '${envName}-worker-identity'
  location: location
  tags: tags
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
    keyVaultName: '${toLower(replace(envName, '-', ''))}kvx${take(uniqueString(resourceGroup().id), 5)}'
    tags: tags
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
    tags: tags
  }
}

// =============================================================================
// Zep Configuration
// =============================================================================
// SaaS URL (v2 API)
var zepApiUrl = 'https://api.getzep.com/api/v2'

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
    tags: tags
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
    tags: tags
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
module dnsModule 'modules/dns.bicep' = {
  name: 'dns'
  scope: resourceGroup('dns-rg')
  params: {
    dnsZoneName: 'engram.work'
    backendFqdn: backendModule.outputs.backendDefaultFqdn
    temporalUIFqdn: temporalModule.outputs.temporalUIDefaultFqdn
  }
}

// =============================================================================
// Outputs
// =============================================================================
output acaEnvId string = acaEnv.id
output postgresFqdn string = postgres.properties.fullyQualifiedDomainName
output keyVaultUri string = keyVaultModule.outputs.keyVaultUri
output backendUrl string = backendModule.outputs.backendUrl
output swaDefaultHostname string = swaModule.outputs.swaDefaultHostname
