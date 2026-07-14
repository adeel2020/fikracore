import os
import socket
import asyncio
import logging
import math
from collections import Counter
from typing import Any, List, Dict, Tuple
from llama_index.core.schema import NodeWithScore, BaseNode

from backend.rag.core.abstractions import BaseRetriever
from backend.rag.config import rag_settings
from backend.rag.infrastructure.vector_factory import get_vector_store
from backend.rag.infrastructure.graph_builder import get_graph_manager
from backend.rag.pipelines.ingestion import get_docstore

logger = logging.getLogger("rag.retriever")

def is_huggingface_reachable() -> bool:
    try:
        # Check port 443 on huggingface.co with a 1.0s timeout
        socket.create_connection(("huggingface.co", 443), timeout=1.0)
        return True
    except Exception:
        return False


# ---------------------------------------------------------
# Pure-Python BM25 Index for Hybrid Search
# ---------------------------------------------------------
class SimpleBM25:
    def __init__(self, nodes: List[BaseNode]):
        self.nodes = nodes
        self.corpus_size = len(nodes)
        self.avg_doc_len = sum(len(node.get_content().split()) for node in nodes) / self.corpus_size if self.corpus_size > 0 else 1.0
        self.doc_freqs = []
        self.df = Counter()
        self.doc_lens = []
        
        for node in nodes:
            words = node.get_content().lower().split()
            self.doc_lens.append(len(words))
            freqs = Counter(words)
            self.doc_freqs.append(freqs)
            for word in freqs.keys():
                self.df[word] += 1
                
    def query(self, query_str: str, top_k: int = 10) -> List[Tuple[BaseNode, float]]:
        if self.corpus_size == 0:
            return []
            
        scores = []
        query_words = query_str.lower().split()
        k1 = 1.5
        b = 0.75
        
        for idx, node in enumerate(self.nodes):
            score = 0.0
            doc_freq = self.doc_freqs[idx]
            doc_len = self.doc_lens[idx]
            
            for word in query_words:
                if word not in doc_freq:
                    continue
                df = self.df[word]
                # Inverse Document Frequency (with smoothing)
                idf = math.log((self.corpus_size - df + 0.5) / (df + 0.5) + 1.0)
                # Term Frequency normalization
                tf = doc_freq[word]
                val = (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * (doc_len / self.avg_doc_len)))
                score += idf * val
                
            scores.append((node, score))
            
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]


