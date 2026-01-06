---
layout: default
title: Using Foundry-Created Agents in Engram
parent: Architecture
nav_order: 6
---

# Using Foundry-Created Agents in Engram

> **Status**: Analysis & Implementation Guide  
> **Last Updated**: January 2026  
> **Approach**: Using Foundry Agent Service runtime instead of LangGraph

---

## Overview

Yes, you can create agents in Azure AI Foundry and use them in Engram! This is a different approach than our current LangGraph-based agents, offering managed infrastructure and built-in capabilities.

---

## Two Approaches Compared

### Current Approach: LangGraph Agents

**What We Have**:
- Custom LangGraph agents (Elena, Marcus, Sage)
- Custom system prompts
- Custom tools (LangChain tools)
- Custom reasoning workflows
- Full control over agent logic

**Pros**:
- ✅ Maximum flexibility
- ✅ Custom workflows (reason → tool → respond)
- ✅ Full control over tool execution
- ✅ Can use any LangChain tool
- ✅ Complex multi-step reasoning

**Cons**:
- ❌ More infrastructure to manage
- ❌ Custom thread management (now using Foundry for this)
- ❌ More code to maintain

### Alternative Approach: Foundry Agents

**What Foundry Provides**:
- Agent definitions (system prompt, tools, model)
- Built-in thread management
- Built-in tool orchestration
- Managed infrastructure
- Agent catalog

**Pros**:
- ✅ Managed infrastructure
- ✅ Built-in thread management
- ✅ Built-in tool orchestration
- ✅ Agent catalog for discovery
- ✅ Less code to maintain

**Cons**:
- ❌ Less flexibility than LangGraph
- ❌ Limited to Foundry's agent model
- ❌ Tool execution model may differ
- ❌ May need to adapt existing tools

---

## Creating Agents in Foundry

### Option 1: Azure Portal

1. **Navigate to Foundry Portal**:
   - Go to Azure Portal → Azure AI Foundry
   - Select your project
   - Go to "Agents" section

2. **Create Agent**:
   - Click "Create Agent"
   - Provide agent name (e.g., "Elena", "Marcus", "Sage")
   - Configure:
     - **System Prompt**: Copy from Engram agent definition
     - **Model**: Select deployment (e.g., gpt-4o, gpt-5.2-chat)
     - **Tools**: Add function definitions
     - **Temperature**: Set as needed

3. **Define Tools**:
   - Add function definitions (JSON schema)
   - Configure tool endpoints (if using external tools)
   - Set tool descriptions

4. **Save Agent**:
   - Agent is now available in Foundry catalog
   - Note the agent ID for integration

### Option 2: REST API

```python
# Create agent via REST API
import httpx
from azure.identity import DefaultAzureCredential

async def create_foundry_agent(
    agent_name: str,
    system_prompt: str,
    model_deployment: str,
    tools: list[dict]
):
    endpoint = "https://<account>.services.ai.azure.com"
    project = "<project-name>"
    credential = DefaultAzureCredential()
    
    token = credential.get_token("https://cognitiveservices.azure.com/.default")
    headers = {
        "Authorization": f"Bearer {token.token}",
        "Content-Type": "application/json",
    }
    
    url = f"{endpoint}/api/projects/{project}/agents"
    
    payload = {
        "name": agent_name,
        "instructions": system_prompt,
        "model": model_deployment,
        "tools": tools,
        "temperature": 0.7,
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            headers=headers,
            json=payload,
            params={"api-version": "2024-10-01-preview"},
        )
        response.raise_for_status()
        return response.json()
```

### Option 3: SDK (if available)

```python
from azure.ai.foundry import FoundryClient

client = FoundryClient(
    endpoint="https://<account>.services.ai.azure.com",
    project="<project-name>",
    credential=DefaultAzureCredential(),
)

agent = await client.agents.create(
    name="Elena",
    instructions=elena_system_prompt,
    model="gpt-5.2-chat",
    tools=[...],
)
```

---

## Integrating Foundry Agents into Engram

### Approach 1: Hybrid - Use Foundry Agent Runtime

Create a wrapper that uses Foundry's agent runtime while maintaining Engram's interface:

