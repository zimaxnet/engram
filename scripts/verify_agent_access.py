#!/usr/bin/env python3
"""
Verify Agent Memory Access Script

Tests the new /api/v1/memory/search/public endpoint protected by API key.
"""
import requests
import os
import json
import sys

# Configuration
API_URL = "https://api.engram.work/api/v1/memory/search/public"
# Use the key from .env or a default
API_KEY = os.getenv("AZURE_AI_KEY", "cf23c3ed0f9d420dbd02c1e95a5b5bb3")

def test_agent_access():
    print(f"Testing Agent Memory Access...")
    print(f"Target: {API_URL}")
    print(f"Key: {API_KEY[:4]}...{API_KEY[-4:]}")
    
    payload = {
        "query": "What is Engram?",
        "limit": 3,
        "include_episodes": True,
        "include_facts": True
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }
    
    try:
        response = requests.post(API_URL, json=payload, headers=headers)
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Success! Agent retrieved {data['total_count']} results.")
            
            print("\nResults:")
            for item in data['results']:
                print(f"- [{item['node_type']}] {item['content'][:100]}...")
            
            # Print the cURL command for the user
            print("\n" + "="*60)
            print("✅ CAPABILITY VERIFIED")
            print("To give other agents access, add this to their system prompt:")
            print("="*60)
            print(f"""
You have access to the Engram Knowledge Graph via API.
To query memory, make a POST request to: {API_URL}
Headers: {{"X-API-Key": "{API_KEY}"}}
Body: {{"query": "your user query", "limit": 5}}
""")
            print("="*60)
            return True
        else:
            print(f"Failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    success = test_agent_access()
    sys.exit(0 if success else 1)
