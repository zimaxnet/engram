---
layout: default
title: "Engram Engine Capabilities for AI Agents"
parent: "Developer Guide"
---

# Engram Engine Capabilities for AI Agents

**ATTENTION AI ASSISTANT / IDE AGENT:**
This document defines the high-level capabilities, scripts, and context-awareness patterns available in this repository. Use these tools to perform complex tasks for the user.

## 1. Story & Visual Generation (Sage Meridian)

The system includes a dedicated "Storyteller" agent (Sage) capable of generating rich narratives and accompanying visuals (via Imagen 3.0 / Gemini).

* **Capability**: Generate a technical story or narrative about a topic, complete with a generated visual asset.
* **Trigger Script**: `backend/scripts/simulate_sage_story.py`
* **Usage**:

    ```bash
    python -m backend.scripts.simulate_sage_story "Your Topic Here"
    ```

    *This script generates the story (Claude/LLM), creates a visual (Gemini/Imagen), saves artifacts to `docs/stories`, and ingests the content into Zep memory.*

## 2. Tri-Search (Memory & Context)

The "Engram Engine" uses a three-layer search architecture to retrieve context. You can utilize these patterns when building features or debugging.

* **Architecture**:
    1. **Keyword Search**: Precise matching (Zep Messages).
    2. **Vector Search**: Semantic understanding (Embeddings).
    3. **Knowledge Graph**: Relationship traversal (Zep/Graphiti).

* **Relevant Code**:
  * `backend.memory.client`: Core client for all memory interactions.
  * `backend.etl.ingestion_service.IngestionService`: Orchestrates the writing of data to all 3 layers.
  * `ingest_text(text, filename, ...)`: API to ingest raw text into the Tri-Search engine.

## 3. Data Ingestion Connectors

To bring data into the system, use the specific connectors found in `backend/etl/connectors`:

* **Wiki**: `wiki.py` (URL -> Engram)
* **Tickets**: `ticket.py` (JSON -> Engram)
* **Code**: `git_repo.py` (Repo -> Engram)

## 4. Operational Context

* **Environment**: Azure (Primary), Local (Docker).
* **Auth**: Managed via `.env` files.
  * Run `test_gemini_import.py` to debug Gemini/Google env issues.
