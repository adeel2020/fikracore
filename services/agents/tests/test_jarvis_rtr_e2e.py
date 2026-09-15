"""
End-to-end integration test verifying Mark process() returns rtr_journey.
"""

import anyio
import pytest
from assistant.mark.core import JARVIS
from assistant.mark.user_actions import UserAction


def test_jarvis_process_customer_ticket_journey():
    async def _run():
        jarvis = JARVIS()
        jarvis._initialized = True
        
        query = "Mark, trace journey for ticket TT-984210"
        reply = await jarvis.process(query)

        assert "Customer Trouble Ticket Journey" in str(reply)
        assert hasattr(reply, "presentation")
        assert "rtr_journey" in reply.presentation

        rtr_data = reply.presentation["rtr_journey"]
        assert rtr_data["ticket_token"] == "TT-984210"
        assert rtr_data["aola_achieved"] is True
        assert rtr_data["ola_achieved"] is False
        assert rtr_data["delinquent_queue"] == "HPSA"
        assert len(rtr_data["hops"]) == 4

    anyio.run(_run)


def test_jarvis_process_rtr_shift_summary():
    async def _run():
        jarvis = JARVIS()
        jarvis._initialized = True

        query = "Mark, give me the RTR shift summary"
        reply = await jarvis.process(query)

        assert "Mobile Core RTR Shift Curated Summary" in str(reply)
        assert hasattr(reply, "spoken_reply")
        assert "twelve hours" in reply.spoken_reply.lower() or "tickets" in reply.spoken_reply.lower()

    anyio.run(_run)
