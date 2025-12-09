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

// ... (existing code) ...

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
    registryUsername: registryUsername
    registryPassword: registryPassword
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
    registryUsername: registryUsername
    registryPassword: registryPassword
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
