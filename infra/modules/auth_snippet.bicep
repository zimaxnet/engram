
resource authConfig 'Microsoft.App/containerApps/authConfigs@2023-05-01' = {
  parent: backendApp
  name: 'current'
  properties: {
    identityProviders: {
      azureActiveDirectory: {
        enabled: true
        registration: {
          clientId: identityClientId
          openIdIssuer: 'https://sts.windows.net/${subscription().tenantId}/v2.0'
        }
        validation: {
          allowedAudiences: [
            'api://engram-${environment}'
          ]
        }
      }
    }
    globalValidation: {
      unauthenticatedClientAction: 'AllowAnonymous'
    }
  }
}
