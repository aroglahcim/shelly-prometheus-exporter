from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Application settings that can be configured via environment variables and command line arguments."""
    
    PORT: int = Field(default=8000, description="Port to run the server on")
    DEV_RELOAD: bool = Field(default=False, description="Enable auto-reload for development")
    
    model_config = SettingsConfigDict(
        env_prefix="SHELLY_PROMETHEUS_EXPORTER_",
        case_sensitive=True,
        extra="ignore",
        cli_parse_args=True, 
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance with values from environment variables and command line arguments.
    Command line arguments take precedence over environment variables.
    """
    return Settings() 