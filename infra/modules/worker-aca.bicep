@description('Location for all resources.')
param location string = resourceGroup().location

@description('Name of the Container Apps Environment.')
param acaEnvId string

@description('Name of the worker container app.')
param appName string = 'engram-worker'

@description('Container image for the worker.')
param containerImage string

@description('PostgreSQL FQDN.')
param postgresFqdn string

@description('Temporal host.')
param temporalHost string

@description('Zep API URL.')
param zepApiUrl string

@description('PostgreSQL password.')
@secure()
param postgresPassword string

@description('Azure AI Services unified endpoint (base URL).')
param azureAiEndpoint string = ''

@description('Azure AI Services project name.')
param azureAiProjectName string = ''

@description('Key Vault URI.')
param keyVaultUri string

@description('User-assigned identity resource ID used for Key Vault access.')
param identityResourceId string

@description('Registry username.')
param registryUsername string

@description('Registry password.')
@secure()
param registryPassword string

@description('Tags to apply to all resources.')
param tags object = {
  Project: 'Engram'
  Component: 'Worker'
}

// Worker Container App
resource workerApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: appName
  location: location
  tags: tags
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${identityResourceId}': {}
    }
  }
  properties: {
    managedEnvironmentId: acaEnvId
    configuration: {
      ingress: {
        external: false
      }
      dapr: {
        enabled: false
      }
      secrets: [
        {
          name: 'postgres-password'
          value: postgresPassword
        }
        {
          name: 'zep-api-key'
          keyVaultUrl: '${keyVaultUri}secrets/zep-api-key'
          identity: identityResourceId
        }
        {
          name: 'azure-ai-key'
          keyVaultUrl: '${keyVaultUri}secrets/azure-ai-key'
          identity: identityResourceId
        }
        {
          name: 'registry-password'
          value: registryPassword
        }
      ]
      registries: [
        {
          server: 'ghcr.io'
          username: registryUsername
          passwordSecretRef: 'registry-password'
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'worker'
          image: containerImage
          env: [
            {
              name: 'ENVIRONMENT'
              value: 'production'
            }
            {
              name: 'AZURE_KEYVAULT_URL'
              value: keyVaultUri
            }
            {
              name: 'POSTGRES_HOST'
              value: postgresFqdn
            }
            {
              name: 'POSTGRES_PORT'
              value: '5432'
            }
            {
              name: 'POSTGRES_USER'
              value: 'cogadmin'
            }
            {
              name: 'POSTGRES_PASSWORD'
              secretRef: 'postgres-password'
            }
            {
              name: 'POSTGRES_DB'
              value: 'engram'
            }
            {
              name: 'TEMPORAL_HOST'
              value: temporalHost
            }
            {
              name: 'TEMPORAL_NAMESPACE'
              value: 'default'
            }
            {
              name: 'TEMPORAL_TASK_QUEUE'
              value: 'engram-agents'
            }
            {
              name: 'ZEP_API_URL'
              value: zepApiUrl
            }
            {
              name: 'ZEP_API_KEY'
              secretRef: 'zep-api-key'
            }
            {
              name: 'AZURE_AI_KEY'
              secretRef: 'azure-ai-key'
            }
            {
              name: 'AZURE_AI_ENDPOINT'
              value: azureAiEndpoint
            }
            {
              name: 'AZURE_AI_PROJECT_NAME'
              value: azureAiProjectName
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
        // Keep max low for cost control; allow scale-to-zero after idle
        maxReplicas: 1
        rules: [
          {
            name: 'http-scale'
            http: {
              metadata: {
                concurrentRequests: '5'
                cooldownPeriod: '1800' // seconds (30 minutes) before scaling down
              }
            }
          }
        ]
      }
    }
  }
}

// Outputs
output workerAppName string = workerApp.name

