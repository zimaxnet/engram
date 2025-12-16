@description('Environment name (dev/test/uat/staging/prod)')
param environment string

@description('Display name for the app registration')
param appDisplayName string

@description('App ID URI (api://engram-<env>)')
param appIdUri string

@description('Reply URLs (for SPA/SWA)')
param redirectUris array = []

@description('Allow implicit ID tokens (for SPA) - only for lower envs if needed')
param allowImplicit bool = false

// App roles
var appRoles = [
  {
    allowedMemberTypes: [
      'User'
      'Application'
    ]
    description: 'Full access'
    displayName: 'Admin'
    id: guid(appDisplayName, 'admin-role')
    value: 'Admin'
    isEnabled: true
  }
  {
    allowedMemberTypes: [
      'User'
      'Application'
    ]
    description: 'Chat, memory, agents'
    displayName: 'Analyst'
    id: guid(appDisplayName, 'analyst-role')
    value: 'Analyst'
    isEnabled: true
  }
  {
    allowedMemberTypes: [
      'User'
      'Application'
    ]
    description: 'Workflows, agents'
    displayName: 'PM'
    id: guid(appDisplayName, 'pm-role')
    value: 'PM'
    isEnabled: true
  }
  {
    allowedMemberTypes: [
      'User'
      'Application'
    ]
    description: 'Read-only'
    displayName: 'Viewer'
    id: guid(appDisplayName, 'viewer-role')
    value: 'Viewer'
    isEnabled: true
  }
]

resource app 'Microsoft.Graph/applications@1.0' = {
  displayName: appDisplayName
  signInAudience: 'AzureADMyOrg'
  api: {
    requestedAccessTokenVersion: 2
    oauth2PermissionScopes: [
      {
        adminConsentDescription: 'Access Engram API'
        adminConsentDisplayName: 'Access Engram API'
        id: guid(appDisplayName, 'user-impersonation')
        isEnabled: true
        type: 'User'
        value: 'user_impersonation'
      }
    ]
    appRoles: appRoles
  }
  web: {
    redirectUris: redirectUris
    implicitGrantSettings: {
      enableIdTokenIssuance: allowImplicit
      enableAccessTokenIssuance: false
    }
  }
  identifierUris: [
    appIdUri
  ]
}

resource sp 'Microsoft.Graph/servicePrincipals@1.0' = {
  appId: app.properties.appId
}

output appId string = app.properties.appId
output objectId string = app.id
output spObjectId string = sp.id
@description('Environment name suffix, e.g., dev, test, uat, staging, prod')
param environment string

@description('Display name of the application (e.g., engram-api-staging)')
param appDisplayName string

@description('Identifier URI for the API (e.g., api://engram-staging)')
param identifierUri string

@description('Reply URLs (if SWA/SPA uses implicit/hybrid). Optional.')
param redirectUris array = []

@description('Optional logout URL.')
param logoutUrl string = ''

@description('Optional SPA redirect URIs.')
param spaRedirectUris array = []

var roles = [
  {
    name: 'Admin'
    description: 'Full platform administration'
    value: 'Admin'
  }
  {
    name: 'Analyst'
    description: 'Chat, memory, agents'
    value: 'Analyst'
  }
  {
    name: 'PM'
    description: 'Workflow/project management'
    value: 'PM'
  }
  {
    name: 'Viewer'
    description: 'Read-only access'
    value: 'Viewer'
  }
]

resource app 'Microsoft.Graph/applications@1.0' = {
  displayName: appDisplayName
  api: {
    requestedAccessTokenVersion: 2
    oauth2PermissionScopes: [
      {
        id: newGuid()
        adminConsentDescription: 'Allow the app to access Engram API on behalf of the signed-in user.'
        adminConsentDisplayName: 'Access Engram API'
        userConsentDescription: 'Allow the app to access Engram API on your behalf.'
        userConsentDisplayName: 'Access Engram API'
        value: 'user_impersonation'
        type: 'User'
      }
    ]
  }
  identifierUris: [
    identifierUri
  ]
  signInAudience: 'AzureADMyOrg'
  web: {
    redirectUris: redirectUris
    logoutUrl: empty(logoutUrl) ? null : logoutUrl
    implicitGrantSettings: {
      enableIdTokenIssuance: true
      enableAccessTokenIssuance: true
    }
  }
  spa: {
    redirectUris: spaRedirectUris
  }
  appRoles: [for role in roles: {
    id: newGuid()
    allowedMemberTypes: [
      'User'
      'Application'
    ]
    description: role.description
    displayName: role.name
    isEnabled: true
    value: role.value
  }]
}

resource sp 'Microsoft.Graph/servicePrincipals@1.0' = {
  appId: app.properties.appId
}

