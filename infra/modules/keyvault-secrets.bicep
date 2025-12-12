@description('Name of the existing Key Vault.')
param keyVaultName string

@description('PostgreSQL connection string.')
@secure()
param postgresConnectionString string = ''

@description('Zep API key.')
@secure()
param zepApiKey string = ''

@description('Azure AI Services API key for Foundry.')
@secure()
param azureAiKey string = ''

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

// Azure AI Foundry API Key
resource azureAiKeySecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = if (!empty(azureAiKey)) {
  parent: keyVault
  name: 'azure-ai-key'
  properties: {
    value: azureAiKey
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
  'azure-ai-key'
  'entra-client-secret'
  'entra-client-id'
  'entra-tenant-id'
]

