"""
Tests for the /api/qna/chat endpoint.

Verifies that:
  1. A storyteller-style query is routed to the Storyteller workflow.
  2. A direct question is routed to the QnA workflow.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)

CHAT_URL = "/api/qna/chat"


# ------------------------------------------------------------------
# Storyteller workflow route
# ------------------------------------------------------------------
class TestStorytellerRoute:
    """Queries requesting deep analysis should dispatch to the Storyteller crew."""

    def test_storyteller_returns_complete_reply(self):
        """POST a storyteller-style query and verify the response shape."""
        response = client.post(
            CHAT_URL,
            json={
                "session_id": "test-001",
                "message": "Build me a comprehensive analysis report on Q4 revenue",
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert data["reply"]
        assert len(data["reply"]) > 0
        assert data["session_id"] == "test-001"
        assert isinstance(data["messages"], list)

    def test_storyteller_deep_dive_query(self):
        """Another storyteller variant — deep-dive analysis."""
        response = client.post(
            CHAT_URL,
            json={
                "session_id": "test-002",
                "message": "Run a deep-dive analysis across all datasets",
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert data["reply"]
        assert len(data["reply"]) > 0
        assert data["session_id"] == "test-002"

    def test_storyteller_datastory_query(self):
        """Data story requests should trigger the storyteller path."""
        response = client.post(
            CHAT_URL,
            json={
                "session_id": "test-003",
                "message": "Share the datastory for inventory snapshot data set",
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert data["reply"]
        assert len(data["reply"]) > 0
        assert data["session_id"] == "test-003"


# ------------------------------------------------------------------
# QnA workflow route
# ------------------------------------------------------------------
class TestQnARoute:
    """Direct questions should dispatch to the QnA crew and return a reply."""

    def test_qna_returns_complete_status(self):
        """POST a QnA-style query and verify the response shape."""
        response = client.post(
            CHAT_URL,
            json={
                "session_id": "test-001",
                "message": "What was the churn rate last quarter?",
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert data["reply"]
        assert len(data["reply"]) > 0
        assert data["session_id"] == "test-001"

    def test_qna_metric_query(self):
        """A specific metric question should route to QnA."""
        response = client.post(
            CHAT_URL,
            json={
                "session_id": "test-004",
                "message": "Which warehouse has the lowest inventory count?",
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert data["reply"]
        assert len(data["reply"]) > 0
        assert data["session_id"] == "test-004"

    def test_qna_question_with_storyteller_keywords(self):
        """A direct question should still route to QnA even if it contains analysis words."""
        response = client.post(
            CHAT_URL,
            json={
                "session_id": "test-005",
                "message": "What is the headline finding from the churn analysis?",
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert data["reply"]
        assert len(data["reply"]) > 0
        assert data["session_id"] == "test-005"


class TestQnAChatRoute:
    """Direct QnA chat endpoint should accept a message and return chat state."""

    def test_chat_endpoint_returns_reply_and_messages(self):
        response = client.post(
            "/api/qna/chat",
            json={
                "session_id": "chat-001",
                "message": "What is the average revenue per enterprise customer?",
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert data["session_id"] == "chat-001"
        assert data["reply"]
        assert isinstance(data["messages"], list)
        assert len(data["messages"]) >= 2
        assert data["telemetry"]["estimated_tokens"] >= 0


# ------------------------------------------------------------------
# Input validation
# ------------------------------------------------------------------
class TestInputValidation:
    """Pydantic validation should reject malformed requests."""

    def test_missing_message_returns_422(self):
        response = client.post(
            CHAT_URL,
            json={"session_id": "test-001"},
        )
        assert response.status_code == 422

    def test_empty_message_returns_422(self):
        response = client.post(
            CHAT_URL,
            json={"session_id": "test-001", "message": ""},
        )
        assert response.status_code == 422


# ------------------------------------------------------------------
# Session Locked Context & Signaling Analyst Validation
# ------------------------------------------------------------------
class TestSessionLockedContext:
    """Verifies session-locked routing and signaling analyst validation."""

    def test_signaling_lock_and_intercept(self):
        session_id = "session-lock-test-123"

        # 1. Send trace command to establish signaling lock
        response = client.post(
            CHAT_URL,
            json={
                "session_id": session_id,
                "message": "/trace-analyzer camel2.pcap",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["reply"]

        # 2. Send follow-up off-topic message under the locked session
        response2 = client.post(
            CHAT_URL,
            json={
                "session_id": session_id,
                "message": "unable to use data",
            },
        )
        assert response2.status_code == 200
        data2 = response2.json()
        
        # Should gracefully answer and explain that it only provides pcap tracing
        assert "Senior Telecom Signaling Analyst" in data2["reply"]
        assert "PCAP" in data2["reply"] or "trace file" in data2["reply"]

        # 3. Verify a different/new session is NOT locked and processes normally
        other_session_id = "session-lock-test-other"
        response3 = client.post(
            CHAT_URL,
            json={
                "session_id": other_session_id,
                "message": "unable to use data",
            },
        )
        assert response3.status_code == 200
        data3 = response3.json()
        # Should route to complaint analyst or QnA, not the signaling redirect
        assert "Senior Telecom Signaling Analyst" not in data3["reply"]

