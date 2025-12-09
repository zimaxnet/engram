@description('Location for all resources.')
param location string = resourceGroup().location

@description('Name of the Container Apps Environment.')
param acaEnvId string

@description('Name of the Zep container app.')
param appName string = 'zep'

@description('PostgreSQL FQDN.')
param postgresFqdn string

@description('PostgreSQL admin user.')
param postgresUser string = 'cogadmin'

@description('PostgreSQL admin password.')
@secure()
param postgresPassword string

@description('PostgreSQL database name.')
param postgresDb string = 'engram'

@description('Zep API key (optional).')
@secure()
param zepApiKey string = ''

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
        external: true
        targetPort: 8000
        transport: 'http'
        allowInsecure: false
      }
      dapr: {
        enabled: false
      }
    }
    template: {
      containers: [
        {
          name: 'zep'
          image: 'docker.io/getzep/zep:latest'
          env: [
            {
              name: 'ZEP_POSTGRES_DSN'
              value: 'postgresql://${postgresUser}:${postgresPassword}@${postgresFqdn}:5432/${postgresDb}?sslmode=require'
            }
            {
              name: 'ZEP_STORE_TYPE'
              value: 'postgres'
            }
            {
              name: 'ZEP_API_KEY'
              value: zepApiKey
            }
          ]
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
        }
      ]
      scale: {
        minReplicas: 0
        maxReplicas: 3
      }
    }
  }
}

// Outputs
output zepFqdn string = zepApp.properties.configuration.ingress.fqdn
output zepApiUrl string = 'https://${zepApp.properties.configuration.ingress.fqdn}'

