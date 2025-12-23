from abc import ABC, abstractmethod
from typing import List, Optional
from ..domain.models import Response


class LLMService(ABC):
    """Abstract base class for LLM service implementations."""

    @abstractmethod
    async def generate_response(
        self,
        prompt: str,
        context: Optional[List[Response]] = None
    ) -> Response:
        """
        Generate initial response to user prompt.

        Args:
            prompt: The user's prompt
            context: Optional list of previous responses for context

        Returns:
            Response object containing the LLM's response
        """
        pass

    @abstractmethod
    async def generate_critique(
        self,
        original_prompt: str,
        other_response: Response,
        own_previous: Response
    ) -> Response:
        """
        Critique another LLM's response.

        Args:
            original_prompt: The original user prompt
            other_response: The other LLM's response to critique
            own_previous: This LLM's previous response

        Returns:
            Response object containing the critique
        """
        pass
