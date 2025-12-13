@description('Location for all resources.')
param location string = resourceGroup().location

@description('ID of the Container Apps Environment.')
param acaEnvId string

@description('Name of the Zep container app.')
param appName string = 'zep'

@description('PostgreSQL FQDN for Zep storage.')
param zepPostgresFqdn string

@description('PostgreSQL admin user for Zep.')
param zepPostgresUser string = 'cogadmin'

@description('PostgreSQL admin password for Zep.')
@secure()
param zepPostgresPassword string

@description('PostgreSQL database name for Zep.')
param zepPostgresDb string = 'zep'

@description('Zep API key (optional, for authentication).')
@secure()
param zepApiKey string = ''

@description('Container image for Zep.')
param zepImage string = 'ghcr.io/getzep/zep:latest'

@description('Container registry server for Zep image.')
param registryServer string = 'ghcr.io'

@description('Registry username (optional, if image is private).')
param registryUsername string = ''

@description('Registry password (optional, if image is private).')
@secure()
param registryPassword string = ''

// Optionally include API key secret/env only when provided to avoid invalid empty secret
var zepApiSecret = empty(zepApiKey) ? [] : [
  {
    name: 'zep-api-key'
    value: zepApiKey
  }
]

var zepApiEnv = empty(zepApiKey) ? [] : [
  {
    name: 'ZEP_API_KEY'
    secretRef: 'zep-api-key'
  }
]

var zepRegistrySecret = empty(registryUsername) ? [] : [
  {
    name: 'zep-registry-password'
    value: registryPassword
  }
]

var zepRegistries = empty(registryUsername) ? [] : [
  {
    server: registryServer
    username: registryUsername
    passwordSecretRef: 'zep-registry-password'
  }
]

@description('Tags to apply to all resources.')
param tags object = {
  Project: 'Engram'
  Component: 'Zep'
}

// Zep Container App
resource zepApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: appName
  location: location
  tags: tags
  properties: {
    managedEnvironmentId: acaEnvId
    configuration: {
      ingress: {
        external: false  // Internal only (accessed by backend/worker within ACA env)
        targetPort: 8000
        allowInsecure: false
      }
      dapr: {
        enabled: false
      }
      secrets: concat([
        {
          name: 'zep-postgres-password'
          value: zepPostgresPassword
        }
      ], zepApiSecret, zepRegistrySecret)
      registries: zepRegistries
    }
    template: {
      containers: [
        {
          name: 'zep'
          image: zepImage
          env: concat([
            {
              name: 'ZEP_SERVER_ADDRESS'
              value: '0.0.0.0:8000'
            }
            {
              name: 'ZEP_STORE'
              value: 'postgres'
            }
            {
              name: 'ZEP_STORE_POSTGRES_DSN'
              value: 'postgresql://${zepPostgresUser}:${zepPostgresPassword}@${zepPostgresFqdn}:5432/${zepPostgresDb}?sslmode=require'
            }
          ], zepApiEnv)
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
        }
      ]
      scale: {
        minReplicas: 0  // Scale-to-zero for POC cost optimization
        maxReplicas: 2
        rules: [
          {
            name: 'http-scale'
            http: {
              metadata: {
                concurrentRequests: '10'
                cooldownPeriod: '1800'  // 30 minutes before scaling down
              }
            }
          }
        ]
      }
    }
  }
}

// Outputs
// For internal-only ingress (external: false), Container Apps still provides an FQDN
// The FQDN works from within the same Container Apps Environment
// Format: http://{fqdn}:{port}
output zepFqdn string = zepApp.properties.configuration.ingress.fqdn
output zepApiUrl string = 'http://${zepApp.properties.configuration.ingress.fqdn}:8000'  // Internal ACA networking (accessible from backend/worker in same env)
