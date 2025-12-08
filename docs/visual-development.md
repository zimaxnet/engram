---
layout: default
title: Visual Development Guide
---

# Visual Development Guide

This guide documents the visual assets for the Engram platform and provides JSON prompts for generating consistent imagery using AI image generation tools like Nano Banana Pro.

## Platform Visuals

### 1. Platform Architecture Diagram

![Engram Platform Architecture](assets/images/engram-platform-architecture.png)

**Description**: A comprehensive visual representation of the Engram platform showing the Brain + Spine architecture, data flows, and component interactions.

#### JSON Prompt

```json
{
  "diagram_type": "technical_architecture",
  "title": "Engram Context Engineering Platform",
  "style": {
    "aesthetic": "modern_tech_dark_theme",
    "color_scheme": {
      "background": "#0a0e1a",
      "primary": "#00d4ff",
      "secondary": "#a855f7",
      "accent": "#10b981",
      "text": "#e2e8f0"
    },
    "visual_style": "glassmorphism_with_glow"
  },
  "components": [
    {
      "name": "Frontend",
      "type": "layer",
      "position": "top",
      "elements": ["React UI", "Voice Controls", "Avatar Display"],
      "color": "#3b82f6"
    },
    {
      "name": "API Gateway",
      "type": "middleware",
      "position": "upper-middle",
      "elements": ["FastAPI", "Auth Middleware", "RBAC"],
      "color": "#10b981"
    },
    {
      "name": "Brain Layer",
      "type": "core_component",
      "position": "middle-left",
      "elements": ["LangGraph Agents", "Elena", "Marcus", "Router"],
      "color": "#00d4ff",
      "glow": true
    },
    {
      "name": "Spine Layer",
      "type": "core_component",
      "position": "middle-center",
      "elements": ["Temporal Workflows", "Activities", "Signals"],
      "color": "#a855f7",
      "glow": true
    },
    {
      "name": "Memory Layer",
      "type": "core_component",
      "position": "middle-right",
      "elements": ["Zep", "Graphiti", "Vector Store"],
      "color": "#f59e0b",
      "glow": true
    },
    {
      "name": "Infrastructure",
      "type": "layer",
      "position": "bottom",
      "elements": ["Azure Container Apps", "PostgreSQL", "Key Vault"],
      "color": "#6b7280"
    }
  ],
  "connections": [
    {"from": "Frontend", "to": "API Gateway", "type": "https"},
    {"from": "API Gateway", "to": "Brain Layer", "type": "internal"},
    {"from": "Brain Layer", "to": "Spine Layer", "type": "workflow"},
    {"from": "Spine Layer", "to": "Memory Layer", "type": "activity"},
    {"from": "All", "to": "Infrastructure", "type": "deployment"}
  ],
  "annotations": [
    {"text": "Context Engineering", "position": "center", "style": "highlight"},
    {"text": "4-Layer Context Schema", "position": "below-brain", "style": "callout"}
  ]
}
```

---

### 2. Voice Interaction Flow

![Voice Interaction Flow](assets/images/voice-interaction-flow.png)

**Description**: Shows the complete voice interaction pipeline from user speech to avatar response with lip-sync.

#### JSON Prompt

```json
{
  "diagram_type": "flow_diagram",
  "title": "Voice Interaction Pipeline",
  "style": {
    "aesthetic": "modern_tech_dark_theme",
    "flow_direction": "left_to_right",
    "color_scheme": {
      "background": "#0a0e1a",
      "flow_lines": "#00d4ff",
      "components": "#1a1f35"
    }
  },
  "stages": [
    {
      "name": "User Input",
      "icon": "microphone",
      "description": "Voice capture",
      "color": "#10b981"
    },
    {
      "name": "Speech-to-Text",
      "icon": "waveform_to_text",
      "description": "Azure Speech STT",
      "color": "#3b82f6"
    },
    {
      "name": "Agent Processing",
      "icon": "brain_cog",
      "description": "LangGraph reasoning",
      "color": "#00d4ff"
    },
    {
      "name": "Text-to-Speech",
      "icon": "text_to_waveform",
      "description": "Azure Speech TTS + Visemes",
      "color": "#a855f7"
    },
    {
      "name": "Avatar Render",
      "icon": "avatar_speaking",
      "description": "Lip-sync animation",
      "color": "#f59e0b"
    }
  ],
  "data_labels": [
    {"between": [0, 1], "label": "Audio WAV"},
    {"between": [1, 2], "label": "Transcript"},
    {"between": [2, 3], "label": "Response Text"},
    {"between": [3, 4], "label": "Audio + Visemes"}
  ]
}
```

---

### 3. Agent Workflow Diagram

![Agent Workflow Diagram](assets/images/agent-workflow-diagram.png)

**Description**: Illustrates how Elena and Marcus collaborate with handoff patterns.

#### JSON Prompt

