@description('The principal ID to assign the role to.')
param principalId string

@description('The role definition ID.')
param roleDefinitionId string

@description('A seed value to ensure unique name generation (e.g. resource name).')
param nameSeed string

resource roleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, principalId, roleDefinitionId, nameSeed)
  properties: {
    roleDefinitionId: roleDefinitionId
    principalId: principalId
    principalType: 'ServicePrincipal'
  }
}
