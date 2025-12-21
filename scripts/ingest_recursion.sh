#!/bin/bash

ZEP_URL="https://staging-env-zep.gentleriver-dd0de193.eastus2.azurecontainerapps.io"
SESSION_ID="sess-recursion-002"

echo "Creating Session $SESSION_ID..."
curl -X POST "$ZEP_URL/api/v1/sessions" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "'"$SESSION_ID"'",
    "user_id": "derek",
    "metadata": {
        "type": "recursive_debugging",
        "topic": "sage_visual_troubleshooting",
        "system": "engram"
    }
  }'

echo -e "\n\nAdding Memory..."
curl -X POST "$ZEP_URL/api/v1/sessions/$SESSION_ID/memory" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
        {
            "role": "system",
            "content": "You are Engram, an AI system engaging in recursive self-awareness. You document your own troubleshooting and evolution."
        },
        {
            "role": "user",
            "content": "Report on the recent outage regarding Sage and Elena agents."
        },
        {
            "role": "assistant",
            "content": "Issue: 401 Unauthorized errors on Sage (Storyteller) and Elena (Business Analyst). Recovery completed via two fixes: 1. Implemented ClaudeLangChainAdapter for Sage to bypass failing default Azure AI client. 2. Corrected Azure AI Endpoint secret for Elena to match APIM Gateway."
        },
        {
            "role": "user",
            "content": "What was the status of VoiceLive?"
        },
        {
            "role": "assistant",
            "content": "VoiceLive audio output was silent. Cause: Direct Foundry endpoint configuration was incompatible with current secrets. Fix: Routed VoiceLive through APIM Gateway (https://zimax-gw...). Audio delta stream verified."
        },
        {
            "role": "user",
            "content": "Is Zep memory functional?"
        },
         {
            "role": "assistant",
            "content": "Affirmative. This very conversation is being ingested into Zep Session '"$SESSION_ID"' to demonstrate recursive memory capability."
        }
    ]
  }'

echo -e "\n\nRetrieving Session..."
curl -s "$ZEP_URL/api/v1/sessions/$SESSION_ID" | grep "session_id"
