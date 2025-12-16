#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./scripts/setup-entra-apps.sh <env> <tenant_id> <resource_group> <redirect_uri>
# Example:
#   ./scripts/setup-entra-apps.sh staging 00000000-0000-0000-0000-000000000000 engram-rg "https://staging.engram.work/.auth/login/aad/callback"

ENVIRONMENT="${1:-staging}"
TENANT_ID="${2:-}"
RESOURCE_GROUP="${3:-}"
REDIRECT_URI="${4:-}"

if [[ -z "${TENANT_ID}" || -z "${RESOURCE_GROUP}" ]]; then
  echo "TENANT_ID and RESOURCE_GROUP are required."
  exit 1
fi

APP_NAME="engram-api-${ENVIRONMENT}"
APP_ID_URI="api://engram-${ENVIRONMENT}"

echo "Creating app registration ${APP_NAME} in tenant ${TENANT_ID}..."

az deployment tenant create \
  --template-file infra/entra/app-registration.bicep \
  --parameters environment="${ENVIRONMENT}" \
               appDisplayName="${APP_NAME}" \
               appIdUri="${APP_ID_URI}" \
               redirectUris="[${REDIRECT_URI:+\"${REDIRECT_URI}\"}]" \
               allowImplicit=false \
  --only-show-errors

echo "Done. Assign app roles to Entra groups per environment."
#!/usr/bin/env bash
set -euo pipefail

# Usage: ./scripts/setup-entra-apps.sh <tenant_id>
# Requires: az cli logged in with permissions to create app registrations.

TENANT_ID="${1:-}"
if [[ -z "$TENANT_ID" ]]; then
  echo "Usage: $0 <tenant_id>"
  exit 1
fi

ENVS=("dev" "test" "uat" "staging" "prod")
APP_BASE="engram-api"

for ENV in "${ENVS[@]}"; do
  APP_NAME="${APP_BASE}-${ENV}"
  IDENTIFIER_URI="api://engram-${ENV}"

  echo "Creating app: ${APP_NAME} (${IDENTIFIER_URI})"
  az deployment tenant create \
    --template-file infra/entra/app-registration.bicep \
    --parameters environment="${ENV}" \
                 appDisplayName="${APP_NAME}" \
                 identifierUri="${IDENTIFIER_URI}" \
    --query "properties.outputs.appId.value" -o tsv
done

echo "Done. Assign roles to Entra groups and configure SWA/client redirect URIs as needed."
#!/usr/bin/env bash
set -euo pipefail

# Usage: ./scripts/setup-entra-apps.sh <tenant-id>
# Requires: az login (with consent to create apps) and Microsoft Graph AppRoleAssignment.ReadWrite.All

TENANT_ID="${1:-$(az account show --query tenantId -o tsv)}"
APP_BASE="engram-api"
ENVS=("dev" "test" "uat" "staging" "prod")

create_app() {
  local env="$1"
  local app_name="${APP_BASE}-${env}"
  local app_id_uri="api://engram-${env}"

  echo "Creating app ${app_name} (${app_id_uri})"

  az rest --method POST \
    --url "https://graph.microsoft.com/v1.0/applications" \
    --body @- <<EOF
{
  "displayName": "${app_name}",
  "signInAudience": "AzureADMyOrg",
  "identifierUris": ["${app_id_uri}"],
  "api": {
    "requestedAccessTokenVersion": 2,
    "oauth2PermissionScopes": [
      {
        "id": "$(uuidgen)",
        "adminConsentDescription": "Access the Engram API on behalf of the user",
        "adminConsentDisplayName": "Access Engram API",
        "isEnabled": true,
        "type": "User",
        "value": "user_impersonation"
      }
    ]
  },
  "appRoles": [
    { "allowedMemberTypes": ["User","Application"], "description": "Full access to all APIs", "displayName": "Admin", "id": "$(uuidgen)", "isEnabled": true, "value": "Admin" },
    { "allowedMemberTypes": ["User","Application"], "description": "Chat, memory, agents", "displayName": "Analyst", "id": "$(uuidgen)", "isEnabled": true, "value": "Analyst" },
    { "allowedMemberTypes": ["User","Application"], "description": "Workflow and agent management", "displayName": "PM", "id": "$(uuidgen)", "isEnabled": true, "value": "PM" },
    { "allowedMemberTypes": ["User","Application"], "description": "Read-only access", "displayName": "Viewer", "id": "$(uuidgen)", "isEnabled": true, "value": "Viewer" }
  ]
}
EOF
}

for env in "${ENVS[@]}"; do
  create_app "$env"
done

echo "Done. Assign roles via Entra portal or automation as needed."
#!/usr/bin/env bash
set -euo pipefail

# Bootstrap Entra app registrations per environment.
# Requires: az cli logged in with rights to create apps.

TENANT_ID=$(az account show --query tenantId -o tsv)

environments=("dev" "test" "uat" "staging" "prod")

for env in "${environments[@]}"; do
  APP_NAME="engram-api-${env}"
  APP_ID_URI="api://engram-${env}"

  echo "Creating/updating app: ${APP_NAME}"

  APP_ID=$(az ad app list --display-name "${APP_NAME}" --query "[0].appId" -o tsv)
  if [[ -z "${APP_ID}" ]]; then
    APP_ID=$(az ad app create \
      --display-name "${APP_NAME}" \
      --sign-in-audience AzureADMyOrg \
      --identifier-uris "${APP_ID_URI}" \
      --enable-access-token-issuance true \
      --enable-id-token-issuance true \
      --query appId -o tsv)
  fi

  echo "AppId: ${APP_ID}"

  # Define app roles
  read -r -d '' ROLES_JSON <<EOF
[
  {"allowedMemberTypes":["User","Application"],"description":"Full access","displayName":"Admin","value":"Admin","id":"$(uuidgen)","isEnabled":true},
  {"allowedMemberTypes":["User","Application"],"description":"Chat, memory, agents","displayName":"Analyst","value":"Analyst","id":"$(uuidgen)","isEnabled":true},
  {"allowedMemberTypes":["User","Application"],"description":"Workflows and agents","displayName":"PM","value":"PM","id":"$(uuidgen)","isEnabled":true},
  {"allowedMemberTypes":["User","Application"],"description":"Read-only","displayName":"Viewer","value":"Viewer","id":"$(uuidgen)","isEnabled":true}
]
EOF

  # Expose API scope
  SCOPE_ID=$(uuidgen)
  read -r -d '' API_JSON <<EOF
{
  "identifierUris": ["${APP_ID_URI}"],
  "api": {
    "requestedAccessTokenVersion": 2,
    "oauth2PermissionScopes": [{
      "adminConsentDescription": "Allow the app to access API on behalf of the signed-in user.",
      "adminConsentDisplayName": "Access API as user",
      "id": "${SCOPE_ID}",
      "isEnabled": true,
      "type": "User",
      "userConsentDescription": "Allow the app to access API on your behalf.",
      "userConsentDisplayName": "Access API as you",
      "value": "user_impersonation"
    }],
    "appRoles": ${ROLES_JSON}
  },
  "optionalClaims": {
    "idToken": [{"name":"roles"}],
    "accessToken": [{"name":"roles"}]
  },
  "signInAudience": "AzureADMyOrg"
}
EOF

  az rest --method PATCH \
    --url "https://graph.microsoft.com/v1.0/applications/appId=${APP_ID}" \
    --body "${API_JSON}"

  echo "Updated roles and scopes for ${APP_NAME}"
done

echo "Done."

