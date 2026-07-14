import logging
from typing import Dict, Any, List
from llama_index.llms.openai import OpenAI
from backend.rag.config import rag_settings
from backend.rag.services.retriever import ConcurrentRetriever

logger = logging.getLogger("rag.qna")

class RAGQueryEngine:
    def __init__(self):
        self.retriever = ConcurrentRetriever()
        self.llm = OpenAI(model=rag_settings.openai_model, api_key=rag_settings.openai_api_key or "ollama", api_base=rag_settings.openai_api_base)

    async def aquery(self, query_str: str, chat_history: List[Dict[str, str]] = []) -> Dict[str, Any]:
        try:
            rag_retrievals = []
            
            # 1. Always use the original query as-is (history condensation disabled)
            #    Every query is treated as a fresh standalone question.
            search_query = query_str
            if chat_history:
                rag_retrievals.append(f"• Active conversation history detected ({len(chat_history)} messages). Query condensation disabled — using raw user query.")
            else:
                rag_retrievals.append("• No active conversation history. Using original user query.")

            # 2. Formulate routing logic
            # Extract column names from registered schemas to use as dynamic routing keywords
            from backend.rag.pipelines.ingestion import get_docstore
            import re
            
            docstore = get_docstore()
            schema_nodes = [node for node in docstore.docs.values() if node.metadata.get("is_schema") is True]
            
            schema_cols = []
            for s_node in schema_nodes:
                cols = re.findall(r"Sanitized SQL Column Name:\s*'([^']+)'", s_node.text)
                schema_cols.extend(cols)
                orig_cols = re.findall(r"Column Name \(Original\):\s*'([^']+)'", s_node.text)
                schema_cols.extend(orig_cols)
            
            lower_query = search_query.lower()

            # ── CHART CATALOG ─────────────────────────────────────────────────────────
            # Each entry: (display_name, dom_element_id, [match_keywords])
            # dom_element_id must match the `id` attribute on the chart's GlassCard in the frontend
            CHART_CATALOG = [
                ("Top Complaint Categories",                "top-complaint-categories-card", ["first response", "response time", "issue category", "category response", "top complaint", "complaint category", "top issue"]),
                ("Top Roaming Complaints by Country",       "roaming-complaints-card",  ["roaming", "country trend", "monthly trend", "by country", "international", "ksa", "saudi", "germany", "singapore", "uk trend", "us trend", "top roaming"]),
                ("Top Rejection Reason",                    "rejection-reason-card",    ["rejection reason", "top rejection", "rejection trend", "why rejected", "top rejection"]),
                ("Top Reassignments Queue",                 "reassignments-card",       ["reassignment", "reassigned", "top queue", "reassignment trend", "top reassignments"]),
            ]

            # Graph/trend intent keywords — these trigger chart picker instead of SQL
            graph_intent_keywords = [
                "trend", "graph", "chart", "plot", "visuali", "show me the",
                "show graph", "show chart", "show trend", "display graph",
                "display chart", "see the graph", "see the chart", "see the trend"
            ]
            is_graph_request = any(kw in lower_query for kw in graph_intent_keywords)

            if is_graph_request:
                # Build the full options list for ALL charts (always shown as pills)
                chart_options = [
                    {"name": name, "dom_id": dom_id}
                    for name, dom_id, _ in CHART_CATALOG
                ]

                # Check if the query matches a specific chart — if so, mark it as pre-selected
                pre_selected_dom_id = None
                for (name, dom_id, keywords) in CHART_CATALOG:
                    if any(kw in lower_query for kw in keywords):
                        pre_selected_dom_id = dom_id
                        rag_retrievals.append(f"• Graph request — pre-selected: '{name}' (#{dom_id}).")
                        break

                if not pre_selected_dom_id:
                    rag_retrievals.append("• Graph request — no specific chart matched. Showing all options.")

                return {
                    "answer": "I cannot answer this based on the retrieved context.",
                    "source_nodes": [],
                    "hyde_query": search_query,
                    "graph_triples": [],
                    "chart_hint": pre_selected_dom_id,
                    "chart_screenshot": None,
                    "chart_options": chart_options,
                    "pre_selected_dom_id": pre_selected_dom_id,
                    "rag_retrievals": "\n".join(rag_retrievals)
                }
            # ── END CHART CATALOG ─────────────────────────────────────────────────────

            # Broad set of tabular, BI, and aggregation terms
            tabular_keywords = [
                "categories", "category", "rows", "row", "tickets", "ticket", "rejection", "rejections",
                "countries", "country", "occurrences", "occurrence", "frequency", "frequencies", "freq",
                "descending", "ascending", "xlsx", "csv", "dataset", "table", "column", "columns", "count",
                "summary", "total", "how many", "how much", "number of", "list", "share", "average", "avg",
                "sum", "distribution", "occurred", "represent", "represented", "complaint", "complaints"
            ]
            
            # Route to SQL if query matches tabular terms OR matches any columns of the active tables
            is_tabular = any(kw in lower_query for kw in tabular_keywords) or any(col.lower() in lower_query for col in schema_cols)
            
            is_sql_execution = False
            context_text = ""
            source_nodes_data = []
            graph_triples = []
            hyde_query = search_query
            
            if is_tabular and schema_nodes:
                rag_retrievals.append(f"• Tabular/BI query detected (heuristics match). Active table schemas found: {len(schema_nodes)}.")
                try:
                    # Construct table schema representation for SQL generation prompt
                    schemas_text_list = []
                    for s_node in schema_nodes:
                        schemas_text_list.append(s_node.get_content())
                    schemas_text = "\n\n".join(schemas_text_list)
                    
                    sql_gen_prompt = (
                        "You are an expert SQLite SQL generator. Given the database schemas and the user's question, "
                        "generate a single valid SQLite SQL query that answers the question.\n"
                        "CRITICAL RULES:\n"
                        "1. Use column names EXACTLY as defined in the schema — do not guess or rename them.\n"
                        "2. String comparisons for country names and categories MUST use exact case-sensitive matching (e.g., WHERE country = 'UK', not LIKE or LOWER).\n"
                        "3. If the question asks about MULTIPLE separate entities (e.g., count for UK AND count for Germany), generate a SINGLE query using a CASE/GROUP BY approach, NOT a WHERE IN clause that merges them. Example:\n"
                        "   SELECT country, COUNT(*) as total FROM tbl WHERE country IN ('UK','Germany') GROUP BY country\n"
                        "4. Never combine rows from different categories into a single count unless the user explicitly asks for a combined total.\n"
                        "5. Do not use functions or syntax not supported by SQLite.\n"
                        "6. Reply ONLY with the SQL query inside a markdown code block (```sql ... ```). Do not explain anything.\n\n"
                        "--- DATABASE SCHEMAS ---\n"
                        f"{schemas_text}\n\n"
                        "--- USER QUESTION ---\n"
                        f"{search_query}\n\n"
                        "SQL Query:"
                    )
                    
                    logger.info("Generating SQL query using LLM...")
                    sql_res = await self.llm.acomplete(sql_gen_prompt)
                    sql_output = sql_res.text.strip()
                    
                    # Parse SQL query
                    import re
                    sql_match = re.search(r"```sql\s*(.*?)\s*```", sql_output, re.DOTALL | re.IGNORECASE)
                    if sql_match:
                        sql_query = sql_match.group(1).strip()
                    else:
                        sql_query = sql_output.strip('"').strip("'").strip("`").strip()
                        
                    rag_retrievals.append(f"• Structured Relational Index Route: Formulated SQL Statement:\n  {sql_query}")
                    
                    # Execute SQL query against SQLite
                    from backend.rag.services.sql_executor import execute_sql_query
                    db_results = execute_sql_query(sql_query)
                    
                    import json
                    db_results_str = json.dumps(db_results, indent=2)
                    # Include the SQL query in context so LLM knows WHAT the results represent
                    context_text = (
                        f"SQL Query Executed:\n{sql_query}\n\n"
                        f"Query Results:\n{db_results_str}"
                    )
                    is_sql_execution = True
                    
                    rag_retrievals.append(f"• Executed SQL query successfully, retrieved {len(db_results)} rows.")
                    
                    # Create diagnostic source node data representing SQL query
                    table_name = schema_nodes[0].metadata.get("table_name", "dataset")
                    source_nodes_data.append({
                        "id": f"sql_{table_name}",
                        "content": f"SQL Statement: {sql_query}\nDatabase Output: {db_results_str[:300]}...",
                        "score": 1.0,
                        "metadata": {"table_name": table_name, "sql": sql_query}
                    })
                    
                except Exception as sql_err:
                    logger.warning(f"SQL execution failed: {sql_err}. Falling back to unstructured hybrid search path.")
                    rag_retrievals.append(f"• Relational Index Route failed: {sql_err}. Falling back to Unstructured Hybrid Search.")
                    
            if not is_sql_execution:
                # 3. Retrieve context using standard unstructured retriever (Vector + BM25 + Graph)
                retrieval_meta = {}
                context_nodes = await self.retriever.retrieve(search_query, **retrieval_meta)
                
                graph_triples = retrieval_meta.get("graph_triples", [])
                hyde_query = retrieval_meta.get("hyde_query", search_query)
                
                if hyde_query != search_query:
                    rag_retrievals.append(f"• HyDE query expansion active. Generated hypothetical response: '{hyde_query}'")
                    
                rag_retrievals.append(f"• Searched Vector Store: Retrieved {len(context_nodes)} nodes (confidence score >= -9.0).")
                if graph_triples:
                    rag_retrievals.append(f"• Traversed Neo4j Knowledge Graph: Retrieved {len(graph_triples)} neighborhood relationships.")
                else:
                    rag_retrievals.append("• Traversed Neo4j Knowledge Graph: No direct entity neighborhood matches.")
                
                # Guardrail: If no context nodes are returned, return fallback message
                if not context_nodes:
                    return {
                        "answer": "I cannot answer this based on the retrieved context.",
                        "source_nodes": [],
                        "hyde_query": hyde_query,
                        "graph_triples": [],
                        "rag_retrievals": "\n".join(rag_retrievals)
                    }
                    
                context_text_list = []
                for idx, node_with_score in enumerate(context_nodes):
                    node = node_with_score.node
                    context_text_list.append(f"[Document Chunk {idx+1}]:\n{node.get_content()}")
                    source_nodes_data.append({
                        "id": node.node_id,
                        "content": node.get_content()[:200] + "...",
                        "score": node_with_score.score,
                        "metadata": node.metadata
                    })
                    
                context_text = "\n\n".join(context_text_list)
            
            graph_text = ""
            if graph_triples:
                graph_lines = [f"- ({t['source']}) -> [{t['relation']}] -> ({t['target']})" for t in graph_triples]
                graph_text = "\n".join(graph_lines)
                
            # 4. Construct strict prompt (no history — every query is stateless)
            # Use different prompts depending on whether we have SQL results or document chunks
            if is_sql_execution:
                system_prompt = (
                    "You are an expert data analyst. Answer the user's question using ONLY the SQL query and results provided below.\n\n"
                    "STRICT FORMATTING RULES — follow these exactly:\n"
                    "1. ALWAYS present your answer as a clean markdown table with a header row and divider, even for a single value.\n"
                    "   Example for a single count:\n"
                    "   | Metric | Value |\n"
                    "   |--------|-------|\n"
                    "   | Complaints from Singapore | 148 |\n\n"
                    "   Example for multiple rows:\n"
                    "   | Country | Total Tickets |\n"
                    "   |---------|---------------|\n"
                    "   | UK | 156 |\n"
                    "   | Germany | 154 |\n\n"
                    "2. Use clear, human-readable column headers (not raw SQL column names like 'complaint_count' — write 'Complaint Count' instead).\n"
                    f"3. After the table, add one short plain-English sentence summarising the key insight. Note that the SQL results contain exactly {len(db_results)} rows.\n"
                    "4. Do NOT add any extra commentary, disclaimers, or apologies.\n"
                    "5. Treat the SQL results as verified facts — never say 'I cannot answer' when results are present.\n\n"
                    f"--- SQL QUERY & RESULTS ---\n{context_text}\n\n"
                )
            else:
                system_prompt = (
                    "You are an expert data analyst assistant. Answer the user's question using ONLY the data provided below.\n\n"
                    "RULES:\n"
                    "1. If the data contains structured results, present them as a clean markdown table.\n"
                    "2. If the context genuinely does not contain enough information to answer, say: 'I cannot answer this based on the retrieved context.'\n\n"
                    f"--- DATA CONTEXT ---\n{context_text}\n\n"
                )

            if graph_text:
                system_prompt += f"--- KNOWLEDGE GRAPH RELATIONSHIPS ---\n{graph_text}\n\n"

            system_prompt += f"--- USER QUERY ---\n{query_str}\n\nAnswer:"
            
            # 5. Call LLM
            logger.info("Executing LLM generation...")
            logger.info(f"CONSTRUCTED PROMPT FOR GENERATOR:\n{system_prompt}")
            response = await self.llm.acomplete(system_prompt)
            
            return {
                "answer": response.text.strip(),
                "source_nodes": source_nodes_data,
                "hyde_query": hyde_query,
                "graph_triples": graph_triples,
                "rag_retrievals": "\n".join(rag_retrievals)
            }
            
        except Exception as e:
            logger.error(f"Error in RAGQueryEngine: {e}", exc_info=True)
            return {
                "answer": f"An error occurred while processing your query: {str(e)}",
                "source_nodes": [],
                "hyde_query": query_str,
                "graph_triples": [],
                "rag_retrievals": "Failed to complete query pre-processing."
            }
long_term_memory_query_engine = RAGQueryEngine()