```json
{
  "diagram_type": "collaboration_flow",
  "title": "Agent Collaboration Workflow",
  "style": {
    "aesthetic": "modern_tech_dark_theme",
    "layout": "circular_with_center"
  },
  "agents": [
    {
      "name": "Elena",
      "role": "Business Analyst",
      "position": "left",
      "color": "#00d4ff",
      "avatar": "elena_portrait"
    },
    {
      "name": "Marcus",
      "role": "Project Manager",
      "position": "right",
      "color": "#a855f7",
      "avatar": "marcus_portrait"
    }
  ],
  "center_element": {
    "name": "Agent Router",
    "description": "Context-aware routing",
    "icon": "router_switch"
  },
  "workflows": [
    {
      "trigger": "Requirements question",
      "from": "User",
      "to": "Elena",
      "arrow_style": "solid"
    },
    {
      "trigger": "Planning question",
      "from": "User",
      "to": "Marcus",
      "arrow_style": "solid"
    },
    {
      "trigger": "Handoff: plan this",
      "from": "Elena",
      "to": "Marcus",
      "arrow_style": "dashed",
      "label": "Context Transfer"
    },
    {
      "trigger": "Handoff: analyze requirements",
      "from": "Marcus",
      "to": "Elena",
      "arrow_style": "dashed",
      "label": "Context Transfer"
    }
  ]
}
```

---

### 4. Context Schema Visualization

![4-Layer Context Schema](assets/images/context-schema.png)

**Description**: Visual representation of the 4-layer EnterpriseContext schema.

#### JSON Prompt

```json
{
  "diagram_type": "layered_schema",
  "title": "4-Layer Enterprise Context Schema",
  "style": {
    "aesthetic": "modern_tech_dark_theme",
    "layout": "stacked_layers_3d"
  },
  "layers": [
    {
      "number": 1,
      "name": "Security Context",
      "color": "#ef4444",
      "fields": ["user_id", "tenant_id", "roles", "scopes", "session_id"],
      "description": "WHO is asking"
    },
    {
      "number": 2,
      "name": "Episodic State",
      "color": "#f59e0b",
      "fields": ["conversation_id", "recent_turns", "summary"],
      "description": "WHAT happened recently"
    },
    {
      "number": 3,
      "name": "Semantic Knowledge",
      "color": "#10b981",
      "fields": ["retrieved_facts", "entity_context", "graph_nodes"],
      "description": "WHAT we know"
    },
    {
      "number": 4,
      "name": "Operational State",
      "color": "#3b82f6",
      "fields": ["current_plan", "active_tools", "workflow_id", "status"],
      "description": "WHAT we're doing"
    }
  ],
  "flow_arrow": {
    "direction": "top_to_bottom",
    "label": "Context flows through all layers"
  }
}
```

---

### 5. Engram Logo

![Engram Logo](assets/images/engram-logo.png)

**Description**: The Engram platform logo representing memory and neural connections.

#### JSON Prompt

```json
{
  "logo_type": "abstract_tech",
  "name": "Engram",
  "concept": "memory_trace_neural_pathway",
  "style": {
    "aesthetic": "minimalist_futuristic",
    "color_palette": {
      "primary": "#00d4ff",
      "secondary": "#a855f7",
      "glow": true
    }
  },
  "elements": {
    "primary_shape": "stylized_brain_outline",
    "accent": "neural_pathway_traces",
    "integration": "memory_node_constellation"
  },
  "variations": [
    {"type": "full_color", "background": "dark"},
    {"type": "monochrome", "background": "light"},
    {"type": "icon_only", "size": "favicon"}
  ]
}
```

---

## Image Asset Locations

| Asset | Path | Resolution | Format |
|-------|------|------------|--------|
| Platform Architecture | `assets/images/engram-platform-architecture.png` | 1920x1080 | PNG |
| Voice Interaction Flow | `assets/images/voice-interaction-flow.png` | 1920x600 | PNG |
| Agent Workflow | `assets/images/agent-workflow-diagram.png` | 1200x800 | PNG |
| Context Schema | `assets/images/context-schema.png` | 1200x900 | PNG |
| Elena Portrait | `assets/images/elena-portrait.png` | 512x512 | PNG |
| Marcus Portrait | `assets/images/marcus-portrait.png` | 512x512 | PNG |
| Engram Logo | `assets/images/engram-logo.png` | 800x200 | PNG |
| Logo Icon | `assets/images/engram-icon.png` | 512x512 | PNG |

---

## Generating New Visuals

To generate consistent visuals for the Engram platform:

1. **Use the JSON prompts** above as templates
2. **Maintain the color scheme**:
   - Background: `#0a0e1a`
   - Primary (Cyan): `#00d4ff`
   - Secondary (Purple): `#a855f7`
   - Accent (Green): `#10b981`
   - Text: `#e2e8f0`
3. **Apply glassmorphism** effects with subtle glows
4. **Export at appropriate resolutions** for web use

### Tips for Nano Banana Pro

- Use `"render_style": "photorealistic_with_slight_stylization"` for portraits
- Use `"aesthetic": "modern_tech_dark_theme"` for diagrams
- Include `"glow": true` for interactive elements
- Specify exact hex colors for brand consistency

