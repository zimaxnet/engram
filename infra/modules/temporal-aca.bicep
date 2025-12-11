@description('Location for all resources.')
param location string = resourceGroup().location

@description('ID of the Container Apps Environment.')
param acaEnvId string

@description('Name of the Container Apps Environment (for internal networking).')
param acaEnvName string

@description('Name of the Temporal container app.')
param appName string = 'temporal'

@description('Custom domain name for Temporal UI.')
param customDomainName string = 'temporal.engram.work'

@description('PostgreSQL FQDN.')
param postgresFqdn string

@description('PostgreSQL admin user.')
param postgresUser string = 'cogadmin'

@description('PostgreSQL admin password.')
@secure()
param postgresPassword string

@description('PostgreSQL database name.')
param postgresDb string = 'engram'

@description('Tags to apply to all resources.')
param tags object = {
  Project: 'Engram'
  Component: 'Temporal'
}

resource certificate 'Microsoft.App/managedEnvironments/managedCertificates@2024-03-01' = {
  parent: acaEnv
  name: 'cert-${appName}-ui'
  location: location
  tags: tags
  properties: {
    subjectName: customDomainName
    domainControlValidation: 'CNAME'
  }
}

resource acaEnv 'Microsoft.App/managedEnvironments@2022-03-01' existing = {
  name: acaEnvName
}

// Temporal Server Container App
resource temporalServer 'Microsoft.App/containerApps@2023-05-01' = {
  name: '${appName}-server'
  location: location
  tags: tags
  properties: {
    managedEnvironmentId: acaEnvId
    configuration: {
      ingress: {
        external: false
        targetPort: 7233
        // transport: 'tcp' // Internal ingress handles this automatically, external TCP needs VNet
        allowInsecure: false
      }
      dapr: {
        enabled: false
      }
      secrets: [
        {
          name: 'postgres-password'
          value: postgresPassword
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'temporal-server'
          image: 'temporalio/auto-setup:latest'
          env: [
            {
              name: 'DB'
              value: 'postgresql'
            }
            {
              name: 'DB_PORT'
              value: '5432'
            }
            {
              name: 'POSTGRES_USER'
              value: postgresUser
            }
            {
              name: 'POSTGRES_PWD'
              secretRef: 'postgres-password'
            }
            {
              name: 'POSTGRES_SEEDS'
              value: postgresFqdn
            }
            {
              name: 'POSTGRES_DB'
              value: postgresDb
            }
            {
              name: 'SKIP_DB_CREATE'
              value: 'true'
            }
            {
              name: 'SKIP_DB_SETUP'
              value: 'true'
            }
            {
              name: 'SKIP_DEFAULT_NAMESPACE_CREATION'
              value: 'true'
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

// Temporal UI Container App
resource temporalUI 'Microsoft.App/containerApps@2023-05-01' = {
  name: '${appName}-ui'
  location: location
  tags: tags
  properties: {
    managedEnvironmentId: acaEnvId
    configuration: {
      ingress: {
        external: true
        targetPort: 8080
        transport: 'http'
        allowInsecure: false
        customDomains: [
          {
            name: customDomainName
            certificateId: certificate.id
            bindingType: 'SniEnabled'
          }
        ]

      }
      dapr: {
        enabled: false
      }
    }
    template: {
      containers: [
        {
          name: 'temporal-ui'
          image: 'temporalio/ui:latest'
          env: [
            {
              name: 'TEMPORAL_ADDRESS'
              value: '${temporalServer.name}.${acaEnvName}:7233'
            }
            {
              name: 'TEMPORAL_CORS_ORIGINS'
              value: '*'
            }
          ]
          resources: {
            cpu: json('0.25')
            memory: '0.5Gi'
          }
        }
      ]
      scale: {
        minReplicas: 0
        maxReplicas: 2
      }
    }
  }
}

// Outputs
output temporalServerFqdn string = temporalServer.properties.configuration.ingress.fqdn
output temporalUIUrl string = 'https://${temporalUI.properties.configuration.ingress.fqdn}'
output temporalUIDefaultFqdn string = temporalUI.properties.configuration.ingress.fqdn
output temporalHost string = '${temporalServer.properties.configuration.ingress.fqdn}:7233'

