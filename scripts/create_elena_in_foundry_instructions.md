# Creating Elena in Foundry - Instructions

## Prerequisites

1. **Python Environment**:
   ```bash
   # Activate virtual environment (if using one)
   source venv/bin/activate  # or your venv path
   
   # Install dependencies
   pip install -r backend/requirements.txt
   ```

2. **Foundry Configuration**:
   ```bash
   export AZURE_FOUNDRY_AGENT_ENDPOINT="https://zimax.services.ai.azure.com"
   export AZURE_FOUNDRY_AGENT_PROJECT="zimax"
   export AZURE_FOUNDRY_AGENT_KEY="<optional-api-key>"  # Or use Managed Identity
   ```

3. **Azure Authentication** (if using Managed Identity):
   ```bash
   az login
   # Or ensure Managed Identity is configured in your environment
   ```

## Run Migration Script

```bash
cd /Users/derek/Library/CloudStorage/OneDrive-zimaxnet/code/engram
python3 scripts/create_elena_in_foundry.py
```

## Expected Output

```
============================================================
Creating Elena Agent in Azure AI Foundry
============================================================
Foundry Endpoint: https://zimax.services.ai.azure.com
Foundry Project: zimax

✅ Foundry client initialized
Elena System Prompt Length: 2500 characters
Elena Tools Count: 12
  ✅ Converted tool: send_email
  ✅ Converted tool: list_emails
  ✅ Converted tool: list_onedrive_files
  ✅ Converted tool: save_to_onedrive
  ✅ Converted tool: search_memory
  ✅ Converted tool: analyze_requirements
  ✅ Converted tool: stakeholder_mapping
  ✅ Converted tool: create_user_story
  ...

============================================================
✅ Elena created in Foundry!
   Agent ID: agent_abc123...
   Name: Elena
   Tools: 12
============================================================
   Agent ID saved to: backend/agents/elena_foundry_id.txt
```

## After Creation

1. **Note the Agent ID** from the output

2. **Configure Tool Endpoints in Foundry**:
   - Go to Azure Portal → Azure AI Foundry → Your Project → Agents → Elena
   - Edit agent configuration
   - For each tool, set endpoint URL to: `https://engram.work/api/v1/tools/{tool_name}`

3. **Store Agent ID in Key Vault**:
   ```bash
   az keyvault secret set \
     --vault-name "staging-env-kv" \
     --name "elena-foundry-agent-id" \
     --value "<agent-id-from-output>"
   ```

4. **Add to GitHub Secrets**:
   - Go to GitHub → Settings → Secrets → Actions
   - Add: `ELENA_FOUNDRY_AGENT_ID` → `<agent-id>`

5. **Enable Foundry Elena** (after deployment):
   ```bash
   export ELENA_FOUNDRY_AGENT_ID="<agent-id>"
   export USE_FOUNDRY_ELENA=true
   ```

## Troubleshooting

### "ModuleNotFoundError: No module named 'azure'"

**Solution**: Install dependencies
```bash
pip install -r backend/requirements.txt
```

### "Foundry Agent Service not configured"

**Solution**: Set environment variables
```bash
export AZURE_FOUNDRY_AGENT_ENDPOINT="https://zimax.services.ai.azure.com"
export AZURE_FOUNDRY_AGENT_PROJECT="zimax"
```

### "Failed to create Elena in Foundry: 409 Conflict"

**Solution**: Elena may already exist. The script will try to find and return the existing agent ID.

### Authentication Errors

**Solution**: 
- If using API key: Set `AZURE_FOUNDRY_AGENT_KEY`
- If using Managed Identity: Ensure `az login` completed or MI is configured

