"""
Unit test verifying that gbrain client retrieves the newly scaffolded Mobile RTR pages.
"""

import anyio
import pytest
from storyteller.knowledge.gbrain_client import GbrainClient


def test_gbrain_mobile_rtr_customer_ticket_journey_slug():
    client = GbrainClient(cli="embedded")
    slug = "telecom-brain/domains/mobile-core/roles/mobile-rtr/customer-ticket-journey"
    page = client.call("get_page", {"slug": slug})

    assert page is not None
    assert page["title"] == "Customer Trouble Ticket Journey: Schema, SLA Hierarchy & Bouncing Rules"
    assert "AOLA: <= 2.0 hours" in page["compiled_truth"]
    assert page["frontmatter"].get("aola_target_hours") == 2.0
    assert page["frontmatter"].get("ola_target_hours") == 6.0


def test_gbrain_mobile_rtr_queue_topology_slug():
    client = GbrainClient(cli="embedded")
    slug = "telecom-brain/domains/mobile-core/roles/mobile-rtr/queue-topology"
    page = client.call("get_page", {"slug": slug})

    assert page is not None
    assert "RTR_Mobile_Core" in page["compiled_truth"]
    assert "HPSA" in page["compiled_truth"]


def test_gbrain_mobile_rtr_curated_summary_slug():
    client = GbrainClient(cli="embedded")
    slug = "telecom-brain/domains/mobile-core/roles/mobile-rtr/rtr-curated-summary"
    page = client.call("get_page", {"slug": slug})

    assert page is not None
    assert "Mobile Core RTR Shift Curated Summary" in page["compiled_truth"]

