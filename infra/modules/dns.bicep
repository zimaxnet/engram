@description('Location for all resources.')
param location string = resourceGroup().location

@description('DNS zone resource group.')
param dnsResourceGroup string = 'dns-rg'

@description('DNS zone name.')
param dnsZoneName string = 'engram.work'

@description('Backend API FQDN.')
param backendFqdn string

@description('Temporal UI FQDN.')
param temporalUIFqdn string

@description('Tags to apply to all resources.')
param tags object = {
  Project: 'Engram'
  Component: 'DNS'
}

// Get DNS zone reference
resource dnsZone 'Microsoft.Network/dnszones@2018-05-01' existing = {
  name: dnsZoneName
  scope: resourceGroup(dnsResourceGroup)
}

// Backend API CNAME record
resource backendDns 'Microsoft.Network/dnszones/CNAME@2018-05-01' = {
  parent: dnsZone
  name: 'api'
  properties: {
    TTL: 3600
    CNAMERecord: {
      cname: backendFqdn
    }
  }
  tags: tags
}

// Temporal UI CNAME record
resource temporalDns 'Microsoft.Network/dnszones/CNAME@2018-05-01' = {
  parent: dnsZone
  name: 'temporal'
  properties: {
    TTL: 3600
    CNAMERecord: {
      cname: temporalUIFqdn
    }
  }
  tags: tags
}

// Note: Frontend uses apex domain (engram.work) which is already configured
// No DNS record needed here as it's managed separately

// Outputs
output backendDnsName string = 'api.${dnsZoneName}'
output temporalDnsName string = 'temporal.${dnsZoneName}'
output frontendDnsName string = dnsZoneName  // Apex domain

