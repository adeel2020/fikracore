import pytest
from backend.agent.rag_agent import _create_rag_agent, execute_qna, stream_qna
from unittest.mock import patch, MagicMock

def test_rag_agent_initialization():
    """Verify that the RAG agent is created with the correct tools and settings."""
    agent = _create_rag_agent(streaming=False)
    assert agent.role == "QnA Assistant"
    assert len(agent.tools) == 1
    assert agent.tools[0].name == "query_rag_system"

@pytest.mark.anyio
@patch("backend.agent.rag_agent.Crew.kickoff_async")
async def test_execute_qna_mocked(mock_kickoff):
    """Verify that execute_qna runs the crew and returns the expected result."""
    mock_kickoff.return_value = "Mocked RAG response output."
    
    result = await execute_qna("What is the total ticket count?", "session-123")
    assert result == "Mocked RAG response output."
    mock_kickoff.assert_called_once()
