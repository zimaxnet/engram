from __future__ import annotations

import os
import sys
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


def apply_environment(env_name: str, *, strict: bool = True, default: str = "azure") -> str:
    """Set ZEP_API_URL from a named preset and return the resolved URL.

    Used by CLI scripts and other tooling so that environment selection is consistent.
    """

    if env_name not in ENVIRONMENT_PRESETS:
        if strict:
            print(f"❌ Unknown environment: {env_name}", file=sys.stderr)
            print(f"   Available: {', '.join(ENVIRONMENT_PRESETS.keys())}", file=sys.stderr)
            raise SystemExit(1)

        env_name = default

    zep_url = ENVIRONMENT_PRESETS[env_name]["ZEP_API_URL"]
    os.environ["ZEP_API_URL"] = zep_url
    return zep_url
