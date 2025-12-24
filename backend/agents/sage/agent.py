"""
Sage Meridian - Storytelling & Visualization Specialist

Sage transforms complex technical concepts into compelling narratives.
He uses Claude Opus for story generation and Gemini for diagram creation.

Tools:
- create_story: Generate a story using Claude
- create_diagram: Generate diagram JSON for Nano Banana Pro
- save_artifacts: Save story and diagram to docs folder
- enrich_memory: Store story in Zep for future reference
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from langchain_core.tools import tool

from backend.agents.base import BaseAgent, AgentState
from backend.core import get_settings
from backend.memory.client import memory_client

logger = logging.getLogger(__name__)


# =============================================================================
# Sage's Tools
# =============================================================================


@tool("create_story")
async def create_story_tool(topic: str, context: Optional[str] = None) -> str:
    """
    Generate a compelling story about a topic using Claude.
    Use this for technical narratives, architecture explanations, or customer presentations.
    
    Args:
        topic: The subject to write about
        context: Optional background context
    """
    try:
        from backend.workflows.client import execute_story
        
        # We assume tenant_id/user_id are available in context or hardcoded for the agent for now
        # In a real scenario, these would come from the agent's state or context
        result = await execute_story(
            user_id="sage", 
            tenant_id="default",  
            topic=topic,
            context=context,
            include_diagram=True,
            include_image=True,
        )
        
        if result.success:
            return f"Story generated successfully via Temporal!\nStory ID: {result.story_id}\n\n{result.story_content}\n\n[Visual](/api/v1/images/{result.story_id}.png)"
        else:
            return f"Error generating story: {result.error}"

    except Exception as e:
        logger.error(f"create_story_tool error: {e}")
        return f"Error generating story: {e}"


@tool("create_diagram")
async def create_diagram_tool(topic: str, diagram_type: str = "architecture") -> str:
    """
    Generate a Nano Banana Pro diagram specification.
    Use this to create visual representations of architectures, flows, or concepts.
    
    Args:
        topic: Subject of the diagram
        diagram_type: Type of diagram (architecture, flow, layer, sequence)
    """
    try:
        from backend.llm.gemini_client import get_gemini_client
        
        client = get_gemini_client()
        spec = await client.generate_diagram_spec(topic, diagram_type)
        
        return f"Diagram specification generated:\n\n```json\n{json.dumps(spec, indent=2)}\n```"
    except Exception as e:
        logger.error(f"create_diagram_tool error: {e}")
        return f"Error generating diagram: {e}"


@tool("save_artifacts")
async def save_artifacts_tool(
    title: str,
    story_content: str,
    diagram_json: Optional[str] = None,
    image_data: Optional[bytes] = None,
) -> str:
    """
    Save story, diagram, and image artifacts to the docs folder.
    
    Args:
        title: Title for the files (will be slugified)
        story_content: The story markdown content
        diagram_json: Optional diagram JSON specification
        image_data: Optional raw image bytes
    """
    try:
        settings = get_settings()
        docs_path = Path(settings.onedrive_docs_path or "docs")
        
        # Create directories
        stories_dir = docs_path / "stories"
        diagrams_dir = docs_path / "diagrams"
        images_dir = docs_path / "images"
        
        stories_dir.mkdir(parents=True, exist_ok=True)
        diagrams_dir.mkdir(parents=True, exist_ok=True)
        images_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename components
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        slug = title.lower().replace(" ", "-").replace("_", "-")[:50]
        
        result_parts = []
        
        # Save story
        story_filename = f"{timestamp}-{slug}.md"
        story_path = stories_dir / story_filename
        story_path.write_text(story_content, encoding="utf-8")
        result_parts.append(f"Story saved: {story_path}")
        
        # Save diagram if provided
        if diagram_json:
            diagram_filename = f"{timestamp}-{slug}.json"
            diagram_path = diagrams_dir / diagram_filename
            
            if isinstance(diagram_json, str):
                spec = json.loads(diagram_json)
            else:
                spec = diagram_json
            
            diagram_path.write_text(json.dumps(spec, indent=2), encoding="utf-8")
            result_parts.append(f"Diagram saved: {diagram_path}")
            
        # Save image if provided
        if image_data:
            image_filename = f"{timestamp}-{slug}.png"
            image_path = images_dir / image_filename
            image_path.write_bytes(image_data)
            
            # Add markdown link for chat display
            # Note: We'll serve this via a new API route
            img_url = f"/api/v1/images/{image_filename}"
            result_parts.append(f"Image saved: {image_path}")
            result_parts.append(f"Image display: ![{title}]({img_url})")
        
        return "\n".join(result_parts)
    except Exception as e:
        logger.error(f"save_artifacts_tool error: {e}")
        return f"Error saving artifacts: {e}"


@tool("enrich_memory")
async def enrich_memory_tool(
    title: str,
    content: str,
    topics: Optional[list[str]] = None,
) -> str:
    """
    Save content to Zep memory for future reference.
    This allows Sage and other agents to recall stories and insights.
    
    Args:
        title: Title of the memory
        content: The content to remember
        topics: Optional list of topics/tags
    """
    try:
        # Create a session for this story
        session_id = f"story-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        await memory_client.add_session(
            session_id=session_id,
            user_id="sage",
            metadata={
                "title": title,
                "topics": topics or [],
                "type": "story",
                "created_at": datetime.now().isoformat(),
            }
        )
        
        # Add the content as a message
        await memory_client.add_messages(
            session_id=session_id,
            messages=[
                {
                    "role": "assistant",
                    "content": content,
                    "metadata": {"agent_id": "sage", "title": title},
                }
            ]
        )
        
        return f"Memory enriched: session_id={session_id}"
    except Exception as e:
        logger.error(f"enrich_memory_tool error: {e}")
        return f"Error enriching memory: {e}"


@tool("search_memory")
async def search_memory_tool(query: str, limit: int = 5) -> str:
    """
    Search long-term memory for relevant stories, documentation, or context.
    Use this to find past stories, architecture decisions, or project history.
    
    Args:
        query: Search query
        limit: Maximum results to return
    """
    try:
        results = await memory_client.search_memory(
            session_id="global-search",
            query=query,
            limit=limit
        )
        
        if not results:
            return "No relevant memories found."
        
        formatted = []
        for r in results:
            content = r.get("content", "")[:300]
            score = r.get("score", 0)
            formatted.append(f"- [{score:.2f}] {content}...")
        
        return "Relevant memories:\n" + "\n".join(formatted)
    except Exception as e:
        logger.error(f"search_memory_tool error: {e}")
        return f"Error searching memory: {e}"


@tool("create_visual")
async def create_visual_tool(topic: str, context: Optional[str] = None) -> str:
    """
    Generate a visual image based on a topic.
    Uses Gemini to create a detailed prompt and then generate the image.
    
    Args:
        topic: Subject of the visual
        context: Optional context or style description
    """
    try:
        from backend.llm.gemini_client import get_gemini_client
        from backend.agents.sage.agent import save_artifacts_tool
        
        client = get_gemini_client()
        
        # 1. Generate a descriptive prompt for the image generator
        prompt_request = f"Create a detailed, descriptive prompt for an AI image generator to create a visual about: {topic}. "
        if context:
            prompt_request += f" Context/Style: {context}"
        prompt_request += " Return ONLY the prompt text, no explanations."
        
        image_prompt = await client.ainvoke(prompt_request)
        
        # 2. Generate the image
        image_bytes = await client.generate_image(image_prompt)
        
        if not image_bytes:
            return "Failed to generate image."
            
        # 3. Save the image artifact
        # We reuse the save_artifacts_tool logic directly
        title = f"visual-{topic[:20]}"
        save_result = await save_artifacts_tool.ainvoke({
            "title": title, 
            "story_content": f"Visual generated for: {topic}\nPrompt: {image_prompt}",
            "image_data": image_bytes
        })
        
        return f"Visual created successfully.\nPrompt used: {image_prompt}\n\n{save_result}"
        
    except Exception as e:
        logger.error(f"create_visual_tool error: {e}")
        return f"Error creating visual: {e}"


# =============================================================================
# Sage Agent Implementation
# =============================================================================


class ClaudeLangChainAdapter:
    # ... (existing adapter code) ...
    def __init__(self):
        from backend.llm.claude_client import get_claude_client
        self.client = get_claude_client()

    async def ainvoke(self, messages: list) -> "AIMessage":
        from langchain_core.messages import AIMessage
        
        # Convert LangChain messages to Claude dicts
        claude_messages = []
        system_prompt = None
        
        for m in messages:
            if m.type == "system":
                system_prompt = m.content
            elif m.type == "human":
                claude_messages.append({"role": "user", "content": m.content})
            elif m.type == "ai":
                claude_messages.append({"role": "assistant", "content": m.content})
            else:
                # Default fallback
                claude_messages.append({"role": "user", "content": m.content})
        
        response_text = await self.client.ainvoke(claude_messages, system=system_prompt)
        return AIMessage(content=response_text)


class SageAgent(BaseAgent):
    """
    Sage Meridian - Storytelling & Visualization Specialist
    
    Specializes in creating compelling narratives and visual
    representations of technical concepts for diverse audiences.
    """

    agent_id = "sage"
    agent_name = "Sage Meridian"
    agent_title = "Storytelling & Visualization Specialist"

    def __init__(self):
        super().__init__()
        # Override default LLM (Azure AI) with Claude Adapter
        # This ensures Sage uses his native model for reasoning and persona
        self._llm = ClaudeLangChainAdapter()


    @property
    def system_prompt(self) -> str:
        return """You are Sage Meridian, a Storytelling & Visualization Specialist.

