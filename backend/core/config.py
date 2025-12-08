"""
Engram Configuration Management

Centralizes all configuration with support for:
- Environment variables
- Azure Key Vault secrets
- Local development overrides
"""

import os
from functools import lru_cache
from typing import Optional

from pydantic import Field
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
    # Azure OpenAI
    # ==========================================================================
    azure_openai_endpoint: Optional[str] = Field(None, alias="AZURE_OPENAI_ENDPOINT")
    azure_openai_key: Optional[str] = Field(None, alias="AZURE_OPENAI_KEY")
    azure_openai_deployment: str = Field("gpt-4o", alias="AZURE_OPENAI_DEPLOYMENT")
    azure_openai_api_version: str = Field("2024-02-15-preview", alias="AZURE_OPENAI_API_VERSION")
    
    # ==========================================================================
    # Azure Speech Services
    # ==========================================================================
    azure_speech_key: Optional[str] = Field(None, alias="AZURE_SPEECH_KEY")
    azure_speech_region: str = Field("eastus", alias="AZURE_SPEECH_REGION")
    
    # Elena voice configuration
    elena_voice_name: str = Field("en-US-JennyNeural", alias="ELENA_VOICE_NAME")
    # Marcus voice configuration  
    marcus_voice_name: str = Field("en-US-GuyNeural", alias="MARCUS_VOICE_NAME")
    
    # ==========================================================================
    # Microsoft Entra ID (Authentication)
    # ==========================================================================
    entra_tenant_id: Optional[str] = Field(None, alias="ENTRA_TENANT_ID")
    entra_client_id: Optional[str] = Field(None, alias="ENTRA_CLIENT_ID")
    entra_client_secret: Optional[str] = Field(None, alias="ENTRA_CLIENT_SECRET")
    entra_authority: Optional[str] = None
    
    @property
    def entra_authority_url(self) -> Optional[str]:
        if self.entra_authority:
            return self.entra_authority
        if self.entra_tenant_id:
            return f"https://login.microsoftonline.com/{self.entra_tenant_id}"
        return None
    
    # ==========================================================================
    # CORS & Security
    # ==========================================================================
    cors_origins: list[str] = Field(
        default=["http://localhost:5173", "http://localhost:3000"],
        alias="CORS_ORIGINS"
    )
    api_key_header: str = "X-API-Key"
    
    # ==========================================================================
    # Observability
    # ==========================================================================
    applicationinsights_connection_string: Optional[str] = Field(
        None, alias="APPLICATIONINSIGHTS_CONNECTION_STRING"
    )
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    
    # ==========================================================================
    # Rate Limiting
    # ==========================================================================
    rate_limit_requests: int = Field(100, alias="RATE_LIMIT_REQUESTS")
    rate_limit_window_seconds: int = Field(60, alias="RATE_LIMIT_WINDOW_SECONDS")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


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
            "azure-openai-key": "azure_openai_key",
            "azure-openai-endpoint": "azure_openai_endpoint",
            "azure-speech-key": "azure_speech_key",
            "entra-client-secret": "entra_client_secret",
            "entra-client-id": "entra_client_id",
            "entra-tenant-id": "entra_tenant_id",
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

