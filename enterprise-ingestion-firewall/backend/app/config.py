from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Loads configuration from environment variables / .env file."""

    groq_api_key: str = ""
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_model: str = "llama-3.3-70b-versatile"
    request_timeout_seconds: float = 20

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
