@description('Location for all resources.')
param location string = resourceGroup().location

@description('Name of the Container Apps Environment.')
param acaEnvName string

@description('Name of the backend container app.')
param appName string = 'engram-api'

@description('Custom domain name for the backend.')
param customDomainName string = 'api.engram.work'

@description('Container image for the backend.')
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

@description('Azure Speech key.')
@secure()
param speechKey string = ''

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
  Component: 'Backend'
}

// Get reference to existing ACA environment for parenting the cert
 resource acaEnv 'Microsoft.App/managedEnvironments@2022-03-01' existing = {
  name: acaEnvName
}

resource certificate 'Microsoft.App/managedEnvironments/managedCertificates@2022-03-01' = {
  parent: acaEnv
  name: 'cert-${appName}'
  location: location
  tags: tags
  properties: {
    subjectName: customDomainName
    domainControlValidation: 'CNAME'
  }
}

// Backend API Container App
resource backendApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: appName
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    managedEnvironmentId: acaEnv.id
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
      secrets: [
        {
          name: 'postgres-password'
          value: postgresPassword
        }
        {
          name: 'zep-api-key'
          keyVaultUrl: '${keyVaultUri}secrets/zep-api-key'
          identity: 'system'
        }
        {
          name: 'azure-openai-key'
          value: openAiKey
        }
        {
          name: 'azure-speech-key'
          value: speechKey
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
          name: 'api'
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
              name: 'AZURE_SPEECH_KEY'
              secretRef: speechKey != '' ? 'azure-speech-key' : null
            }
            {
              name: 'AZURE_SPEECH_REGION'
              value: location
            }
            {
              name: 'AZURE_AI_ENDPOINT'
              value: azureAiEndpoint
            }
            {
              name: 'AZURE_AI_PROJECT_NAME'
              value: azureAiProjectName
            }
            {
              name: 'CORS_ORIGINS'
              value: '["https://engram.work", "https://*.azurestaticapps.net", "http://localhost:5173", "*"]'
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
        maxReplicas: 10
        rules: [
          {
            name: 'http-scale'
            http: {
              metadata: {
                concurrentRequests: '10'
              }
            }
          }
        ]
      }
    }
  }
}

// Output default ACA FQDN as URL
output backendFqdn string = backendApp.properties.configuration.ingress.fqdn
output backendUrl string = 'https://${backendApp.properties.configuration.ingress.fqdn}'
output backendDefaultFqdn string = backendApp.properties.configuration.ingress.fqdn
output principalId string = backendApp.identity.principalId


