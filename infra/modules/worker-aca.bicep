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

@description('Azure OpenAI key.')
@secure()
param openAiKey string

@description('Azure OpenAI endpoint.')
param openAiEndpoint string

@description('Azure AI Services unified endpoint (base URL).')
param azureAiEndpoint string = ''

@description('Azure AI Services project name.')
param azureAiProjectName string = ''

@description('Key Vault URI.')
param keyVaultUri string

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
    type: 'SystemAssigned'
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
          name: 'azure-openai-key'
          value: openAiKey
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
              name: 'AZURE_OPENAI_KEY'
              secretRef: 'azure-openai-key'
            }
            {
              name: 'AZURE_OPENAI_ENDPOINT'
              value: openAiEndpoint
            }
            {
              name: 'AZURE_OPENAI_DEPLOYMENT'
              value: 'gpt-4o'
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
        maxReplicas: 5
      }
    }
  }
}

@description('Key Vault Name.')
param keyVaultName string

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' existing = {
  name: keyVaultName
}

resource keyVaultSecretUserRole 'Microsoft.Authorization/roleDefinitions@2022-04-01' existing = {
  name: '4633458b-17de-408a-b874-0445c86b69e6'
  scope: subscription()
}

resource keyVaultRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: keyVault
  name: guid(keyVault.id, workerApp.id, keyVaultSecretUserRole.id)
  properties: {
    roleDefinitionId: keyVaultSecretUserRole.id
    principalId: workerApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// Outputs
output workerAppName string = workerApp.name
output principalId string = workerApp.identity.principalId

