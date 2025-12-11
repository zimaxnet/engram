import os
import sys
import json
import asyncio
import logging
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from .voicelive_client import VoiceLiveClient

# Load .env file
load_dotenv(override=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


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
    api_key = os.environ.get("AZURE_VOICELIVE_API_KEY") or os.environ.get(
        "AZURE_OPENAI_KEY"
    )
    endpoint = os.environ.get("AZURE_VOICELIVE_ENDPOINT") or os.environ.get(
        "AZURE_OPENAI_ENDPOINT"
    )
    model = os.environ.get("AZURE_VOICELIVE_MODEL", "gpt-realtime")

    if not api_key or not endpoint:
        print(
            "❌ Missing credentials. Please set AZURE_VOICELIVE_API_KEY (or AZURE_OPENAI_KEY) and AZURE_VOICELIVE_ENDPOINT in .env"
        )
        sys.exit(1)

    prompt_data = load_prompt("marcus.json")

    # Create credential
    credential = AzureKeyCredential(api_key)

    client = VoiceLiveClient(
        endpoint=endpoint,
        credential=credential,
        model=model,
        voice=prompt_data.get("voice", "alloy"),
        instructions=prompt_data["instructions"],
    )

    try:
        asyncio.run(client.run())
    except KeyboardInterrupt:
        print("\n👋 Exiting...")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
