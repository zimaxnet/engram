@description('Location for all resources.')
param location string = resourceGroup().location

@description('Name of the Azure OpenAI resource.')
param openAiName string

@description('Name of the Key Vault to store secrets.')
param keyVaultName string

@description('SKU for Azure OpenAI (S0 = Standard).')
param sku string = 'S0'

@description('Deployment name for GPT-4o model.')
param deploymentName string = 'gpt-4o'

@description('Model name for deployment.')
param modelName string = 'gpt-4o'

@description('Model version.')
param modelVersion string = '2024-05-13'

@description('Tags to apply to all resources.')
param tags object = {
  Project: 'Engram'
  Environment: 'Development'
}

// Azure OpenAI resource
resource openAiAccount 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: openAiName
  location: location
  kind: 'OpenAI'
  sku: {
    name: sku
  }
  tags: tags
  properties: {
    apiProperties: {
      statisticsEnabled: false
    }
    customSubDomainName: openAiName
    publicNetworkAccess: 'Enabled'
  }
}

// GPT-4o deployment
resource gpt4oDeployment 'Microsoft.CognitiveServices/accounts/deployments@2023-05-01' = {
  parent: openAiAccount
  name: deploymentName
  properties: {
    model: {
      format: 'OpenAI'
      name: modelName
      version: modelVersion
    }
    raiPolicyName: 'Microsoft.Default'
    versionUpgradeOption: 'OnceNewDefaultVersionAvailable'
  }
}

// Reference existing Key Vault
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' existing = {
  name: keyVaultName
}

// Store OpenAI endpoint in Key Vault
resource openAiEndpointSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'azure-openai-endpoint'
  properties: {
    value: 'https://${openAiAccount.properties.endpoint}'
    contentType: 'text/plain'
    attributes: {
      enabled: true
    }
  }
}

// Store OpenAI key in Key Vault
resource openAiKeySecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'azure-openai-key'
  properties: {
    value: openAiAccount.listKeys().key1
    contentType: 'text/plain'
    attributes: {
      enabled: true
    }
  }
}

// Outputs
output openAiEndpoint string = openAiAccount.properties.endpoint
output openAiName string = openAiAccount.name
output deploymentName string = deploymentName
output keyVaultSecretNames object = {
  endpoint: 'azure-openai-endpoint'
  key: 'azure-openai-key'
}

