# Next Steps - Engram Platform Development

This document outlines the recommended next steps for completing the Engram platform development and deployment.

## Immediate Next Steps (Priority 1)

### 1. Test VoiceLive Integration Locally

**Goal**: Verify VoiceLive works with both Elena and Marcus before deploying.

**Steps**:
```bash
# Install VoiceLive SDK
cd backend
pip install azure-ai-voicelive

# Set environment variables
export AZURE_AI_ENDPOINT="https://zimax.services.ai.azure.com"
export AZURE_AI_PROJECT_NAME="zimax"
export AZURE_OPENAI_KEY="your-key"

# Start backend
uvicorn backend.api.main:app --host 0.0.0.0 --port 8082 --reload

# Test VoiceLive WebSocket
# Use a WebSocket client to connect to:
# ws://localhost:8082/api/v1/voice/voicelive/test-session-123
```

**Test Cases**:
- [ ] Connect to VoiceLive WebSocket
- [ ] Send audio data and receive response
- [ ] Switch between Elena and Marcus
- [ ] Test barge-in (cancel response)
- [ ] Verify transcription status updates

### 2. Update Frontend VoiceChat Component

**Goal**: Integrate VoiceLive WebSocket into the frontend.

**Files to Update**:
- `frontend/src/components/VoiceChat/VoiceChat.tsx`
- `frontend/src/components/ChatPanel/ChatPanel.tsx`

**Changes Needed**:
- Replace traditional Speech Services WebSocket with VoiceLive endpoint
- Update audio format handling (PCM16, 24kHz)
- Add agent switching UI
- Handle VoiceLive-specific message types

**Implementation**:
```typescript
// Connect to VoiceLive instead of traditional voice
const ws = new WebSocket(
  `${WS_URL}/api/v1/voice/voicelive/${sessionId}`
);

// Send audio
ws.send(JSON.stringify({
  type: "audio",
  data: base64Audio
}));

// Switch agent
ws.send(JSON.stringify({
  type: "agent",
  agent_id: "marcus"
}));
```

### 3. Verify Azure Deployment Configuration

**Goal**: Ensure all Bicep templates and deployment workflows are correct.

**Checklist**:
- [ ] Review `infra/main.bicep` for all required parameters
- [ ] Verify `.github/workflows/deploy.yml` passes all secrets
- [ ] Check Container App environment variables
- [ ] Verify Key Vault access policies
- [ ] Test Bicep deployment in a dev environment

**Commands**:
```bash
# Validate Bicep templates
az bicep build --file infra/main.bicep

# Test deployment (dry-run)
az deployment group validate \
  --resource-group engram-dev-rg \
  --template-file infra/main.bicep \
  --parameters @infra/parameters/dev.json
```

## Short-term Steps (Priority 2)

### 4. Complete Agent Brain Implementation

**Current Status**: Placeholder LangGraph implementations

**Tasks**:
- [ ] Implement actual LangGraph workflows for Elena
- [ ] Implement actual LangGraph workflows for Marcus
- [ ] Add tool calling and execution
- [ ] Integrate with Zep memory for context retrieval
- [ ] Add error handling and retry logic

**Files**:
- `backend/agents/elena/agent.py` - Complete `_reason_node` implementation
- `backend/agents/marcus/agent.py` - Complete `_reason_node` implementation
- `backend/agents/base.py` - Enhance graph building

### 5. Integrate Zep Memory Service

**Current Status**: Placeholder implementations

**Tasks**:
- [ ] Implement actual Zep client calls
- [ ] Add episodic memory storage
- [ ] Add semantic knowledge graph retrieval
- [ ] Implement memory summarization
- [ ] Add memory search and retrieval

**Files**:
- `backend/memory/client.py` - Complete Zep integration
- `backend/workflows/activities.py` - Add memory activities

### 6. Complete Temporal Workflows

**Current Status**: Basic workflow structure

**Tasks**:
- [ ] Implement all workflow activities
- [ ] Add proper error handling and retries
- [ ] Implement human-in-the-loop approval workflow
- [ ] Add workflow monitoring and observability
- [ ] Test long-running conversations

**Files**:
- `backend/workflows/activities.py` - Complete all activities
- `backend/workflows/agent_workflow.py` - Enhance workflows
- `backend/workflows/worker.py` - Verify worker setup

