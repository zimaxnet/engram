
import asyncio
import websockets
import json
import logging
import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def inspect_sdk():
    # First, verify HTTP connectivity
    url = "http://127.0.0.1:8080/health"
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url)
            logger.info(f"Health check {url}: {resp.status_code}")
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return

    uri = "ws://127.0.0.1:8080/api/v1/voice/voicelive/test-session?agent_id=elena"
    logger.info(f"Connecting to {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            logger.info("Connected!")
            
            # Send avatar_connect message to trigger introspection
            msg = {
                "type": "avatar_connect",
                "agent_id": "elena",
                "sdp": "v=0\r\no=- 12345 67890 IN IP4 127.0.0.1\r\ns=-\r\nt=0 0\r\n" # Dummy SDP
            }
            
            logger.info("Sending avatar_connect message...")
            await websocket.send(json.dumps(msg))
            
            # Wait for response
            response = await websocket.recv()
            logger.info(f"Received response: {response}")
            
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(inspect_sdk())
