from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    openai_api_key: str | None = None
    openai_api_base: str = "http://localhost:11434"
    openai_model: str = "ollama/llama3.1:8b"
    openai_embedding_model: str = "text-embedding-3-small"

    max_context_messages: int = 20
    context_window_tokens: int = 50_000

    # Database
    database_url: str | None = None  # postgresql://user:password@localhost/sa4dst

    # WhatsApp Bot
    whatsapp_verify_token: str = "sa4dst_verify_token"
    whatsapp_phone_number_id: str | None = None
    whatsapp_token: str | None = None


settings = Settings()

