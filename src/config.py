"""
Configuration settings for the Research Agent.
"""

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # OpenAI Configuration
    openai_api_key: str = ""
    openai_model: str = "gpt-4.1"

    # PokeAPI Configuration
    pokeapi_base_url: str = "https://pokeapi.co/api/v2"

    # Web Scraping Configuration
    max_web_results: int = 5
    request_timeout: int = 15
    web_scraping_enabled: bool = False  # Disabled by default to avoid timeouts
    #web_scraping_enabled: bool = True  # Enable web scraping

    # Agent Configuration
    max_research_steps: int = 10
    max_tokens: int = 5000

    # Logging Configuration
    log_level: str = "INFO"
    enable_rich_output: bool = True

    # check to ensure an API key was provided
    @field_validator("openai_api_key")
    def must_be_non_empty(cls, v: str) -> str:
        if not v:
            raise ValueError("OPENAI_API_KEY must be set in .env file")
        return v

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
