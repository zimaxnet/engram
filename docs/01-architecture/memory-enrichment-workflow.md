---
layout: default
title: "Memory Enrichment Workflow: Sessions, Episodes, Stories, and Chat"
parent: "Architecture"
---

# Memory Enrichment Workflow: Sessions, Episodes, Stories, and Chat

**Date:** December 31, 2025  
**Overview:** How sessions, episodes, stories, and chat interactions automatically enrich Zep memory through agent interactions.

---

## Overview

Engram's memory system automatically enriches Zep memory through multiple interaction patterns:

1. **Chat Conversations** → Sessions → Episodes → Memory
2. **Voice Interactions** → Sessions → Episodes → Memory  
3. **Story Creation** → Sessions → Memory
4. **Manual Episode Ingestion** → Memory (via agents/MCP tools)

All interactions go through **agents** (Elena, Marcus, Sage) who automatically:
- Search existing memory for relevant context
- Persist new conversations to memory
- Enrich memory with facts and entities

---

## 1. Chat Conversations

### Flow

```
User Message → Agent (Elena/Marcus) → Response → Persist to Memory
```

### Implementation

**Endpoint:** `POST /api/v1/chat`

**Steps:**
1. User sends message via frontend
2. Backend creates/gets session: `get_or_create_session(session_id, user)`
3. **Enrich context with memory** (RAG):
   ```python
   context = await enrich_context(context, message.content)
   # Searches existing memory for relevant episodes
   ```
4. Agent processes message (with memory context injected)
5. **Persist conversation to memory** (background):
   ```python
   await persist_conversation(updated_context)
   # Saves user + assistant turn to Zep session
   ```

**Code Location:** `backend/api/routers/chat.py` → `send_message()`

### What Gets Saved

- **Session:** Created with `session_id` (UUID or frontend-provided)
- **Messages:** User message + Agent response
- **Metadata:** `user_id`, `tenant_id`, `agent_id`, `turn_count`, `email`, `display_name`
- **Episodes:** Zep automatically segments long sessions into episodes

### Example

```python
# User sends: "What's the status of Project X?"
# 1. Session created/retrieved
session_id = "session-2025-12-31-abc123"

# 2. Memory enriched (searches for relevant past conversations)
context = await enrich_context(context, "What's the status of Project X?")
# Finds: past episodes about Project X

# 3. Agent responds (with memory context)
response = await agent_chat(query, context, agent_id="elena")

# 4. Persisted to memory
await persist_conversation(updated_context)
# Creates/updates Zep session with this turn
```

---

## 2. Voice Interactions

### Flow

```
Voice Input → Transcription → Agent → Response → Persist to Memory
```

### Implementation

**Endpoints:**
- WebSocket: `/api/v1/voice/voicelive/{session_id}`
- REST: `POST /api/v1/voice/conversation/turn`

**Steps:**
1. User speaks via VoiceLive WebSocket
2. Backend receives transcription
3. Agent processes (same as chat)
4. **Persist turn to memory**:
   ```python
   await persist_conversation(voice_context)
   ```

**Code Locations:**
- `backend/api/routers/voice.py` → `voicelive_websocket()`
- `backend/api/routers/voice.py` → `persist_conversation_turn()`

### What Gets Saved

Same as chat:
- **Session:** Voice session ID
- **Messages:** User transcription + Agent response
- **Metadata:** `channel: "voice"`, `agent_id`, user identity

---

## 3. Story Creation

### Flow

```
Story Request → Sage Agent → Story + Diagram → Save Files → Enrich Memory
```

### Implementation

**Endpoint:** `POST /api/v1/story/create`

**Steps:**
1. User requests story creation (via frontend or API)
2. **Temporal workflow executes** (or direct if unavailable):
   - Sage generates story with Claude
   - Sage generates diagram with Gemini
   - Artifacts saved to `docs/stories/` and `docs/diagrams/`
3. **Memory automatically enriched**:
   ```python
   session_id = f"story-{story_id}"
   await memory_client.get_or_create_session(
       session_id=session_id,
       user_id=user.user_id,
       metadata={
           "title": topic,
           "type": "story",
           "story_id": story_id,
       }
   )
   await memory_client.add_memory(
       session_id=session_id,
       messages=[{"role": "assistant", "content": story_content}]
   )
   ```

**Code Location:** `backend/api/routers/story.py` → `create_story()`

### What Gets Saved

- **Session:** `story-{story_id}`
- **Message:** Full story content (truncated to 5000 chars)
- **Metadata:** `title`, `type: "story"`, `story_id`, `image_path`, `created_at`

### Story Memory Benefits

Stories are searchable in memory:
- Agents can find stories when users ask about topics
- Stories provide context for future conversations
- Enables continuity across sessions

---

## 4. Manual Episode Ingestion

### Flow

```
Agent Tool → Ingest Episode → Create Session → Add Messages → Memory Enriched
```

### Implementation

**MCP Tool:** `ingest_episode`

**Usage:**
Agents can manually ingest episodes via MCP tools:

```python
await ingest_episode(
    session_id="episode-2025-12-31-project-x-review",
    summary="Project X architecture review meeting",
    messages='[{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]',
    topics="project-x,architecture,review",
    agent_id="marcus"
)
```

**Code Location:** `backend/api/routers/mcp_server.py` → `ingest_episode()`

### Use Cases

- Ingesting external conversations
- Documenting important meetings
- Creating canonical knowledge sessions
- Historical data import