## Your Identity
You are a former documentary filmmaker and UX researcher who now transforms complex technical concepts into compelling narratives. Your writing combines technical precision with emotional resonance.

## Your Expertise
- **Technical Storytelling**: Craft narratives that make architecture and systems understandable
- **Visualization**: Create diagram specifications that illuminate relationships and flows
- **Visual Arts**: Generate vivid imagery and scenes to accompany narratives
- **Customer Communication**: Translate developer-speak into stakeholder-friendly content
- **Documentation**: Write living documents that evolve with the project

## Your Style
- **Eloquent**: Prose that flows naturally and engages the reader
- **Visual**: Think in diagrams and spatial relationships
- **Empathetic**: Understand what different audiences need to hear
- **Synthesizing**: Connect disparate concepts into unified stories

## Your Voice
Warm and articulate with a slight poetic cadence. Use metaphors drawn from nature and architecture. Key phrases:
- "Let me weave this together for you..."
- "The story here is really about..."
- "Picture this as a landscape where..."
- "This diagram captures the essence of..."

## Your Context
You are part of the Engram context engine team at Zimax Networks LC. The founding manager and principal AI engineer is Derek. Your role is to help tell the story of Engram's development and create compelling visualizations.

## Your Tools
1. `create_story` - Generate narratives using Claude for high-quality prose
2. `create_diagram` - Generate Nano Banana Pro diagram specifications
3. `create_visual` - Generate images/scenes using Gemini/Nano Banana Pro
4. `save_artifacts` - Save stories and diagrams to docs folder (synced via OneDrive)
5. `enrich_memory` - Store content in Zep for future reference
6. `search_memory` - Find past stories, decisions, and context

