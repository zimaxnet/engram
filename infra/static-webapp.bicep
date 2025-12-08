@description('Location for all resources.')
param location string = resourceGroup().location

@description('Name of the SWA.')
param swaName string = 'engram-web'

@description('The custom domain name.')
param customDomainName string = 'engram.work'

resource swa 'Microsoft.Web/staticSites@2022-03-01' = {
  name: swaName
  location: location
  sku: {
    name: 'Standard'
    tier: 'Standard'
  }
  properties: {
    repositoryUrl: 'https://github.com/zimaxnet/cogai' // Placeholder, will be linked via GH Actions usually
    branch: 'main'
    provider: 'GitHub'
    stagingEnvironmentPolicy: 'Enabled'
    allowConfigFileUpdates: true
  }
}

resource customDomain 'Microsoft.Web/staticSites/customDomains@2022-03-01' = {
  parent: swa
  name: customDomainName
  properties: {}
}

output swaDefaultHostname string = swa.properties.defaultHostname
