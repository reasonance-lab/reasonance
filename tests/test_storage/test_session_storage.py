"""Tests for session storage."""

import pytest
from llm_convergence.llm_convergence.storage.session_storage import SessionStorage
from llm_convergence.llm_convergence.domain.models import Conversation


@pytest.mark.asyncio
async def test_save_and_get():
    """Test saving and retrieving a conversation."""
    storage = SessionStorage()
    conversation = Conversation(
        id="test-123",
        user_prompt="Test prompt"
    )

    await storage.save(conversation)
    retrieved = await storage.get("test-123")

    assert retrieved is not None
    assert retrieved.id == "test-123"
    assert retrieved.user_prompt == "Test prompt"


@pytest.mark.asyncio
async def test_get_nonexistent():
    """Test retrieving a non-existent conversation."""
    storage = SessionStorage()
    retrieved = await storage.get("nonexistent")

    assert retrieved is None


@pytest.mark.asyncio
async def test_delete():
    """Test deleting a conversation."""
    storage = SessionStorage()
    conversation = Conversation(
        id="test-123",
        user_prompt="Test prompt"
    )

    await storage.save(conversation)
    await storage.delete("test-123")
    retrieved = await storage.get("test-123")

    assert retrieved is None


@pytest.mark.asyncio
async def test_clear():
    """Test clearing all conversations."""
    storage = SessionStorage()

    conv1 = Conversation(id="test-1", user_prompt="Prompt 1")
    conv2 = Conversation(id="test-2", user_prompt="Prompt 2")

    await storage.save(conv1)
    await storage.save(conv2)

    storage.clear()

    assert await storage.get("test-1") is None
    assert await storage.get("test-2") is None
