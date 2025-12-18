# Virtual Context Store Implementation Plan

**Goal**: Transform Engram from a simple proxy to a "Virtual Context Store" that orchestrates data fetching from multiple providers (Zep, Postgres) using declarative definitions.

## Goal Description

We will implement the core components defined in the V1 Architecture Diagram:

1. **Context Registry**: A "Context-as-Code" system to define context requirements in Python.
2. **Context Providers**: Standardized adapters for our data sources (Zep, Postgres).
3. **Virtual Store**: The logic that resolves a Context Definition by querying the appropriate Provider.

## Proposed Changes

### [NEW] `backend/context` Module

We will create a new top-level module (or strictly organized submodule) for the Context Engine.

#### [NEW] [backend/context/registry.py](file:///Users/derek/Library/CloudStorage/OneDrive-zimaxnet/code/engram/backend/context/registry.py)

- **Purpose**: Stores "Reference Definitions".
- **Components**:
  - `ContextDefinition`: A Pydantic model describing a context type.
  - `@register_context`: A decorator to register functions as context providers.
  - `ContextRegistry`: Singleton to hold all definitions.

#### [NEW] [backend/context/providers/base.py](file:///Users/derek/Library/CloudStorage/OneDrive-zimaxnet/code/engram/backend/context/providers/base.py)

- **Purpose**: Abstract Base Class for data providers.
- **Methods**: `fetch(query)`, `stats()`.

#### [NEW] [backend/context/providers/zep.py](file:///Users/derek/Library/CloudStorage/OneDrive-zimaxnet/code/engram/backend/context/providers/zep.py)

- **Purpose**: Implementation for Zep (Hot Memory).
- **Logic**: Wraps `backend.memory.client` to conform to the Provider interface.

#### [NEW] [backend/context/store.py](file:///Users/derek/Library/CloudStorage/OneDrive-zimaxnet/code/engram/backend/context/store.py)

- **Purpose**: The "Brain".
- **Logic**:
  - `get_context(name, params)`: Looks up the definition, invokes the registered function/provider, and returns the result.
  - Handles error handling and fallback logic (e.g., if Zep is down, try Postgres?).

## Verification Plan

### Automated Tests

1. **Unit Tests**: `tests/context/test_registry.py` to verify decorators work.
2. **Integration**: Define a mock context `@register_context("test")` and retrieve it via `store.get_context("test")`.

### Manual Verification

1. Expose a new `fastapi` route `/api/v1/context/{name}`.
2. Call it locally via Curl.
