# Quick Start: VoiceLive Testing

## The Problem
Python 3.14 is externally managed by Homebrew, so you can't install packages directly.

## Solution: Use a Virtual Environment

### Option 1: Automated Setup (Recommended)

```bash
# Create and setup virtual environment
./scripts/setup-venv.sh

# Activate it
source venv/bin/activate

# Run test
./test-voicelive.sh
```

### Option 2: Manual Setup

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
cd backend
pip install -r requirements.txt
cd ..

# Run test
./test-voicelive.sh
```

### Option 3: User Install (No venv)

```bash
# Install to user directory
cd backend
pip install --user -r requirements.txt
cd ..

# Run test
./test-voicelive.sh
```

## After Setup

Once dependencies are installed:

1. **Set environment variables:**
   ```bash
   export AZURE_AI_ENDPOINT="https://zimax.services.ai.azure.com"
   export AZURE_AI_PROJECT_NAME="zimax"
   export AZURE_OPENAI_KEY="cf23c3ed0f9d420dbd02c1e95a5b5bb3"
   ```

2. **Start backend:**
   ```bash
   source venv/bin/activate  # If using venv
   cd backend
   uvicorn backend.api.main:app --host 0.0.0.0 --port 8082 --reload
   ```

3. **Test WebSocket (browser console):**
   ```javascript
   const ws = new WebSocket('ws://localhost:8082/api/v1/voice/voicelive/test-123');
   ws.onopen = () => {
     console.log('✓ Connected');
     ws.send(JSON.stringify({type: 'agent', agent_id: 'elena'}));
   };
   ws.onmessage = (e) => console.log('Received:', JSON.parse(e.data));
   ```

## Troubleshooting

- **"No module named 'pydantic'"**: Install dependencies (see options above)
- **"externally-managed-environment"**: Use a virtual environment
- **"Connection refused"**: Make sure backend is running
- **"401 Unauthorized"**: Check your `AZURE_OPENAI_KEY` is correct

