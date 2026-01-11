"""
Feature Flags Configuration

Simple file-based feature flag system for:
- Gradual rollouts
- A/B testing
- Quick feature disabling in production

NIST AI RMF: MANAGE 4.1 (Incident Response) - Quick feature disable
"""

import os
import json
import logging
from typing import Any, Optional
from pathlib import Path
from functools import lru_cache

logger = logging.getLogger(__name__)


# Default flags - can be overridden by environment or config file
DEFAULT_FLAGS = {
    # Core features
    "voice_enabled": True,
    "avatar_enabled": False,  # WebRTC avatar (experimental)
    "story_generation_enabled": True,
    
    # Agents
    "agent_elena_enabled": True,
    "agent_marcus_enabled": True,
    "agent_sage_enabled": True,
    
    # Memory features
    "trisearch_enabled": True,         # Tri-Search hybrid mode
    "graph_search_enabled": True,       # Graphiti integration
    "memory_enrichment_enabled": True,  # Auto-enrich context
    
    # ETL features
    "docling_enabled": False,   # High-fidelity extraction (requires license)
    "class_a_fallback": True,   # Fall back to Unstructured for Class A
    
    # Security features
    "auth_required": True,
    "rbac_enabled": True,
    "audit_logging_enabled": True,
    
    # Experimental
    "ai_code_review_enabled": False,  # Qodo Merge integration
    "risk_scoring_enabled": True,      # PR risk scoring
    
    # Rate limiting
    "rate_limit_chat": 100,      # Requests per minute
    "rate_limit_memory": 200,    # Requests per minute
    "rate_limit_etl": 50,        # Requests per minute
}


class FeatureFlags:
    """
    Feature flag manager with environment and file-based configuration.
    
    Priority (highest to lowest):
    1. Environment variables (FEATURE_<flag_name>)
    2. Config file (config/features.json)
    3. Default values
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self._flags = DEFAULT_FLAGS.copy()
        self._config_path = config_path or os.getenv(
            "FEATURE_FLAGS_PATH",
            "config/features.json"
        )
        self._load_config()
        self._load_env_overrides()
    
    def _load_config(self):
        """Load flags from JSON config file."""
        path = Path(self._config_path)
        if path.exists():
            try:
                with open(path) as f:
                    file_flags = json.load(f)
                    self._flags.update(file_flags)
                    logger.info(f"Loaded {len(file_flags)} feature flags from {path}")
            except Exception as e:
                logger.warning(f"Failed to load feature flags from {path}: {e}")
    
    def _load_env_overrides(self):
        """Load flags from environment variables."""
        for key in self._flags.keys():
            env_key = f"FEATURE_{key.upper()}"
            env_value = os.getenv(env_key)
            
            if env_value is not None:
                # Parse boolean and numeric values
                if env_value.lower() in ("true", "1", "yes"):
                    self._flags[key] = True
                elif env_value.lower() in ("false", "0", "no"):
                    self._flags[key] = False
                elif env_value.isdigit():
                    self._flags[key] = int(env_value)
                else:
                    self._flags[key] = env_value
                
                logger.debug(f"Flag override from env: {key}={self._flags[key]}")
    
    def is_enabled(self, flag_name: str) -> bool:
        """
        Check if a feature flag is enabled.
        
        Args:
            flag_name: Name of the feature flag
        
        Returns:
            True if enabled, False otherwise
        """
        value = self._flags.get(flag_name)
        
        if value is None:
            logger.warning(f"Unknown feature flag: {flag_name}")
            return False
        
        return bool(value)
    
    def get(self, flag_name: str, default: Any = None) -> Any:
        """
        Get the value of a feature flag.
        
        Args:
            flag_name: Name of the feature flag
            default: Default value if flag not found
        
        Returns:
            Flag value
        """
        return self._flags.get(flag_name, default)
    
    def all_flags(self) -> dict:
        """Return all flag values."""
        return self._flags.copy()
    
    def set_flag(self, flag_name: str, value: Any) -> None:
        """
        Dynamically set a flag value (runtime only).
        
        Use for testing or emergency overrides.
        """
        old_value = self._flags.get(flag_name)
        self._flags[flag_name] = value
        logger.info(f"Flag changed: {flag_name} = {value} (was: {old_value})")


# Singleton instance
@lru_cache(maxsize=1)
def get_feature_flags() -> FeatureFlags:
    """Get the singleton feature flags instance."""
    return FeatureFlags()


# Convenience functions
def is_enabled(flag_name: str) -> bool:
    """Check if a feature is enabled."""
    return get_feature_flags().is_enabled(flag_name)


def get_flag(flag_name: str, default: Any = None) -> Any:
    """Get a feature flag value."""
    return get_feature_flags().get(flag_name, default)


# Decorator for feature-gated endpoints
def require_feature(flag_name: str):
    """
    Decorator to gate an endpoint behind a feature flag.
    
    Usage:
        @router.get("/experimental")
        @require_feature("experimental_endpoint")
        async def experimental_endpoint():
            ...
    """
    from functools import wraps
    from fastapi import HTTPException
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not is_enabled(flag_name):
                raise HTTPException(
                    status_code=503,
                    detail=f"Feature '{flag_name}' is currently disabled"
                )
            return await func(*args, **kwargs)
        return wrapper
    return decorator
