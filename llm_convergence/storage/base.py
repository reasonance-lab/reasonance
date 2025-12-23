from abc import ABC, abstractmethod
from typing import Optional
from ..domain.models import Conversation


class StorageBackend(ABC):
    """Abstract base class for storage backends."""

    @abstractmethod
    async def save(self, conversation: Conversation) -> None:
        """Save a conversation to storage."""
        pass

    @abstractmethod
    async def get(self, conversation_id: str) -> Optional[Conversation]:
        """Retrieve a conversation by ID."""
        pass

    @abstractmethod
    async def delete(self, conversation_id: str) -> None:
        """Delete a conversation by ID."""
        pass