# ---------------------------------------------------------
# Multi-Step Advanced Retrieval Pipeline
# ---------------------------------------------------------
class ConcurrentRetriever(BaseRetriever):
    def __init__(self):
        self._cross_encoder = None
        self._cross_encoder_loaded = False

    def _load_cross_encoder(self):
        if self._cross_encoder_loaded:
            return
            
        if not rag_settings.use_reranker:
            logger.info("CrossEncoder reranker is disabled via configuration.")
            self._cross_encoder = None
            self._cross_encoder_loaded = True
            return
            
        # Check if local model directory exists
        from backend.rag.config import BASE_DIR
        local_model_path = os.path.join(BASE_DIR, "rag", "models", "ms-marco-MiniLM-L-6-v2")
        
        if os.path.exists(local_model_path) and os.path.isdir(local_model_path):
            model_to_load = local_model_path
            logger.info(f"Loading local CrossEncoder model from: {model_to_load}")
            is_offline = True
        else:
            model_to_load = rag_settings.reranker_model
            # Check if huggingface.co is reachable to prevent slow connection hangs
            if not is_huggingface_reachable():
                logger.warning("huggingface.co is not reachable and local model not found. Reranking will operate in offline/fallback mode (RRF).")
                self._cross_encoder = None
                self._cross_encoder_loaded = True
                return
            is_offline = False
            
        try:
            from sentence_transformers import CrossEncoder
            kwargs = {"local_files_only": True} if is_offline else {}
            self._cross_encoder = CrossEncoder(model_to_load, **kwargs)
            logger.info("CrossEncoder loaded successfully.")
        except Exception as e:
            logger.warning(f"Failed to load CrossEncoder ({e}). Reranking will use RRF scores only.")
            self._cross_encoder = None
        self._cross_encoder_loaded = True


    async def rewrite_query_hyde(self, query_str: str) -> str:
        """HyDE (Hypothetical Document Embeddings): Expands the query by generating a hypothetical answer."""
        try:
            from llama_index.llms.openai import OpenAI
            llm = OpenAI(model=rag_settings.openai_model, api_key=rag_settings.openai_api_key or "ollama", api_base=rag_settings.openai_api_base)
            prompt = (
                f"Please write a hypothetical paragraph answering the query. "
                f"Include technical details and target keywords. Do not explain anything, just output the answer.\n"
                f"Query: {query_str}\n"
                f"Answer:"
            )
            response = await llm.acomplete(prompt)
            hyde_query = f"{query_str} {response.text}"
            logger.info(f"HyDE expansion completed.")
            return hyde_query
        except Exception as e:
            logger.warning(f"HyDE query rewriting failed: {e}. Using original query.")
            return query_str

    async def retrieve(self, query_str: str, **kwargs: Any) -> List[NodeWithScore]:
        # 1. Expand query via HyDE if enabled and not a tabular query (to prevent hallucinated answers from throwing off structured search)
        lower_query = query_str.lower()
        tabular_keywords = ["categories", "rows", "tickets", "rejection", "countries", "occurrences", "frequency", "descending", "xlsx", "csv", "dataset", "table", "column", "count", "summary"]
        is_tabular_query = any(kw in lower_query for kw in tabular_keywords)
        
        if rag_settings.use_hyde and not is_tabular_query:
            expanded_query = await self.rewrite_query_hyde(query_str)
        else:
            expanded_query = query_str


        
        # 2. Get active child nodes from docstore to construct BM25 corpus
        docstore = get_docstore()
        all_nodes = list(docstore.docs.values())
        child_nodes = [node for node in all_nodes if node.parent_node is not None]
        
        # 3. Concurrent search: Vector, BM25, and Graph Traversal
        vector_store = await get_vector_store()
        
        # Run Vector and Graph queries in parallel
        vector_task = vector_store.query(expanded_query, similarity_top_k=rag_settings.similarity_top_k)
        
        # Extract entity from query for graph traversal
        entity_name = query_str.strip() # simplest heuristic, can be improved via Named Entity Recognition
        graph_manager = get_graph_manager()
        graph_task = graph_manager.query_neighborhood(entity_name)
        
        vector_results, graph_triples = await asyncio.gather(vector_task, graph_task)
        
        # Run BM25 keyword matching
        bm25_index = SimpleBM25(child_nodes)
        bm25_results = bm25_index.query(query_str, top_k=rag_settings.similarity_top_k)
        
        # 4. Fusing results using Reciprocal Rank Fusion (RRF)
        rrf_scores: Dict[str, float] = {}
        node_map: Dict[str, BaseNode] = {}
        
        # Process Vector rank
        for rank, node_with_score in enumerate(vector_results):
            node = node_with_score.node
            node_id = node.node_id
            node_map[node_id] = node
            rrf_scores[node_id] = rrf_scores.get(node_id, 0.0) + (1.0 / (60.0 + rank))
            
        # Process BM25 rank
        for rank, (node, score) in enumerate(bm25_results):
            node_id = node.node_id
            node_map[node_id] = node
            rrf_scores[node_id] = rrf_scores.get(node_id, 0.0) + (1.0 / (60.0 + rank))
            
        # Sort by RRF score descending
        fused_node_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)
        fused_nodes = [node_map[nid] for nid in fused_node_ids]
        
        # 5. Cross-Encoder Reranking
        self._load_cross_encoder()
        reranked_nodes: List[NodeWithScore] = []
        
        if self._cross_encoder and fused_nodes:
            try:
                pairs = [(query_str, node.get_content()) for node in fused_nodes]
                scores = self._cross_encoder.predict(pairs)
                
                for idx, score in enumerate(scores):
                    reranked_nodes.append(NodeWithScore(node=fused_nodes[idx], score=float(score)))
                reranked_nodes.sort(key=lambda x: x.score, reverse=True)
            except Exception as e:
                logger.error(f"Reranking error: {e}")
                # Fallback to RRF ranking
                for nid in fused_node_ids:
                    reranked_nodes.append(NodeWithScore(node=node_map[nid], score=rrf_scores[nid]))
        else:
            # Fallback if cross-encoder isn't loaded
            for nid in fused_node_ids:
                reranked_nodes.append(NodeWithScore(node=node_map[nid], score=rrf_scores[nid]))
                
        # Filter top-K and apply confidence guardrail threshold
        top_reranked = reranked_nodes[:rag_settings.rerank_top_k]
        
        # Filter using a threshold if using Cross-Encoder scores
        if self._cross_encoder:
            # Keep nodes with score >= -9.0 (prevent filtering out semi-structured summaries while still discarding garbage/noise)
            top_reranked = [n for n in top_reranked if n.score >= -9.0]
            
        # 6. Resolve back to 1000-token Parent Nodes
        final_context_nodes: List[NodeWithScore] = []
        for child_node_with_score in top_reranked:
            child_node = child_node_with_score.node
            parent_id = child_node.parent_node.node_id if child_node.parent_node else None
            
            if parent_id and parent_id in docstore.docs:
                parent_node = docstore.docs[parent_id]
                # Combine child score with parent context
                final_context_nodes.append(NodeWithScore(node=parent_node, score=child_node_with_score.score))
            else:
                final_context_nodes.append(child_node_with_score)
                
        # Store metadata about graph triples in kwargs to pass along
        kwargs["graph_triples"] = graph_triples
        kwargs["hyde_query"] = expanded_query
        
        return final_context_nodes
