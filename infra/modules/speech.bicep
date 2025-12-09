@description('Location for all resources.')
param location string = resourceGroup().location

@description('Name of the Azure Speech Services resource.')
param speechName string

@description('Name of the Key Vault to store secrets.')
param keyVaultName string

@description('SKU for Speech Services (S0 = Standard).')
param sku string = 'S0'

@description('Tags to apply to all resources.')
param tags object = {
  Project: 'Engram'
  Environment: 'Development'
}

// Azure Speech Services resource
resource speechAccount 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: speechName
  location: location
  kind: 'SpeechServices'
  sku: {
    name: sku
  }
  tags: tags
  properties: {
    apiProperties: {
      statisticsEnabled: false
    }
    customSubDomainName: speechName
    publicNetworkAccess: 'Enabled'
  }
}

// Reference existing Key Vault
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' existing = {
  name: keyVaultName
}

// Store Speech key in Key Vault
resource speechKeySecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'azure-speech-key'
  properties: {
    value: speechAccount.listKeys().key1
    contentType: 'text/plain'
    attributes: {
      enabled: true
    }
  }
}

// Store Speech region in Key Vault
resource speechRegionSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'azure-speech-region'
  properties: {
    value: location
    contentType: 'text/plain'
    attributes: {
      enabled: true
    }
  }
}

// Outputs
output speechEndpoint string = speechAccount.properties.endpoint
output speechName string = speechAccount.name
output speechRegion string = location
output keyVaultSecretNames object = {
  key: 'azure-speech-key'
  region: 'azure-speech-region'
}

