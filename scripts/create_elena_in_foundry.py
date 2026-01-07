#!/usr/bin/env python3
"""
Create Elena Agent in Azure AI Foundry

This script exports Elena's definition and creates her as a Foundry agent
with all her tools, including Microsoft Graph integration.

Usage:
    python scripts/create_elena_in_foundry.py

Prerequisites:
    - Set environment variables:
      - AZURE_FOUNDRY_AGENT_ENDPOINT
      - AZURE_FOUNDRY_AGENT_PROJECT
      - AZURE_FOUNDRY_AGENT_KEY (optional, uses Managed Identity if not set)
    - Microsoft Graph credentials configured (MS_GRAPH_* env vars)
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx

# Check for required modules with helpful error message
try:
    from backend.agents.elena.agent import ElenaAgent
    from backend.agents.foundry_client import FoundryAgentServiceClient, get_foundry_client
    from backend.core import get_settings
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("\nPlease ensure:")
    print("1. You're in the project root directory")
    print("2. Dependencies are installed: pip install -r backend/requirements.txt")
    print("3. Python path includes the project root")
    print("\nIf using a virtual environment, activate it first:")
    print("  source venv/bin/activate  # or your venv path")
    sys.exit(1)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def convert_langchain_tool_to_foundry(tool) -> dict:
    """
    Convert a LangChain tool to Foundry function definition format.
    """
    # Get tool name and description
    name = tool.name if hasattr(tool, 'name') else str(tool)
    description = tool.description if hasattr(tool, 'description') else ""
    
    # Sanitize tool name to match Foundry pattern: ^[a-zA-Z0-9_\.-]+$
    # Replace any invalid characters with underscores
    import re
    name = re.sub(r'[^a-zA-Z0-9_\.-]', '_', name)
    
    # Get parameters schema
    parameters = {
        "type": "object",
        "properties": {},
        "required": [],
    }
    
    # Try to extract schema from tool
    if hasattr(tool, 'args_schema') and tool.args_schema:
        try:
            schema = tool.args_schema.model_json_schema() if hasattr(tool.args_schema, 'model_json_schema') else {}
            if "properties" in schema:
                parameters["properties"] = schema["properties"]
            if "required" in schema:
                parameters["required"] = schema.get("required", [])
        except Exception as e:
            logger.warning(f"Could not extract schema from tool {name}: {e}")
    
    # Foundry expects tools with "type" at root level and "function" nested
    # Structure: {"type": "function", "function": {"name": "...", "description": "...", "parameters": {...}}}
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": parameters,
        }
    }


async def create_elena_in_foundry() -> str:
    """
    Create Elena agent in Azure AI Foundry.
    
    Returns:
        Foundry agent ID
    """
    logger.info("=" * 60)
    logger.info("Creating Elena Agent in Azure AI Foundry")
    logger.info("=" * 60)
    
    # Check Foundry configuration
    settings = get_settings()
    
    # Check environment variables first (may not be in .env)
    endpoint = os.getenv("AZURE_FOUNDRY_AGENT_ENDPOINT") or settings.azure_foundry_agent_endpoint
    project = os.getenv("AZURE_FOUNDRY_AGENT_PROJECT") or settings.azure_foundry_agent_project
    
    if not endpoint or not project:
        logger.error("=" * 60)
        logger.error("❌ Foundry Agent Service not configured!")
        logger.error("=" * 60)
        logger.error("\nPlease set the following environment variables:")
        logger.error("  export AZURE_FOUNDRY_AGENT_ENDPOINT='https://<account>.services.ai.azure.com'")
        logger.error("  export AZURE_FOUNDRY_AGENT_PROJECT='<project-name>'")
        logger.error("\nOptional (uses Managed Identity if not set):")
        logger.error("  export AZURE_FOUNDRY_AGENT_KEY='<api-key>'")
        logger.error("\nThen run this script again.")
        return None
    
    logger.info(f"Foundry Endpoint: {endpoint}")
    logger.info(f"Foundry Project: {project}")
    logger.info("")
    
    # Get Elena's definition
    elena = ElenaAgent()
    system_prompt = elena.system_prompt
    tools = elena.tools
    
    logger.info(f"Elena System Prompt Length: {len(system_prompt)} characters")
    logger.info(f"Elena Tools Count: {len(tools)}")
    
    # Convert tools to Foundry format
    foundry_tools = []
    for tool in tools:
        try:
            foundry_tool = convert_langchain_tool_to_foundry(tool)
            foundry_tools.append(foundry_tool)
            logger.info(f"  ✅ Converted tool: {foundry_tool['function']['name']}")
        except Exception as e:
            logger.warning(f"  ⚠️  Failed to convert tool {tool}: {e}")
    
    # Create Foundry client directly (bypass feature flag check for agent creation)
    try:
        # Use correct API version for Foundry Agent Service
        api_version = os.getenv("AZURE_FOUNDRY_AGENT_API_VERSION") or "2025-11-15-preview"
        foundry_client = FoundryAgentServiceClient(
            endpoint=endpoint,
            project=project,
            api_key=os.getenv("AZURE_FOUNDRY_AGENT_KEY") or settings.azure_foundry_agent_key,
            api_version=api_version,
        )
        logger.info("✅ Foundry client initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Foundry client: {e}")
        logger.error("\nPlease check:")
        logger.error("1. Foundry endpoint is correct")
        logger.error("2. Foundry project exists")
        logger.error("3. Authentication is configured (API key or Managed Identity)")
        return None
    
    # Create agent using Foundry client
    try:
        metadata = {
            "agent_id": "elena",
            "agent_name": "Dr. Elena Vasquez",
            "agent_title": "Business Analyst",
            "user_email": "elena@zimax.net",
            "created_by": "engram-migration-script",
        }
        
        data = await foundry_client.create_agent(
            name="Elena",
            instructions=system_prompt,
            model=settings.azure_ai_deployment,
            tools=foundry_tools,
            metadata=metadata,
        )
        
        agent_id = data.get("id")
        if not agent_id:
            # Try alternative response format
            agent_id = data.get("agent_id") or data.get("name")
        
        if not agent_id:
            raise ValueError(f"Agent creation response missing 'id': {data}")
        
        logger.info("=" * 60)
        logger.info(f"✅ Elena created in Foundry!")
        logger.info(f"   Agent ID: {agent_id}")
        logger.info(f"   Name: {data.get('name', 'Elena')}")
        logger.info(f"   Tools: {len(foundry_tools)}")
        logger.info("=" * 60)
        
        # Save agent ID to config file for reference
        config_path = Path(__file__).parent.parent / "backend" / "agents" / "elena_foundry_id.txt"
        config_path.write_text(agent_id)
        logger.info(f"   Agent ID saved to: {config_path}")
        
        return agent_id
        
    except httpx.HTTPStatusError as e:
        logger.error(f"Failed to create Elena in Foundry: {e.response.status_code}")
        logger.error(f"Response: {e.response.text}")
        
        # If agent already exists, try to find it
        if e.response.status_code == 409:  # Conflict
            logger.info("Elena may already exist. Trying to list agents...")
            try:
                agents = await foundry_client.list_agents(limit=50)
                for agent in agents:
                    if agent.get("name") == "Elena" or agent.get("metadata", {}).get("agent_id") == "elena":
                        agent_id = agent.get("id")
                        logger.info(f"✅ Found existing Elena agent: {agent_id}")
                        return agent_id
            except Exception as list_error:
                logger.error(f"Failed to list agents: {list_error}")
        
        raise
    except Exception as e:
        logger.error(f"Error creating Elena in Foundry: {e}", exc_info=True)
        raise


async def main():
    """Main function."""
    try:
        agent_id = await create_elena_in_foundry()
        if agent_id:
            print(f"\n✅ Success! Elena's Foundry Agent ID: {agent_id}")
            print("\nNext steps:")
            print("1. Set ELENA_FOUNDRY_AGENT_ID environment variable")
            print("2. Create tool endpoints for Microsoft Graph functions")
            print("3. Enable USE_FOUNDRY_ELENA feature flag")
            sys.exit(0)
        else:
            print("\n❌ Failed to create Elena in Foundry")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Script failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

