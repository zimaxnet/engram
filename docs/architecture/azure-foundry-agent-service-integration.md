---
layout: default
title: Azure AI Foundry Agent Service Integration
parent: Architecture
nav_order: 2
---

# Azure AI Foundry Agent Service Integration

> **Status**: Analysis & Planning  
> **Last Updated**: January 2026  
> **Reference**: [Azure AI Foundry Agent Service Documentation](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/environment-setup?view=foundry)

---

## Executive Summary

Azure AI Foundry Agent Service provides **tremendous functionality** that can significantly enhance Engram's agent capabilities. This document analyzes the integration opportunity and provides an implementation roadmap.

### Key Opportunities

1. **Built-in Thread Management**: Replace custom `EnterpriseContext` with Foundry's thread storage
2. **File Storage**: Leverage Foundry's file storage for agent-uploaded documents
3. **Vector Stores**: Use Foundry's managed vector stores instead of Zep for some use cases
4. **Tool Infrastructure**: Built-in tool calling framework
5. **Project-Based Isolation**: Aligns perfectly with our recent isolation implementation
6. **Cost Optimization**: Managed infrastructure reduces operational overhead

---

## Current State Analysis

### What We Have

✅ **Custom Agent Architecture**:
- `BaseAgent` class with LangGraph state machines
- `FoundryChatClient` for OpenAI-compatible API calls
- `EnterpriseContext` for conversation state management
- Zep for long-term memory storage
- Project-based isolation (just implemented)

✅ **Azure AI Foundry Integration**:
- Already using Foundry's chat completions API
- Project name support (`AZURE_AI_PROJECT_NAME`)
- Model Router support (`AZURE_AI_MODEL_ROUTER`)
- Managed Identity authentication

### What Foundry Agent Service Offers

🎯 **Thread Management**:
- Built-in conversation thread storage (Cosmos DB or managed)
- Automatic message history management
- Thread-level metadata and filtering

🎯 **File Storage**:
- Upload and manage files per agent/thread
- Automatic file indexing for RAG
- File-based tool calling

🎯 **Vector Stores**:
- Managed vector stores (Azure AI Search)
- Automatic embedding generation
- Vector search integration

🎯 **Tool Calling**:
- Built-in tool execution framework
- Function calling with automatic validation
- Tool result management

🎯 **Project Isolation**:
- Native project-based data isolation
- Project-scoped resources (files, threads, vectors)
- Perfect alignment with our `project_id` implementation

---

## Integration Architecture

### Option 1: Hybrid Approach (Recommended)

**Strategy**: Use Foundry Agent Service for infrastructure, keep LangGraph for agent logic

```
┌─────────────────────────────────────────────────────────┐
│                    Engram Frontend                        │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│              FastAPI Backend (Engram)                     │
│  ┌──────────────────────────────────────────────────┐   │
│  │         LangGraph Agent Logic (Brain)            │   │
│  │  - BaseAgent.run()                               │   │
│  │  - AgentState management                         │   │
│  │  - Tool orchestration                            │   │
│  └──────────────┬───────────────────────────────────┘   │
│                 │                                        │
│                 ▼                                        │
│  ┌──────────────────────────────────────────────────┐   │
│  │    Foundry Agent Service Client (Spine)           │   │
│  │  - Thread management                              │   │
│  │  - File storage                                   │   │
│  │  - Vector store operations                        │   │
│  │  - Tool execution                                 │   │
│  └──────────────┬───────────────────────────────────┘   │
└─────────────────┼────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│         Azure AI Foundry Agent Service                   │
│  - Thread Storage (Cosmos DB)                            │
│  - File Storage (Blob Storage)                          │
│  - Vector Stores (Azure AI Search)                      │
│  - Tool Execution                                        │
└─────────────────────────────────────────────────────────┘
```

**Benefits**:
- ✅ Keep our sophisticated LangGraph agent logic
- ✅ Leverage Foundry's managed infrastructure
- ✅ Maintain flexibility for custom workflows
- ✅ Gradual migration path

**Implementation**:
1. Create `FoundryAgentServiceClient` wrapper
2. Replace `EnterpriseContext` thread storage with Foundry threads
3. Use Foundry file storage for agent-uploaded documents
4. Keep LangGraph for agent reasoning and tool orchestration

