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

@description('Azure AI Services API key.')
@secure()
param azureAiKey string

@description('Azure AI Services Endpoint.')
param azureAiEndpoint string

@description('Azure OpenAI LLM deployment name.')
param azureOpenAiLlmDeployment string = 'gpt-5-chat'

@description('Azure OpenAI Embedding deployment name.')
param azureOpenAiEmbeddingDeployment string = 'text-embedding-ada-002'

// Zep API Key Secret (only if provided)
var zepSecret = empty(zepApiKey) ? [] : [
  {
    name: 'zep-api-key'
    value: zepApiKey
  }
]

// Azure AI Key Secret (only if provided)
var azureAiSecret = empty(azureAiKey) ? [] : [
  {
    name: 'azure-ai-key'
    value: azureAiKey
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

// Build the Zep config.yaml content using string concatenation
var zepDsn = 'postgresql://${zepPostgresUser}:${zepPostgresPassword}@${zepPostgresFqdn}:5432/${zepPostgresDb}?sslmode=require'
var zepConfigContent = 'store:\n  type: postgres\n  postgres:\n    dsn: "${zepDsn}"\nllm:\n  service: openai\n  azure_openai_endpoint: ${azureAiEndpoint}\n  azure_openai:\n    llm_deployment: ${azureOpenAiLlmDeployment}\n    embedding_deployment: ${azureOpenAiEmbeddingDeployment}\nserver:\n  host: 0.0.0.0\n  port: 8000\n  web_enabled: false\nlog:\n  level: debug\nauth:\n  required: false\n'

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
        {
          name: 'zep-config-yaml'
          value: zepConfigContent
        }
      ], zepSecret, azureAiSecret, zepRegistrySecret)
      registries: zepRegistries
    }
    template: {
      volumes: [
        {
          name: 'zep-config-volume'
          storageType: 'Secret'
          secrets: [
            {
              secretRef: 'zep-config-yaml'
              path: 'config.yaml'
            }
          ]
        }
      ]
      containers: [
        {
          name: 'zep'
          image: zepImage
          command: ['/app/zep']
          args: ['--config', '/config/config.yaml']
          volumeMounts: [
            {
              volumeName: 'zep-config-volume'
              mountPath: '/config'
            }
          ]
          env: concat([
            {
              name: 'ZEP_OPENAI_API_KEY'
              secretRef: 'azure-ai-key'
            }
          ], zepApiEnv)
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          probes: [
            {
              type: 'Startup'
              httpGet: {
                port: 8000
                path: '/healthz'
              }
              initialDelaySeconds: 45  // Zep starts SECOND (priority 2) - wait for Temporal
              periodSeconds: 10
              failureThreshold: 12     // 165s total window
            }
            {
              type: 'Readiness'
              httpGet: {
                port: 8000
                path: '/healthz'
              }
              initialDelaySeconds: 5   // Reduced - startup probe handles initial wait
              periodSeconds: 10
              failureThreshold: 3
            }
            {
              type: 'Liveness'
              httpGet: {
                port: 8000
                path: '/healthz'
              }
              initialDelaySeconds: 90  // After startup probe completes
              periodSeconds: 20
              failureThreshold: 10
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1  // Scale-to-zero disabled for POC verification (Warm Start)
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
