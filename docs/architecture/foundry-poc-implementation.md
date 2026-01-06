---
layout: default
title: Foundry Agent Service POC - Implementation Summary
parent: Architecture
nav_order: 4
---

# Foundry Agent Service POC - Implementation Summary

> **Status**: ✅ POC Complete - Ready for Testing  
> **Last Updated**: January 2026  
> **Impact**: Zero production impact (all features disabled by default)

---

## What Was Implemented

### 1. Configuration (`backend/core/config.py`)

Added Foundry Agent Service configuration with feature flags:

```python
# Azure AI Foundry Agent Service (Optional - POC)
azure_foundry_agent_endpoint: Optional[str] = Field(None, alias="AZURE_FOUNDRY_AGENT_ENDPOINT")
azure_foundry_agent_project: Optional[str] = Field(None, alias="AZURE_FOUNDRY_AGENT_PROJECT")
azure_foundry_agent_key: Optional[str] = Field(None, alias="AZURE_FOUNDRY_AGENT_KEY")
azure_foundry_agent_api_version: str = Field("2024-10-01-preview", alias="AZURE_FOUNDRY_AGENT_API_VERSION")

# Feature flags - all disabled by default
use_foundry_threads: bool = Field(False, alias="USE_FOUNDRY_THREADS")
use_foundry_files: bool = Field(False, alias="USE_FOUNDRY_FILES")
use_foundry_vectors: bool = Field(False, alias="USE_FOUNDRY_VECTORS")
use_foundry_tools: bool = Field(False, alias="USE_FOUNDRY_TOOLS")
```

