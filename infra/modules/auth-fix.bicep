@description('Name of the Container App to fix auth for')
param containerAppName string

resource containerApp 'Microsoft.App/containerApps@2023-05-01' existing = {
  name: containerAppName
}

resource authConfig 'Microsoft.App/containerApps/authConfigs@2023-05-01' = {
  parent: containerApp
  name: 'current'
  properties: {
    platform: {
      enabled: false
    }
    globalValidation: {
      unauthenticatedClientAction: 'AllowAnonymous'
    }
    // Explicitly clearing identity providers to ensure no partial state remains
    identityProviders: null
  }
}
