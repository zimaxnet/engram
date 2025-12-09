@description('DNS zone resource group.')
param dnsResourceGroup string = 'dns-rg'

@description('DNS zone name.')
param dnsZoneName string = 'engram.work'

@description('Backend API FQDN.')
param backendFqdn string

@description('Temporal UI FQDN.')
param temporalUIFqdn string

// Get DNS zone reference (module is deployed to dns-rg, so zone is in same scope)
resource dnsZone 'Microsoft.Network/dnszones@2018-05-01' existing = {
  name: dnsZoneName
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
}

// Note: Frontend uses apex domain (engram.work) which is already configured
// No DNS record needed here as it's managed separately

// Outputs
output backendDnsName string = 'api.${dnsZoneName}'
output temporalDnsName string = 'temporal.${dnsZoneName}'
output frontendDnsName string = dnsZoneName  // Apex domain

