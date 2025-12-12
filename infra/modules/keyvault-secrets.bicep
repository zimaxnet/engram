@description('Name of the existing Key Vault.')
param keyVaultName string

@description('PostgreSQL connection string.')
@secure()
param postgresConnectionString string = ''

@description('Zep API key.')
@secure()
param zepApiKey string = ''

@description('Azure OpenAI API key.')
@secure()
param azureOpenAiKey string = ''

@description('Azure OpenAI endpoint.')
param azureOpenAiEndpoint string = ''

@description('Azure Speech API key.')
@secure()
param azureSpeechKey string = ''

@description('Azure Speech region.')
param azureSpeechRegion string = ''

@description('Entra ID client secret.')
@secure()
param entraClientSecret string = ''

@description('Entra ID client ID.')
param entraClientId string = ''

@description('Entra ID tenant ID.')
param entraTenantId string = ''

// Reference existing Key Vault
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' existing = {
  name: keyVaultName
}

// PostgreSQL Connection String
resource postgresSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = if (!empty(postgresConnectionString)) {
  parent: keyVault
  name: 'postgres-connection-string'
  properties: {
    value: postgresConnectionString
    contentType: 'text/plain'
    attributes: {
      enabled: true
    }
  }
}

// Zep API Key (ensure secret exists even if value not provided)
resource zepSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'zep-api-key'
  properties: {
    value: empty(zepApiKey) ? 'placeholder-zep-key' : zepApiKey
    contentType: 'text/plain'
    attributes: {
      enabled: true
    }
  }
}

// Azure OpenAI API Key
resource openAiKeySecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = if (!empty(azureOpenAiKey)) {
  parent: keyVault
  name: 'azure-openai-key'
  properties: {
    value: azureOpenAiKey
    contentType: 'text/plain'
    attributes: {
      enabled: true
    }
  }
}

// Azure OpenAI Endpoint
resource openAiEndpointSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = if (!empty(azureOpenAiEndpoint)) {
  parent: keyVault
  name: 'azure-openai-endpoint'
  properties: {
    value: azureOpenAiEndpoint
    contentType: 'text/plain'
    attributes: {
      enabled: true
    }
  }
}

// Azure Speech API Key
resource speechKeySecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = if (!empty(azureSpeechKey)) {
  parent: keyVault
  name: 'azure-speech-key'
  properties: {
    value: azureSpeechKey
    contentType: 'text/plain'
    attributes: {
      enabled: true
    }
  }
}

// Azure Speech Region
resource speechRegionSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = if (!empty(azureSpeechRegion)) {
  parent: keyVault
  name: 'azure-speech-region'
  properties: {
    value: azureSpeechRegion
    contentType: 'text/plain'
    attributes: {
      enabled: true
    }
  }
}

// Entra ID Client Secret
resource entraSecretResource 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = if (!empty(entraClientSecret)) {
  parent: keyVault
  name: 'entra-client-secret'
  properties: {
    value: entraClientSecret
    contentType: 'text/plain'
    attributes: {
      enabled: true
    }
  }
}

// Entra ID Client ID
resource entraClientIdSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = if (!empty(entraClientId)) {
  parent: keyVault
  name: 'entra-client-id'
  properties: {
    value: entraClientId
    contentType: 'text/plain'
    attributes: {
      enabled: true
    }
  }
}

// Entra ID Tenant ID
resource entraTenantIdSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = if (!empty(entraTenantId)) {
  parent: keyVault
  name: 'entra-tenant-id'
  properties: {
    value: entraTenantId
    contentType: 'text/plain'
    attributes: {
      enabled: true
    }
  }
}

// Outputs
output secretNames array = [
  'postgres-connection-string'
  'zep-api-key'
  'azure-openai-key'
  'azure-openai-endpoint'
  'azure-speech-key'
  'azure-speech-region'
  'entra-client-secret'
  'entra-client-id'
  'entra-tenant-id'
]

