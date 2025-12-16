@description('Location for AKS.')
param location string

@description('AKS cluster name.')
param aksName string

@description('DNS prefix.')
param dnsPrefix string

@description('Node size.')
param nodeSize string = 'Standard_D4s_v3'

@description('Node count.')
param nodeCount int = 3

@description('Min node count.')
param nodeMinCount int = 3

@description('Max node count.')
param nodeMaxCount int = 10

@description('Enable private cluster.')
param enablePrivateCluster bool = true

@description('Enable Azure Policy addon.')
param enableAzurePolicy bool = true

@description('Tags to apply.')
param tags object = {}

resource aks 'Microsoft.ContainerService/managedClusters@2023-08-01' = {
  name: aksName
  location: location
  tags: tags
  properties: {
    kubernetesVersion: ''
    dnsPrefix: dnsPrefix
    apiServerAccessProfile: {
      enablePrivateCluster: enablePrivateCluster
    }
    identity: {
      type: 'SystemAssigned'
    }
    sku: {
      name: 'Base'
      tier: 'Standard'
    }
    aadProfile: {
      managed: true
      enableAzureRBAC: true
    }
    oidcIssuerProfile: {
      enabled: true
    }
    workloadIdentityProfile: {
      enabled: true
    }
    networkProfile: {
      networkPlugin: 'azure'
      loadBalancerSku: 'standard'
      outboundType: 'loadBalancer'
    }
    addonProfiles: {
      azurepolicy: {
        enabled: enableAzurePolicy
      }
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
        orchestratorVersion: ''
        availabilityZones: [
          '1'
          '2'
          '3'
        ]
        enableAutoScaling: true
      }
    ]
  }
}

output kubeletIdentityPrincipalId string = aks.properties.identityProfile.kubeletidentity.objectId
output oidcIssuerUrl string = aks.properties.oidcIssuerProfile.issuerUrl
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
    privateClusterProfile: {
      enabled: enablePrivateCluster
    }
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

output kubeletIdentityClientId string = aks.identityProfile.kubeletidentity.clientId
output kubeletIdentityObjectId string = aks.identityProfile.kubeletidentity.objectId
output clusterId string = aks.id
@description('AKS cluster name')
param clusterName string

@description('Location')
param location string = resourceGroup().location

@description('Node size')
param nodeSize string = 'Standard_D4s_v3'

@description('Node count')
param nodeCount int = 3

@description('Min node count')
param nodeMinCount int = 3

@description('Max node count')
param nodeMaxCount int = 10

@description('Enable private cluster')
param enablePrivateCluster bool = true

@description('Tags')
param tags object = {}

resource aks 'Microsoft.ContainerService/managedClusters@2023-08-02-preview' = {
  name: clusterName
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    kubernetesVersion: '1.29.7'
    dnsPrefix: replace(clusterName, '_', '-')
    enableRBAC: true
    networkProfile: {
      networkPlugin: 'azure'
      networkPolicy: 'azure'
      outboundType: 'loadBalancer'
    }
    apiServerAccessProfile: {
      enablePrivateCluster: enablePrivateCluster
    }
    oidcIssuerProfile: {
      enabled: true
    }
    workloadIdentityProfile: {
      enabled: true
    }
    addonProfiles: {
      azurePolicy: {
        enabled: true
      }
    }
    agentPoolProfiles: [
      {
        name: 'systempool'
        mode: 'System'
        vmSize: nodeSize
        count: nodeCount
        minCount: nodeMinCount
        maxCount: nodeMaxCount
        enableAutoScaling: true
        osType: 'Linux'
        type: 'VirtualMachineScaleSets'
      }
    ]
  }
}

output kubeletIdentity string = aks.properties.identityProfile.kubeletidentity.objectId
output oidcIssuerUrl string = aks.properties.oidcIssuerProfile.issuerUrl
output clusterId string = aks.id

