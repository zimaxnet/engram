"""
MCP Router for Engram

Exposes Engram context and capabilities via the Model Context Protocol (MCP).
Uses SSE (Server-Sent Events) for transport.
"""

import logging
from mcp.server.fastmcp import FastMCP

from backend.core import get_settings

logger = logging.getLogger(__name__)

# Initialize FastMCP server
# This handles the JSON-RPC nuances and tool/resource registration
mcp_server = FastMCP("Engram MCP Server")

@mcp_server.resource("context://current")
async def get_current_context() -> str:
    """Get the current test context"""
    return "Engram MCP Context: Active"