**Key Points**:
- ✅ All flags default to `False` (zero production impact)
- ✅ Configuration is optional (won't break if not set)
- ✅ Supports both API key and Managed Identity authentication

---

### 2. Foundry Client (`backend/agents/foundry_client.py`)

Created `FoundryAgentServiceClient` class with REST API implementation:

**Features**:
- ✅ Thread management (create, get, list, delete)
- ✅ Message management (add, list)
- ✅ File upload support
- ✅ Project-based isolation support
- ✅ Automatic authentication (API key or Managed Identity)
- ✅ Comprehensive error handling and logging

**Key Methods**:
```python
# Thread management
await client.create_thread(user_id, agent_id, project_id, metadata)
await client.get_thread(thread_id)
await client.list_threads(user_id, agent_id, project_id, limit)
await client.delete_thread(thread_id)

# Message management
await client.add_message(thread_id, role, content, metadata)
await client.list_messages(thread_id, limit)

# File management
await client.upload_file(thread_id, file_path, purpose)
```

**Singleton Pattern**:
- `get_foundry_client()` returns `None` if flags are disabled
- Ensures zero impact when Foundry is not in use
- Lazy initialization (only created when needed)

---

### 3. Test Script (`scripts/test_foundry_client.py`)

Created comprehensive test script for POC validation:

**Features**:
- ✅ Tests thread creation and retrieval
- ✅ Tests message management
- ✅ Tests thread listing with filters
- ✅ Tests feature flag behavior
- ✅ Optional cleanup (controlled by env var)

**Usage**:
```bash
# Set environment variables
export AZURE_FOUNDRY_AGENT_ENDPOINT="https://<account>.services.ai.azure.com"
export AZURE_FOUNDRY_AGENT_PROJECT="<project-name>"
export AZURE_FOUNDRY_AGENT_KEY="<optional-api-key>"  # Or use Managed Identity
export USE_FOUNDRY_THREADS=true  # Enable for testing

# Run test
python scripts/test_foundry_client.py

# Optional: Enable cleanup
export FOUNDRY_TEST_CLEANUP=true
python scripts/test_foundry_client.py
```

---

## Zero Impact Guarantees

### ✅ No Breaking Changes

1. **Feature Flags Disabled by Default**:
   - All `use_foundry_*` flags default to `False`
   - Existing code continues to work unchanged

2. **Optional Configuration**:
   - Foundry config is optional
   - System works without Foundry configured

3. **Graceful Degradation**:
   - `get_foundry_client()` returns `None` when disabled
   - No exceptions thrown when Foundry is not configured

4. **No Production Impact**:
   - Client is never initialized unless flags are enabled
   - No API calls made unless explicitly enabled

---

## Testing the POC

### Prerequisites

1. **Azure AI Foundry Account**:
   - Create Foundry account and project
   - Note the endpoint and project name

2. **Authentication**:
   - Option A: API key (set `AZURE_FOUNDRY_AGENT_KEY`)
   - Option B: Managed Identity (no key needed, uses DefaultAzureCredential)

3. **Environment Variables**:
   ```bash
   export AZURE_FOUNDRY_AGENT_ENDPOINT="https://<account>.services.ai.azure.com"
   export AZURE_FOUNDRY_AGENT_PROJECT="<project-name>"
   export USE_FOUNDRY_THREADS=true  # Enable for testing
   ```

### Run Tests

```bash
# Test feature flags
python scripts/test_foundry_client.py

# Test with cleanup
FOUNDRY_TEST_CLEANUP=true python scripts/test_foundry_client.py
```

### Expected Output

```
Foundry Agent Service Client POC Test
============================================================

Testing Feature Flags
============================================================
USE_FOUNDRY_THREADS: True
USE_FOUNDRY_FILES: False
USE_FOUNDRY_VECTORS: False
USE_FOUNDRY_TOOLS: False
✅ Client correctly initialized when flags are enabled
============================================================

Testing Foundry Agent Service Thread Management
============================================================

[Test 1] Creating thread...
✅ Created thread: thread_abc123...

[Test 2] Getting thread details...
✅ Retrieved thread: thread_abc123...
   Metadata: {'user_id': 'test-user-123', 'agent_id': 'elena', ...}

[Test 3] Adding messages...
✅ Added user message: msg_xyz789...
✅ Added assistant message: msg_def456...

[Test 4] Listing messages...
✅ Retrieved 2 messages
   1. [user] Hello, this is a test message...
   2. [assistant] Hello! I'm Elena...

[Test 5] Listing threads...
✅ Found 1 threads
   1. Thread thread_abc123... (agent: elena)

[Test 6] Cleaning up...
✅ Deleted thread: thread_abc123...

============================================================
✅ All tests passed!
============================================================
```

---

## Next Steps (Optional Integration)

### Phase 2: Thread Management Integration

**Goal**: Replace in-memory sessions with Foundry threads (optional)

**Changes Required**:
1. Update `backend/api/routers/chat.py`:
   ```python
   async def get_or_create_session(...):
       if settings.use_foundry_threads:
           foundry_client = get_foundry_client()
           if foundry_client:
               # Use Foundry thread
               thread_id = await foundry_client.create_thread(...)
               # Load messages into EnterpriseContext
               messages = await foundry_client.list_messages(thread_id)
               context = EnterpriseContext.from_foundry_messages(thread_id, messages)
               return context
       
       # Fallback to existing in-memory sessions
       return get_or_create_session_legacy(...)
   ```

2. **Feature Flag**: `USE_FOUNDRY_THREADS=true` (disabled by default)

3. **Rollback**: Set flag to `false` to instantly revert

**Benefits**:
- ✅ Persistent conversation history
- ✅ Automatic thread management
- ✅ Project-based thread isolation
- ✅ Zero downtime migration

---

## API Reference

### FoundryAgentServiceClient

#### `create_thread(user_id, agent_id, project_id=None, metadata=None) -> str`

Create a new conversation thread.

**Parameters**:
- `user_id` (str): User identifier
- `agent_id` (str): Agent identifier (elena, marcus, sage)
- `project_id` (str, optional): Project identifier for isolation
- `metadata` (dict, optional): Additional metadata

**Returns**: Thread ID (str)

**Example**:
```python
thread_id = await client.create_thread(
    user_id="user-123",
    agent_id="elena",
    project_id="project-alpha",
    metadata={"source": "web", "session_type": "chat"}
)
```

#### `get_thread(thread_id) -> dict`

Get thread details.

**Parameters**:
- `thread_id` (str): Thread identifier

**Returns**: Thread details (dict)

#### `list_threads(user_id=None, agent_id=None, project_id=None, limit=20) -> list[dict]`

List threads with optional filters.

**Parameters**:
- `user_id` (str, optional): Filter by user
- `agent_id` (str, optional): Filter by agent
- `project_id` (str, optional): Filter by project
- `limit` (int): Maximum results (default: 20)

**Returns**: List of thread dictionaries

#### `add_message(thread_id, role, content, metadata=None) -> dict`

Add a message to a thread.

**Parameters**:
- `thread_id` (str): Thread identifier
- `role` (str): Message role (user, assistant, system)
- `content` (str): Message content
- `metadata` (dict, optional): Message metadata

**Returns**: Message details (dict)

#### `list_messages(thread_id, limit=20) -> list[dict]`

List messages in a thread.

**Parameters**:
- `thread_id` (str): Thread identifier
- `limit` (int): Maximum results (default: 20)

**Returns**: List of message dictionaries

#### `upload_file(thread_id, file_path, purpose="assistant") -> dict`

Upload a file to a thread.

**Parameters**:
- `thread_id` (str): Thread identifier
- `file_path` (str): Path to file
- `purpose` (str): File purpose (default: "assistant")

**Returns**: File details (dict)

#### `delete_thread(thread_id) -> None`

Delete a thread.

**Parameters**:
- `thread_id` (str): Thread identifier

---

## Error Handling

The client includes comprehensive error handling:

- **HTTP Errors**: Logged with status code and response text
- **Network Errors**: Caught and re-raised with context
- **Configuration Errors**: Clear error messages for missing config
- **Graceful Degradation**: Returns `None` when flags are disabled

**Example Error Handling**:
```python
try:
    thread_id = await client.create_thread(...)
except httpx.HTTPStatusError as e:
    logger.error(f"Foundry API error: {e.response.status_code}")
    # Fallback to existing behavior
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    # Fallback to existing behavior
```

---

## Security Considerations

1. **Authentication**:
   - Supports Managed Identity (recommended for production)
   - Falls back to API key for development/testing
   - Credentials never logged

2. **Project Isolation**:
   - Threads include `project_id` in metadata
   - Client-side filtering ensures proper isolation
   - Aligns with existing `SecurityContext.project_id` implementation

3. **Feature Flags**:
   - All features disabled by default
   - Requires explicit opt-in via environment variables
   - No accidental production usage

---

## Troubleshooting

### Client Returns None

**Cause**: Feature flags are disabled or Foundry is not configured.

**Solution**:
```bash
# Enable feature flag
export USE_FOUNDRY_THREADS=true

# Set configuration
export AZURE_FOUNDRY_AGENT_ENDPOINT="https://..."
export AZURE_FOUNDRY_AGENT_PROJECT="..."
```

### Authentication Errors

**Cause**: Invalid credentials or missing permissions.

**Solution**:
- Verify API key is correct (if using API key)
- Verify Managed Identity has proper permissions (if using MI)
- Check Azure portal for account/project access

### API Version Errors

**Cause**: Unsupported API version.

**Solution**:
- Check Foundry documentation for latest API version
- Update `AZURE_FOUNDRY_AGENT_API_VERSION` if needed
- Default: `2024-10-01-preview`

---

## Summary

✅ **POC Complete**: Foundry Agent Service client implemented  
✅ **Zero Impact**: All features disabled by default  
✅ **Production Safe**: No breaking changes, graceful degradation  
✅ **Tested**: Comprehensive test script included  
✅ **Documented**: Full API reference and usage examples  

**Ready for**: Testing in development environment  
**Not Ready for**: Production use (requires thorough testing first)

---

*Last Updated: January 2026*

