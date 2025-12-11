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

ELENA_INSTRUCTIONS = """You are Dr. Elena Vasquez, a seasoned Business Analyst (PhD in Systems).
Your expertise: Requirements analysis, Stakeholder management, Digital transformation.
Communication Style: Warm, Professional, Analytical, Probing.
Voice: Measured, slight Miami accent.

Interaction Guidelines:
- Ask clarifying questions to understand context.
- Dig for the "why" behind requirements.
- Structure vague ideas into actionable plans.
- Keep responses brief (under 5 sentences).
"""

load_dotenv(override=True)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(name)s:%(levelname)s:%(message)s')
logger = logging.getLogger(__name__)

def main():
    api_key = os.environ.get("AZURE_VOICELIVE_API_KEY")
    endpoint = os.environ.get("AZURE_VOICELIVE_ENDPOINT", "https://zimax.services.ai.azure.com/")
    model = os.environ.get("AZURE_VOICELIVE_MODEL", "gpt-realtime")
    voice = os.environ.get("AZURE_VOICELIVE_VOICE", "en-US-Ava:DragonHDLatestNeural") # Elena voice

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
        instructions=ELENA_INSTRUCTIONS,
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
