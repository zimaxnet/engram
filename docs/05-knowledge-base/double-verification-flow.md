---
layout: default
title: "Standard Operating Procedure: Double Tri-Search Verification"
parent: "Knowledge Base"
---

# Standard Operating Procedure: Double Tri-Search Verification

## Overview

To ensure the highest accuracy and depth in automated storytelling, Engram enforces a **"Double Tri-Search"** verification process. This ensures that information is not only retrieved by the delegating agent (Elena) but also independently verified and enriched by the executing agent (Sage) before content generation.

## The Flow

### 1. Primary Search & Delegation (Elena)

- **Role**: Business Analyst / Orchestrator
- **Trigger**: User request (e.g., "Tell me a story about...")
- **Action**:
  1. **Analyze Request**: Identify key entities.
  2. **Tri-Search**: execute `search_memory` (Keyword + Vector + Graph).
  3. **Synthesize**: Create a rich context packet.
  4. **Delegate**: Call `delegate_to_sage(topic, context)`.

### 2. Secondary Verification Search (Sage)

- **Role**: Storyteller / Verifier
- **Trigger**: Receipt of delegation.
- **Action**:
  1. **Receive Context**: Accept topic and context from Elena.
  2. **Verification Search**: *Independent* execution of `search_memory` using the topic as the query.
      - **Goal**: Find "narrative threads" or adjacent facts potentially missed in the initial pass.
      - **Pattern**: "Trust but Verify".
  3. **Synthesis**: Combine [Elena's Context] + [Sage's Findings].
  4. **Generation**: Feed combined context to Claude Opus.

## Technical Implementation

- **Elena**: Prompt instruction to "always search before delegating".
- **Sage**: Enforced code-level step in `generate_story_activity`.
  - The workflow *must* perform a lookup on the `topic` before calling the LLM.
  - Verification results are appended to the context with a header `## Verification Context (Sage Tri-Search)`.

## Benefits

1. **Reduced Hallucination**: Two independent retrieval passes reduce the chance of missing critical facts.
2. **Contextual Depth**: Elena finds "business" context; Sage finds "narrative" context.
3. **Resilience**: If one agent's search fails or is shallow, the second provides a safety net.