### Option 2: Full Foundry Integration

**Strategy**: Use Foundry Agent Service as the primary agent runtime

**Benefits**:
- ✅ Maximum leverage of Foundry features
- ✅ Reduced operational overhead
- ✅ Built-in observability and monitoring

**Challenges**:
- ❌ Less control over agent logic
- ❌ Migration complexity
- ❌ Potential loss of LangGraph flexibility

**Recommendation**: Start with Option 1, evaluate Option 2 after gaining experience.

---

## Implementation Plan

### Phase 1: Foundry Agent Service Client (Week 1-2)

**Goal**: Create a client wrapper for Foundry Agent Service APIs

**Tasks**:
1. Add Azure AI Foundry Agent Service SDK to `requirements.txt`
2. Create `backend/agents/foundry_client.py`:
   ```python
   class FoundryAgentServiceClient:
       """Client for Azure AI Foundry Agent Service"""
       
       async def create_thread(
           self, 
           user_id: str, 
           agent_id: str, 
           project_id: Optional[str] = None
       ) -> str:
           """Create a new conversation thread"""
           
       async def add_message(
           self, 
           thread_id: str, 
           role: str, 
           content: str
       ) -> dict:
           """Add message to thread"""
           
       async def list_threads(
           self, 
           user_id: str, 
           project_id: Optional[str] = None
       ) -> list[dict]:
           """List threads for user/project"""
           
       async def upload_file(
           self, 
           thread_id: str, 
           file_path: str, 
           purpose: str = "assistant"
       ) -> dict:
           """Upload file to thread"""
   ```

3. Configuration in `backend/core/config.py`:
   ```python
   # Azure AI Foundry Agent Service
   azure_foundry_agent_endpoint: Optional[str] = Field(
       None, 
       alias="AZURE_FOUNDRY_AGENT_ENDPOINT"
   )
   azure_foundry_agent_project: Optional[str] = Field(
       None, 
       alias="AZURE_FOUNDRY_AGENT_PROJECT"
   )
   ```

**Dependencies**:
- **Option A**: `azure-ai-foundry` SDK (if available - verify package name)
- **Option B**: Use REST API directly with `httpx` (more flexible, works immediately)
  
**Note**: As of January 2026, the exact Python SDK package name may vary. The REST API approach is recommended for initial implementation as it:
- Works immediately without waiting for SDK availability
- Provides full control over API calls
- Can be easily replaced with SDK later
- Aligns with our existing `httpx` usage pattern

### Phase 2: Thread Management Integration (Week 2-3)

**Goal**: Replace in-memory session storage with Foundry threads

**Tasks**:
1. Update `backend/api/routers/chat.py`:
   - Replace `_sessions` dict with Foundry thread storage
   - Use Foundry thread IDs as session keys
   - Maintain composite key format: `{user_id}:{agent_id}:{project_id}:{thread_id}`

2. Update `get_or_create_session()`:
   ```python
   async def get_or_create_session(
       session_id: str,
       security: SecurityContext,
       agent_id: str = "elena"
   ) -> EnterpriseContext:
       # Check if Foundry thread exists
       thread_id = await foundry_client.get_or_create_thread(
           user_id=security.user_id,
           agent_id=agent_id,
           project_id=security.project_id,
           session_id=session_id
       )
       
       # Load thread messages into EnterpriseContext
       messages = await foundry_client.list_messages(thread_id)
       context = EnterpriseContext.from_foundry_thread(thread_id, messages)
       
       return context
   ```

3. Update `websocket_chat()` to use Foundry threads

**Benefits**:
- ✅ Persistent conversation history
- ✅ Automatic thread management
- ✅ Project-based thread isolation

### Phase 3: File Storage Integration (Week 3-4)

**Goal**: Use Foundry file storage for agent-uploaded documents

**Tasks**:
1. Create file upload endpoint:
   ```python
   @router.post("/agents/{agent_id}/files")
   async def upload_file(
       agent_id: str,
       file: UploadFile,
       user: SecurityContext = Depends(get_current_user)
   ):
       thread_id = await get_current_thread(user, agent_id)
       file_info = await foundry_client.upload_file(
           thread_id=thread_id,
           file=file,
           purpose="assistant"
       )
       return file_info
   ```