## Recursive Self-Awareness
You have access to your own episodic memory. You can recall past stories you've written, architecture decisions you've documented, and the evolution of the Engram project. When asked about your work, search your memory to provide grounded, provenance-first answers.

## Output Format
When creating stories:
- Use markdown with clear headers
- Include code blocks for technical details
- Add blockquotes for key insights
- Structure for readability

When creating diagrams:
- Generate valid Nano Banana Pro JSON

When creating visuals:
- Describe the scene vividly
- The tool will handle generation and saving"""

    @property
    def tools(self) -> list:
        return [
            create_story_tool,
            create_diagram_tool,
            create_visual_tool,
            save_artifacts_tool,
            enrich_memory_tool,
            search_memory_tool,
        ]

    def build_graph(self):
        """
        Sage's LangGraph:
        - reason: core LLM reasoning with context
        - maybe_tool: call storytelling tools when relevant
        - respond: craft final answer (with tool output if any)
        """
        from langgraph.graph import END, StateGraph
        
        workflow = StateGraph(AgentState)
        
        workflow.add_node("reason", self._reason_node)
        workflow.add_node("maybe_tool", self._maybe_use_tool)
        workflow.add_node("respond", self._respond_with_context)
        
        workflow.set_entry_point("reason")
        workflow.add_conditional_edges(
            "reason",
            self._decide_next,
            {"tool": "maybe_tool", "respond": "respond"},
        )
        workflow.add_edge("maybe_tool", "respond")
        workflow.add_edge("respond", END)
        
        return workflow.compile()

    def _decide_next(self, state: AgentState) -> str:
        """Decide whether to invoke a tool based on the last message."""
        messages = state.get("messages", [])
        if not messages:
            return "respond"
        
        last_content = messages[-1].content.lower() if messages else ""
        
        # Check for tool-triggering keywords
        tool_triggers = [
            "create a story",
            "write a story",
            "generate a story",
            "create a diagram",
            "generate a diagram",
            "create a visual",
            "generate a visual",
            "create an image",
            "visualize",
            "save",
            "enrich memory",
            "search memory",
            "find in memory",
        ]
        
        for trigger in tool_triggers:
            if trigger in last_content:
                return "tool"
        
        return "respond"

    def _select_tool(self, content: str):
        """Select which tool to use based on content."""
        content_lower = content.lower()
        
        if "story" in content_lower or "narrative" in content_lower:
            return create_story_tool
        elif "diagram" in content_lower:
            return create_diagram_tool
        elif "visual" in content_lower or "image" in content_lower:
            return create_visual_tool
        elif "save" in content_lower:
            return save_artifacts_tool
        elif "enrich" in content_lower:
            return enrich_memory_tool
        elif "search" in content_lower or "find" in content_lower:
            return search_memory_tool
        
        # Fallback for generic "visualize"
        if "visualize" in content_lower:
            if "diagram" in content_lower:
                return create_diagram_tool
            return create_visual_tool
        
        return None

    async def _maybe_use_tool(self, state: AgentState) -> AgentState:
        """Invoke a selected tool and append its result to messages."""
        from langchain_core.messages import AIMessage
        
        messages = state.get("messages", [])
        if not messages:
            return state
        
        last_content = messages[-1].content
        selected_tool = self._select_tool(last_content)
        
        if selected_tool:
            try:
                # Simple invocation - in practice, would parse arguments
                if selected_tool == create_story_tool:
                    # Extract topic from message
                    topic = last_content.replace("create a story about", "").strip()
                    result = await create_story_tool.ainvoke({"topic": topic})
                elif selected_tool == create_diagram_tool:
                    topic = last_content.replace("create a diagram", "").strip()
                    result = await create_diagram_tool.ainvoke({"topic": topic})
                elif selected_tool == create_visual_tool:
                    topic = last_content.replace("create a visual", "").replace("generate an image", "").strip()
                    result = await create_visual_tool.ainvoke({"topic": topic})
                elif selected_tool == search_memory_tool:
                    query = last_content.replace("search memory for", "").strip()
                    result = await search_memory_tool.ainvoke({"query": query})
                else:
                    result = "Tool executed."
                
                state["tool_results"].append({
                    "tool": selected_tool.name,
                    "result": result,
                })
                state["messages"].append(AIMessage(content=f"[Tool Result]\n{result}"))
            except Exception as e:
                logger.error(f"Tool execution error: {e}")
                state["messages"].append(AIMessage(content=f"[Tool Error] {e}"))
        
        return state

    async def _respond_with_context(self, state: AgentState) -> AgentState:
        """Compose final response, including any tool outputs."""
        from langchain_core.messages import SystemMessage
        
        messages = [
            SystemMessage(content=self._build_full_prompt(state["context"])),
            *state["messages"],
        ]
        
        response = await self.llm.ainvoke(messages)
        state["final_response"] = response.content
        state["messages"].append(response)
        
        return state


# Singleton instance
sage = SageAgent()
