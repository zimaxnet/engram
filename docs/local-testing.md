# Local Testing Guide

This guide walks you through testing the complete Engram platform locally with all services connected.

## Prerequisites

1. **Docker & Docker Compose** - For running local services
2. **Azure OpenAI Account** - For agent functionality
3. **Azure Speech Services** (Optional) - For voice features
4. **Node.js 20+** - For frontend development
5. **Python 3.11+** - For backend development

## Step 1: Configure Environment

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your Azure credentials:
   ```env
   # Required for agent functionality
   AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
   AZURE_OPENAI_KEY=your-key-here
   AZURE_OPENAI_DEPLOYMENT=gpt-4o
   
   # Optional for voice features
   AZURE_SPEECH_KEY=your-key-here
   AZURE_SPEECH_REGION=eastus
   ```

## Step 2: Start Local Services

Start all backend services with Docker Compose:

```bash
docker-compose up -d postgres zep temporal temporal-ui unstructured
```

Wait for services to be healthy (check with `docker-compose ps`).

## Step 3: Start Backend API

In a separate terminal:

```bash
cd backend
pip install -r requirements.txt
uvicorn backend.api.main:app --host 0.0.0.0 --port 8082 --reload
```

The API will be available at: `http://localhost:8082`

## Step 4: Start Temporal Worker

In another terminal:

```bash
cd backend
python -m backend.workflows.worker
```

The worker will connect to Temporal and start processing workflows.

## Step 5: Start Frontend

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at: `http://localhost:5173`

## Step 6: Verify Services

### Check API Health
```bash
curl http://localhost:8082/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2024-...",
  "version": "0.1.0"
}
```

### Check Zep
```bash
curl http://localhost:8000/healthz
```

### Check Temporal UI
Open browser: `http://localhost:8080`

### Check Backend Logs
```bash
# API logs
docker-compose logs -f api

# Worker logs
docker-compose logs -f worker
```

## Step 7: Test Chat Functionality

1. Open `http://localhost:5173` in your browser
2. Select an agent (Elena or Marcus)
3. Type a message in the chat
4. Verify:
   - Message appears in chat
   - Agent responds (if Azure OpenAI is configured)
   - Metrics update in the right panel
   - No errors in browser console

## Step 8: Test Voice Features (Optional)

If Azure Speech is configured:

1. Click the microphone button in chat
2. Allow microphone access
3. Speak a message
4. Verify transcription and response

## Troubleshooting

### Backend API won't start

**Error**: `ModuleNotFoundError: No module named 'backend'`

**Solution**: Ensure you're in the `backend/` directory or set `PYTHONPATH`:
```bash
export PYTHONPATH="${PWD}/backend:${PYTHONPATH}"
```

### Frontend can't connect to API

**Error**: `Failed to fetch` or CORS errors

**Solution**: 
1. Verify API is running on port 8082
2. Check `VITE_API_URL` in frontend `.env` (should be `http://localhost:8082`)
3. Verify CORS is enabled in backend (check `backend/core/config.py`)

### Temporal connection errors

**Error**: `Connection refused` to Temporal

**Solution**:
1. Verify Temporal is running: `docker-compose ps temporal`
2. Check `TEMPORAL_HOST` environment variable
3. Ensure Temporal is healthy: `docker-compose logs temporal`

### Zep connection errors

**Error**: `Failed to connect to Zep`

**Solution**:
1. Verify Zep is running: `docker-compose ps zep`
2. Check Zep logs: `docker-compose logs zep`
3. Verify PostgreSQL connection: `docker-compose logs postgres`

### Azure OpenAI errors

**Error**: `401 Unauthorized` or `Invalid API key`

**Solution**:
1. Verify `AZURE_OPENAI_KEY` in `.env` is correct
2. Check `AZURE_OPENAI_ENDPOINT` format (should be `https://your-resource.openai.azure.com`)
3. Ensure deployment name matches: `AZURE_OPENAI_DEPLOYMENT=gpt-4o`
4. Verify the deployment exists in Azure Portal

## Testing Checklist

- [ ] All Docker services are running and healthy
- [ ] Backend API responds to `/health` endpoint
- [ ] Frontend loads without errors
- [ ] Chat messages send successfully
- [ ] Agent responses are received (if Azure OpenAI configured)
- [ ] Metrics update in Visual Panel
- [ ] Temporal UI is accessible
- [ ] Zep health check passes
- [ ] No errors in browser console
- [ ] No errors in backend logs

## Next Steps

Once local testing passes:

1. **Deploy to Azure** - Follow the deployment guide
2. **Configure GitHub Secrets** - See `docs/github-secrets.md`
3. **Run CI/CD Pipeline** - Push to main branch
4. **Monitor Production** - Check Application Insights

## Development Tips

### Hot Reload

- **Backend**: Uses `--reload` flag, changes auto-restart
- **Frontend**: Vite HMR, changes auto-refresh
- **Docker Services**: Restart with `docker-compose restart <service>`

### Debugging

- **Backend**: Add `import pdb; pdb.set_trace()` for breakpoints
- **Frontend**: Use browser DevTools
- **Temporal**: Check Temporal UI for workflow status
- **Zep**: Check Zep logs for memory operations

### Database Access

Connect to PostgreSQL:
```bash
docker-compose exec postgres psql -U postgres -d engram
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f worker
docker-compose logs -f zep
docker-compose logs -f temporal
```

