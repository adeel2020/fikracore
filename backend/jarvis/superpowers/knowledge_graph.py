"""
JARVIS Knowledge Graph Engine - Graph Traversal & Analysis
Neo4j-powered knowledge graph operations.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, AsyncIterator

logger = logging.getLogger("jarvis.knowledge_graph")


class KnowledgeGraphEngine:
    """JARVIS knowledge graph superpower - navigate the graph of knowledge."""

    def __init__(self, config):
        self.config = config
        self._graph_manager = None
        self._neo4j_driver = None

    async def initialize(self) -> None:
        """Initialize knowledge graph connection."""
        try:
            from backend.rag.infrastructure.graph_builder import get_graph_manager
            self._graph_manager = get_graph_manager()
            logger.info("[KnowledgeGraphEngine] Graph manager loaded.")
        except ImportError:
            logger.warning("[KnowledgeGraphEngine] Graph manager not available.")
        
        try:
            from neo4j import GraphDatabase
            # Try to connect to Neo4j
            self._neo4j_driver = GraphDatabase.driver(
                "bolt://localhost:7687",
                auth=("neo4j", "password")
            )
            logger.info("[KnowledgeGraphEngine] Neo4j connected.")
        except Exception as e:
            logger.warning(f"[KnowledgeGraphEngine] Neo4j connection failed: {e}")
        
        logger.info("[KnowledgeGraphEngine] Initialized.")

    async def process(
        self,
        query: str,
        session_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> str:
        """Process knowledge graph queries."""
        lower_query = query.lower()
        
        # Entity lookup
        if "entity" in lower_query or "what is" in lower_query:
            entity = self._extract_entity(query)
            if entity:
                return await self.query_entity(entity)
        
        # Relationship query
        if "relationship" in lower_query or "connection" in lower_query or "related" in lower_query:
            entity = self._extract_entity(query)
            if entity:
                return await self.query_relationships(entity)
        
        # Path finding
        if "path" in lower_query or "connect" in lower_query:
            source = context.get("source") if context else None
            target = context.get("target") if context else None
            if source and target:
                return await self.find_path(source, target)
        
        # Graph stats
        if "stats" in lower_query or "statistics" in lower_query:
            return await self.get_graph_stats()
        
        # Default: query neighborhood
        entity = self._extract_entity(query)
        if entity:
            return await self.query_neighborhood(entity)
        
        return "Please specify an entity or relationship to query."

    def _extract_entity(self, query: str) -> str | None:
        """Extract entity name from query."""
        # Simple heuristic - take the main noun phrase
        words = query.lower().split()
        stop_words = {"what", "is", "the", "a", "an", "tell", "me", "about", "show", "find", "get", "query"}
        entity_words = [w for w in words if w not in stop_words]
        return " ".join(entity_words) if entity_words else None

    async def query_entity(self, entity: str) -> str:
        """Query entity details from knowledge graph."""
        if self._graph_manager:
            try:
                triples = await self._graph_manager.query_neighborhood(entity)
                if triples:
                    result_lines = [f"**Entity: {entity}**\n"]
                    for subj, pred, obj in triples[:20]:
                        result_lines.append(f"- {pred}: {obj}")
                    return "\n".join(result_lines)
            except Exception as e:
                logger.warning(f"Graph query failed: {e}")
        
        if self._neo4j_driver:
            try:
                with self._neo4j_driver.session() as session:
                    result = session.run(
                        "MATCH (n)-[r]->(m) WHERE n.name CONTAINS $entity RETURN n, r, m LIMIT 20",
                        entity=entity
                    )
                    lines = [f"**Entity: {entity}**\n"]
                    for record in result:
                        n = record["n"]
                        r = record["r"]
                        m = record["m"]
                        lines.append(f"- [{r.type}] {m.get('name', 'unknown')}")
                    return "\n".join(lines) if len(lines) > 1 else f"No information found for: {entity}"
            except Exception as e:
                return f"Neo4j query error: {e}"
        
        return "Knowledge graph not available."

    async def query_relationships(self, entity: str) -> str:
        """Query relationships for an entity."""
        if self._neo4j_driver:
            try:
                with self._neo4j_driver.session() as session:
                    result = session.run(
                        """MATCH (n)-[r]->(m) 
                        WHERE n.name CONTAINS $entity OR m.name CONTAINS $entity 
                        RETURN n.name as source, type(r) as rel, m.name as target LIMIT 30""",
                        entity=entity
                    )
                    lines = [f"**Relationships for: {entity}**\n"]
                    for record in result:
                        lines.append(f"- {record['source']} --[{record['rel']}]--> {record['target']}")
                    return "\n".join(lines) if len(lines) > 1 else f"No relationships found for: {entity}"
            except Exception as e:
                return f"Neo4j query error: {e}"
        
        return "Knowledge graph not available."

    async def find_path(self, source: str, target: str) -> str:
        """Find path between two entities."""
        if self._neo4j_driver:
            try:
                with self._neo4j_driver.session() as session:
                    result = session.run(
                        """MATCH path = shortestPath(
                            (n1 {name: $source})-[*]-(n2 {name: $target})
                        ) RETURN path LIMIT 1""",
                        source=source, target=target
                    )
                    record = result.single()
                    if record:
                        path = record["path"]
                        nodes = path.nodes
                        relationships = path.relationships
                        lines = [f"**Path from {source} to {target}:**\n"]
                        for i, rel in enumerate(relationships):
                            lines.append(f"{nodes[i].get('name', '?')} --[{rel.type}]--> {nodes[i+1].get('name', '?')}")
                        return "\n".join(lines)
                    return f"No path found between {source} and {target}"
            except Exception as e:
                return f"Neo4j path query error: {e}"
        
        return "Knowledge graph not available."

    async def get_graph_stats(self) -> str:
        """Get knowledge graph statistics."""
        if self._neo4j_driver:
            try:
                with self._neo4j_driver.session() as session:
                    node_count = session.run("MATCH (n) RETURN count(n) as count").single()["count"]
                    rel_count = session.run("MATCH ()-[r]->() RETURN count(r) as count").single()["count"]
                    label_counts = session.run(
                        "MATCH (n) RETURN labels(n)[0] as label, count(n) as cnt ORDER BY cnt DESC LIMIT 10"
                    )
                    
                    lines = [
                        "**Knowledge Graph Statistics**\n",
                        f"- Total Nodes: {node_count}",
                        f"- Total Relationships: {rel_count}",
                        "\n**Top Entity Types:**"
                    ]
                    for record in label_counts:
                        lines.append(f"- {record['label']}: {record['cnt']}")
                    
                    return "\n".join(lines)
            except Exception as e:
                return f"Stats query error: {e}"
        
        return "Knowledge graph not available."

    async def query_neighborhood(self, entity: str) -> str:
        """Query entity neighborhood (1-hop)."""
        return await self.query_entity(entity)

    async def stream(
        self,
        query: str,
        session_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> AsyncIterator[str]:
        """Stream knowledge graph results."""
        result = await self.process(query, session_id, context)
        yield result

    async def shutdown(self) -> None:
        """Cleanup knowledge graph resources."""
        if self._neo4j_driver:
            self._neo4j_driver.close()
        self._graph_manager = None
