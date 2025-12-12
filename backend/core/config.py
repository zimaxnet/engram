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
    # Zep Memory Service
    # ==========================================================================
    zep_api_url: str = Field("http://localhost:8000", alias="ZEP_API_URL")
    zep_api_key: Optional[str] = Field(None, alias="ZEP_API_KEY")

    # ==========================================================================
    # Temporal Orchestration
    # ==========================================================================
    temporal_host: str = Field("localhost:7233", alias="TEMPORAL_HOST")
    temporal_namespace: str = Field("default", alias="TEMPORAL_NAMESPACE")
    temporal_task_queue: str = Field("engram-agents", alias="TEMPORAL_TASK_QUEUE")

    # ==========================================================================
    # Azure AI Foundry (key-auth)
    # ==========================================================================
    azure_ai_endpoint: Optional[str] = Field(None, alias="AZURE_AI_ENDPOINT")
    azure_ai_project_name: Optional[str] = Field(None, alias="AZURE_AI_PROJECT_NAME")
    azure_ai_key: Optional[str] = Field(None, alias="AZURE_AI_KEY")
    azure_ai_deployment: str = Field("gpt-4o-mini", alias="AZURE_AI_DEPLOYMENT")
    azure_ai_api_version: str = Field("2024-10-01-preview", alias="AZURE_AI_API_VERSION")

    # Elena voice configuration
    elena_voice_name: str = Field("en-US-JennyNeural", alias="ELENA_VOICE_NAME")
    # Marcus voice configuration
    marcus_voice_name: str = Field("en-US-GuyNeural", alias="MARCUS_VOICE_NAME")

    # ==========================================================================
    # Azure VoiceLive (Real-time Voice)
    # ==========================================================================
    azure_voicelive_model: str = Field("gpt-realtime", alias="AZURE_VOICELIVE_MODEL")
    azure_voicelive_voice: str = Field("en-US-Ava:DragonHDLatestNeural", alias="AZURE_VOICELIVE_VOICE")
    # Marcus voice configuration for VoiceLive
    marcus_voicelive_voice: str = Field("en-US-GuyNeural", alias="MARCUS_VOICELIVE_VOICE")

    # ==========================================================================
    # Microsoft Entra ID (Authentication)
    # ==========================================================================
    azure_tenant_id: Optional[str] = Field(None, alias="AZURE_TENANT_ID")
    azure_client_id: Optional[str] = Field(None, alias="AZURE_CLIENT_ID")
    azure_client_secret: Optional[str] = Field(None, alias="AZURE_CLIENT_SECRET")

    @property
    def entra_authority_url(self) -> Optional[str]:
        if self.azure_tenant_id:
            return f"https://login.microsoftonline.com/{self.azure_tenant_id}"
        return None

    # ==========================================================================
    # CORS & Security
    # ==========================================================================
    cors_origins: list[str] = Field(default=["http://localhost:5173", "http://localhost:3000"], alias="CORS_ORIGINS")
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
            "postgres-connection-string": "postgres_dsn",
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
                setattr(settings, setting_attr, value)

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
