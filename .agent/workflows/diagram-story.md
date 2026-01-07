---
description: Generate architecture diagram, upload to Azure, and create a Sage story
---

# Architecture Diagram + Story Workflow

**Purpose**: Create technical architecture diagrams with Nano Banana Pro and have Sage write accompanying stories.

## Steps

1. **Generate JSON diagram spec** for Nano Banana Pro:

```bash
# Create a JSON file with architecture details
# Save to docs/architecture/<feature-name>-diagram.json
```

The JSON should follow this schema:

```json
{
  "name": "Feature Name Architecture",
  "version": "1.0.0",
  "description": "Description of the architecture",
  "components": {
    "component_id": {
      "name": "Component Name",
      "type": "client|server|azure_service|database",
      "responsibilities": ["..."]
    }
  },
  "flow": [
    {"step": 1, "from": "component1", "to": "component2", "action": "Description"}
  ]
}
```

1. **Render diagram with Nano Banana Pro**:
   - Open the JSON in Nano Banana Pro
   - Export as PNG to `docs/architecture/<feature-name>-architecture.png`

2. **Create architecture directory in Azure Files** (if needed):
// turbo

```bash
az storage directory create --account-name stagingenvstore --share-name docs --name architecture
```

1. **Upload diagram PNG to Azure Files**:

```bash
az storage file upload \
  --account-name stagingenvstore \
  --share-name docs \
  --source docs/architecture/<feature-name>-architecture.png \
  --path architecture/<feature-name>-architecture.png
```

1. **Upload JSON spec to Azure Files**:

```bash
az storage file upload \
  --account-name stagingenvstore \
  --share-name docs \
  --source docs/architecture/<feature-name>-diagram.json \
  --path architecture/<feature-name>-diagram.json
```

1. **Trigger Sage to write story with diagram link**:
// turbo

```bash
./scripts/api-call.sh POST /api/v1/story/create '{
  "topic": "<Feature Name> Architecture",
  "context": "Technical story about <description>. Architecture diagram: https://stagingenvstore.file.core.windows.net/docs/architecture/<feature-name>-architecture.png",
  "include_diagram": false,
  "include_image": true
}'
```

1. **Commit and push**:
// turbo

```bash
git add docs/architecture/<feature-name>* && git commit -m "docs: Add <feature> architecture diagram and story" && git push
```

## Azure Files URLs

- **Storage Account**: `stagingenvstore`
- **Share**: `docs`
- **Path**: `architecture/`
- **URL Format**: `https://stagingenvstore.file.core.windows.net/docs/architecture/<filename>`

## Example: WebRTC Avatar

```bash
# Files created:
docs/architecture/webrtc-avatar-diagram.json        # JSON spec for Nano Banana Pro
docs/architecture/engram-webrtc-avatar-video-archetecture.png  # Rendered PNG

# Upload commands:
az storage file upload --account-name stagingenvstore --share-name docs \
  --source docs/architecture/engram-webrtc-avatar-video-archetecture.png \
  --path architecture/engram-webrtc-avatar-video-archetecture.png

# Story generation:
./scripts/api-call.sh POST /api/v1/story/create '{
  "topic": "WebRTC Avatar Video Architecture for Elena",
  "context": "Diagram: https://stagingenvstore.file.core.windows.net/docs/architecture/engram-webrtc-avatar-video-archetecture.png",
  "include_diagram": false,
  "include_image": true
}'
```
