# Engram Memory Architecture: Zep & Agents

## Overview

Engram uses **Zep** as its long-term memory store. This allows agents like Elena, Marcus, and Sage to recall past interactions, facts about the user, and context across different conversations.

## Core Concepts

### 1. Sessions (`session_id`)

A **Session** is the top-level container for a conversation thread.

* **Creation**: Identifying a unique interaction stream.
* **Frontend**: When a user clicks "New Chat", a new UUID is generated (e.g., `v3-sage-origin`).
* **Role**: It isolates context. Agents only see the immediate history of the *current* session strictly.
* **Zep**: Zep indexes the entire session for semantic search, allowing agents to "recall" information from *other* past sessions if relevant.

### 2. Episodes

An **Episode** is a semantic sub-segment of a Session, managed automatically by Zep.

* **What it is**: As a conversation grows, Zep breaks it down into "episodes" (e.g., "Discussing Project X", then "Switching to Project Y").
* **Usage**: Agents don't manage episodes directly. Zep uses them to improve retrieval accuracy, so the agent retrieves the relevant *cluster* of turns rather than just keyword matches.

### 3. Facts & Entities

Zep automatically extracts:

* **Entities**: People, Organizations, Locations (e.g., "Engram", "Marcus").
* **Facts**: Statements about the user or world (e.g., "User prefers Python", "Project deadline is Friday").
* **Relevance**: When Sage or Elena starts a turn, they query Zep for *facts* relevant to the current user input to personalize the response.

## Sage Meridian & Memory

Sage interacts with Zep exactly like the other agents, even though he uses different LLMs (Claude/Gemini) for his work.

### The Flow

1. **Input**: User sends "Create an origin story." within Session `A`.
2. **Recall**: Sage queries Zep for Session `A` history + relevant Facts from *all* sessions.
3. **Reasoning (Claude)**: Sage uses this context to draft the story.
4. **Diagram (Gemini)**: Sage generates the diagram code.
5. **Output**: Sage sends the final response to the user.
6. **Persistence**: The backend (`BaseAgent.memorize_turn`) sends the *text* of the conversation (User request + Sage response) to Zep.

### What is Stored?

* **Stored**: The chat transcript ("Create a story..." -> "Here is the story...").
* **Not Stored in Zep**: The actual `.md` or `.png` files generated. These go to **OneDrive/Disk**. Zep only stores the *conversation* about them.

## VoiceLive Memory

Voice interactions are also persisted to Zep:

1. **Transcripts**: The text-to-speech and speech-to-text transcripts are saved as standard chat turns.
2. **Context**: The `session_id` used for the voice call determines which memory bucket is used.
3. **Cross-Channel**: If you use the same `session_id` for Chat and Voice, the agent will remember the context across both modes.