2. Update agent tools to reference Foundry files:
   - `search_documents` tool can query Foundry file storage
   - `read_file` tool can fetch from Foundry

**Benefits**:
- ✅ Managed file storage
- ✅ Automatic indexing for RAG
- ✅ Project-scoped file access

### Phase 4: Vector Store Integration (Week 4-5)

**Goal**: Use Foundry vector stores for semantic search

**Tasks**:
1. Create vector store per project:
   ```python
   async def get_or_create_vector_store(
       project_id: str
   ) -> str:
       """Get or create Foundry vector store for project"""
   ```

2. Update memory search to use Foundry vector stores:
   - Keep Zep for episodic memory
   - Use Foundry for document-based semantic search

**Benefits**:
- ✅ Managed vector infrastructure
- ✅ Automatic embedding generation
- ✅ Project-scoped vector stores

### Phase 5: Tool Integration (Week 5-6)

**Goal**: Leverage Foundry's tool calling framework

**Tasks**:
1. Register agent tools with Foundry:
   ```python
   tools = [
       {
           "type": "function",
           "function": {
               "name": "search_memory",
               "description": "Search long-term memory",
               "parameters": {...}
           }
       }
   ]
   await foundry_client.register_tools(agent_id, tools)
   ```

2. Use Foundry's tool execution:
   - Foundry handles tool calling orchestration
   - Engram agents execute tool logic
   - Results returned to Foundry

**Benefits**:
- ✅ Built-in tool validation
- ✅ Automatic tool result management
- ✅ Better observability

---

## Configuration

### Environment Variables

```bash
# Azure AI Foundry Agent Service
AZURE_FOUNDRY_AGENT_ENDPOINT=https://<account>.services.ai.azure.com
AZURE_FOUNDRY_AGENT_PROJECT=<project-name>
AZURE_FOUNDRY_AGENT_KEY=<optional-api-key>  # Or use Managed Identity

# Optional: Use Foundry for specific features
USE_FOUNDRY_THREADS=true
USE_FOUNDRY_FILES=true
USE_FOUNDRY_VECTORS=false  # Keep Zep for now
USE_FOUNDRY_TOOLS=false   # Keep custom tool execution
```

### Setup Options

Based on [Foundry documentation](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/environment-setup?view=foundry), we should use:

**Standard Setup** (Recommended):
- ✅ Customer data in our own Azure resources
- ✅ Full control over Cosmos DB, Storage, Search
- ✅ Customer Managed Keys (CMK) support
- ✅ Aligns with enterprise requirements

**Deployment**:
- Use Azure Resource Manager (ARM) template
- Or deploy via Azure Portal
- Configure project-based isolation

---

## Code Examples

### Creating a Foundry Agent Client

**REST API Approach** (Recommended for initial implementation):

```python
import httpx
from azure.identity import DefaultAzureCredential

class FoundryAgentServiceClient:
    """Client for Azure AI Foundry Agent Service using REST API"""
    
    def __init__(self):
        self.settings = get_settings()
        self.endpoint = self.settings.azure_foundry_agent_endpoint
        self.project = self.settings.azure_foundry_agent_project
        self.api_version = "2024-10-01-preview"  # Latest Agent Service API version
        
        # Use Managed Identity or API key
        self.credential = DefaultAzureCredential() if not self.settings.azure_foundry_agent_key else None
        self.api_key = self.settings.azure_foundry_agent_key
        
        # Base URL for Agent Service APIs
        self.base_url = f"{self.endpoint.rstrip('/')}/api/projects/{self.project}"
    
    async def _get_headers(self) -> dict:
        """Get authentication headers"""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["api-key"] = self.api_key
        elif self.credential:
            token = self.credential.get_token("https://cognitiveservices.azure.com/.default")
            headers["Authorization"] = f"Bearer {token.token}"
        return headers
    
    async def create_thread(
        self,
        user_id: str,
        agent_id: str,
        project_id: Optional[str] = None
    ) -> str:
        """Create a new conversation thread"""
        url = f"{self.base_url}/threads"
        headers = await self._get_headers()
        
        payload = {
            "metadata": {
                "user_id": user_id,
                "agent_id": agent_id,
                "project_id": project_id or "default"
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=headers,
                json=payload,
                params={"api-version": self.api_version}
            )
            response.raise_for_status()
            data = response.json()
            return data["id"]
```

