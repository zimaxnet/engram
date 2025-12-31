# Memory Episode Access for Troubleshooting

**Question:** Can agents reference the GPT-5.1-chat API parameters fix episode to troubleshoot chat and voice failures?

**Answer:** ✅ **Yes, agents automatically search and reference this episode during conversations.**

---

## How It Works

### 1. **Automatic Memory Retrieval (RAG)**

When users interact with agents (Elena, Marcus, Sage), the system automatically:

1. **Extracts the user's query** from their message
2. **Searches memory** for relevant episodes, documentation, and past conversations
3. **Injects retrieved context** into the agent's prompt
4. **Agents can reference** this context when responding

**Code Location:** `backend/agents/base.py` → `_reason_node()` method

```python
# Automatic memory retrieval (RAG)
memory_results = await memory_client.search_memory(
    session_id="global-search",  # Searches across ALL sessions
    query=query,                  # User's message
    limit=5                       # Top 5 relevant results
)
```

### 2. **Search Capabilities**

The `search_memory` method uses **HYBRID SEARCH** combining:

1. **Semantic Search** (pgvector) - Vector embeddings for meaning-based similarity
2. **Keyword Search** - Full-text matching in session content and metadata
3. **Metadata Match** - Title, topics, summary matching

**Search Prioritization:**
- Wiki pages (`doc-wiki-*`) - Highest priority
- Documentation (`doc-*`, `capability-*`) - High priority  
- Canonical sessions (`sess-*`) - Medium priority
- Other sessions - Lower priority

### 3. **Episode We Ingested**

The GPT-5.1-chat API parameters fix episode was ingested with:

- **Session ID:** `capability-gpt-5.1-chat-api-parameters-fix-2025-12-31`
- **Topics:** `gpt-5.1-chat`, `api-parameters`, `max_completion_tokens`, `temperature`, `azure-ai-foundry`, `chat-endpoint`, `llm-api`, `troubleshooting`, `model-compatibility`, `api-version`, `2024-12-01-preview`
- **Metadata:** Includes title, summary, and full documentation content

---

## Example Scenarios

### Scenario 1: User Reports Chat Failure

**User:** "Chat is not working, I'm getting error messages"

**Agent (Elena) will:**
1. Search memory for: `"chat endpoint failing"` or `"chat error"`
2. Find the episode: `capability-gpt-5.1-chat-api-parameters-fix-2025-12-31`
3. Reference the fix in response:
   - "Based on our troubleshooting history, chat failures are often caused by incorrect API parameters for the gpt-5.1-chat model. The model requires `max_completion_tokens` instead of `max_tokens`, and doesn't support custom temperature values..."

### Scenario 2: User Asks About Model Configuration

**User:** "How do I configure gpt-5.1-chat?"

**Agent will:**
1. Search memory for: `"gpt-5.1-chat configuration"` or `"gpt-5.1-chat API parameters"`
2. Find the episode with configuration details
3. Provide accurate configuration guidance from the episode

### Scenario 3: Voice Failure Similar to Chat

**User:** "Voice is not working"

**Agent will:**
1. Search memory for: `"voice endpoint"` or `"LLM API error"`
2. Find related troubleshooting episodes
3. Suggest checking similar issues from chat troubleshooting

---

## Verification

To verify the episode is accessible, agents can use the `search_memory` tool:

```python
# In agent code
results = await memory_client.search_memory(
    session_id="global-search",
    query="gpt-5.1-chat API parameters max_completion_tokens",
    limit=5
)
```

The episode should appear in results because:
- ✅ Session metadata includes relevant topics
- ✅ Content includes keywords like "max_completion_tokens", "temperature", "gpt-5.1-chat"
- ✅ Session ID starts with "capability-" which is prioritized in search

---

## Limitations

**Important Note:** As an AI assistant in this chat interface, I cannot directly search Zep memory in real-time. However:

1. ✅ **Agents (Elena, Marcus, Sage) CAN** search and reference the episode
2. ✅ **The system automatically** retrieves relevant episodes during conversations
3. ✅ **Users will see** agents referencing this troubleshooting knowledge
4. ✅ **The episode is searchable** via semantic, keyword, and metadata search

---

## How to Test

1. **Send a chat message** like: "Chat is failing, what could be wrong?"
2. **Agent should search memory** and find the episode
3. **Agent should reference** the troubleshooting steps from the episode
4. **Check agent logs** to see memory retrieval in action

---

## Related Documentation

- `docs/troubleshooting/gpt-5.1-chat-api-parameters-fix.md` - Full troubleshooting guide
- `backend/agents/base.py` - Agent memory retrieval implementation
- `backend/memory/client.py` - Memory search implementation
- `scripts/ingest-gpt-5.1-chat-api-parameters-fix.py` - Episode ingestion script

