import os
from backend.config import settings
from backend.agent.kg_retriever import kg_retriever

if settings.openai_api_key:
    os.environ["OPENAI_API_KEY"] = settings.openai_api_key

res = kg_retriever.retrieve_intent_and_pointers("5G cellular network speed degradation, high packet latency and low bandwidth")
print("Intent:", res["intent_node"])
print("Pointers:", res["proxy_pointers"])
