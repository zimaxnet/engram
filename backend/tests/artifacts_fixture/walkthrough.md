# Walkthrough: Backend Fix & Context Architecture

## 1. Backend Crash Resolution

The persistent failure of the backend API (and E2E tests) was traced to:

- **Root Cause**: Missing system library `libmagic1` in the Docker container. This is required by `unstructured` (ETL pipeline).
- **Fix**: Updated `backend/Dockerfile` to install `libmagic1`, `poppler-utils`, and `tesseract-ocr`.
- **Status**: Verified locally. Containers pass health checks.

## 2. Virtual Context Store Implementation

We have successfully implemented the **Virtual Context Store**, transforming Engram into a context-aware orchestrator.

### Components

1. **Registry (`backend/context/registry.py`)**:
    - Implements "Context-as-Code".
    - Developers use `@register_context` to define reusable context logic.
    - Example: `@register_context("project_status")`

2. **Orchestrator (`backend/context/store.py`)**:
    - The "Brain" that resolves context requests.
    - Dispatches to Python functions or physical Providers (Zep).

3. **Zep Provider (`backend/context/providers/zep.py`)**:
    - Wraps our Zep Memory Client.
    - Exposes semantic memory search via the standard Provider interface.

4. **MCP Integration (`backend/api/routers/mcp_server.py`)**:
    - **Tools**: `get_context(name, params)`, `list_contexts`.
    - **Resources**: `context://{name}`.
    - **Impact**: Any MCP Client (Clause, Cursor, etc.) can now query Engram's Virtual Context.

## 3. MCP Java SDK Research

Research confirmed the **MCP Java SDK** is the strategic key for enterprise integration. We have defined a "Dual-Stack" strategy where Engram (Python) handles logic and Legacy Apps (Java) act as data connectors.

## Verification

- **Local Container**: Verified API startup works with the new Docker image.
- **Context Logic**: Verified via `tests/test_context_store_manual.py`.
- **MCP Logic**: Verified via `tests/test_mcp_context_exposure.py`.
