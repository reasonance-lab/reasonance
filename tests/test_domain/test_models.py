"""Tests for domain models."""

import pytest
from datetime import datetime, timezone
from llm_convergence.llm_convergence.domain.models import Response, Round, Conversation
from llm_convergence.llm_convergence.domain.enums import LLMProvider, ConvergenceStatus


def test_response_creation():
    """Test creating a Response object."""
    response = Response(
        provider=LLMProvider.ANTHROPIC,
        content="Test response",
        is_critique=False,
        declares_convergence=False
    )

    assert response.provider == LLMProvider.ANTHROPIC
    assert response.content == "Test response"
    assert response.is_critique is False
    assert response.declares_convergence is False
    assert isinstance(response.timestamp, datetime)


def test_response_serialization():
    """Test Response to_dict and from_dict methods."""
    original = Response(
        provider=LLMProvider.ANTHROPIC,
        content="Test response",
        is_critique=True,
        declares_convergence=True
    )

    # Serialize to dict
    data = original.to_dict()
    assert data["provider"] == "anthropic"
    assert data["content"] == "Test response"
    assert data["is_critique"] is True
    assert data["declares_convergence"] is True
    assert "timestamp" in data

    # Deserialize from dict
    restored = Response.from_dict(data)
    assert restored.provider == original.provider
    assert restored.content == original.content
    assert restored.is_critique == original.is_critique
    assert restored.declares_convergence == original.declares_convergence


def test_round_creation():
    """Test creating a Round object."""
    claude_response = Response(
        provider=LLMProvider.ANTHROPIC,
        content="Claude's response"
    )
    openai_response = Response(
        provider=LLMProvider.OPENAI,
        content="GPT's response"
    )

    round_obj = Round(
        round_number=1,
        claude_response=claude_response,
        openai_response=openai_response
    )

    assert round_obj.round_number == 1
    assert round_obj.claude_response == claude_response
    assert round_obj.openai_response == openai_response
    assert round_obj.claude_critique is None
    assert round_obj.openai_critique is None


def test_round_serialization():
    """Test Round to_dict and from_dict methods."""
    original = Round(
        round_number=2,
        claude_response=Response(LLMProvider.ANTHROPIC, "Claude response"),
        openai_response=Response(LLMProvider.OPENAI, "GPT response"),
        claude_critique=Response(LLMProvider.ANTHROPIC, "Claude critique", is_critique=True),
        openai_critique=Response(LLMProvider.OPENAI, "GPT critique", is_critique=True)
    )

    # Serialize to dict
    data = original.to_dict()
    assert data["round_number"] == 2
    assert data["claude_response"]["content"] == "Claude response"
    assert data["openai_response"]["content"] == "GPT response"
    assert data["claude_critique"]["content"] == "Claude critique"
    assert data["openai_critique"]["content"] == "GPT critique"

    # Deserialize from dict
    restored = Round.from_dict(data)
    assert restored.round_number == original.round_number
    assert restored.claude_response.content == original.claude_response.content
    assert restored.openai_response.content == original.openai_response.content


def test_conversation_creation():
    """Test creating a Conversation object."""
    conversation = Conversation(
        id="test-123",
        user_prompt="What is AI?"
    )

    assert conversation.id == "test-123"
    assert conversation.user_prompt == "What is AI?"
    assert len(conversation.rounds) == 0
    assert conversation.status == ConvergenceStatus.PENDING
    assert isinstance(conversation.created_at, datetime)


def test_conversation_serialization():
    """Test Conversation to_dict and from_dict methods."""
    original = Conversation(
        id="test-456",
        user_prompt="What is AI?",
        status=ConvergenceStatus.CONVERGED
    )

    # Add a round
    original.rounds.append(Round(
        round_number=1,
        claude_response=Response(LLMProvider.ANTHROPIC, "AI is..."),
        openai_response=Response(LLMProvider.OPENAI, "AI stands for...")
    ))

    # Serialize to dict
    data = original.to_dict()
    assert data["id"] == "test-456"
    assert data["user_prompt"] == "What is AI?"
    assert data["status"] == "converged"
    assert len(data["rounds"]) == 1
    assert "created_at" in data

    # Deserialize from dict
    restored = Conversation.from_dict(data)
    assert restored.id == original.id
    assert restored.user_prompt == original.user_prompt
    assert restored.status == original.status
    assert len(restored.rounds) == len(original.rounds)
    assert restored.rounds[0].claude_response.content == "AI is..."


def test_none_handling_in_round():
    """Test that Round handles None responses correctly."""
    round_obj = Round(round_number=1)

    data = round_obj.to_dict()
    assert data["claude_response"] is None
    assert data["openai_response"] is None

    restored = Round.from_dict(data)
    assert restored.claude_response is None
    assert restored.openai_response is None
