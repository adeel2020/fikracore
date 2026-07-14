from abc import ABC, abstractmethod
from typing import Any, List, Dict

class BaseVectorStore(ABC):
    """Abstract Base Class for Vector Store operations to decouple database provider implementation details."""

    @abstractmethod
    async def add_nodes(self, nodes: List[Any], **kwargs: Any) -> None:
        """Asynchronously add node embeddings/documents to the vector store.
        
        Args:
            nodes: A list of node documents or schema representations.
        """
        pass

    @abstractmethod
    async def query(self, query_str: str, similarity_top_k: int = 5, **kwargs: Any) -> List[Any]:
        """Asynchronously query the vector store for top-K similar items.
        
        Args:
            query_str: The raw or processed search query.
            similarity_top_k: Number of similarity matches to return.
        """
        pass

    @abstractmethod
    async def delete_nodes(self, node_ids: List[str], **kwargs: Any) -> None:
        """Asynchronously delete node embeddings/documents from the vector store by ID.
        
        Args:
            node_ids: List of unique node identifiers.
        """
        pass


class BaseGraphStore(ABC):
    """Abstract Base Class for Graph Store operations to interface with property graphs."""

    @abstractmethod
    async def upsert_triplets(self, triplets: List[Any], **kwargs: Any) -> None:
        """Asynchronously upsert semantic triplets (subject, relation, object) into the graph.
        
        Args:
            triplets: A list of triplet items or relationship maps.
        """
        pass

    @abstractmethod
    async def query_relations(self, query_str: str, **kwargs: Any) -> List[Dict[str, Any]]:
        """Asynchronously execute graph queries/traversals to retrieve semantic connections.
        
        Args:
            query_str: A graph query (e.g. Cypher query or text query resolved to graph path).
        """
        pass

    @abstractmethod
    async def get_community_summaries(self, **kwargs: Any) -> List[Dict[str, Any]]:
        """Asynchronously retrieve pre-computed or dynamic global community summaries.
        
        Used to support global context questions across the property graph.
        """
        pass


class BaseRetriever(ABC):
    """Abstract Base Class for the retrieval orchestration pipeline."""

    @abstractmethod
    async def retrieve(self, query_str: str, **kwargs: Any) -> List[Any]:
        """Asynchronously retrieve relevant context nodes/documents using hybrid search,
        graph traversal, and ranking fusion.
        
        Args:
            query_str: The search query string.
        """
        pass
