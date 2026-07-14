import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Patch LlamaIndex OpenAI validation to accept custom local/ollama models
try:
    import llama_index.llms.openai.utils as openai_utils
    import llama_index.llms.openai.base as openai_base
    
    openai_utils.CHAT_MODELS["ollama/llama3.1:8b"] = True
    openai_utils.CHAT_MODELS["llama3.1:8b"] = True
    
    orig_contextsize = openai_utils.openai_modelname_to_contextsize
    def patched_contextsize(model_name: str) -> int:
        try:
            return orig_contextsize(model_name)
        except ValueError:
            return 4096
            
    openai_utils.openai_modelname_to_contextsize = patched_contextsize
    openai_base.openai_modelname_to_contextsize = patched_contextsize
except Exception as patch_err:
    pass


# Base directory points to the backend folder (which contains .env)
BASE_DIR = Path(__file__).resolve().parent.parent

from pydantic import model_validator

class RAGSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="after")
    def sanitize_local_settings(self) -> "RAGSettings":
        if self.openai_model.startswith("ollama/"):
            self.openai_model = self.openai_model[len("ollama/"):]
        if "11434" in self.openai_api_base and not self.openai_api_base.endswith("/v1") and not self.openai_api_base.endswith("/v1/"):
            self.openai_api_base = self.openai_api_base.rstrip("/") + "/v1"
        return self

    # Environment setting: 'production', 'development', or 'edge'
    rag_env: str = "development"

    # LLM and Embeddings
    openai_api_key: str | None = None
    openai_api_base: str = "http://localhost:11434"
    openai_model: str = "ollama/llama3.1:8b"
    openai_embedding_model: str = "text-embedding-3-small"

    # Production Vector Database (Qdrant or Pinecone)
    qdrant_url: str | None = None
    qdrant_api_key: str | None = None
    
    pinecone_api_key: str | None = None
    pinecone_environment: str | None = None
    pinecone_index_name: str = "sa4dst-rag"

    # Development Vector Database (ChromaDB)
    chroma_db_path: str = "./chroma_db"
    chroma_collection_name: str = "sa4dst-rag-collection"

    # Edge Vector Database (FAISS)
    faiss_persist_dir: str = "./faiss_db"

    # Graph Database (Neo4j)
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_username: str = "neo4j"
    neo4j_password: str = "password"

    # Advanced retrieval settings
    use_reranker: bool = True
    use_hyde: bool = True
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    similarity_top_k: int = 10
    rerank_top_k: int = 5


rag_settings = RAGSettings()

