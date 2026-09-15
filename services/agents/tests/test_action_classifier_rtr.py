"""
Unit test verifying that Mark correctly classifies Customer Ticket Journeys and RTR Shift Summaries.
"""

import pytest
from assistant.mark.action_classifier import classify_action
from assistant.mark.user_actions import UserAction


def test_classify_customer_ticket_journey():
    query = "Mark, trace journey for ticket TT-984210"
    classified = classify_action(query)
    assert classified.action == UserAction.CUSTOMER_TICKET_JOURNEY
    assert classified.engine_id == "telecom_brain"


def test_classify_customer_ticket_variations():
    queries = [
        "walk me through the ticket TT-10293",
        "show me the customer ticket journey for TT-5512",
        "what are the ticket hops for TT-88219",
    ]
    for q in queries:
        classified = classify_action(q)
        assert classified.action == UserAction.CUSTOMER_TICKET_JOURNEY


def test_classify_rtr_shift_summary():
    queries = [
        "Mark, give me the RTR shift summary",
        "share the curated summary of the customer tickets handled by RTR",
        "summary of tickets in rtr queues",
    ]
    for q in queries:
        classified = classify_action(q)
        assert classified.action == UserAction.RTR_SHIFT_SUMMARY


def test_major_incident_still_routes_to_incident_storytelling():
    query = "Explain incident INC-9812"
    classified = classify_action(query)
    assert classified.action == UserAction.EXPLAIN_INCIDENT
    assert classified.target_intent == "story"
