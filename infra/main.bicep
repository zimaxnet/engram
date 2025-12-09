@description('Location for all resources.')
param location string = resourceGroup().location

@description('Name of the environment.')
param envName string = 'engram-env'

@description('Postgres Admin Password')
@secure()
param postgresPassword string

@description('Object ID of the admin user/service principal.')
param adminObjectId string

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
    keyVaultName: '${envName}-kv-${take(uniqueString(resourceGroup().id), 5)}'
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
    openAiName: '${envName}-openai'
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
    speechName: '${envName}-speech'
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
// Zep Container App
// =============================================================================
module zepModule 'modules/zep-aca.bicep' = {
  name: 'zep'
  params: {
    location: location
    acaEnvId: acaEnv.id
    postgresFqdn: postgres.properties.fullyQualifiedDomainName
    postgresUser: 'cogadmin'
    postgresPassword: postgresPassword
    postgresDb: 'engram'
    tags: tags
  }
}

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
    zepApiUrl: zepModule.outputs.zepApiUrl
    openAiKey: azureOpenAiKey
    openAiEndpoint: openAiModule.outputs.openAiEndpoint
    speechKey: azureSpeechKey
    azureAiEndpoint: azureAiEndpoint
    azureAiProjectName: azureAiProjectName
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
    zepApiUrl: zepModule.outputs.zepApiUrl
    openAiKey: azureOpenAiKey
    openAiEndpoint: openAiModule.outputs.openAiEndpoint
    azureAiEndpoint: azureAiEndpoint
    azureAiProjectName: azureAiProjectName
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
// Outputs
// =============================================================================
output acaEnvId string = acaEnv.id
output postgresFqdn string = postgres.properties.fullyQualifiedDomainName
output keyVaultUri string = keyVaultModule.outputs.keyVaultUri
output backendUrl string = backendModule.outputs.backendUrl
output temporalUIFqdn string = temporalModule.outputs.temporalUIFqdn
output zepApiUrl string = zepModule.outputs.zepApiUrl
output openAiEndpoint string = openAiModule.outputs.openAiEndpoint
output swaDefaultHostname string = swaModule.outputs.swaDefaultHostname
