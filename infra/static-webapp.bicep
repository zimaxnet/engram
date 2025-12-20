@description('Location for all resources.')
param location string = resourceGroup().location

@description('Name of the SWA.')
param swaName string = 'engram-web'

@description('Whether to bind the custom domain (requires DNS TXT token).')
param enableCustomDomain bool = false

param customDomainName string = 'engram.work'

@description('Resource ID of the backend container app to link.')
param backendResourceId string = ''

resource swa 'Microsoft.Web/staticSites@2022-03-01' = {
  name: swaName
  location: location
  sku: {
    name: 'Standard'
    tier: 'Standard'
  }
  properties: {
    repositoryUrl: 'https://github.com/zimaxnet/engram'
    branch: 'main'
    provider: 'GitHub'
    stagingEnvironmentPolicy: 'Enabled'
    allowConfigFileUpdates: true
  }
  identity: {
    type: 'SystemAssigned'
  }
}

resource customDomain 'Microsoft.Web/staticSites/customDomains@2022-03-01' = if (enableCustomDomain) {
  parent: swa
  name: customDomainName
  properties: {
    validationMethod: 'dns-txt-token'
  }
}

resource linkedBackend 'Microsoft.Web/staticSites/linkedBackends@2022-03-01' = if (!empty(backendResourceId)) {
  parent: swa
  name: 'backend'
  properties: {
    backendResourceId: backendResourceId
    region: location
  }
}

output swaDefaultHostname string = swa.properties.defaultHostname
output swaIdentityPrincipalId string = swa.identity.principalId
