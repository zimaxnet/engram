# Diagrams Directory

This directory contains JSON specifications for Nano Banana Pro diagrams.

## Diagram Organization

### JSON Specifications
- **Location:** `docs/diagrams/*.json`
- **Purpose:** JSON specifications for Nano Banana Pro (Gemini 3) diagram generation
- **Usage:** These JSON files are used by Sage or Nano Banana Pro to generate actual diagram images

### Generated Diagram Images
- **Location:** `docs/assets/diagrams/*.png`
- **Purpose:** Generated PNG images from the JSON specifications
- **Naming Convention:** Match the JSON filename (e.g., `memory-enrichment-workflow-diagram.json` → `memory-enrichment-workflow-diagram.png` or `engram-memory-enrichment-workflow.png`)

## Current Diagrams

### Memory Enrichment Workflow
- **JSON:** `memory-enrichment-workflow-diagram.json`
- **Image:** `docs/assets/diagrams/engram-memory-enrichment-workflow.png` (to be generated)
- **Description:** Shows how sessions, episodes, stories, and chat interactions work together to enrich Zep memory

### Other Architecture Diagrams
- Architecture diagram images are in `docs/architecture/*.png`
- Diagram JSON specs may be in `docs/architecture/*.json` or `docs/assets/diagrams/*.json`

## Generating Diagrams

To generate a diagram from a JSON specification:

1. **Using Sage Agent:**
   - Use the `create_visual` or `create_diagram` tool
   - Sage will generate the diagram image using Nano Banana Pro

2. **Using Nano Banana Pro directly:**
   - Provide the JSON specification to Nano Banana Pro
   - Save the generated PNG to `docs/assets/diagrams/`

3. **Naming Convention:**
   - Use descriptive names matching the JSON file
   - Prefix with `engram-` for consistency (optional)
   - Example: `engram-memory-enrichment-workflow.png`

## Related Documentation

- `docs/architecture/memory-enrichment-workflow.md` - Full documentation
- `docs/sop/sage_nano_banana.md` - Sage Nano Banana Pro SOP
- `backend/llm/gemini_client.py` - Diagram generation implementation