## Medium-term Steps (Priority 3)

### 7. Frontend Enhancements

**Tasks**:
- [ ] Add VoiceLive connection status indicator
- [ ] Show agent switching UI
- [ ] Display transcription in real-time
- [ ] Add audio level visualization
- [ ] Improve error handling and user feedback
- [ ] Add voice settings (volume, speed)

### 8. Observability and Monitoring

**Tasks**:
- [ ] Verify OpenTelemetry integration
- [ ] Set up Application Insights dashboards
- [ ] Add custom metrics for agent performance
- [ ] Configure alerting for errors
- [ ] Add distributed tracing

**Files**:
- `backend/observability/telemetry.py` - Verify configuration
- `backend/observability/logging.py` - Add structured logging

### 9. Security Hardening

**Tasks**:
- [ ] Test Microsoft Entra ID authentication
- [ ] Verify RBAC enforcement
- [ ] Add rate limiting
- [ ] Implement PII masking
- [ ] Add audit logging
- [ ] Security testing and penetration testing

**Files**:
- `backend/api/middleware/auth.py` - Test authentication
- `backend/api/middleware/rbac.py` - Verify RBAC

### 10. Performance Optimization

**Tasks**:
- [ ] Optimize LangGraph execution
- [ ] Cache frequently accessed memory
- [ ] Optimize database queries
- [ ] Add connection pooling
- [ ] Load testing

## Long-term Steps (Priority 4)

### 11. Documentation

**Tasks**:
- [ ] Complete API documentation
- [ ] Add architecture diagrams
- [ ] Create user guides
- [ ] Document deployment procedures
- [ ] Add troubleshooting guides

### 12. Testing

**Tasks**:
- [ ] Unit tests for all agents
- [ ] Integration tests for workflows
- [ ] End-to-end tests
- [ ] Performance tests
- [ ] Security tests

### 13. Production Readiness

**Tasks**:
- [ ] Disaster recovery plan
- [ ] Backup and restore procedures
- [ ] Monitoring runbooks
- [ ] Incident response procedures
- [ ] Capacity planning

## Recommended Order

1. **Week 1**: Test VoiceLive locally + Update frontend
2. **Week 2**: Complete agent brain + Zep integration
3. **Week 3**: Complete Temporal workflows + Testing
4. **Week 4**: Frontend enhancements + Observability
5. **Week 5**: Security hardening + Performance optimization
6. **Week 6**: Documentation + Production readiness

## Quick Start Commands

### Local Development
```bash
# Start all services
docker-compose up -d

# Start backend
cd backend
pip install -r requirements.txt
uvicorn backend.api.main:app --reload

# Start frontend
cd frontend
npm install
npm run dev
```

### Testing VoiceLive
```bash
# Test VoiceLive connection
python -c "
import asyncio
from backend.voice.voicelive_service import voicelive_service

async def test():
    session = await voicelive_service.create_session('test-123', 'elena')
    print('Session created:', session.session_id)

asyncio.run(test())
"
```

### Deploy to Azure
```bash
# Push to main branch to trigger deployment
git push origin main

# Or deploy manually
az deployment group create \
  --resource-group engram-rg \
  --template-file infra/main.bicep \
  --parameters postgresPassword='...' \
               adminObjectId='...' \
               azureOpenAiKey='...'
```

## Questions to Resolve

1. **VoiceLive SDK Version**: Confirm `azure-ai-voicelive>=1.0.0` is correct
2. **Endpoint Format**: Verify VoiceLive endpoint format (base vs project path)
3. **Frontend Audio**: Determine if we need to handle PCM16 conversion in browser
4. **Agent Switching**: Test if agent switching works smoothly in production
5. **Cost Monitoring**: Set up Azure cost alerts for VoiceLive usage

## Getting Help

- **Backend Issues**: Check `backend/` directory and logs
- **Frontend Issues**: Check `frontend/` directory and browser console
- **Deployment Issues**: Check GitHub Actions logs
- **Azure Issues**: Check Azure Portal → Container Apps → Logs

## Success Criteria

✅ VoiceLive works for both Elena and Marcus  
✅ Frontend can connect and stream audio  
✅ Agents respond with correct personas  
✅ Memory persists across conversations  
✅ Workflows handle errors gracefully  
✅ Deployment succeeds in Azure  
✅ Monitoring shows healthy metrics  