---

## Memory Enrichment Details

### Automatic Memory Retrieval (RAG)

**Every agent interaction automatically:**

1. **Searches existing memory** before responding:
   ```python
   results = await memory_client.search_memory(
       session_id="global-search",
       query=user_message,
       limit=5
   )
   ```

2. **Injects context into agent prompt:**
   ```python
   memory_context = "\n\n## Retrieved Knowledge\n" + "\n".join(memory_items)
   # Added to system prompt
   ```

3. **Agent uses this context** to provide informed responses

**Code Location:** `backend/agents/base.py` → `_reason_node()`

### Automatic Memory Persistence

**Every agent interaction automatically:**

1. **Persists conversation turn** after response:
   ```python
   await persist_conversation(context)
   ```

2. **Updates session metadata:**
   - `turn_count`
   - `agent_id`
   - `tenant_id`
   - `email`, `display_name` (for user attribution)

3. **Zep automatically:**
   - Creates episodes from long sessions
   - Extracts entities (people, organizations, locations)
   - Extracts facts (statements about user/world)
   - Indexes for semantic search

**Code Location:** `backend/memory/client.py` → `persist_conversation()`

---

## Session vs Episode

### Sessions

- **What:** Top-level container for a conversation thread
- **Created:** When user starts new chat/voice interaction
- **ID:** UUID or frontend-provided (e.g., `session-2025-12-31-abc123`)
- **Contains:** All messages in a conversation thread
- **Managed:** Explicitly by application

### Episodes

- **What:** Semantic sub-segments of a session
- **Created:** Automatically by Zep based on context shifts
- **Purpose:** Improves retrieval accuracy by clustering related turns
- **Managed:** Automatically by Zep (not directly controlled)

**Example:**
```
Session: "session-2025-12-31-abc123"
├── Episode 1: "Discussing Project X architecture" (turns 1-5)
├── Episode 2: "Switching to Project Y requirements" (turns 6-10)
└── Episode 3: "Debugging CI/CD pipeline" (turns 11-15)
```

---

## Complete Workflow Example

### Scenario: User Creates Story, Then Chats About It

1. **User creates story:**
   ```
   POST /api/v1/story/create
   { "topic": "Project X Architecture" }
   ```
   - Story generated by Sage
   - Saved to `docs/stories/`
   - **Memory enriched:** `story-{story_id}` session created

2. **User chats about the story:**
   ```
   POST /api/v1/chat
   { "content": "Tell me about Project X Architecture" }
   ```
   - Agent searches memory: Finds `story-{story_id}` session
   - Agent responds with story content
   - **Memory enriched:** Chat session created with this conversation

3. **User continues conversation:**
   ```
   POST /api/v1/chat
   { "content": "How does it relate to Project Y?" }
   ```
   - Agent searches memory: Finds both story session and previous chat
   - Agent responds with context from both
   - **Memory enriched:** Chat session updated with new turn

4. **Zep automatically:**
   - Segments chat session into episodes
   - Extracts entities: "Project X", "Project Y"
   - Extracts facts: "User asked about Project X Architecture"
   - Indexes everything for future searches

---

## Agent Tools for Memory Enrichment

Agents have access to tools for memory enrichment:

### 1. `search_memory` (All Agents)

```python
@tool("search_memory")
async def search_memory_tool(query: str, limit: int = 5) -> str:
    """Search long-term memory for facts, documents, or past episodes."""
    results = await memory_client.search_memory(
        session_id="global-search",
        query=query,
        limit=limit
    )
    return formatted_results
```

### 2. `enrich_memory` (Sage)

```python
@tool("enrich_memory")
async def enrich_memory_tool(title: str, content: str, topics: Optional[list[str]] = None) -> str:
    """Save content to Zep memory for future reference."""
    # Creates session and adds content
```

### 3. `ingest_episode` (MCP Tool)

```python
@mcp_server.tool()
async def ingest_episode(
    session_id: str,
    summary: str,
    messages: str,
    topics: Optional[str] = None,
    agent_id: str = "elena",
) -> str:
    """Ingest a conversation episode into Zep memory."""
    # Creates session with metadata and adds messages
```

---

## Best Practices

### 1. Consistent User Identity

**Always use authenticated user context:**
```python
security = SecurityContext(
    user_id=user.user_id,  # From JWT token
    tenant_id=user.tenant_id,
    email=user.email,
    display_name=user.display_name,
)
```

### 2. Rich Metadata

**Include descriptive metadata:**
```python
metadata={
    "title": "Project X Review",
    "topics": ["project-x", "architecture", "review"],
    "type": "episode",
    "summary": "Architecture review meeting",
}
```

### 3. Session Naming

**Use descriptive session IDs:**
- Stories: `story-{story_id}`
- Episodes: `episode-{date}-{topic}`
- Capabilities: `capability-{name}-{date}`
- Chats: UUID or frontend-provided

### 4. Background Persistence

**Don't block responses:**
```python
# Fire-and-forget background task
asyncio.create_task(persist_conversation(context))
```

---

## Related Documentation

- `docs/concept/sessions-vs-episodes.md` - Sessions vs episodes distinction
- `docs/concept/memory-architecture.md` - Memory architecture overview
- `docs/architecture/user-identity-flow-comprehensive.md` - User identity flow
- `backend/api/routers/chat.py` - Chat endpoint implementation
- `backend/api/routers/story.py` - Story creation implementation
- `backend/memory/client.py` - Memory client implementation

