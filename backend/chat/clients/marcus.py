import os
import sys
import json
from dotenv import load_dotenv
from .chat_client import ChatClient

# Load .env file
# Go up two levels to find .env in backend/chat/
base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(base_path, ".env"), override=True)

def load_prompt(filename):
    try:
        path = os.path.join(base_path, "prompts", filename)
        with open(path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading prompt {filename}: {e}")
        sys.exit(1)

def main():
    api_key = os.environ.get("AZURE_OPENAI_API_KEY")
    endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    model = os.environ.get("AZURE_OPENAI_DEPLOYMENT_MODEL", "gpt-5.1-chat")
    
    if not api_key or not endpoint:
        print("❌ Missing credentials. Please ensure AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT are set in backend/chat/.env")
        sys.exit(1)
 
    prompt_data = load_prompt("marcus.json")
    
    client = ChatClient(
        endpoint=endpoint,
        api_key=api_key,
        model=model,
        system_prompt=prompt_data["instructions"]
    )
    
    client.run()

if __name__ == "__main__":
    main()
