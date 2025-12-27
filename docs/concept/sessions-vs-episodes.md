# Sessions vs Episodes: Clarifying the Distinction

## Executive Summary

In Engram's memory architecture, there's an important distinction between **Sessions** and **Episodes**, and how they relate to **Workflows**. This document clarifies these concepts and their usage.

---

## 1. Sessions (Zep's Primary Concept)

### Definition
A **Session** is the top-level container for a conversation thread in Zep. It's identified by a unique `session_id` (typically a UUID).

### Characteristics
- **Creation**: Created when a user starts a new conversation (e.g., clicks "New Chat")
- **Scope**: Contains all messages in a single conversation thread
- **Isolation**: Agents see only the immediate history of the *current* session strictly
- **Search**: Zep indexes the entire session for semantic search, allowing agents to "recall" information from *other* past sessions if relevant
- **Persistence**: Sessions persist across application restarts

### Example
```python
# When user starts a new chat
session_id = "session-2024-12-20-abc123"
# All messages in this conversation belong to this session
```

### In Code
```python
# backend/memory/client.py
await memory_client.get_or_create_session(
    session_id=session_id,
    user_id=user_id,
    metadata={"agent_id": "elena", "summary": "..."}
)
```

---

## 2. Episodes (Zep's Automatic Segmentation)

### Definition
An **Episode** is a semantic sub-segment of a Session, **automatically managed by Zep**.

### Characteristics
- **Automatic**: Zep automatically breaks long sessions into episodes based on context shifts
- **Purpose**: Improves retrieval accuracy by clustering related turns together
- **Example**: A session might have episodes like:
  - Episode 1: "Discussing Project X architecture"
  - Episode 2: "Switching to Project Y requirements"
  - Episode 3: "Debugging CI/CD pipeline"
- **Not Directly Managed**: Agents don't create or manage episodes directly

### Zep's Internal Use
Zep uses episodes internally to:
- Improve semantic search accuracy
- Group related conversation turns
- Generate better summaries
- Optimize memory retrieval

---

## 3. Episodes in Engram's UI/API (Terminology Overlap)

### Important Note: Terminology Confusion

In Engram's current implementation, there's a terminology overlap:

- **Zep's "Episodes"**: Automatic sub-segments within a session (managed by Zep)
- **Engram's "Episodes"**: Historical conversation sessions displayed in the UI

### Engram's `/episodes` Endpoint

The `/api/v1/memory/episodes` endpoint actually lists **Sessions**, not Zep's internal episodes:

```python
# backend/api/routers/memory.py
@router.get("/episodes", response_model=EpisodeListResponse)
async def list_episodes(...):
    """
    List conversation episodes from memory.
    
    Episodes are discrete conversation sessions that have been
    processed and stored in the knowledge graph.
    """
    sessions = await client_list_episodes(...)  # Actually calls list_sessions
```

### Why This Naming?

In Engram's UI, "Episodes" refers to **historical conversation sessions** that:
- Have been completed
- Have summaries and metadata
- Can be viewed and continued
- Are displayed in the Episodes page

This is a **UI/UX term** rather than a strict Zep concept.

---

## 4. Workflows (Temporal Durable Execution)

### Definition
A **Workflow** is a durable execution process managed by Temporal, not directly a session or episode.

### Characteristics
- **Durable**: Survives crashes and restarts
- **Observable**: Can be queried for status and progress
- **Independent**: Not necessarily tied to a conversation session
- **Types**: 
  - Agent workflows (conversation turns)
  - Story workflows (Elena → Sage delegations)
  - Approval workflows
  - Conversation workflows

### Relationship to Sessions

Workflows can be **associated** with sessions but are not sessions themselves:

1. **Agent Workflows**: Execute a single agent turn within a session
   - Workflow ID: `agent-{session_id}-{uuid}`
   - Associated with a session via the session_id

2. **Story Workflows**: Independent execution for story/visual creation
   - Workflow ID: `story-{uuid}`
   - **Not directly tied to a session** (though they can be)
   - Executed when Elena delegates to Sage

3. **Conversation Workflows**: Long-running conversation orchestration
   - Workflow ID: `conversation-{session_id}`
   - Manages the entire conversation flow

### Example: Story Workflow

```python
# Elena delegates to Sage
workflow_id = "story-abc123def456"  # Independent workflow
# This workflow:
# 1. Generates story with Claude
# 2. Generates diagram with Gemini
# 3. Saves artifacts
# 4. Enriches Zep memory
# 
# It's NOT a session, but it can create/update a session
# if the story is stored as part of a conversation
```

---

## 5. Practical Usage Guide

### When to Use Sessions

✅ **Use Sessions for:**
- New conversation threads
- Continuing existing conversations
- Grouping related messages
- User-initiated chat interactions