```python
# backend/agents/foundry_agent_wrapper.py
from backend.agents.foundry_client import FoundryAgentServiceClient
from backend.core import EnterpriseContext

class FoundryAgentWrapper:
    """
    Wrapper for Foundry-created agents.
    Provides Engram-compatible interface.
    """
    
    def __init__(self, agent_id: str, foundry_agent_id: str):
        self.agent_id = agent_id  # Engram agent ID (elena, marcus, sage)
        self.foundry_agent_id = foundry_agent_id  # Foundry agent ID
        self.foundry_client = get_foundry_client()
    
    async def run(
        self,
        user_message: str,
        context: EnterpriseContext,
        thread_id: Optional[str] = None
    ) -> tuple[str, EnterpriseContext]:
        """
        Execute Foundry agent with user message.
        
        Returns:
            Tuple of (response_text, updated_context)
        """
        # Get or create thread
        if not thread_id:
            thread_id = await self.foundry_client.create_thread(
                user_id=context.security.user_id,
                agent_id=self.agent_id,
                project_id=context.security.project_id,
            )
        
        # Add user message to thread
        await self.foundry_client.add_message(
            thread_id=thread_id,
            role="user",
            content=user_message,
        )
        
        # Run Foundry agent
        # Note: This requires Foundry's agent execution API
        response = await self._run_foundry_agent(thread_id)
        
        # Add assistant response to thread
        await self.foundry_client.add_message(
            thread_id=thread_id,
            role="assistant",
            content=response,
        )
        
        # Update context
        context.episodic.conversation_id = thread_id
        context.episodic.metadata["foundry_thread_id"] = thread_id
        context.episodic.metadata["foundry_agent_id"] = self.foundry_agent_id
        
        return response, context
    
    async def _run_foundry_agent(self, thread_id: str) -> str:
        """
        Execute Foundry agent on thread.
        
        This uses Foundry's agent execution API.
        """
        # Foundry agent execution endpoint
        url = f"{self.foundry_client.base_url}/agents/{self.foundry_agent_id}/runs"
        headers = await self.foundry_client._get_headers()
        
        payload = {
            "thread_id": thread_id,
            "assistant_id": self.foundry_agent_id,
        }
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                url,
                headers=headers,
                json=payload,
                params={"api-version": self.foundry_client.api_version},
            )
            response.raise_for_status()
            data = response.json()
            
            # Poll for completion or wait for streaming
            run_id = data.get("id")
            return await self._wait_for_completion(run_id, thread_id)
    
    async def _wait_for_completion(self, run_id: str, thread_id: str) -> str:
        """Wait for agent run to complete and get response."""
        # Poll run status
        # When complete, get latest assistant message from thread
        messages = await self.foundry_client.list_messages(thread_id, limit=1)
        if messages and messages[0].get("role") == "assistant":
            return messages[0].get("content", "")
        return "Agent response not available"
```

### Approach 2: Replace LangGraph Agents

Update `backend/agents/router.py` to use Foundry agents:

```python
# backend/agents/router.py
from backend.agents.foundry_agent_wrapper import FoundryAgentWrapper

class AgentRouter:
    def __init__(self):
        settings = get_settings()
        
        if settings.use_foundry_agents:
            # Use Foundry-created agents
            self.agents = {
                "elena": FoundryAgentWrapper("elena", "foundry-elena-id"),
                "marcus": FoundryAgentWrapper("marcus", "foundry-marcus-id"),
                "sage": FoundryAgentWrapper("sage", "foundry-sage-id"),
            }
        else:
            # Use existing LangGraph agents
            self.agents = {
                "elena": elena,
                "marcus": marcus,
                "sage": sage,
            }
```

---

## Tool Integration

### Converting LangChain Tools to Foundry Tools

Foundry agents use function definitions (OpenAI function calling format):

```python
# LangChain tool
@tool("search_memory")
async def search_memory_tool(query: str, limit: int = 5) -> str:
    """Search memory for relevant content."""
    # ... implementation
    return results

# Foundry function definition
foundry_tool = {
    "type": "function",
    "function": {
        "name": "search_memory",
        "description": "Search memory for relevant content using tri-search (keyword, vector, graph).",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results",
                    "default": 5
                }
            },
            "required": ["query"]
        }
    }
}
```

### Tool Execution

Foundry agents call tools via function calling. You need to:

1. **Register Tool Endpoints**:
   - Create API endpoints for each tool
   - Foundry will call these endpoints when agent uses tool

