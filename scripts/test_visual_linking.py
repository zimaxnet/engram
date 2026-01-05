#!/usr/bin/env python3
"""
Test Visual Linking

Verifies that GeminiClient.generate_visual_spec correctly incorporates
architectural diagram details into the visual generation prompt.

Usage:
    export GEMINI_API_KEY="..."
    python scripts/test_visual_linking.py
"""

import asyncio
import os
import sys
import logging

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.llm.gemini_client import get_gemini_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_visual_linking")

from backend.core import get_settings

async def test_linking():
    settings = get_settings()
    if not settings.gemini_api_key:
        print("Skipping test: GEMINI_API_KEY not configured in settings")
        return

    client = get_gemini_client()
    
    topic = "The Vibe Coding Architecture"
    
    # Mock Architectural Diagram Spec
    diagram_spec = {
        "title": "Vibe Coding System",
        "theme": "cyberpunk-neon", 
        "nodes": [
            {"label": "User Intent"},
            {"label": "AI Agent Swarm"},
            {"label": "Self-Healing Codebase"},
            {"label": "Temporal Workflow"},
            {"label": "Zep Memory Bank"}
        ]
    }
    
    print(f"\n--- Testing Visual Generation for topic: '{topic}' ---")
    print(f"Input Diagram Theme: {diagram_spec['theme']}")
    print(f"Input Diagram Nodes: {[n['label'] for n in diagram_spec['nodes']]}")
    
    print("\nGenerating Visual Spec...")
    
    visual_spec = await client.generate_visual_spec(
        topic=topic,
        context="Testing visual alignment feature",
        diagram_spec=diagram_spec
    )
    
    print("\n--- Resulting Visual Spec ---")
    print(f"Title: {visual_spec.get('title')}")
    print(f"Style: {visual_spec.get('style')}")
    print(f"Colors: {visual_spec.get('colors')}")
    print(f"Elements: {visual_spec.get('elements')}")
    print(f"\nPrompt: {visual_spec.get('prompt')}")
    
    # Validation Logic
    prompt = visual_spec.get('prompt', '').lower()
    elements = [e.lower() for e in visual_spec.get('elements', [])]
    combined_text = prompt + " " + " ".join(elements)
    
    checks = []
    
    # Check 1: Should reflect the theme
    if "cyberpunk" in combined_text or "neon" in combined_text:
        checks.append("✅ Theme 'cyberpunk-neon' detected in prompt/elements")
    else:
        checks.append("❌ Theme 'cyberpunk-neon' NOT detected")
        
    # Check 2: Should mention key nodes
    found_nodes = 0
    for node in diagram_spec['nodes']:
        label = node['label'].lower()
        if label in combined_text:
            found_nodes += 1
            
    if found_nodes >= 2:
        checks.append(f"✅ Found {found_nodes}/5 architectural nodes in visual spec")
    else:
        checks.append(f"❌ Only found {found_nodes}/5 architectural nodes (Expected >= 2)")

    print("\n--- Verification Results ---")
    for check in checks:
        print(check)
        
    if "❌" in "".join(checks):
        sys.exit(1)
    else:
        print("\nSUCCESS: Visual Spec is aligned with Diagram Spec!")

if __name__ == "__main__":
    asyncio.run(test_linking())
