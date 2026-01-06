from __future__ import annotations

from typing import Any


# Centralized environment metadata used by both CLI tools and the backend API.
ENVIRONMENT_PRESETS: dict[str, dict[str, str]] = {
    "local": {
        "ZEP_API_URL": "http://localhost:8000",
        "description": "Local development Zep",
    },
    "azure": {
        "ZEP_API_URL": "https://zep.engram.work",
        "description": "Azure Container Apps (Production)",
    },
    "staging": {
        "ZEP_API_URL": "https://zep-staging.engram.work",
        "description": "Azure Staging Environment",
    },
}


def list_environment_presets() -> list[dict[str, Any]]:
    return [
        {
            "name": name,
            "zep_api_url": preset.get("ZEP_API_URL", ""),
            "description": preset.get("description", ""),
        }
        for name, preset in ENVIRONMENT_PRESETS.items()
    ]
