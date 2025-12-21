@description('Location for all resources.')
param location string = resourceGroup().location

@description('Name of the Container Apps Environment.')
param acaEnvName string

@description('Name of the backend container app.')
param appName string = 'engram-api'

@description('Whether to attach a custom domain and managed certificate to the backend.')
param enableCustomDomain bool = false

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

@description('Azure AI Services unified endpoint for Chat (APIM Gateway).')
param azureAiEndpoint string = ''

@description('Azure AI Services project name.')
param azureAiProjectName string = ''

@description('Azure VoiceLive endpoint (Azure AI Services direct).')
param azureVoiceLiveEndpoint string = 'https://zimax.services.ai.azure.com'

@description('Key Vault URI.')
param keyVaultUri string

@description('User-assigned identity resource ID used for Key Vault access.')
param identityResourceId string

@description('User-assigned identity client ID (for DefaultAzureCredential).')
param identityClientId string

@description('Whether API requests require user auth (Entra JWT). Set false for POC/staging to reduce friction.')
param authRequired bool = true

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

// Reference EXISTING managed certificate (already provisioned in Azure)
resource certificate 'Microsoft.App/managedEnvironments/managedCertificates@2024-03-01' existing = if (enableCustomDomain) {
  parent: acaEnv
  name: 'api.engram.work-staging--251217000337'  // Existing certificate name from Azure
}

// Backend API Container App
resource backendApp 'Microsoft.App/containerApps@2023-05-01' = {
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
    managedEnvironmentId: acaEnv.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8080
        transport: 'http'
        allowInsecure: false
        customDomains: enableCustomDomain ? [
          {
            name: customDomainName
            certificateId: certificate.id
            bindingType: 'SniEnabled'
          }
        ] : []


      }
      dapr: {
        enabled: false
      }
      secrets: [
        {
          name: 'postgres-password'
          keyVaultUrl: '${keyVaultUri}secrets/postgres-password'
          identity: identityResourceId
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
          name: 'anthropic-api-key'
          keyVaultUrl: '${keyVaultUri}secrets/anthropic-api-key'
          identity: identityResourceId
        }
        {
          name: 'gemini-api-key'
          keyVaultUrl: '${keyVaultUri}secrets/gemini-api-key'
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
              name: 'AZURE_CLIENT_ID'
              value: identityClientId
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
              name: 'AZURE_AI_ENDPOINT'
              value: azureAiEndpoint
            }
            {
              name: 'AZURE_AI_PROJECT_NAME'
              value: azureAiProjectName
            }
            {
              name: 'AZURE_AI_DEPLOYMENT'
              value: 'gpt-5-chat'
            }
            {
              name: 'AZURE_AI_API_VERSION'
              value: '2024-10-01-preview'
            }
            {
              name: 'AZURE_AI_KEY'
              secretRef: 'azure-ai-key'
            }
            {
              name: 'AZURE_VOICELIVE_ENDPOINT'
              value: azureVoiceLiveEndpoint
            }
            {
              name: 'AZURE_VOICELIVE_MODEL'
              value: 'gpt-realtime'
            }
            {
              name: 'CORS_ORIGINS'
              value: '["https://engram.work", "https://*.azurestaticapps.net", "http://localhost:5173", "*"]'
            }
            {
              name: 'AUTH_REQUIRED'
              value: authRequired ? 'true' : 'false'
            }
            // Sage Agent LLM keys
            {
              name: 'ANTHROPIC_API_KEY'
              secretRef: 'anthropic-api-key'
            }
            {
              name: 'GEMINI_API_KEY'
              secretRef: 'gemini-api-key'
            }
            {
              name: 'ONEDRIVE_DOCS_PATH'
              value: 'docs'
            }
          ]
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          probes: [
            {
              type: 'Startup'
              httpGet: {
                port: 8080
                path: '/health'
              }
              initialDelaySeconds: 60  // Backend starts THIRD (priority 3) - wait for Temporal+Zep
              periodSeconds: 10
              failureThreshold: 12     // 180s total window
            }
            {
              type: 'Readiness'
              httpGet: {
                port: 8080
                path: '/health'
              }
              initialDelaySeconds: 5   // Reduced - startup probe handles initial wait
              periodSeconds: 10
              failureThreshold: 3
            }
            {
              type: 'Liveness'
              httpGet: {
                port: 8080
                path: '/health'
              }
              initialDelaySeconds: 60  // Max allowed (after startup probe completes)
              periodSeconds: 30
              failureThreshold: 5
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        // Warm Start: Set minReplicas to 1 if you want to avoid initial cold start.
        // Current: Warm start enabled for production verification
        maxReplicas: 1
        rules: [
          {
            name: 'http-scale'
            http: {
              metadata: {
                concurrentRequests: '10'
                cooldownPeriod: '1800' // 30 minutes idle before stopping
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
// Use custom domain when enabled, otherwise use default FQDN
output backendUrl string = enableCustomDomain ? 'https://${customDomainName}' : 'https://${backendApp.properties.configuration.ingress.fqdn}'
output backendDefaultFqdn string = backendApp.properties.configuration.ingress.fqdn
output backendId string = backendApp.id

resource authConfig 'Microsoft.App/containerApps/authConfigs@2023-05-01' = {
  parent: backendApp
  name: 'current'
  properties: {
    platform: {
      enabled: false  // Auth handled by application code, not platform
    }
    globalValidation: {
      unauthenticatedClientAction: 'AllowAnonymous'
    }
    // AAD config disabled for staging - enable for production with proper client registration
  }
}



