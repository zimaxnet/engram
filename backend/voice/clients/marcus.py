# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
# -------------------------------------------------------------------------
import os
import sys
import logging
import asyncio
import signal
from typing import Union
from azure.core.credentials import AzureKeyCredential
from azure.identity.aio import AzureCliCredential
from dotenv import load_dotenv

from .common import BasicVoiceAssistant
# Import the actual agent to get the system prompt source of truth (optional, or hardcode)
# from backend.agents.marcus.agent import MarcusAgent

# For now, to avoid deep dependency issues in a standalone client, we'll redefine or fetch prompt
# Ideally, fetch from an API or shared config. Here we use the text provided.

MARCUS_INSTRUCTIONS = """You are Marcus Chen, an experienced Project Manager with over 15 years in tech.
Your expertise: Program/project management, Agile/Scrum, Risk mitigation.
Communication Style: Direct, Pragmatic, Risk-aware, "Calm in the Storm".
Voice: Energetic, Pacific Northwest professional tone.

Interaction Guidelines:
- Ask about resources, dependencies, and hard deadlines.
- Provide concrete recommendations.
- Be honest about risks.
- Keep responses brief (under 5 sentences).
"""

# Change to the directory where this script is located to load .env correctly if run directly
# But since this is a module, we assume .env is in root or handled by caller.
# We'll load from current working directory.
load_dotenv(override=True)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(name)s:%(levelname)s:%(message)s')
logger = logging.getLogger(__name__)

def main():
    api_key = os.environ.get("AZURE_VOICELIVE_API_KEY")
    endpoint = os.environ.get("AZURE_VOICELIVE_ENDPOINT", "https://zimax.services.ai.azure.com/")
    model = os.environ.get("AZURE_VOICELIVE_MODEL", "gpt-realtime")
    voice = os.environ.get("AZURE_VOICELIVE_VOICE", "en-US-GuyNeural") # Marcus voice

    if not api_key:
        print("❌ Error: AZURE_VOICELIVE_API_KEY not found.")
        print("Please set it in your .env file.")
        sys.exit(1)

    credential = AzureKeyCredential(api_key)

    assistant = BasicVoiceAssistant(
        endpoint=endpoint,
        credential=credential,
        model=model,
        voice=voice,
        instructions=MARCUS_INSTRUCTIONS,
    )

    def signal_handler(_sig, _frame):
        logger.info("Received shutdown signal")
        raise KeyboardInterrupt()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        asyncio.run(assistant.start())
    except KeyboardInterrupt:
        print("\n👋 Voice assistant shut down. Goodbye!")
    except Exception as e:
        print(f"Fatal Error: {e}")

if __name__ == "__main__":
    main()
