import os
import sys
import json
import asyncio
import logging
from dotenv import load_dotenv
from .common import RealtimeClient

# Load .env file
load_dotenv(override=True)

def load_prompt(filename):
    try:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(base_path, "prompts", filename)
        with open(path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading prompt {filename}: {e}")
        sys.exit(1)

def main():
    api_key = os.environ.get("AZURE_OPENAI_KEY")
    endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-realtime-preview")
    
    if not api_key or not endpoint:
        print("❌ Missing credentials. Please set AZURE_OPENAI_KEY and AZURE_OPENAI_ENDPOINT in .env")
        sys.exit(1)

    prompt_data = load_prompt("marcus.json")
    
    client = RealtimeClient(
        endpoint=endpoint,
        api_key=api_key,
        deployment_name=deployment,
        system_message=prompt_data["instructions"],
        voice=prompt_data.get("voice", "alloy")
    )

    try:
        asyncio.run(client.run())
    except KeyboardInterrupt:
        print("\n👋 Exiting...")

if __name__ == "__main__":
    main()
