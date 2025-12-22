from __future__ import annotations
import os
import sys
import asyncio
import logging
from typing import Union

from azure.core.credentials import AzureKeyCredential
from azure.identity.aio import DefaultAzureCredential
from azure.ai.voicelive.aio import connect
from azure.ai.voicelive.models import RequestSession, Modality, ServerEventType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_test():
    # Load from Env (simulated)
    endpoint = os.environ.get("AZURE_VOICELIVE_ENDPOINT")
    model = os.environ.get("AZURE_VOICELIVE_MODEL")
    key = os.environ.get("AZURE_VOICELIVE_API_KEY") # We will pass this if provided

    print(f"Connecting to: {endpoint} Model: {model}")

    if key:
        credential = AzureKeyCredential(key)
        print("Using API Key")
    else:
        credential = DefaultAzureCredential()
        print("Using Default Credentials")

    try:
        async with connect(
            endpoint=endpoint,
            credential=credential,
            model=model,
             # Note: The SDK 'connect' might look for AZURE_VOICELIVE_API_VERSION in os.environ?
             # Or we might need to pass api_version if supported? 
             # Checking source code of 'connect' is hard, but we rely on Env vars.
        ) as connection:
            print("Successfully Connected!")
            print(f"Session ID: {connection.session.id}")
            
            # Setup simple session to confirm it's real
            # await connection.session.update(session=RequestSession(modalities=[Modality.TEXT]))
            # print("Session Updated.")
            
    except Exception as e:
        print(f"Connection Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_test())
