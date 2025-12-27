"""
Engram Configuration Management

Centralizes all configuration with support for:
- Environment variables
- Azure Key Vault secrets
- Local development overrides
"""

from functools import lru_cache
from typing import Optional

from pydantic import Field, ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    # ==========================================================================
    # Application
    # ==========================================================================
    app_name: str = "Engram"
    app_version: str = "0.1.0"
    environment: str = Field("development", alias="ENVIRONMENT")
    debug: bool = Field(False, alias="DEBUG")

    # ==========================================================================
    # Azure Key Vault
    # ==========================================================================
    azure_keyvault_url: Optional[str] = Field(None, alias="AZURE_KEYVAULT_URL")

    # ==========================================================================
    # Database (PostgreSQL)
    # ==========================================================================
    postgres_host: str = Field("localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(5432, alias="POSTGRES_PORT")
    postgres_user: str = Field("postgres", alias="POSTGRES_USER")
    postgres_password: str = Field("password", alias="POSTGRES_PASSWORD")
    postgres_db: str = Field("engram", alias="POSTGRES_DB")

    @property
    def postgres_dsn(self) -> str:
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    # ==========================================================================
    # Zep Memory Service (Self-hosted in Azure Container Apps)
    # ==========================================================================
    # ZEP_API_URL must be set to the Zep Container App internal FQDN (e.g., http://zep-app-name.internal:8000)
    # In ACA, internal services use: http://{app-name}.internal:{port} or the ingress FQDN
    zep_api_url: str = Field("", alias="ZEP_API_URL")  # Must be provided via environment variable
    zep_api_key: Optional[str] = Field(None, alias="ZEP_API_KEY")
    zep_mode: str = Field("selfhost", alias="ZEP_MODE")  # Always self-hosted for enterprise

    # ==========================================================================
    # Temporal Orchestration
    # ==========================================================================
    temporal_host: str = Field("localhost:7233", alias="TEMPORAL_HOST")
    temporal_namespace: str = Field("default", alias="TEMPORAL_NAMESPACE")
    temporal_task_queue: str = Field("engram-agents", alias="TEMPORAL_TASK_QUEUE")

    # ==========================================================================
    # Chat API Gateway (OpenAI-compatible)
    # ==========================================================================
    azure_ai_endpoint: Optional[str] = Field(None, alias="AZURE_AI_ENDPOINT")
    azure_ai_project_name: Optional[str] = Field(None, alias="AZURE_AI_PROJECT_NAME")
    azure_ai_key: Optional[str] = Field(None, alias="AZURE_AI_KEY")
    azure_ai_deployment: str = Field("gpt-5.1-chat", alias="AZURE_AI_DEPLOYMENT")
    azure_ai_api_version: str = Field("2024-10-01-preview", alias="AZURE_AI_API_VERSION")

    # Elena voice configuration
    elena_voice_name: str = Field("en-US-JennyNeural", alias="ELENA_VOICE_NAME")
    # Marcus voice configuration
    marcus_voice_name: str = Field("en-US-GuyNeural", alias="MARCUS_VOICE_NAME")

    # ==========================================================================
    # Azure VoiceLive (Real-time Voice) - Direct Azure AI Services
    # ==========================================================================
    # Authentication: DefaultAzureCredential (Managed Identity) for enterprise
    # Falls back to API key for POC/staging if AZURE_VOICELIVE_KEY is set
    azure_voicelive_endpoint: Optional[str] = Field(None, alias="AZURE_VOICELIVE_ENDPOINT")
    azure_voicelive_key: Optional[str] = Field(None, alias="AZURE_VOICELIVE_KEY")  # Optional for POC
    azure_voicelive_model: str = Field("gpt-realtime", alias="AZURE_VOICELIVE_MODEL")
    azure_voicelive_voice: str = Field("en-US-Ava:DragonHDLatestNeural", alias="AZURE_VOICELIVE_VOICE")
    # Marcus voice configuration for VoiceLive
    marcus_voicelive_voice: str = Field("en-US-GuyNeural", alias="MARCUS_VOICELIVE_VOICE")
    # Project name for unified endpoints (optional, used for project-based endpoints)
    # When using Azure AI Foundry projects, set this to the project name (e.g., "zimax")
    azure_voicelive_project_name: Optional[str] = Field(None, alias="AZURE_VOICELIVE_PROJECT_NAME")
    # API version for Realtime API
    # Use "2024-10-01-preview" for standard endpoints, "2025-10-01" for project-based endpoints
    azure_voicelive_api_version: str = Field("2024-10-01-preview", alias="AZURE_VOICELIVE_API_VERSION")

    # ==========================================================================
    # Multi-Model LLM Integration (Sage Agent)
    # ==========================================================================
    # Anthropic Claude for story generation
    anthropic_api_key: Optional[str] = Field(None, alias="ANTHROPIC_API_KEY")
    # Google Gemini for diagram generation via Nano Banana Pro
    gemini_api_key: Optional[str] = Field(None, alias="GEMINI_API_KEY")
    # OneDrive docs path (local folder that syncs)
    onedrive_docs_path: str = Field("docs", alias="ONEDRIVE_DOCS_PATH")

    # ==========================================================================
    # Microsoft Entra ID (Authentication)
    # ==========================================================================
    azure_tenant_id: Optional[str] = Field(None, alias="AZURE_TENANT_ID")
    # Entra/App Registration client ID (audience validation for API tokens)
    # NOTE: This is intentionally NOT AZURE_CLIENT_ID, because that env var is
    # used by Azure SDKs (DefaultAzureCredential) to select a user-assigned
    # Managed Identity. See: auth SOP.
    azure_client_id: Optional[str] = Field(None, alias="AZURE_AD_CLIENT_ID")
    azure_client_secret: Optional[str] = Field(None, alias="AZURE_CLIENT_SECRET")

    # User-assigned Managed Identity client ID for Azure SDKs (DefaultAzureCredential)
    # This is consumed by azure-identity; we keep it available for diagnostics.
    azure_managed_identity_client_id: Optional[str] = Field(None, alias="AZURE_CLIENT_ID")

    # POC / validation switch: when false, API auth is bypassed (DO NOT use in prod)
    auth_required: bool = Field(True, alias="AUTH_REQUIRED")

    @property
    def entra_authority_url(self) -> Optional[str]:
        if self.azure_tenant_id:
            return f"https://login.microsoftonline.com/{self.azure_tenant_id}"
        return None

    # ==========================================================================
    # CORS & Security
    # ==========================================================================
    cors_origins: list[str] = Field(default=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"], alias="CORS_ORIGINS")
    api_key_header: str = "X-API-Key"

    # ==========================================================================
    # Observability
    # ==========================================================================
    appinsights_connection_string: Optional[str] = Field(None, alias="APPLICATIONINSIGHTS_CONNECTION_STRING")
    log_level: str = Field("INFO", alias="LOG_LEVEL")

    # ==========================================================================
    # Rate Limiting
    # ==========================================================================
    rate_limit_requests: int = Field(100, alias="RATE_LIMIT_REQUESTS")
    rate_limit_window_seconds: int = Field(60, alias="RATE_LIMIT_WINDOW_SECONDS")

    model_config = ConfigDict(
        env_file=[".env", "../.env"],
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra fields from .env that aren't in this model
    )


class KeyVaultSettings:
    """
    Loads secrets from Azure Key Vault.
    Used in production to override Settings with secure values.
    """

    def __init__(self, vault_url: str):
        self.vault_url = vault_url
        self._client = None

    @property
    def client(self):
        if self._client is None:
            from azure.identity import DefaultAzureCredential
            from azure.keyvault.secrets import SecretClient

            credential = DefaultAzureCredential()
            self._client = SecretClient(vault_url=self.vault_url, credential=credential)
        return self._client

    def get_secret(self, name: str) -> Optional[str]:
        """Get a secret from Key Vault"""
        try:
            secret = self.client.get_secret(name)
            return secret.value
        except Exception:
            return None

    def apply_to_settings(self, settings: Settings) -> Settings:
        """Override settings with Key Vault secrets"""
        secret_mappings = {
            "zep-api-key": "zep_api_key",
            "azure-ai-key": "azure_ai_key",
            "azure-ai-endpoint": "azure_ai_endpoint",
            "azure-ai-project-name": "azure_ai_project_name",
            "azure-client-secret": "azure_client_secret",
            "azure-client-id": "azure_client_id",
            "azure-tenant-id": "azure_tenant_id",
            "appinsights-connection-string": "appinsights_connection_string",
        }

        for secret_name, setting_attr in secret_mappings.items():
            value = self.get_secret(secret_name)
            if value and hasattr(settings, setting_attr):
                try:
                    setattr(settings, setting_attr, value)
                except AttributeError:
                    # Skip read-only properties
                    continue

        return settings


@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings.
    Cached for performance - only loaded once.
    """
    settings = Settings()

    # In production, overlay Key Vault secrets
    if settings.azure_keyvault_url and settings.environment != "development":
        kv_settings = KeyVaultSettings(settings.azure_keyvault_url)
        settings = kv_settings.apply_to_settings(settings)

    return settings
