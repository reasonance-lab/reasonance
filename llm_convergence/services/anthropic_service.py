import os
import logging
from typing import List, Optional
from datetime import datetime, timezone
from anthropic import APIError, APITimeoutError
from .llm_base import LLMService
from .registry import get_anthropic_client
from ..domain.models import Response
from ..domain.enums import LLMProvider

logger = logging.getLogger(__name__)


class AnthropicService(LLMService):
    """Anthropic Claude LLM service implementation with extended thinking support."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-opus-4-5-20251101",
        thinking_enabled: bool = True,
        thinking_budget: int = 16000
    ):
        """
        Initialize Anthropic service.

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            model: Model to use (defaults to claude-opus-4-5-20251101)
            thinking_enabled: Whether to enable extended thinking mode
            thinking_budget: Token budget for thinking (when enabled)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY must be provided or set in environment")

        self.client = get_anthropic_client(self.api_key)
        self.model = model
        self.thinking_enabled = thinking_enabled
        self.thinking_budget = thinking_budget
        logger.info(f"Initialized Anthropic service with model: {model}, thinking: {thinking_enabled}")

    async def generate_response(
        self,
        prompt: str,
        context: Optional[List[Response]] = None,
        system_prompt: Optional[str] = None
    ) -> Response:
        """Generate initial response to user prompt."""
        default_system = (
            "You are participating in a collaborative reasoning exercise. "
            "Another AI will also respond to this prompt independently. "
            "After initial responses, you will critique each other's outputs "
            "until you converge on a shared conclusion."
        )
        system_prompt = system_prompt or default_system

        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"{prompt}\n\nProvide your response. Be thorough but concise."
                    }
                ]
            }
        ]

        try:
            logger.info(f"Generating Claude response for prompt: {prompt[:50]}...")

            # Build request parameters
            request_params = {
                "model": self.model,
                "max_tokens": 20000,
                "system": system_prompt,
                "messages": messages,
                "timeout": 120.0
            }

            # Add thinking configuration if enabled
            if self.thinking_enabled:
                request_params["temperature"] = 1  # Required for thinking mode
                request_params["thinking"] = {
                    "type": "enabled",
                    "budget_tokens": self.thinking_budget
                }

            message = await self.client.messages.create(**request_params)

            # Extract content - handle both thinking and non-thinking responses
            content = ""
            if message.content:
                for block in message.content:
                    if hasattr(block, 'text'):
                        content += block.text
                    elif hasattr(block, 'type') and block.type == 'text':
                        content += block.text

            logger.info(f"Claude response generated successfully ({len(content)} chars)")

            return Response(
                provider=LLMProvider.ANTHROPIC,
                content=content,
                timestamp=datetime.now(timezone.utc),
                is_critique=False,
                declares_convergence=False
            )

        except APITimeoutError as e:
            logger.error(f"Claude API timeout: {e}")
            raise TimeoutError("Claude API request timed out") from e
        except APIError as e:
            logger.error(f"Claude API error: {e}")
            raise RuntimeError(f"Claude API error: {str(e)}") from e
        except Exception as e:
            logger.error(f"Unexpected error in Claude response generation: {e}")
            raise

    async def generate_critique(
        self,
        original_prompt: str,
        other_response: Response,
        own_previous: Response,
        system_prompt: Optional[str] = None,
        critique_instruction: Optional[str] = None
    ) -> Response:
        """Critique another LLM's response."""
        default_system = "You are continuing a collaborative reasoning exercise."
        default_instruction = (
            "Critique the other AI's response. Identify agreements, disagreements, "
            "and suggest refinements. If you believe you have converged on a shared "
            "conclusion, explicitly state: 'CONVERGENCE DECLARED' at the end of your response."
        )
        system_prompt = system_prompt or default_system
        critique_instruction = critique_instruction or default_instruction

        critique_text = (
            f"Original user prompt: {original_prompt}\n\n"
            f"Your previous response:\n{own_previous.content}\n\n"
            f"The other AI's response:\n{other_response.content}\n\n"
            f"{critique_instruction}"
        )

        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Here is my previous response for context."
                    }
                ]
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": own_previous.content
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": critique_text
                    }
                ]
            }
        ]

        try:
            logger.info("Generating Claude critique...")

            # Build request parameters
            request_params = {
                "model": self.model,
                "max_tokens": 20000,
                "system": system_prompt,
                "messages": messages,
                "timeout": 120.0
            }

            # Add thinking configuration if enabled
            if self.thinking_enabled:
                request_params["temperature"] = 1  # Required for thinking mode
                request_params["thinking"] = {
                    "type": "enabled",
                    "budget_tokens": self.thinking_budget
                }

            message = await self.client.messages.create(**request_params)

            # Extract content - handle both thinking and non-thinking responses
            content = ""
            if message.content:
                for block in message.content:
                    if hasattr(block, 'text'):
                        content += block.text
                    elif hasattr(block, 'type') and block.type == 'text':
                        content += block.text

            declares_convergence = "CONVERGENCE DECLARED" in content.upper()

            logger.info(f"Claude critique generated successfully (convergence: {declares_convergence})")

            return Response(
                provider=LLMProvider.ANTHROPIC,
                content=content,
                timestamp=datetime.now(timezone.utc),
                is_critique=True,
                declares_convergence=declares_convergence
            )

        except APITimeoutError as e:
            logger.error(f"Claude API timeout during critique: {e}")
            raise TimeoutError("Claude API request timed out") from e
        except APIError as e:
            logger.error(f"Claude API error during critique: {e}")
            raise RuntimeError(f"Claude API error: {str(e)}") from e
        except Exception as e:
            logger.error(f"Unexpected error in Claude critique generation: {e}")
            raise

    async def generate_peer_review_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> Response:
        """Generate initial response for peer review mode."""
        default_system = (
            "You are developing a comprehensive response to the following user prompt. "
            "Focus on clarity, accuracy, and thoroughness of your response."
        )
        system_prompt = system_prompt or default_system

        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"{prompt}\n\nProvide your response."
                    }
                ]
            }
        ]

        try:
            logger.info(f"Generating Claude peer review response for prompt: {prompt[:50]}...")

            request_params = {
                "model": self.model,
                "max_tokens": 20000,
                "system": system_prompt,
                "messages": messages,
                "timeout": 120.0
            }

            if self.thinking_enabled:
                request_params["temperature"] = 1
                request_params["thinking"] = {
                    "type": "enabled",
                    "budget_tokens": self.thinking_budget
                }

            message = await self.client.messages.create(**request_params)

            content = ""
            if message.content:
                for block in message.content:
                    if hasattr(block, 'text'):
                        content += block.text
                    elif hasattr(block, 'type') and block.type == 'text':
                        content += block.text

            logger.info(f"Claude peer review response generated ({len(content)} chars)")

            return Response(
                provider=LLMProvider.ANTHROPIC,
                content=content,
                timestamp=datetime.now(timezone.utc),
                is_critique=False,
                declares_convergence=False
            )

        except APITimeoutError as e:
            logger.error(f"Claude API timeout: {e}")
            raise TimeoutError("Claude API request timed out") from e
        except APIError as e:
            logger.error(f"Claude API error: {e}")
            raise RuntimeError(f"Claude API error: {str(e)}") from e
        except Exception as e:
            logger.error(f"Unexpected error in Claude peer review response: {e}")
            raise

    async def generate_revision(
        self,
        original_prompt: str,
        previous_response: Response,
        review_feedback: Response,
        system_prompt: Optional[str] = None,
        revision_instruction: Optional[str] = None
    ) -> Response:
        """Generate rebuttal and revised response addressing reviewer feedback."""
        default_system = (
            "You are revising your response based on feedback received. "
            "Address each point thoughtfully and improve your response where appropriate."
        )
        default_instruction = (
            "Review the feedback provided. Respond in two parts:\n\n"
            "**Part 1 - Response to Feedback:**\n"
            "Address each numbered point (M1, M2, m1, Q1, etc.):\n"
            "- State whether you: ACCEPT, PARTIALLY ACCEPT, or RESPECTFULLY DISAGREE\n"
            "- Provide brief reasoning\n"
            "- Note what changes you will make (if any)\n\n"
            "**Part 2 - Revised Response:**\n"
            "Provide your improved response incorporating accepted feedback."
        )
        system_prompt = system_prompt or default_system
        revision_instruction = revision_instruction or default_instruction

        revision_text = (
            f"Original user prompt: {original_prompt}\n\n"
            f"Your previous response:\n{previous_response.content}\n\n"
            f"Feedback received:\n{review_feedback.content}\n\n"
            f"{revision_instruction}"
        )

        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Here is my previous response for context."
                    }
                ]
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": previous_response.content
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": revision_text
                    }
                ]
            }
        ]

        try:
            logger.info("Generating Claude revision with rebuttal...")

            request_params = {
                "model": self.model,
                "max_tokens": 20000,
                "system": system_prompt,
                "messages": messages,
                "timeout": 120.0
            }

            if self.thinking_enabled:
                request_params["temperature"] = 1
                request_params["thinking"] = {
                    "type": "enabled",
                    "budget_tokens": self.thinking_budget
                }

            message = await self.client.messages.create(**request_params)

            content = ""
            if message.content:
                for block in message.content:
                    if hasattr(block, 'text'):
                        content += block.text
                    elif hasattr(block, 'type') and block.type == 'text':
                        content += block.text

            logger.info(f"Claude revision generated ({len(content)} chars)")

            return Response(
                provider=LLMProvider.ANTHROPIC,
                content=content,
                timestamp=datetime.now(timezone.utc),
                is_critique=False,
                declares_convergence=False
            )

        except APITimeoutError as e:
            logger.error(f"Claude API timeout during revision: {e}")
            raise TimeoutError("Claude API request timed out") from e
        except APIError as e:
            logger.error(f"Claude API error during revision: {e}")
            raise RuntimeError(f"Claude API error: {str(e)}") from e
        except Exception as e:
            logger.error(f"Unexpected error in Claude revision: {e}")
            raise
