@description('Location for all resources.')
param location string = resourceGroup().location

@description('Name of the Key Vault.')
param keyVaultName string

@description('The tenant ID for the Key Vault.')
param tenantId string = subscription().tenantId

@description('Object ID of the user or service principal that will have access to the Key Vault.')
param adminObjectId string

@description('Enable soft delete for the Key Vault.')
param enableSoftDelete bool = true

@description('Enable purge protection for the Key Vault.')
param enablePurgeProtection bool = true

@description('Tags to apply to all resources.')
param tags object = {
  Project: 'Engram'
  Environment: 'Development'
}

// Key Vault resource
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyVaultName
  location: location
  tags: tags
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: tenantId
    enableSoftDelete: enableSoftDelete
    enablePurgeProtection: enablePurgeProtection ? true : null
    enableRbacAuthorization: true
    enabledForDeployment: false
    enabledForDiskEncryption: false
    enabledForTemplateDeployment: true
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      defaultAction: 'Allow'
      bypass: 'AzureServices'
    }
  }
}

// Role assignment for admin access (Key Vault Administrator)
resource adminRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, adminObjectId, 'Key Vault Administrator')
  scope: keyVault
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '00482a5a-887f-4fb3-b363-3b7fe8e74483') // Key Vault Administrator
    principalId: adminObjectId
    principalType: 'User'
  }
}

// Outputs
output keyVaultId string = keyVault.id
output keyVaultName string = keyVault.name
output keyVaultUri string = keyVault.properties.vaultUri

