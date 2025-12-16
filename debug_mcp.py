
from mcp.server.fastmcp import FastMCP
import inspect

server = FastMCP("test")
print(f"Type: {type(server.sse_app)}")
try:
    print(f"Signature: {inspect.signature(server.sse_app)}")
except Exception as e:
    print(f"Could not get signature: {e}")

print(f"Is Coroutine: {inspect.iscoroutinefunction(server.sse_app)}")
