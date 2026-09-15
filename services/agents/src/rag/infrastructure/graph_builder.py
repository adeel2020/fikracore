import logging
import socket
from urllib.parse import urlparse
from typing import List, Dict, Any
from rag.config import rag_settings

logger = logging.getLogger("rag.graph_builder")

def check_neo4j_port() -> bool:
    try:
        parsed = urlparse(rag_settings.neo4j_uri)
        host = parsed.hostname or "localhost"
        port = parsed.port or 7687
        with socket.create_connection((host, port), timeout=0.5):
            return True
    except Exception:
        return False

class Neo4jGraphManager:
    def __init__(self):
        self.is_connected = False
        self.graph_store = None
        
        if not check_neo4j_port():
            logger.warning("Neo4j port is not reachable. GraphRAG will operate in offline/fallback mode.")
            return

        try:
            from llama_index.graph_stores.neo4j import Neo4jPropertyGraphStore
            self.graph_store = Neo4jPropertyGraphStore(
                username=rag_settings.neo4j_username,
                password=rag_settings.neo4j_password,
                url=rag_settings.neo4j_uri
            )
            self.is_connected = True
            logger.info("Successfully connected to Neo4j PropertyGraph database.")
        except Exception as e:
            logger.warning(f"Failed to connect to Neo4j: {e}. GraphRAG will operate in offline/fallback mode.")
            self.graph_store = None
            self.is_connected = False

    async def build_graph_index(self, documents: List[Any]) -> None:
        if not self.is_connected or not self.graph_store:
            logger.warning("Neo4j database is not connected. Skipping GraphRAG PropertyGraphIndex upsert.")
            return

        try:
            from llama_index.core import PropertyGraphIndex
            from llama_index.embeddings.openai import OpenAIEmbedding
            from llama_index.llms.openai import OpenAI
            
            embed_model = OpenAIEmbedding(
                api_key=rag_settings.openai_api_key,
                model=rag_settings.openai_embedding_model,
                api_base="https://api.openai.com/v1"
            )
            llm = OpenAI(model=rag_settings.openai_model, api_key=rag_settings.openai_api_key or "ollama", api_base=rag_settings.openai_api_base)
            
            # This constructs PropertyGraphIndex and automatically extracts entities/relations into Neo4j
            PropertyGraphIndex.from_documents(
                documents,
                property_graph_store=self.graph_store,
                embed_model=embed_model,
                llm=llm
            )
            logger.info("GraphRAG index updated successfully in Neo4j.")
        except Exception as e:
            logger.error(f"Failed to build PropertyGraphIndex: {e}")

    async def query_neighborhood(self, entity_name: str) -> List[Dict[str, Any]]:
        """Queries Neo4j for the immediate 1-hop and 2-hop neighborhood of a given entity."""
        if not self.is_connected or not self.graph_store:
            return []

        try:
            client = self.graph_store.client
            # Fetch 1-hop relationships
            query = (
                "MATCH (n {name: $entity_name})-[r]->(m) "
                "RETURN n.name AS source, type(r) AS relation, m.name AS target "
                "LIMIT 50"
            )
            with client.session() as session:
                result = session.run(query, entity_name=entity_name)
                triples = []
                for record in result:
                    triples.append({
                        "source": record["source"],
                        "relation": record["relation"],
                        "target": record["target"]
                    })
                return triples
        except Exception as e:
            logger.error(f"Failed to query Neo4j neighborhood for {entity_name}: {e}")
            return []

_graph_manager = None

def get_graph_manager() -> Neo4jGraphManager:
    global _graph_manager
    if _graph_manager is None:
        _graph_manager = Neo4jGraphManager()
    return _graph_manager
