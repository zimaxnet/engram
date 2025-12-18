# Research: MCP Java SDK for Enterprise Data

**Objective**: Evaluate the [MCP Java SDK](https://github.com/modelcontextprotocol/java-sdk) for connecting Engram to enterprise environments (which are predominantly Java/Spring).

## Executive Summary

The MCP Java SDK is mature and capable. It is critical for Engram's "Virtual Context Store" strategy because it allows us to turn **legacy Spring Boot applications** directly into MCP Servers. This means we don't need to write Python connectors for every internal microservice; we just add a library to the existing Java service.

## Key Findings

### 1. Spring Boot is First-Class

- The SDK includes `mcp-spring-webmvc` and `mcp-spring-webflux`.
- **Impact**: Standard Enterprise Java apps (Tomcat/Jetty or Netty) can expose MCP endpoints (`/mcp/sse`) with minimal configuration.
- **Enterprise Standard**: Most Fortune 500 data lives behind Spring Security. This SDK integrates with it, solving the "how do we secure agent access?" problem natively.

### 2. Transport Support

- **SSE (Server-Sent Events)**: Fully supported. This is the primary transport for remote agents (like Engram's Cloud) to talk to on-prem connectors.
- **Stdio**: Supported. Useful for local "sidecar" deployments where an agent runs effectively alongside the Java process.

### 3. Integration with AI Ecosystem

- **Spring AI**: The SDK is maintained in collaboration with Spring AI. This is a massive endorsement for stability.
- **LangChain4j**: Community support exists to bridge standard LLM chains into MCP tools.

## Strategic Recommendation

**"Dual-Stack" Virtual Store**:

1. **Python Core (Engram)**: Handles the "Brain" (Orchestration, Lineage, Fast Memory).
2. **Java Edge (Connectors)**: Use the Java SDK to build "Data Gateways" closer to the source (Mainframes, SQL, ERPs).

### Proposed Connector Pattern

Instead of:
`Engram (Python) -> SQL Driver -> Legacy DB`

Use:
`Engram (Python) -> MCP Client -> [Legacy App + MCP Java SDK] -> Legacy DB`

**Benefit**: The Legacy App likely already handles the complex business logic, authorization, and schema mapping. Exposing that as an MCP resource (`resource://orders/123`) is safer and faster than reverse-engineering the DB.
