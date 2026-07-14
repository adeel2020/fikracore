import asyncio
import os
import sys
import json

# Ensure the root project path is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest
from dotenv import load_dotenv
load_dotenv(dotenv_path="backend/.env")

from backend.agent.kg_retriever import kg_retriever
from backend.agent.complaint_analyst import (
    complaint_analyst as mobile_core_analyst,
    _trace_causal_chain_internal,
    _generate_causal_signature,
)


def test_trace_causal_chain_returns_scored_paths():
    kg_retriever.initialize()
    result = kg_retriever.trace_causal_chain(
        "intent_voice_drops",
        {
            "intent_voice_drops": 0.95,
            "service_ims_volte": 0.85,
            "platform_core_team": 0.75,
        },
    )

    assert result["matched_node"] == "intent_voice_drops"
    assert isinstance(result["paths"], list)
    assert len(result["paths"]) > 0
    assert all("path" in path_obj and "score" in path_obj for path_obj in result["paths"])
    assert result["paths"][0]["score"] >= 0.1


def test_trace_causal_chain_internal_and_causal_signature():
    query = "My voice calls keep dropping randomly when I try to make a phone call."
    trace_output = _trace_causal_chain_internal(query=query, matched_node_id="intent_voice_drops")

    assert "prechecks" in trace_output
    assert "trace" in trace_output
    assert trace_output["prechecks"]["mandatory_prechecks"] == [
        "Enable VoLTE from the handset settings",
        "Verify HLR subscriber voice status",
    ]
    assert trace_output["trace"]["matched_node"] == "intent_voice_drops"

    sig_text = _generate_causal_signature("intent_voice_drops", query)
    assert isinstance(sig_text, str)
    assert sig_text.startswith("intent_voice_drops_")


async def run_tests():
    print("=== Testing Mobile Core Analyst (Refactored CKG Version) ===")
    
    # Clean up unresolved complaints log if it exists
    unresolved_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "unresolved_complaints.json"
    ))
    if os.path.exists(unresolved_path):
        try:
            with open(unresolved_path, "w") as f:
                json.dump([], f)
        except Exception:
            pass

    # Query 1: Voice call drop complaint
    query_voice = "My voice calls keep dropping randomly when I try to make a phone call, maybe bad signaling."
    print(f"\n--- Testing query: '{query_voice}' ---")
    reply_voice = await asyncio.to_thread(mobile_core_analyst.analyze, query_voice)
    print("Response:\n", reply_voice)
    assert "Recognize Intent" in reply_voice, "Should contain ReAct thoughts block"
    assert "causal_signature" in reply_voice, "Should contain causal signature in thoughts block"
    assert "Final Answer:" in reply_voice, "Should prefix response with 'Final Answer:'"

    # Query 2: eSIM activation failure complaint
    query_esim = "I cannot download or activate my eSIM profile on the sm-dp+ server mismatch error."
    print(f"\n--- Testing query: '{query_esim}' ---")
    reply_esim = await asyncio.to_thread(mobile_core_analyst.analyze, query_esim)
    print("Response:\n", reply_esim)
    assert "Recognize Intent" in reply_esim, "Should contain ReAct thoughts block"
    assert "causal_signature" in reply_esim, "Should contain causal signature in thoughts block"
    assert "Final Answer:" in reply_esim, "Should prefix response with 'Final Answer:'"

    # Query 5: Roaming connection failure complaint
    query_roaming = "I am connected to roaming but still not able to use data"
    print(f"\n--- Testing query: '{query_roaming}' ---")
    reply_roaming = await asyncio.to_thread(mobile_core_analyst.analyze, query_roaming)
    print("Response:\n", reply_roaming)
    assert "intent_roaming_fail" in reply_roaming, "Should match roaming fail intent"
    assert "Verify inter-carrier Roaming Agreement status" in reply_roaming, "Should identify roaming agreement check as completed"
    assert "Check BSS profile status" in reply_roaming, "Should identify BSS profile status check as missing"
    assert "Final Answer:" in reply_roaming, "Should prefix response with 'Final Answer:'"

    # Query 3: FAQ Match - Amazon Prime cancellation
    query_amazon = "Can you help me cancel my Amazon Prime subscription?"
    print(f"\n--- Testing query: '{query_amazon}' ---")
    reply_amazon = await asyncio.to_thread(mobile_core_analyst.analyze, query_amazon)
    print("Response:\n", reply_amazon)
    assert "faq_amazon_prime_cancel" in reply_amazon, "Should match Amazon Prime cancellation FAQ node"
    assert "Final Answer:" in reply_amazon, "Should prefix response with 'Final Answer:'"

    # Query 4: Out-of-scope / Unresolved query
    query_pizza = "Can you recommend a good pizza place nearby?"
    print(f"\n--- Testing query: '{query_pizza}' ---")
    reply_pizza = await asyncio.to_thread(mobile_core_analyst.analyze, query_pizza)
    print("Response:\n", reply_pizza)
    assert "admin review" in reply_pizza.lower() or "logged" in reply_pizza.lower(), "Should mention query was logged for admin review"
    assert "Final Answer:" in reply_pizza, "Should prefix response with 'Final Answer:'"
    
    # Verify unresolved complaints file was updated
    assert os.path.exists(unresolved_path), "unresolved_complaints.json should have been created"
    with open(unresolved_path, "r") as f:
        unresolved_data = json.load(f)
    assert len(unresolved_data) > 0, "Should have logged the unresolved query"
    assert unresolved_data[-1]["query"] == query_pizza, "Logged query should match the pizza query"
    print("Unresolved Complaints Log Verified Successfully!")

    # Streaming tests
    print("\n--- Testing streaming for voice query ---")
    chunks = []
    async for chunk in mobile_core_analyst.stream_analyze(query_voice):
        print(chunk.content, end="", flush=True)
        chunks.append(chunk.content)
    full_text = "".join(chunks)
    assert len(full_text) > 0, "Streaming should have returned tokens"
    assert "Final Answer:" in full_text, "Streaming output should contain Final Answer"
    
    print("\n--- Testing streaming for unresolved query ---")
    fallback_chunks = []
    async for chunk in mobile_core_analyst.stream_analyze(query_pizza):
        fallback_chunks.append(chunk.content)
    fallback_text = "".join(fallback_chunks)
    assert "admin review" in fallback_text.lower() or "logged" in fallback_text.lower(), "Expected streaming fallback to mention logging/admin review"

    print("\n=== All Tests Passed Successfully! ===")

if __name__ == "__main__":
    asyncio.run(run_tests())

