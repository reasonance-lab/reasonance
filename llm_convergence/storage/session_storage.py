from typing import Optional, Dict
from .base import StorageBackend
from ..domain.models import Conversation


class SessionStorage(StorageBackend):
    """
    Session-based storage implementation.
    Stores conversations in memory for the duration of the session.
    """

    def __init__(self):
        self._store: Dict[str, Conversation] = {}

    async def save(self, conversation: Conversation) -> None:
        """Save a conversation to the in-memory store."""
        self._store[conversation.id] = conversation

    async def get(self, conversation_id: str) -> Optional[Conversation]:
        """Retrieve a conversation from the in-memory store."""
        return self._store.get(conversation_id)

    async def delete(self, conversation_id: str) -> None:
        """Delete a conversation from the in-memory store."""
        if conversation_id in self._store:
            del self._store[conversation_id]

    def clear(self) -> None:
        """Clear all conversations from storage."""
        self._store.clear()