```python
# Start new conversation
session_id = f"session-{uuid.uuid4()}"
await memory_client.get_or_create_session(session_id, user_id)
```

### When to Use Episodes (Engram's UI Term)

✅ **Use "Episodes" (UI term) for:**
- Displaying historical conversations
- Showing completed conversation sessions
- Allowing users to continue past conversations
- Viewing conversation summaries

```python
# List historical episodes (actually sessions)
episodes = await list_episodes(user_id=user_id)
# Returns sessions with summaries and metadata
```

### When to Use Workflows

✅ **Use Workflows for:**
- Durable execution of long-running tasks
- Agent delegations (Elena → Sage)
- Tasks that need to survive crashes
- Processes that need observability

```python
# Start story workflow
workflow_id = await execute_story(
    user_id=user_id,
    topic="VoiceLive architecture",
    context="..."
)
# This is independent of any session
```

---

## 6. Common Scenarios

### Scenario 1: User Starts a Chat

```
1. User clicks "New Chat"
2. Frontend generates: session_id = "session-2024-12-20-abc123"
3. Session created in Zep
4. Messages added to this session
5. Zep may automatically create episodes within this session
```

### Scenario 2: Elena Delegates to Sage

```
1. User asks Elena: "Create a story about VoiceLive"
2. Elena calls delegate_to_sage()
3. Story workflow starts: workflow_id = "story-xyz789"
4. Workflow executes independently (not tied to session)
5. Workflow completes and may:
   - Create a new session for the story
   - Update existing session with story reference
   - Store story as artifact (not in session)
```

### Scenario 3: Viewing Historical Conversations

```
1. User navigates to Episodes page
2. API calls /api/v1/memory/episodes
3. Returns list of sessions (labeled as "episodes" in UI)
4. Each episode is actually a session with:
   - Summary
   - Topics
   - Agent ID
   - Turn count
   - Date range
```

### Scenario 4: Continuing a Past Conversation

```
1. User clicks "Discuss with Agent" on an episode
2. Frontend uses episode's session_id
3. Session is retrieved from Zep
4. Conversation continues in same session
5. New messages added to existing session
```

---

## 7. Key Takeaways

| Concept | What It Is | Managed By | Use Case |
|---------|-----------|------------|----------|
| **Session** | Conversation thread container | Engram (via Zep) | Grouping messages in a conversation |
| **Episode (Zep)** | Automatic sub-segment of session | Zep automatically | Improving search/retrieval accuracy |
| **Episode (Engram UI)** | Historical conversation session | Engram | Displaying past conversations |
| **Workflow** | Durable execution process | Temporal | Long-running tasks, delegations |

### Important Distinctions

1. **Sessions ≠ Episodes (Zep)**: Episodes are sub-segments within sessions
2. **Episodes (UI) = Sessions**: In Engram's UI, "episodes" are actually sessions
3. **Workflows ≠ Sessions**: Workflows are execution processes, not conversation containers
4. **Workflows can create/update Sessions**: But they're independent entities

---

## 8. Recommendations

### For the Episodes Feature

✅ **Current Implementation is Correct:**
- Episodes page shows historical sessions
- Users can continue conversations using session IDs
- This aligns with user expectations

### For Workflow Visibility

✅ **Workflows Should:**
- Be displayed separately from sessions/episodes
- Show delegation chains (Elena → Sage)
- Be observable independently
- Optionally link to related sessions if applicable

### For Future Enhancements

💡 **Consider:**
- Adding a "Workflows" section separate from Episodes
- Showing workflow-to-session relationships when applicable
- Clarifying terminology in UI (e.g., "Conversation History" instead of "Episodes")
- Documenting Zep's internal episode concept separately

---

## 9. Code References

### Session Management
- `backend/memory/client.py`: `get_or_create_session()`, `add_memory()`
- `backend/api/routers/memory.py`: Session endpoints

### Episodes (UI Term)
- `backend/api/routers/memory.py`: `/episodes` endpoint (actually lists sessions)
- `frontend/src/pages/Memory/Episodes.tsx`: Episodes UI

### Workflows
- `backend/workflows/client.py`: Workflow execution
- `backend/api/routers/workflows.py`: Workflow endpoints
- `frontend/src/pages/Workflows/ActiveWorkflows.tsx`: Workflow UI

---

## Summary

- **Sessions**: Conversation threads in Zep (what we primarily work with)
- **Episodes (Zep)**: Automatic sub-segments within sessions (managed by Zep)
- **Episodes (Engram UI)**: Historical conversation sessions (terminology overlap)
- **Workflows**: Durable execution processes (independent of sessions, but can be associated)

The workflow visibility work we just completed is **separate** from sessions/episodes - workflows are execution processes that can optionally create or update sessions, but they're not sessions themselves.