### Integrating with BaseAgent

```python
class BaseAgent(ABC):
    def __init__(self):
        self.settings = get_settings()
        self._llm: Optional[FoundryChatClient] = None
        self._foundry_client: Optional[FoundryAgentServiceClient] = None
        self._graph: Optional[StateGraph] = None
    
    @property
    def foundry_client(self) -> FoundryAgentServiceClient:
        """Lazy-load Foundry Agent Service client"""
        if self._foundry_client is None:
            self._foundry_client = FoundryAgentServiceClient()
        return self._foundry_client
    
    async def run(
        self,
        user_message: str,
        context: EnterpriseContext,
        thread_id: Optional[str] = None
    ) -> tuple[str, EnterpriseContext]:
        """Execute agent with Foundry thread support"""
        
        # Create or get Foundry thread
        if not thread_id:
            thread_id = await self.foundry_client.create_thread(
                user_id=context.security.user_id,
                agent_id=self.agent_id,
                project_id=context.security.project_id
            )
        
        # Add user message to Foundry thread
        await self.foundry_client.add_message(
            thread_id=thread_id,
            role="user",
            content=user_message
        )
        
        # Run LangGraph agent logic
        response, updated_context = await self._run_agent_logic(
            user_message,
            context
        )
        
        # Add assistant response to Foundry thread
        await self.foundry_client.add_message(
            thread_id=thread_id,
            role="assistant",
            content=response
        )
        
        # Update context with thread ID
        updated_context.episodic.conversation_id = thread_id
        
        return response, updated_context
```

---

## Migration Strategy

### Gradual Migration

1. **Phase 1-2**: Add Foundry client alongside existing code
2. **Phase 3**: Feature flag to use Foundry threads (`USE_FOUNDRY_THREADS=true`)
3. **Phase 4**: Migrate one agent at a time (Elena → Marcus → Sage)
4. **Phase 5**: Full migration, remove legacy code

### Backward Compatibility

- Keep `EnterpriseContext` for agent logic
- Map Foundry threads to `EnterpriseContext` on load
- Support both in-memory and Foundry storage during migration

---

## Benefits Summary

### Operational Benefits

✅ **Reduced Infrastructure Management**:
- No need to manage Cosmos DB for threads
- No need to manage Blob Storage for files
- No need to manage Azure AI Search for vectors (optional)

✅ **Cost Optimization**:
- Pay only for what you use
- Managed infrastructure reduces operational overhead
- Automatic scaling

✅ **Enterprise Features**:
- Customer Managed Keys (CMK)
- Private network isolation (BYO VNet)
- Project-based data isolation (perfect alignment!)

### Developer Benefits

✅ **Simplified Code**:
- Less custom thread management code
- Built-in file handling
- Automatic tool orchestration

✅ **Better Observability**:
- Foundry provides built-in monitoring
- Thread-level metrics
- Tool execution tracking

### User Benefits

✅ **Improved Reliability**:
- Managed infrastructure = higher uptime
- Automatic backups and recovery
- Better performance

✅ **Enhanced Features**:
- File upload and management
- Better conversation history
- Project-based collaboration

---

## Risks & Mitigations

### Risk 1: Vendor Lock-in

**Mitigation**:
- Keep LangGraph for agent logic (portable)
- Abstract Foundry client behind interface
- Maintain ability to switch back to Zep/custom storage

### Risk 2: Migration Complexity

**Mitigation**:
- Gradual migration with feature flags
- Maintain backward compatibility
- Test thoroughly in staging

### Risk 3: Cost Increase

**Mitigation**:
- Monitor usage closely
- Use Standard Setup for cost control
- Compare costs vs. current infrastructure

---

## Next Steps

1. **Research**: Verify Azure AI Foundry Agent Service SDK availability and API
2. **POC**: Create minimal integration to test thread management
3. **Design**: Finalize architecture based on POC results
4. **Implement**: Follow phased implementation plan
5. **Test**: Comprehensive testing in staging environment
6. **Deploy**: Gradual rollout with feature flags

---

## References

- [Azure AI Foundry Agent Service Setup](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/environment-setup?view=foundry)
- [Foundry Agent Service Quickstart](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/quickstart)
- [Foundry Agent Service SDK Documentation](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/sdk-reference)

---

*Last Updated: January 2026*

