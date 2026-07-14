import asyncio
import os
from crewai import Agent, Task, Crew, LLM, Process
from crewai.tools import tool
from backend.config import settings
from backend.agent.kg_retriever import kg_retriever
import json

if settings.openai_api_key:
    os.environ["OPENAI_API_KEY"] = settings.openai_api_key

@tool("recognize_intent_and_extract_entities")
def recognize_intent_and_extract_entities(query: str) -> str:
    """Perform semantic lookup to identify the primary telecom intent and key entity pointers from the customer's query.
    Returns a JSON string containing the matched intent node ID/label and relevant proxy pointer IDs/labels.
    """
    res = kg_retriever.retrieve_intent_and_pointers(query)
    intent = res["intent_node"]
    intent_id = intent["id"] if intent else None
    intent_label = intent["label"] if intent else None
    pointers = [{ "id": p["id"], "label": p["label"], "type": p["type"] } for p in res["proxy_pointers"]]
    
    return json.dumps({
        "intent_id": intent_id,
        "intent_label": intent_label,
        "intent_score": res["intent_score"],
        "proxy_pointers": pointers,
        "avg_proxy_score": res["avg_proxy_score"]
    })

@tool("get_knowledge_graph_triplets")
def get_knowledge_graph_triplets(intent_id: str, proxy_pointer_ids_json: str) -> str:
    """Retrieve all matching ontology triplets (semantic relations) from the knowledge graph connected to the given intent and proxy pointers.
    Pass the intent_id and a JSON array string of proxy pointer IDs (e.g. '["service_ims_volte", "error_low_sinr"]').
    Returns a list of triplets in readable source-relation-target format.
    """
    try:
        pointer_ids = json.loads(proxy_pointer_ids_json)
    except Exception:
        pointer_ids = []
    
    triplets = kg_retriever.get_triplets_matching(intent_id, pointer_ids)
    return json.dumps(triplets)

async def main():
    llm = LLM(
        model=settings.openai_model,
        stream=True,
        temperature=0.0
    )
    
    agent = Agent(
        role="Customer Complaint Analyst",
        goal="Identify the customer's intent, query relevant telecom knowledge graph and guide the customer agent which team can fix the issue",
        backstory=(
            "You are a customer complaint analyst that can use knowledge graph to answer the user query. "
        ),
        verbose=True,
        tools=[recognize_intent_and_extract_entities, get_knowledge_graph_triplets],
        llm=llm
    )
    
    task = Task(
        description=(
            "Identify the telecom intent and entity pointers from the query: '5G cellular network speed degradation, high packet latency and low bandwidth'. "
            "Use recognize_intent_and_extract_entities to do intent lookup, and then use get_knowledge_graph_triplets to find triplets. "
            "Explain the issue and the support team based on these results.\n"
            "   - Keep it concise (under 50 words).\n"
            "   - Do NOT use markdown.\n"
            "   - You MUST prefix your response with 'Final Answer:'."
        ),
        expected_output="Response grounded in the knowledge graph results under 50 words",
        agent=agent,
    )
    
    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=True,
        stream=True
    )
    
    streaming = await crew.kickoff_async()
    async for chunk in streaming:
        print(chunk.content, end="", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
