@description('Location for the AKS cluster.')
param location string = resourceGroup().location

@description('Cluster name.')
param aksName string

@description('DNS prefix.')
param dnsPrefix string = ''

@description('Node size.')
param nodeSize string = 'Standard_D4s_v3'

@description('Node count.')
param nodeCount int = 3

@description('Node min count (autoscale).')
param nodeMinCount int = 3

@description('Node max count (autoscale).')
param nodeMaxCount int = 10

@description('Enable private cluster.')
param enablePrivateCluster bool = true

@description('Enable Azure Policy addon.')
param enableAzurePolicy bool = true

@description('Tags to apply.')
param tags object = {}

resource aks 'Microsoft.ContainerService/managedClusters@2024-02-01' = {
  name: aksName
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  sku: {
    name: 'Base'
    tier: 'Standard'
  }
    properties: {
    dnsPrefix: empty(dnsPrefix) ? aksName : dnsPrefix
    enableRBAC: true
    // privateClusterProfile is set in apiServerAccessProfile for this API version
    securityProfile: {
      workloadIdentity: {
        enabled: true
      }
      defender: {
        enabled: false
      }
      azureKeyVaultKms: {
        enabled: false
      }
    }
    networkProfile: {
      networkPlugin: 'azure'
      loadBalancerSku: 'standard'
      outboundType: 'loadBalancer'
    }
    addonProfiles: union(
      enableAzurePolicy ? {
        azurepolicy: {
          enabled: true
        }
      } : {},
      {}
    )
    autoUpgradeProfile: {
      upgradeChannel: 'node-image'
    }
    apiServerAccessProfile: {
      enablePrivateCluster: enablePrivateCluster
    }
    agentPoolProfiles: [
      {
        name: 'system'
        vmSize: nodeSize
        count: nodeCount
        minCount: nodeMinCount
        maxCount: nodeMaxCount
        type: 'VirtualMachineScaleSets'
        mode: 'System'
        osType: 'Linux'
        enableAutoScaling: true
        availabilityZones: [
          '1'
          '2'
          '3'
        ]
      }
    ]
  }
}

output kubeletIdentityClientId string = aks.properties.identityProfile.kubeletidentity.clientId
output kubeletIdentityObjectId string = aks.properties.identityProfile.kubeletidentity.objectId
output clusterId string = aks.id
