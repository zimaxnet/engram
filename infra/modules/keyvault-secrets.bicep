@description('Name of the existing Key Vault.')
param keyVaultName string

@description('PostgreSQL connection string.')
@secure()
param postgresConnectionString string = ''

@description('PostgreSQL password.')
@secure()
param postgresPassword string = ''

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

@description('Azure AI Foundry Agent Service endpoint.')
param azureFoundryAgentEndpoint string = ''

@description('Azure AI Foundry Agent Service project name.')
param azureFoundryAgentProject string = ''

@description('Azure AI Foundry Agent Service API key (optional, uses Managed Identity if not provided).')
@secure()
param azureFoundryAgentKey string = ''

@description('Elena Foundry Agent ID.')
param elenaFoundryAgentId string = ''

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

// PostgreSQL Password
resource postgresPasswordSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'postgres-password'
  properties: {
    value: empty(postgresPassword) ? 'placeholder-postgres-password' : postgresPassword
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

// Azure AI Foundry API Key (seed with placeholder if not provided)
resource azureAiKeySecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'azure-ai-key'
  properties: {
    value: empty(azureAiKey) ? 'placeholder-azure-ai-key' : azureAiKey
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

// Azure AI Foundry Agent Service Endpoint
resource foundryEndpointSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = if (!empty(azureFoundryAgentEndpoint)) {
  parent: keyVault
  name: 'azure-foundry-agent-endpoint'
  properties: {
    value: azureFoundryAgentEndpoint
    contentType: 'text/plain'
    attributes: {
      enabled: true
    }
  }
}

// Azure AI Foundry Agent Service Project
resource foundryProjectSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = if (!empty(azureFoundryAgentProject)) {
  parent: keyVault
  name: 'azure-foundry-agent-project'
  properties: {
    value: azureFoundryAgentProject
    contentType: 'text/plain'
    attributes: {
      enabled: true
    }
  }
}

// Azure AI Foundry Agent Service API Key (optional)
resource foundryKeySecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = if (!empty(azureFoundryAgentKey)) {
  parent: keyVault
  name: 'azure-foundry-agent-key'
  properties: {
    value: azureFoundryAgentKey
    contentType: 'text/plain'
    attributes: {
      enabled: true
    }
  }
}

// Elena Foundry Agent ID
resource elenaAgentIdSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = if (!empty(elenaFoundryAgentId)) {
  parent: keyVault
  name: 'elena-foundry-agent-id'
  properties: {
    value: elenaFoundryAgentId
    contentType: 'text/plain'
    attributes: {
      enabled: true
    }
  }
}

// Outputs
output secretNames array = [
  'postgres-password'
  'postgres-connection-string'
  'zep-api-key'
  'azure-ai-key'
  'entra-client-secret'
  'entra-client-id'
  'entra-tenant-id'
  'azure-foundry-agent-endpoint'
  'azure-foundry-agent-project'
  'azure-foundry-agent-key'
  'elena-foundry-agent-id'
]