2. **Handle Tool Calls**:
   ```python
   @router.post("/api/v1/tools/search_memory")
   async def search_memory_tool_endpoint(request: ToolRequest):
       """Tool endpoint called by Foundry agent."""
       result = await search_memory_tool(
           query=request.arguments["query"],
           limit=request.arguments.get("limit", 5)
       )
       return {"result": result}
   ```

---

## Migration Strategy

### Phase 1: Create Agents in Foundry

1. **Export Agent Definitions**:
   - Extract system prompts from Engram agents
   - List all tools used by each agent
   - Document tool schemas

2. **Create Foundry Agents**:
   - Create Elena agent in Foundry
   - Create Marcus agent in Foundry
   - Create Sage agent in Foundry

3. **Register Tools**:
   - Create tool endpoints in Engram
   - Register tools with Foundry agents
   - Test tool execution

### Phase 2: Hybrid Mode

1. **Add Feature Flag**:
   ```python
   use_foundry_agents: bool = Field(False, alias="USE_FOUNDRY_AGENTS")
   ```

2. **Update Router**:
   - Support both LangGraph and Foundry agents
   - Switch based on feature flag

3. **Test in Development**:
   - Enable flag for one agent (e.g., Elena)
   - Compare behavior with LangGraph version
   - Fix any issues

### Phase 3: Full Migration (Optional)

1. **Migrate All Agents**:
   - Move all agents to Foundry
   - Update router to use Foundry only

2. **Remove LangGraph Code** (if desired):
   - Remove `BaseAgent` class
   - Remove LangGraph workflows
   - Simplify codebase

---

## Trade-offs

### When to Use Foundry Agents

✅ **Use Foundry Agents If**:
- You want managed infrastructure
- You want built-in thread management
- You want agent catalog/discovery
- You're okay with Foundry's agent model
- You want less code to maintain

### When to Keep LangGraph Agents

✅ **Keep LangGraph Agents If**:
- You need complex multi-step reasoning
- You need custom workflows
- You need full control over tool execution
- You want to use advanced LangGraph features
- You have complex state management needs

### Hybrid Approach (Recommended)

✅ **Use Both**:
- Use Foundry for thread management (already implemented)
- Use LangGraph for agent logic (current approach)
- Get benefits of both worlds

---

## Implementation Example

### Creating Elena in Foundry

```python
# scripts/create_foundry_agents.py
import asyncio
from backend.agents.elena.agent import ElenaAgent
from backend.agents.foundry_client import FoundryAgentServiceClient

async def create_elena_in_foundry():
    """Create Elena agent in Foundry."""
    
    # Get Elena's system prompt
    elena = ElenaAgent()
    system_prompt = elena.system_prompt
    
    # Convert Elena's tools to Foundry format
    tools = []
    for tool in elena.tools:
        foundry_tool = {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.args_schema.schema() if hasattr(tool, 'args_schema') else {},
            }
        }
        tools.append(foundry_tool)
    
    # Create agent in Foundry
    foundry_client = FoundryAgentServiceClient()
    
    # Use Foundry agent creation API
    agent = await foundry_client.create_agent(
        name="Elena",
        instructions=system_prompt,
        model="gpt-5.2-chat",
        tools=tools,
    )
    
    print(f"Created Elena agent in Foundry: {agent['id']}")
    return agent['id']

if __name__ == "__main__":
    asyncio.run(create_elena_in_foundry())
```

---

## Next Steps

1. **Create Agents in Foundry**:
   - Use Azure Portal or REST API
   - Export system prompts from Engram agents
   - Register tools

2. **Implement Wrapper**:
   - Create `FoundryAgentWrapper` class
   - Implement Engram-compatible interface
   - Handle tool execution

3. **Add Feature Flag**:
   - Add `USE_FOUNDRY_AGENTS` flag
   - Update router to support both modes
   - Test in development

4. **Evaluate**:
   - Compare behavior with LangGraph agents
   - Measure performance
   - Decide on migration path

---

## Summary

✅ **Yes, you can create agents in Foundry and use them in Engram!**

**Options**:
1. **Hybrid**: Use Foundry for threads (current) + LangGraph for logic
2. **Foundry Agents**: Use Foundry's agent runtime (requires migration)
3. **Both**: Support both modes with feature flags

**Recommendation**: Start with hybrid approach (Foundry threads + LangGraph agents), then evaluate Foundry agents for specific use cases.

---

*Last Updated: January 2026*

