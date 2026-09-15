import logging
import os
import sys
from pathlib import Path

# Prevent dotenv from searching above repository root and hitting macOS protected /Users/.env
import dotenv
_orig_find_dotenv = dotenv.find_dotenv
def _safe_find_dotenv(*args, **kwargs):
    try:
        res = _orig_find_dotenv(*args, **kwargs)
        if res and (res.startswith("/Users/.env") or res == "/.env"):
            return ""
        return res
    except Exception:
        return ""
dotenv.find_dotenv = _safe_find_dotenv

from dotenv import load_dotenv
try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
    _USE_PYDANTIC_V2 = True
except ImportError:
    from pydantic import BaseSettings
    _USE_PYDANTIC_V2 = False

logger = logging.getLogger(__name__)

_project_root = Path(__file__).resolve().parent.parent.parent

# Try loading .env from multiple locations in order (merging so backend/.env keys are loaded)
loaded_any = False
for env_candidate in [
    _project_root / ".env",               # project root
    _project_root / "shared" / ".env",    # shared .env
    _project_root / "backend" / ".env",   # backend .env
    Path.cwd() / ".env",                  # current working directory
    Path("/app/.env"),                    # Docker mount point
]:
    if env_candidate.is_file():
        load_dotenv(env_candidate, override=False)
        logger.info(f"Loaded configuration from: {env_candidate}")
        loaded_any = True

if not loaded_any:
    logger.warning("No .env file found — relying on environment variables")


class Settings(BaseSettings):
    """Centralized configuration with OpenAI as primary and Ollama as fallback."""

    if _USE_PYDANTIC_V2:
        model_config = SettingsConfigDict(
            env_file=str(_project_root / "backend" / ".env"),
            env_file_encoding="utf-8",
            extra="ignore",
        )
    else:
        class Config:
            env_file = str(_project_root / "backend" / ".env")
            env_file_encoding = "utf-8"
            extra = "ignore"

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # ============ LLM Configuration ============
    openai_api_key: str | None = None
    openai_api_base: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"

    ollama_api_key: str | None = None
    ollama_api_base: str = "http://localhost:11434/v1"
    ollama_model: str = "llama3.1:8b"

    enable_fallback: bool = True
    max_retries: int = 1

    max_context_messages: int = 20
    context_window_tokens: int = 50_000

    # ============ Voice / ElevenLabs Configuration ============
    elevenlabs_api_key: str | None = None
    elevenlabs_voice_id: str = "JBFqnCBsd6RMkjVDRZzb"  # George (British Butler / JARVIS Voice)
    elevenlabs_model: str = "eleven_turbo_v2_5"

    # Database
    database_url: str | None = None

    # WhatsApp Bot
    whatsapp_verify_token: str = "sa4dst_verify_token"
    whatsapp_phone_number_id: str | None = None
    whatsapp_token: str | None = None

    # ============ RAG / Vector Database Configuration ============
    rag_env: str = "development"

    qdrant_url: str | None = None
    qdrant_api_key: str | None = None

    pinecone_api_key: str | None = None
    pinecone_environment: str | None = None
    pinecone_index_name: str = "sa4dst-rag"

    chroma_db_path: str = "./chroma_db"
    chroma_collection_name: str = "sa4dst-rag-collection"

    faiss_persist_dir: str = "./faiss_db"

    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_username: str = "neo4j"
    neo4j_password: str = "password"

    use_reranker: bool = True
    use_hyde: bool = True
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    similarity_top_k: int = 10
    rerank_top_k: int = 5

    def get_llm_config(self, use_primary: bool = True) -> dict:
        if use_primary:
            return {
                "model": self.openai_model,
                "api_base": self.openai_api_base,
                "api_key": self.openai_api_key or "sk-placeholder",
                "is_openai": True,
            }
        else:
            return {
                "model": self.ollama_model,
                "api_base": self.ollama_api_base,
                "api_key": "ollama",
                "is_openai": False,
            }

    def get_active_llm_config(self) -> dict:
        if self.openai_api_key:
            return self.get_llm_config(use_primary=True)
        else:
            logger.info("No OpenAI API key found; using Ollama fallback")
            return self.get_llm_config(use_primary=False)


settings = Settings()
