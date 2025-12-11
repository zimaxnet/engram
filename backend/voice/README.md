# Voice Agent Clients

This directory contains standalone Python clients for testing the Azure OpenAI Realtime API (GPT-4o Realtime Preview) with our agents.

## Prerequisites

1. **Python 3.10+**
2. **Dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

    *Note: `pyaudio` may require system libraries. On macOS: `brew install portaudio`*

3. **Environment Variables**:
    Create a `.env` file in the root of the project (or ensure `backend/voice/clients` can see it) with:

    ```
    AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com/
    AZURE_OPENAI_KEY=<your-key>
    AZURE_OPENAI_DEPLOYMENT=gpt-4o-realtime-preview
    ```

## Usage

Run the clients as modules from the `backend/voice/clients` directory (to resolve relative imports correctly, you might need to run from project root):

**Marcus (Project Manager):**

```bash
python -m backend.voice.clients.marcus
```

**Elena (Business Analyst):**

```bash
python -m backend.voice.clients.elena
```

## Configuration

- **Prompts**: Agent system instructions are stored in json files in `backend/voice/prompts/`. You can edit `marcus.json` or `elena.json` to change their behavior.
- **Code**: key logic is in `common.py` which implements the OpenAI Realtime WebSocket protocol.
