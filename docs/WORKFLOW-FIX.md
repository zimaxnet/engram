# GitHub Actions Workflow Fix

## Issue
The workflow was using an invalid parameter `deploymentOutputs` which is not supported by `azure/arm-deploy@v2`.

## Error Message
```
Unexpected input(s) 'deploymentOutputs', valid inputs are ['scope', 'subscriptionId', 'managementGroupId', 'region', 'resourceGroupName', 'template', 'deploymentMode', 'deploymentName', 'parameters', 'failOnStdErr', 'additionalArguments']
```

## Solution

### 1. Removed Invalid Parameter
Removed `deploymentOutputs: outputs` from the `azure/arm-deploy@v2` action configuration.

### 2. Query Outputs Using Azure CLI
Since `azure/arm-deploy@v2` doesn't automatically expose outputs in a way that's easily accessible, we now query the deployment outputs explicitly using Azure CLI:

```yaml
- name: Get deployment outputs
  id: outputs
  run: |
    DEPLOYMENT_NAME="engram-infra-${{ github.sha }}"
    echo "backend_url=$(az deployment group show \
      --resource-group ${{ env.AZURE_RESOURCE_GROUP }} \
      --name $DEPLOYMENT_NAME \
      --query 'properties.outputs.backendUrl.value' -o tsv)" >> $GITHUB_OUTPUT
    # ... other outputs
```

### 3. Output Naming Convention
Changed output names to snake_case to match GitHub Actions conventions:
- `backendUrl` → `backend_url`
- `temporalUIFqdn` → `temporal_ui_fqdn`
- `zepApiUrl` → `zep_api_url`
- etc.

## Why This Approach?

The `azure/arm-deploy@v2` action doesn't have a built-in way to expose ARM/Bicep template outputs directly. The action focuses on deployment, not output extraction. By querying the deployment using Azure CLI, we:

1. **Get reliable access** to all outputs
2. **Control the output format** (snake_case for GitHub Actions)
3. **Avoid dependency on action internals** that may change

## Alternative Approaches Considered

### Option 1: Use `azure/arm-deploy@v1`
- Older version, may have different behavior
- Not recommended for new deployments

### Option 2: Parse deployment JSON
- More complex
- Requires additional parsing logic

### Option 3: Use separate Azure CLI commands
- What we implemented
- Most reliable and explicit

## Verification

After this fix, the workflow should:
1. ✅ Deploy without warnings about invalid parameters
2. ✅ Successfully extract all Bicep template outputs
3. ✅ Make outputs available to subsequent jobs via `needs.deploy-infra.outputs.*`

## Testing

To verify the fix works:
```bash
# Check workflow runs without warnings
gh run list --workflow deploy.yml --limit 5

# Check a specific run's logs
gh run view <run-id> --log | grep -i "unexpected\|deploymentOutputs"
```

