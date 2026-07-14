import os
import json
import hashlib
import yaml
import numpy as np
import openai
import time
from backend.config import settings

# Global in-memory cache to prevent duplicate query embedding computations
_EMBEDDING_CACHE = {}

class KnowledgeGraphRetriever:
    def __init__(self):
        self.nodes = []
        self.links = []
        self.embeddings = {}
        self.model = None
        self.cross_encoder = None
        self.initialized = False
        self.node_map = {}
        self.causal_rules = {}
        self.adj = {}
        self.label_map = {}
        self.openai_disabled = False

    def initialize(self):
        if self.initialized:
            return

        # 1. Load base graph data from trace_graph.json
        trace_graph_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__), "../../trace_graph.json"
        ))
        
        base_nodes = []
        base_links = []
        
        if os.path.exists(trace_graph_path):
            try:
                with open(trace_graph_path, "r") as f:
                    graph_data = json.load(f)
                    base_nodes = graph_data.get("nodes", [])
                    base_links = graph_data.get("links", [])
                print(f"[KnowledgeGraphRetriever] Loaded {len(base_nodes)} nodes and {len(base_links)} links from trace_graph.json")
            except Exception as e:
                print(f"[KnowledgeGraphRetriever] Error loading trace_graph.json: {e}")
        else:
            print(f"[KnowledgeGraphRetriever] Warning: trace_graph.json not found at {trace_graph_path}")

        # 2. Load dynamic rules/FAQs from causal_rules.yaml and inject them
        faqs = []
        try:
            from backend.agent.complaint_analyst import _get_causal_rules
            self.causal_rules = _get_causal_rules()
            faqs = self.causal_rules.get("faqs", [])
        except Exception as e:
            print(f"[KnowledgeGraphRetriever] Error loading causal_rules: {e}")

        # If causal_rules contains an explicit relationships section, prefer building the
        # canonical graph from the YAML (single source of truth) and auto-sync trace_graph.json
        relationships = self.causal_rules.get("relationships", []) if self.causal_rules else []
        if relationships:
            print(f"[KnowledgeGraphRetriever] Building graph from causal_rules.yaml relationships ({len(relationships)} links)")
            # Build nodes collection from intents, faqs, other_nodes, fallbacks
            built_nodes = {}

            for nid, entry in (self.causal_rules.get("intents", {}) or {}).items():
                built_nodes[nid] = {
                    "id": nid,
                    "label": entry.get("label", nid),
                    "type": "Intent",
                    "description": entry.get("description", "")
                }

            for faq in faqs:
                fid = faq.get("id")
                built_nodes[fid] = {
                    "id": fid,
                    "label": faq.get("label", fid),
                    "type": "FAQ",
                    "description": faq.get("action", "")
                }

            for nid, entry in (self.causal_rules.get("other_nodes", {}) or {}).items():
                built_nodes[nid] = {
                    "id": nid,
                    "label": entry.get("label", nid),
                    "type": entry.get("type", "Node"),
                    "description": entry.get("description", "")
                }

            # Fallbacks as domain nodes
            for fid, entry in (self.causal_rules.get("fallbacks", {}) or {}).items():
                node_id = f"fallback_{fid.lower()}"
                built_nodes[node_id] = {
                    "id": node_id,
                    "label": f"{fid} Fallback",
                    "type": "Fallback",
                    "description": "Domain fallback node"
                }

            # Target teams as Team nodes
            for tid, entry in (self.causal_rules.get("target_teams", {}) or {}).items():
                built_nodes[tid] = {
                    "id": tid,
                    "label": entry.get("name", tid),
                    "type": "Team",
                    "description": f"Escalation queue: {entry.get('queue', '')}. Hotline: {entry.get('hotline', '')}"
                }

            # Replace in-memory nodes and links with built graph
            self.nodes = list(built_nodes.values())
            self.links = []
            for rel in relationships:
                src = rel.get("source")
                tgt = rel.get("target")
                label = rel.get("label", "rel")
                link = {"source": src, "target": tgt, "label": label}
                self.links.append(link)

            # Auto-sync compiled graph to trace_graph.json for frontend/export
            try:
                compiled = {"nodes": self.nodes, "links": self.links}
                with open(trace_graph_path, "w") as f:
                    json.dump(compiled, f, indent=2)
                print(f"[KnowledgeGraphRetriever] Synced compiled graph to {trace_graph_path}")
            except Exception as e:
                print(f"[KnowledgeGraphRetriever] Failed to write trace_graph.json: {e}")
            # Prevent the fallback merge below from re-adding the same graph.
            base_nodes = self.nodes.copy()
            base_links = self.links.copy()

        # Extract standard description fallback dictionary dynamically from causal_rules.yaml
        default_descriptions = {}
        if self.causal_rules:
            # Load other CKG nodes (services, platforms, preconditions, errors, channels, profiles, app types)
            other_nodes_desc = self.causal_rules.get("other_nodes", {})
            for nid, entry in other_nodes_desc.items():
                default_descriptions[nid] = entry.get("description", "")
            # Load core intents
            intents_desc = self.causal_rules.get("intents", {})
            for nid, entry in intents_desc.items():
                default_descriptions[nid] = entry.get("description", "")


        # Build in-memory nodes list
        existing_node_ids = set()
        seen_node_ids = set()
        for node in base_nodes:
            node_id = node["id"]
            if node_id.startswith("hub_"):
                # Hub nodes are transient visual elements, skip embedding computation
                continue
            if node_id in seen_node_ids:
                continue
            
            # Ensure description is populated
            if "description" not in node:
                node["description"] = default_descriptions.get(node_id, node.get("label", ""))
                
            self.nodes.append(node)
            existing_node_ids.add(node_id)
            seen_node_ids.add(node_id)

        # Inject FAQs dynamically from causal_rules.yaml if they aren't already present
        for faq in faqs:
            faq_id = faq["id"]
            if faq_id not in existing_node_ids:
                faq_node = {
                    "id": faq_id,
                    "label": faq["label"],
                    "type": "FAQ",
                    "description": f"FAQ support topic: {faq['label']}. Keywords: {', '.join(faq['keywords'])}. Action: {faq['action']}"
                }
                self.nodes.append(faq_node)
                existing_node_ids.add(faq_id)

        # Build links list (skipping hub links as they are visual-only)
        seen_links = set()
        for link in base_links:
            if link.get("isHubLink"):
                continue
            link_key = (link.get("source"), link.get("target"), link.get("label"))
            if link_key in seen_links:
                continue
            seen_links.add(link_key)
            self.links.append(link)

        # Build node maps for fast lookup
        self.node_map = {node["id"]: node for node in self.nodes}

        # Load vectorstore cache if it exists
        vectorstore_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__), "vectorstore.json"
        ))
        
        vectorstore = {}
        if os.path.exists(vectorstore_path):
            try:
                with open(vectorstore_path, "r") as f:
                    vectorstore = json.load(f)
            except Exception as e:
                print(f"[KnowledgeGraphRetriever] Error loading vectorstore.json cache: {e}")

        # Generate or load embeddings for each node description + label
        print("[KnowledgeGraphRetriever] Initializing node embeddings...")
        updated_cache = False
        
        for node in self.nodes:
            node_id = node['id']
            text = f"{node['label']} {node.get('description', '')}"
            text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
            
            cached_entry = vectorstore.get(node_id)
            if cached_entry and cached_entry.get("text_hash") == text_hash and cached_entry.get("model") == settings.openai_embedding_model:
                emb = np.array(cached_entry["embedding"])
                is_openai = cached_entry.get("is_openai", True)
                self.embeddings[node_id] = (emb, is_openai)
            else:
                print(f"[KnowledgeGraphRetriever] Embedding cache miss for node: {node_id}")
                emb, is_openai = self.get_embedding(text)
                self.embeddings[node_id] = (emb, is_openai)
                vectorstore[node_id] = {
                    "text_hash": text_hash,
                    "embedding": emb.tolist(),
                    "model": settings.openai_embedding_model,
                    "is_openai": is_openai
                }
                updated_cache = True

        if updated_cache:
            try:
                with open(vectorstore_path, "w") as f:
                    json.dump(vectorstore, f, indent=2)
                print(f"[KnowledgeGraphRetriever] Saved updated embeddings cache to {vectorstore_path}")
            except Exception as e:
                print(f"[KnowledgeGraphRetriever] Error saving vectorstore.json: {e}")

        # Pre-compute adjacency list (unique neighbors only) and label map
        self.adj = {}
        for link in self.links:
            src = link.get("source")
            tgt = link.get("target")
            if src and tgt:
                self.adj.setdefault(src, set()).add(tgt)
        self.label_map = {node["id"]: node.get("label", node["id"]) for node in self.nodes}

        self.initialized = True
        print(f"[KnowledgeGraphRetriever] Initialized with {len(self.nodes)} nodes for search.")

    def get_embedding(self, text: str, force_local: bool = False) -> tuple[np.ndarray, bool]:
        cache_key = (text, force_local, settings.openai_embedding_model)
        if cache_key in _EMBEDDING_CACHE:
            return _EMBEDDING_CACHE[cache_key]
            
        emb, is_openai = self._get_embedding_internal(text, force_local)
        _EMBEDDING_CACHE[cache_key] = (emb, is_openai)
        return emb, is_openai

    def _get_embedding_internal(self, text: str, force_local: bool = False) -> tuple[np.ndarray, bool]:
        if settings.openai_api_key and not force_local and not getattr(self, "openai_disabled", False):
            try:
                client = openai.OpenAI(api_key=settings.openai_api_key, max_retries=1)
                response = client.embeddings.create(
                    input=[text],
                    model=settings.openai_embedding_model
                )
                emb = np.array(response.data[0].embedding)
                return emb / np.linalg.norm(emb), True
            except Exception as e:
                self.openai_disabled = True
                print(f"[KnowledgeGraphRetriever] OpenAI embedding failed: {e}. Circuit broken, permanently falling back to local SentenceTransformer model.")

        # Lazy load the SentenceTransformer model on demand as a fallback
        if self.model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self.model = SentenceTransformer('all-MiniLM-L6-v2')
                print("[KnowledgeGraphRetriever] Loaded local SentenceTransformer model on demand.")
            except Exception as e:
                print(f"[KnowledgeGraphRetriever] SentenceTransformer load failed: {e}.")

        if self.model is not None:
            try:
                emb = self.model.encode(text)
                return emb / np.linalg.norm(emb), False
            except Exception as e:
                print(f"[KnowledgeGraphRetriever] Local encoding failed: {e}")

        # Pure-Python BoW Fallback
        words = text.lower().split()
        emb = np.zeros(384)
        for word in words:
            h = hash(word) % 384
            emb[h] += 1.0
        norm = np.linalg.norm(emb)
        if norm > 0:
            emb = emb / norm
        return emb, False

    def _get_cross_encoder(self):
        if self.cross_encoder is None:
            try:
                from sentence_transformers import CrossEncoder
                current_dir = os.path.dirname(os.path.abspath(__file__))
                local_model_path = os.path.abspath(os.path.join(current_dir, "../rag/models/ms-marco-MiniLM-L-6-v2"))
                if os.path.exists(local_model_path) and os.path.isdir(local_model_path):
                    self.cross_encoder = CrossEncoder(local_model_path, local_files_only=True)
                    print(f"[KnowledgeGraphRetriever] Loaded local CrossEncoder from {local_model_path}")
                else:
                    self.cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
                    print("[KnowledgeGraphRetriever] Loaded CrossEncoder from Hugging Face hub")
            except Exception as e:
                print(f"[KnowledgeGraphRetriever] Failed to load CrossEncoder: {e}")
        return self.cross_encoder

    def classify_it_or_network(self, query: str) -> dict:
        self.initialize()
        query_vector, query_is_openai = self.get_embedding(query)
        
        it_desc = "Service activation, SIM provisioning, eSIM, bundle activation, account registration, BSCS, SRO, billing, roaming configuration, number porting"
        net_desc = "Data speed slow, call drops, voice quality, 5G LTE connectivity, coverage weak, packet loss, latency, ping, signal, SINR, roaming usage"
        
        if not hasattr(self, "_it_vector") or getattr(self, "_ref_is_openai", None) != query_is_openai:
            it_vec, _ = self.get_embedding(it_desc, force_local=(not query_is_openai))
            net_vec, _ = self.get_embedding(net_desc, force_local=(not query_is_openai))
            self._it_vector = it_vec
            self._net_vector = net_vec
            self._ref_is_openai = query_is_openai
            
        it_score = float(np.dot(query_vector, self._it_vector))
        network_score = float(np.dot(query_vector, self._net_vector))
        
        diff = abs(it_score - network_score)
        if diff < 0.05:
            category = "Tie"
        elif it_score > network_score:
            category = "IT"
        else:
            category = "Network"
            
        return {
            "category": category,
            "it_score": it_score,
            "network_score": network_score
        }

    def retrieve_intent_and_pointers(self, query: str, k: int = 5, use_cross_encoder: bool = True) -> dict:
        self.initialize()

        query_vector, is_openai = self.get_embedding(query)

        # Compute cosine similarities
        scores = []
        raw_lower = query.lower()
        for node in self.nodes:
            node_vector, node_is_openai = self.embeddings[node['id']]
            if is_openai != node_is_openai:
                node_text = f"{node['label']} {node.get('description', '')}"
                node_vector, _ = self.get_embedding(node_text, force_local=(not is_openai))
            similarity = float(np.dot(query_vector, node_vector))

            # Apply keyword boost for Intents & FAQs (Config-driven Score Boost)
            if self.causal_rules:
                if node["type"] == "Intent":
                    intent_entry = self.causal_rules.get("intents", {}).get(node["id"], {})
                    keywords = intent_entry.get("keywords", [])
                    if any(kw in raw_lower for kw in keywords):
                        similarity = min(1.0, similarity + 0.15)
                elif node["type"] == "FAQ":
                    faq_entry = next((f for f in self.causal_rules.get("faqs", []) if f["id"] == node["id"]), None)
                    if faq_entry:
                        keywords = faq_entry.get("keywords", [])
                        if any(kw in raw_lower for kw in keywords):
                            similarity = min(1.0, similarity + 0.15)

            scores.append((node, similarity))

        # Sort by similarity score descending
        scores.sort(key=lambda x: x[1], reverse=True)

        # Re-rank top candidates using CrossEncoder if available
        candidates_to_rerank = []
        for node, sim in scores:
            if node["type"] in ["Intent", "FAQ"]:
                candidates_to_rerank.append((node, sim))
                if len(candidates_to_rerank) >= 15:
                    break
                    
        if use_cross_encoder:
            cross_encoder = self._get_cross_encoder()
            if cross_encoder is not None and len(candidates_to_rerank) > 0:
                try:
                    pairs = []
                    for node, _ in candidates_to_rerank:
                        node_text = f"{node['label']} {node.get('description', '')}"
                        pairs.append((query, node_text))
                    
                    ce_scores = cross_encoder.predict(pairs)
                    
                    # Sigmoid normalization to 0-1 range
                    normalized_scores = []
                    for score in ce_scores:
                        ns = 1.0 / (1.0 + np.exp(-float(score)))
                        normalized_scores.append(ns)
                        
                    reranked = []
                    for idx, (node, _) in enumerate(candidates_to_rerank):
                        reranked.append((node, normalized_scores[idx]))
                    reranked.sort(key=lambda x: x[1], reverse=True)
                    
                    reranked_ids = {n["id"] for n, _ in reranked}
                    remaining_scores = [(n, s) for n, s in scores if n["id"] not in reranked_ids]
                    
                    scores = reranked + remaining_scores
                except Exception as e:
                    print(f"[KnowledgeGraphRetriever] Error running CrossEncoder reranking: {e}")

        # Find the highest-scoring Intent or FAQ node, and collect sorted candidates
        intent_node = None
        intent_score = 0.0
        
        faq_node = None
        faq_score = 0.0

        ranked_candidates = []
        seen_ranked_ids = set()

        for node, score in scores:
            if node["type"] in ["Intent", "FAQ"]:
                if node["id"] in seen_ranked_ids:
                    continue
                seen_ranked_ids.add(node["id"])
                ranked_candidates.append({
                    "node": node,
                    "score": score
                })
            
            if node["type"] == "FAQ" and faq_node is None:
                faq_node = node
                faq_score = score
            elif node["type"] == "Intent" and intent_node is None:
                intent_node = node
                intent_score = score

        # Get remaining top K high-scoring nodes as Proxy Pointers
        top_k = scores[:k]
        proxy_pointers = []
        proxy_scores = []
        seen_proxy_ids = set()
        
        matched_primary_ids = set()
        if intent_node:
            matched_primary_ids.add(intent_node["id"])
        if faq_node:
            matched_primary_ids.add(faq_node["id"])

        for node, score in top_k:
            if node["id"] in matched_primary_ids:
                continue
            if node["id"] in seen_proxy_ids:
                continue
            proxy_pointers.append(node)
            proxy_scores.append(score)
            seen_proxy_ids.add(node["id"])

        avg_proxy_score = float(np.mean(proxy_scores)) if proxy_scores else 0.0

        return {
            "intent_node": intent_node,
            "intent_score": intent_score,
            "faq_node": faq_node,
            "faq_score": faq_score,
            "proxy_pointers": proxy_pointers,
            "avg_proxy_score": avg_proxy_score,
            "is_openai": is_openai,
            "ranked_candidates": ranked_candidates
        }

    def get_triplets_matching(self, intent_id: str, pointer_ids: list[str]) -> list[str]:
        """Find links connected directly to the intent or pointer entities."""
        self.initialize()
        matched_links = []
        target_ids = set([intent_id] + pointer_ids)

        for link in self.links:
            source = link["source"]
            target = link["target"]
            label = link["label"]

            # If either endpoint is related to our query context
            if source in target_ids or target in target_ids:
                src_node = self.node_map.get(source)
                tgt_node = self.node_map.get(target)

                if src_node and tgt_node:
                    desc_str = f"({src_node['label']} [{src_node['type']}]) --[{label}]--> ({tgt_node['label']} [{tgt_node['type']}])"
                    matched_links.append(desc_str)

        return matched_links

    def trace_causal_chain(
        self,
        matched_node_id: str,
        node_score_map: dict | None = None,
        max_depth: int = 6,
        max_paths: int = 20,
    ) -> dict:
        """Traverse the CKG starting from matched_node_id and compute path likelihood scores.

        node_score_map: optional mapping of node_id -> similarity score (0.0-1.0). If omitted,
        nodes without scores receive a default low score of 0.1.
        """
        self.initialize()

        paths = []

        default_score = 0.1

        def dfs(path, depth):
            if depth > max_depth:
                return
            current = path[-1]
            # Terminal condition: reached an Error, Platform, Team, or Component node
            node = self.node_map.get(current)
            if node and node.get("type") in ("Error", "Platform", "Team", "Component") and len(path) > 1:
                # Compute path likelihood as average of node scores
                scores = [node_score_map.get(n, default_score) if node_score_map else default_score for n in path]
                path_score = float(np.mean(scores))
                
                path_copy = path.copy()
                if not any(p["path"] == path_copy for p in paths):
                    paths.append({
                        "path": path_copy,
                        "labels": [self.label_map.get(n, n) for n in path],
                        "score": path_score
                    })
                # Do not return; allow exploring further terminals

            for nbr in self.adj.get(current, set()):
                if nbr in path:
                    continue
                path.append(nbr)
                dfs(path, depth + 1)
                path.pop()

        dfs([matched_node_id], 0)

        # Sort paths by descending score and cap payload size so the agent
        # does not re-ingest an unbounded reasoning graph.
        paths.sort(key=lambda x: x["score"], reverse=True)
        if len(paths) > max_paths:
            paths = paths[:max_paths]
        print("Total paths:", len(paths))
        return {
            "matched_node": matched_node_id,
            "paths": paths,
            "path_count": len(paths),
            "generated_at": int(time.time())
        }

kg_retriever = KnowledgeGraphRetriever()