output appId string = app.properties.appId
output objectId string = app.id
output servicePrincipalId string = sp.id
output identifier string = identifierUri
@description('Environment name (dev/test/uat/staging/prod)')
param environment string

@description('Display name prefix for the app (e.g., engram-api)')
param appBaseName string = 'engram-api'

@description('API application ID URI base (e.g., api://engram-staging)')
param appIdUri string

@description('Tenant ID')
param tenantId string = subscription().tenantId

@description('Optional reply URLs for frontends')
param replyUrls array = []

@description('Optional logout URL')
param logoutUrl string = ''

@description('Create a service principal for the app')
param createServicePrincipal bool = true

// App roles definition
var appRoles = [
  {
    value: 'Admin'
    description: 'Full access to all APIs'
  }
  {
    value: 'Analyst'
    description: 'Chat, memory, agents'
  }
  {
    value: 'PM'
    description: 'Workflow and agent management'
  }
  {
    value: 'Viewer'
    description: 'Read-only access'
  }
]

resource app 'Microsoft.Graph/applications@1.0' = {
  displayName: '${appBaseName}-${environment}'
  signInAudience: 'AzureADMyOrg'
  web: {
    redirectUris: replyUrls
    logoutUrl: empty(logoutUrl) ? null : logoutUrl
  }
  api: {
    requestedAccessTokenVersion: 2
    oauth2PermissionScopes: [
      {
        id: guid(appIdUri, 'user_impersonation')
        adminConsentDescription: 'Access the Engram API on behalf of the user'
        adminConsentDisplayName: 'Access Engram API'
        isEnabled: true
        type: 'User'
        value: 'user_impersonation'
      }
    ]
  }
  identifierUris: [
    appIdUri
  ]
  appRoles: [
    for role in appRoles: {
      allowedMemberTypes: [
        'User'
        'Application'
      ]
      description: role.description
      displayName: role.value
      id: guid(appBaseName, environment, role.value)
      isEnabled: true
      value: role.value
      origin: 'Application'
    }
  ]
}

resource sp 'Microsoft.Graph/servicePrincipals@1.0' = if (createServicePrincipal) {
  appId: app.appId
  appRoleAssignmentRequired: false
  accountEnabled: true
}

output appId string = app.appId
output appObjectId string = app.id
output spObjectId string = createServicePrincipal ? sp.id : ''
@description('Environment name (dev/test/uat/staging/prod).')
param environment string

@description('Display name for the app registration.')
param appDisplayName string

@description('Identifier URI (App ID URI), e.g., api://engram-staging')
param identifierUri string

@description('Reply URLs for SPA/frontend (optional).')
param redirectUris array = []

var roles = [
  {
    allowedMemberTypes: [
      'User'
      'Application'
    ]
    description: 'Full access'
    displayName: 'Admin'
    id: guid(identifierUri, 'admin')
    isEnabled: true
    value: 'Admin'
  }
  {
    allowedMemberTypes: [
      'User'
      'Application'
    ]
    description: 'Chat, memory, agents'
    displayName: 'Analyst'
    id: guid(identifierUri, 'analyst')
    isEnabled: true
    value: 'Analyst'
  }
  {
    allowedMemberTypes: [
      'User'
      'Application'
    ]
    description: 'Workflows and agents'
    displayName: 'PM'
    id: guid(identifierUri, 'pm')
    isEnabled: true
    value: 'PM'
  }
  {
    allowedMemberTypes: [
      'User'
      'Application'
    ]
    description: 'Read-only'
    displayName: 'Viewer'
    id: guid(identifierUri, 'viewer')
    isEnabled: true
    value: 'Viewer'
  }
]

resource app 'Microsoft.Graph/applications@v1.0' = {
  displayName: appDisplayName
  signInAudience: 'AzureADMyOrg'
  api: {
    requestedAccessTokenVersion: 2
    oauth2PermissionScopes: [
      {
        adminConsentDescription: 'Allow the app to access API on behalf of the signed-in user.'
        adminConsentDisplayName: 'Access API as user'
        id: guid(identifierUri, 'user_impersonation')
        isEnabled: true
        type: 'User'
        userConsentDescription: 'Allow the app to access API on your behalf.'
        userConsentDisplayName: 'Access API as you'
        value: 'user_impersonation'
      }
    ]
    appRoles: roles
  }
  identifierUris: [
    identifierUri
  ]
  web: {
    redirectUris: redirectUris
    implicitGrantSettings: {
      enableIdTokenIssuance: true
      enableAccessTokenIssuance: true
    }
  }
  optionalClaims: {
    idToken: [
      {
        name: 'roles'
      }
    ]
    accessToken: [
      {
        name: 'roles'
      }
    ]
  }
  tags: [
    'engram'
    environment
  ]
}

output clientId string = app.properties.appId
output objectId string = app.id
output identifierUris array = app.identifierUris

