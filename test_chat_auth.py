import asyncio
import httpx
import sys

async def test_chat():
    url = "https://staging-env-api.gentleriver-dd0de193.eastus2.azurecontainerapps.io/api/v1/chat"
    payload = {
        "content": "Hello, Elena. Can you tell me about the story delegation workflow?",
        "user_id": "test-user-123",
        "agent_id": "elena"
    }
    
    print(f"Sending request to {url}...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(url, json=payload)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_chat())
