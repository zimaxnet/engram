# Engram System Architecture & Migration Context

## High-Level Overview

Engram is a **Context Engineering Platform** that enables "Recursive Self-Awareness" for AI agents. The system has migrated from a legacy mock-based architecture to a production-grade "Brain + Spine" design.

## Core Components (The "Brain")

1. **Zep (Memory Layer):**
    * **Function:** Stores long-term episodic memory (chat history) and semantic memory (documents).
    * **Migration:** Moved from local `MockMemory` to production Zep (`zep.engram.work`).
    * **Access:** Agents search Zep to retrieve relevant facts and past conversations.
    * **Data Structure:** Uses a 4-layer context schema (Entity, Session, Episode, Fact).

2. **Unstructured.io (ETL Layer):**
    * **Function:** Ingests raw documents (PDF, HTML, MD).
    * **Process:** Partitions documents -> chunks by title -> generates encodings.
    * **Output:** Chunks are stored in Zep as "facts" linked to their source document.
    * **Key Benefit:** Allows agents to "read" the entire project wiki and technical guides.

## Core Components (The "Spine")

3. **Temporal (Workflow Layer):**
    * **Function:** Orchestrates long-running, durable workflows.
    * **Role:** Guarantees that multi-step agent tasks (like "research topic X" or "deploy service Y") run to completion, even if servers restart.
    * **Integration:** Agents signal workflows to start tasks; workflows query agents for decisions.

## Data Flow: How Chat Enters the System

1. **User Message:** User sends a message via the Frontend (Azure Static Web App).
2. **API Handling:** `backend/api/routers/chat.py` receives the request.
3. **Memory Search:** The system automatically queries Zep for relevant context *before* generating a response.
4. **Agent Processing:** The Agent (Elena or Marcus) processes the user input + retrieved context.
5. **Storage:** The user prompt and agent response are asynchronously saved to Zep as a new "Episode Message", reinforcing the memory loop.

## Key Capabilities for Customers

* **"Recursive Self-Awareness":** Agents know how they are built because they can read their own architecture docs (ingested via Unstructured).
* **Durable Execution:** Tasks don't fail silently; Temporal retries them.
* **Rich Context:** It's not just "vectors"; it's structured, graph-like memory.
