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

@description('Azure OpenAI API key (will be stored in Key Vault).')
@secure()
param azureOpenAiKey string = ''

@description('Azure Speech API key (optional, will be stored in Key Vault).')
@secure()
param azureSpeechKey string = ''

@description('Azure AI Services unified endpoint (base URL).')
param azureAiEndpoint string = ''

@description('Azure AI Services project name.')
param azureAiProjectName string = ''

@description('Registry username.')
param registryUsername string

@description('Registry password.')
@secure()
param registryPassword string

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
// Key Vault
// =============================================================================
module keyVaultModule 'modules/keyvault.bicep' = {
  name: 'keyVault'
  params: {
    location: location
    keyVaultName: '${envName}-kv-v2-${take(uniqueString(resourceGroup().id), 5)}'
    tags: tags
  }
}

// =============================================================================
// Azure OpenAI
// =============================================================================
module openAiModule 'modules/openai.bicep' = {
  name: 'openAi'
  params: {
    location: location
    openAiName: '${envName}-openai-v2'
    keyVaultName: keyVaultModule.outputs.keyVaultName
    tags: tags
  }
}

// =============================================================================
// Azure Speech Services
// =============================================================================
module speechModule 'modules/speech.bicep' = {
  name: 'speech'
  params: {
    location: location
    speechName: '${envName}-speech-v2'
    keyVaultName: keyVaultModule.outputs.keyVaultName
    tags: tags
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
// Using Zep Cloud (app.getzep.com) instead of self-hosted container
// The Zep container module is commented out - we use Zep Cloud API
// module zepModule 'modules/zep-aca.bicep' = {
//   name: 'zep'
//   params: {
//     location: location
//     acaEnvId: acaEnv.id
//     postgresFqdn: postgres.properties.fullyQualifiedDomainName
//     postgresUser: 'cogadmin'
//     postgresPassword: postgresPassword
//     postgresDb: 'engram'
//     tags: tags
//   }
// }

// Zep Cloud API URL
var zepApiUrl = 'https://app.getzep.com'

// =============================================================================
// Backend API Container App
// =============================================================================
module backendModule 'modules/backend-aca.bicep' = {
  name: 'backend'
  params: {
    location: location
    acaEnvId: acaEnv.id
    containerImage: backendImage
    postgresFqdn: postgres.properties.fullyQualifiedDomainName
    postgresPassword: postgresPassword
    temporalHost: temporalModule.outputs.temporalHost
    zepApiUrl: zepApiUrl
    openAiKey: azureOpenAiKey
    openAiEndpoint: openAiModule.outputs.openAiEndpoint
    speechKey: azureSpeechKey
    azureAiEndpoint: azureAiEndpoint
    azureAiProjectName: azureAiProjectName
    registryUsername: registryUsername
    registryPassword: registryPassword
    keyVaultUri: keyVaultModule.outputs.keyVaultUri
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
    containerImage: workerImage
    postgresFqdn: postgres.properties.fullyQualifiedDomainName
    postgresPassword: postgresPassword
    temporalHost: temporalModule.outputs.temporalHost
    zepApiUrl: zepApiUrl
    openAiKey: azureOpenAiKey
    openAiEndpoint: openAiModule.outputs.openAiEndpoint
    azureAiEndpoint: azureAiEndpoint
    azureAiProjectName: azureAiProjectName
    registryUsername: registryUsername
    registryPassword: registryPassword
    keyVaultUri: keyVaultModule.outputs.keyVaultUri
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
    swaName: '${envName}-web'
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
    backendFqdn: replace(backendModule.outputs.backendUrl, 'https://', '')
    temporalUIFqdn: replace(temporalModule.outputs.temporalUIFqdn, 'https://', '')
  }
}

// =============================================================================
// Outputs
// =============================================================================
output acaEnvId string = acaEnv.id
output postgresFqdn string = postgres.properties.fullyQualifiedDomainName
output keyVaultUri string = keyVaultModule.outputs.keyVaultUri
output backendUrl string = backendModule.outputs.backendUrl
output backendDnsName string = dnsModule.outputs.backendDnsName
output temporalUIFqdn string = temporalModule.outputs.temporalUIFqdn
output temporalDnsName string = dnsModule.outputs.temporalDnsName
output zepApiUrl string = zepApiUrl
output openAiEndpoint string = openAiModule.outputs.openAiEndpoint
output swaDefaultHostname string = swaModule.outputs.swaDefaultHostname
output frontendDnsName string = dnsModule.outputs.frontendDnsName
