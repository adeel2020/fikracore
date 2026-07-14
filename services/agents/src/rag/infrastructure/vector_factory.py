import os
import logging
from typing import Any, List
from pydantic import PrivateAttr
from llama_index.core.schema import BaseNode
from llama_index.core.embeddings import BaseEmbedding
from ..core.abstractions import BaseVectorStore
from ..config import rag_settings

logger = logging.getLogger("rag.vector_factory")

class LocalSentenceTransformerEmbedding(BaseEmbedding):
    _model: Any = PrivateAttr()

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", **kwargs):
        super().__init__(**kwargs)
        from sentence_transformers import SentenceTransformer
        self._model = SentenceTransformer(model_name)

    @classmethod
    def class_name(cls) -> str:
        return "LocalSentenceTransformerEmbedding"

    def _get_query_embedding(self, query: str) -> List[float]:
        return self._model.encode(query).tolist()

    def _get_text_embedding(self, text: str) -> List[float]:
        return self._model.encode(text).tolist()

    async def _aget_query_embedding(self, query: str) -> List[float]:
        return self._get_query_embedding(query)

    async def _aget_text_embedding(self, text: str) -> List[float]:
        return self._get_text_embedding(text)


_openai_reachable = None

def is_openai_reachable() -> bool:
    global _openai_reachable
    if _openai_reachable is not None:
        return _openai_reachable
        
    has_openai = bool(rag_settings.openai_api_key and rag_settings.openai_api_key.strip())
    if not has_openai:
        _openai_reachable = False
        return False
        
    try:
        from llama_index.embeddings.openai import OpenAIEmbedding
        model = OpenAIEmbedding(
            api_key=rag_settings.openai_api_key,
            model=rag_settings.openai_embedding_model,
            api_base="https://api.openai.com/v1",
            max_retries=0,
            timeout=5.0
        )
        model.get_query_embedding("test")
        _openai_reachable = True
        logger.info("OpenAI API is reachable and valid for embeddings.")
    except Exception as e:
        logger.warning(f"OpenAI API check failed ({e}). Forcing local embedding fallback.")
        _openai_reachable = False
        
    return _openai_reachable


def _get_embedding_model() -> BaseEmbedding:
    if is_openai_reachable():
        try:
            from llama_index.embeddings.openai import OpenAIEmbedding
            return OpenAIEmbedding(
                api_key=rag_settings.openai_api_key,
                model=rag_settings.openai_embedding_model,
                api_base="https://api.openai.com/v1"
            )
        except Exception as e:
            logger.warning(f"Failed to load OpenAIEmbedding, falling back to local: {e}")
            
    # Fallback to local SentenceTransformer
    logger.info("Using local SentenceTransformer embedding model fallback.")
    return LocalSentenceTransformerEmbedding()

class ChromaVectorStoreWrapper(BaseVectorStore):
    def __init__(self):
        import chromadb
        from llama_index.vector_stores.chroma import ChromaVectorStore
        from llama_index.core import StorageContext
        
        self.db = chromadb.PersistentClient(path=rag_settings.chroma_db_path)
        
        has_openai = is_openai_reachable()
        col_name = rag_settings.chroma_collection_name
        if not has_openai:
            col_name = f"{col_name}-local"
            
        self.chroma_collection = self.db.get_or_create_collection(col_name)
        self.vector_store = ChromaVectorStore(chroma_collection=self.chroma_collection)
        self.storage_context = StorageContext.from_defaults(vector_store=self.vector_store)
        
    async def add_nodes(self, nodes: List[BaseNode], **kwargs: Any) -> None:
        from llama_index.core import VectorStoreIndex
        embed_model = _get_embedding_model()
        # Synchronously block to generate embeddings & index (runs in a thread pool inside LlamaIndex)
        VectorStoreIndex(nodes, storage_context=self.storage_context, embed_model=embed_model)

    async def query(self, query_str: str, similarity_top_k: int = 5, **kwargs: Any) -> List[Any]:
        from llama_index.core import VectorStoreIndex
        embed_model = _get_embedding_model()
        index = VectorStoreIndex.from_vector_store(self.vector_store, embed_model=embed_model)
        retriever = index.as_retriever(similarity_top_k=similarity_top_k)
        # Run synchronous retrieval block
        return retriever.retrieve(query_str)

    async def delete_nodes(self, node_ids: List[str], **kwargs: Any) -> None:
        for nid in node_ids:
            try:
                self.vector_store.delete(nid)
            except Exception as e:
                logger.error(f"Failed to delete node {nid} from Chroma: {e}")


class QdrantVectorStoreWrapper(BaseVectorStore):
    def __init__(self):
        from qdrant_client import QdrantClient
        from llama_index.vector_stores.qdrant import QdrantVectorStore
        from llama_index.core import StorageContext
        
        if rag_settings.qdrant_url:
            self.client = QdrantClient(url=rag_settings.qdrant_url, api_key=rag_settings.qdrant_api_key)
        else:
            self.client = QdrantClient(":memory:")
            
        has_openai = is_openai_reachable()
        col_name = rag_settings.chroma_collection_name
        if not has_openai:
            col_name = f"{col_name}-local"
            
        self.vector_store = QdrantVectorStore(client=self.client, collection_name=col_name)
        self.storage_context = StorageContext.from_defaults(vector_store=self.vector_store)

    async def add_nodes(self, nodes: List[BaseNode], **kwargs: Any) -> None:
        from llama_index.core import VectorStoreIndex
        embed_model = _get_embedding_model()
        VectorStoreIndex(nodes, storage_context=self.storage_context, embed_model=embed_model)

    async def query(self, query_str: str, similarity_top_k: int = 5, **kwargs: Any) -> List[Any]:
        from llama_index.core import VectorStoreIndex
        embed_model = _get_embedding_model()
        index = VectorStoreIndex.from_vector_store(self.vector_store, embed_model=embed_model)
        retriever = index.as_retriever(similarity_top_k=similarity_top_k)
        return retriever.retrieve(query_str)

    async def delete_nodes(self, node_ids: List[str], **kwargs: Any) -> None:
        for nid in node_ids:
            try:
                self.vector_store.delete(nid)
            except Exception as e:
                logger.error(f"Failed to delete node {nid} from Qdrant: {e}")


class PineconeVectorStoreWrapper(BaseVectorStore):
    def __init__(self):
        from pinecone import Pinecone
        from llama_index.vector_stores.pinecone import PineconeVectorStore
        from llama_index.core import StorageContext
        
        self.pc = Pinecone(api_key=rag_settings.pinecone_api_key)
        
        has_openai = is_openai_reachable()
        idx_name = rag_settings.pinecone_index_name
        if not has_openai:
            idx_name = f"{idx_name}-local"
            
        self.pinecone_index = self.pc.Index(idx_name)
        self.vector_store = PineconeVectorStore(pinecone_index=self.pinecone_index)
        self.storage_context = StorageContext.from_defaults(vector_store=self.vector_store)

    async def add_nodes(self, nodes: List[BaseNode], **kwargs: Any) -> None:
        from llama_index.core import VectorStoreIndex
        embed_model = _get_embedding_model()
        VectorStoreIndex(nodes, storage_context=self.storage_context, embed_model=embed_model)

    async def query(self, query_str: str, similarity_top_k: int = 5, **kwargs: Any) -> List[Any]:
        from llama_index.core import VectorStoreIndex
        embed_model = _get_embedding_model()
        index = VectorStoreIndex.from_vector_store(self.vector_store, embed_model=embed_model)
        retriever = index.as_retriever(similarity_top_k=similarity_top_k)
        return retriever.retrieve(query_str)

    async def delete_nodes(self, node_ids: List[str], **kwargs: Any) -> None:
        for nid in node_ids:
            try:
                self.vector_store.delete(nid)
            except Exception as e:
                logger.error(f"Failed to delete node {nid} from Pinecone: {e}")


class FAISSVectorStoreWrapper(BaseVectorStore):
    def __init__(self):
        import faiss
        from llama_index.vector_stores.faiss import FaissVectorStore
        from llama_index.core import StorageContext
        
        has_openai = is_openai_reachable()
        d = 1536 if has_openai else 384
        faiss_index = faiss.IndexFlatIP(d)
        self.vector_store = FaissVectorStore(faiss_index=faiss_index)
        self.storage_context = StorageContext.from_defaults(vector_store=self.vector_store)

    async def add_nodes(self, nodes: List[BaseNode], **kwargs: Any) -> None:
        from llama_index.core import VectorStoreIndex
        embed_model = _get_embedding_model()
        VectorStoreIndex(nodes, storage_context=self.storage_context, embed_model=embed_model)
        
        # Persist index locally
        has_openai = is_openai_reachable()
        persist_dir = rag_settings.faiss_persist_dir
        if not has_openai:
            persist_dir = f"{persist_dir}-local"
            
        os.makedirs(persist_dir, exist_ok=True)
        self.vector_store.persist(os.path.join(persist_dir, "default__vector_store.json"))

    async def query(self, query_str: str, similarity_top_k: int = 5, **kwargs: Any) -> List[Any]:
        from llama_index.core import VectorStoreIndex
        embed_model = _get_embedding_model()
        index = VectorStoreIndex.from_vector_store(self.vector_store, embed_model=embed_model)
        retriever = index.as_retriever(similarity_top_k=similarity_top_k)
        return retriever.retrieve(query_str)

    async def delete_nodes(self, node_ids: List[str], **kwargs: Any) -> None:
        pass


_vector_store_instance = None

async def get_vector_store() -> BaseVectorStore:
    global _vector_store_instance
    if _vector_store_instance is not None:
        return _vector_store_instance

    env = rag_settings.rag_env.lower()
    if env == "production":
        if rag_settings.qdrant_url or rag_settings.qdrant_api_key:
            logger.info("Initializing Qdrant Vector Store Wrapper for production...")
            _vector_store_instance = QdrantVectorStoreWrapper()
        elif rag_settings.pinecone_api_key:
            logger.info("Initializing Pinecone Vector Store Wrapper for production...")
            _vector_store_instance = PineconeVectorStoreWrapper()
        else:
            logger.warning("Production env configured, but no Qdrant or Pinecone configs found. Falling back to ChromaDB.")
            _vector_store_instance = ChromaVectorStoreWrapper()
    elif env == "edge":
        logger.info("Initializing FAISS Vector Store Wrapper for edge...")
        _vector_store_instance = FAISSVectorStoreWrapper()
    else:
        logger.info("Initializing ChromaDB Vector Store Wrapper for development...")
        _vector_store_instance = ChromaVectorStoreWrapper()

    return _vector_store_instance
