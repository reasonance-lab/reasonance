import os
import logging
from typing import List, Optional
from datetime import datetime, timezone
from openai import APIError, APITimeoutError
from .llm_base import LLMService
from .registry import get_openai_client
from ..domain.models import Response
from ..domain.enums import LLMProvider

logger = logging.getLogger(__name__)


class OpenAIService(LLMService):
    """OpenAI GPT LLM service implementation using the Responses API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-5.2",
        effort: Optional[str] = "high"
    ):
        """
        Initialize OpenAI service.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: Model to use (gpt-5.2 or gpt-5.2-pro)
            effort: Reasoning effort level for gpt-5.2 (high or xhigh)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY must be provided or set in environment")

        self.client = get_openai_client(self.api_key)
        self.model = model
        self.effort = effort
        logger.info(f"Initialized OpenAI service with model: {model}, effort: {effort}")

    def _build_text_config(self) -> dict:
        """Build text configuration based on model."""
        if self.model == "gpt-5.2-pro":
            return {
                "format": {
                    "type": "text"
                }
            }
        else:
            return {
                "format": {
                    "type": "text"
                },
                "verbosity": "medium"
            }

    def _build_reasoning_config(self) -> dict:
        """Build reasoning configuration based on model."""
        if self.model == "gpt-5.2-pro":
            return {
                "summary": "auto"
            }
        else:
            return {
                "effort": self.effort or "high",
                "summary": "auto"
            }

    async def generate_response(
        self,
        prompt: str,
        context: Optional[List[Response]] = None,
        developer_message: Optional[str] = None
    ) -> Response:
        """Generate initial response to user prompt using Responses API."""
        default_developer = (
            "You are participating in a collaborative reasoning exercise. "
            "Another AI will also respond to this prompt independently. "
            "After initial responses, you will critique each other's outputs "
            "until you converge on a shared conclusion."
        )
        developer_message = developer_message or default_developer

        input_messages = [
            {
                "role": "developer",
                "content": [
                    {
                        "type": "input_text",
                        "text": developer_message
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": f"{prompt}\n\nProvide your response. Be thorough but concise."
                    }
                ]
            }
        ]

        try:
            logger.info(f"Generating GPT response for prompt: {prompt[:50]}...")
            response = await self.client.responses.create(
                model=self.model,
                input=input_messages,
                text=self._build_text_config(),
                reasoning=self._build_reasoning_config(),
                tools=[],
                store=True,
                include=[
                    "reasoning.encrypted_content",
                    "web_search_call.action.sources"
                ],
                timeout=120.0
            )

            # Extract content from response
            content = ""
            if hasattr(response, 'output') and response.output:
                for item in response.output:
                    if hasattr(item, 'content') and item.content:  # Added null check
                        for content_item in item.content:
                            if hasattr(content_item, 'text'):
                                content += content_item.text

            logger.info(f"GPT response generated successfully ({len(content)} chars)")

            return Response(
                provider=LLMProvider.OPENAI,
                content=content,
                timestamp=datetime.now(timezone.utc),
                is_critique=False,
                declares_convergence=False
            )

        except APITimeoutError as e:
            logger.error(f"OpenAI API timeout: {e}")
            raise TimeoutError("OpenAI API request timed out") from e
        except APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise RuntimeError(f"OpenAI API error: {str(e)}") from e
        except Exception as e:
            logger.error(f"Unexpected error in GPT response generation: {e}")
            raise

    async def generate_critique(
        self,
        original_prompt: str,
        other_response: Response,
        own_previous: Response,
        developer_message: Optional[str] = None,
        critique_instruction: Optional[str] = None
    ) -> Response:
        """Critique another LLM's response using Responses API."""
        default_developer = "You are continuing a collaborative reasoning exercise."
        default_instruction = (
            "Critique the other AI's response. Identify agreements, disagreements, "
            "and suggest refinements. If you believe you have converged on a shared "
            "conclusion, explicitly state: 'CONVERGENCE DECLARED' at the end of your response."
        )
        developer_message = developer_message or default_developer
        critique_instruction = critique_instruction or default_instruction

        critique_text = (
            f"Original user prompt: {original_prompt}\n\n"
            f"Your previous response:\n{own_previous.content}\n\n"
            f"The other AI's response:\n{other_response.content}\n\n"
            f"{critique_instruction}"
        )

        input_messages = [
            {
                "role": "developer",
                "content": [
                    {
                        "type": "input_text",
                        "text": developer_message
                    }
                ]
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "output_text",
                        "text": own_previous.content
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": critique_text
                    }
                ]
            }
        ]

        try:
            logger.info("Generating GPT critique...")
            response = await self.client.responses.create(
                model=self.model,
                input=input_messages,
                text=self._build_text_config(),
                reasoning=self._build_reasoning_config(),
                tools=[],
                store=True,
                include=[
                    "reasoning.encrypted_content",
                    "web_search_call.action.sources"
                ],
                timeout=120.0
            )

            # Extract content from response
            content = ""
            if hasattr(response, 'output') and response.output:
                for item in response.output:
                    if hasattr(item, 'content') and item.content:  # Added null check
                        for content_item in item.content:
                            if hasattr(content_item, 'text'):
                                content += content_item.text

            declares_convergence = "CONVERGENCE DECLARED" in content.upper()

            logger.info(f"GPT critique generated successfully (convergence: {declares_convergence})")

            return Response(
                provider=LLMProvider.OPENAI,
                content=content,
                timestamp=datetime.now(timezone.utc),
                is_critique=True,
                declares_convergence=declares_convergence
            )

        except APITimeoutError as e:
            logger.error(f"OpenAI API timeout during critique: {e}")
            raise TimeoutError("OpenAI API request timed out") from e
        except APIError as e:
            logger.error(f"OpenAI API error during critique: {e}")
            raise RuntimeError(f"OpenAI API error: {str(e)}") from e
        except Exception as e:
            logger.error(f"Unexpected error in GPT critique generation: {e}")
            raise

    async def generate_review(
        self,
        original_prompt: str,
        response_to_review: Response,
        additional_context: Optional[str] = None,
        developer_message: Optional[str] = None,
        review_instruction_template: Optional[str] = None
    ) -> Response:
        """Generate structured review of another AI's response (peer review mode)."""
        default_developer = (
            "You are evaluating a response for quality, accuracy, completeness, "
            "and relevance to the user prompt."
        )
        default_instruction = (
            "Structure your review as follows:\n"
            "1. **Summary**: Briefly describe what the response covers\n"
            "2. **Strengths**: List strengths (numbered S1, S2, etc.)\n"
            "3. **Areas for Improvement**:\n"
            "   - Major issues (M1, M2...) - significant concerns\n"
            "   - Minor issues (m1, m2...) - smaller suggestions\n"
            "4. **Questions**: Any clarifications needed (Q1, Q2...)\n"
            "5. **Assessment**: Score out of 10 with brief justification\n"
            "6. **Recommendation**: State one of:\n"
            "   - \"ACCEPTED\" - response fully addresses the prompt\n"
            "   - \"MINOR REVISION\" - small improvements needed\n"
            "   - \"MAJOR REVISION\" - significant changes required\n\n"
            "Be constructive and specific in your feedback."
        )
        developer_message = developer_message or default_developer
        review_instruction_template = review_instruction_template or default_instruction

        # Build review instruction with optional additional context
        review_instruction = (
            f"Original user prompt: {original_prompt}\n\n"
            f"Response to review:\n{response_to_review.content}\n\n"
        )

        # Add user's additional context if provided
        if additional_context and additional_context.strip():
            review_instruction += (
                f"Additional reviewer instructions from user:\n{additional_context}\n\n"
            )

        review_instruction += review_instruction_template

        input_messages = [
            {
                "role": "developer",
                "content": [
                    {
                        "type": "input_text",
                        "text": developer_message
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": review_instruction
                    }
                ]
            }
        ]

        try:
            logger.info("Generating GPT structured review...")
            response = await self.client.responses.create(
                model=self.model,
                input=input_messages,
                text=self._build_text_config(),
                reasoning=self._build_reasoning_config(),
                tools=[],
                store=True,
                include=[
                    "reasoning.encrypted_content",
                    "web_search_call.action.sources"
                ],
                timeout=120.0
            )

            content = ""
            if hasattr(response, 'output') and response.output:
                for item in response.output:
                    if hasattr(item, 'content') and item.content:
                        for content_item in item.content:
                            if hasattr(content_item, 'text'):
                                content += content_item.text

            declares_convergence = "ACCEPTED" in content.upper() and "MINOR REVISION" not in content.upper() and "MAJOR REVISION" not in content.upper()

            logger.info(f"GPT review generated (accepted: {declares_convergence})")

            return Response(
                provider=LLMProvider.OPENAI,
                content=content,
                timestamp=datetime.now(timezone.utc),
                is_critique=True,
                declares_convergence=declares_convergence
            )

        except APITimeoutError as e:
            logger.error(f"OpenAI API timeout during review: {e}")
            raise TimeoutError("OpenAI API request timed out") from e
        except APIError as e:
            logger.error(f"OpenAI API error during review: {e}")
            raise RuntimeError(f"OpenAI API error: {str(e)}") from e
        except Exception as e:
            logger.error(f"Unexpected error in GPT review: {e}")
            raise

    async def generate_re_review(
        self,
        original_prompt: str,
        previous_review: Response,
        rebuttal_and_revision: Response,
        additional_context: Optional[str] = None,
        developer_message: Optional[str] = None,
        rereview_instruction_template: Optional[str] = None
    ) -> Response:
        """Re-review after receiving rebuttal and revised response."""
        default_developer = (
            "You are re-evaluating a response after the author has addressed your feedback."
        )
        default_instruction = (
            "Evaluate the author's rebuttal and revised response:\n\n"
            "1. **Rebuttal Assessment**: Were the responses to your feedback points "
            "reasonable and well-justified?\n"
            "2. **Revision Quality**: Does the revised response adequately address "
            "the accepted concerns?\n"
            "3. **Remaining Issues**: Any unresolved concerns?\n"
            "4. **Updated Score**: X/10 (compare to your previous score)\n"
            "5. **Final Recommendation**: ACCEPTED / MINOR REVISION / MAJOR REVISION\n\n"
            "If all significant concerns are addressed, state \"ACCEPTED\" at the end."
        )
        developer_message = developer_message or default_developer
        rereview_instruction_template = rereview_instruction_template or default_instruction

        re_review_instruction = (
            f"Original user prompt: {original_prompt}\n\n"
            f"Your previous review:\n{previous_review.content}\n\n"
            f"Author's rebuttal and revised response:\n{rebuttal_and_revision.content}\n\n"
        )

        # Add user's additional context if provided
        if additional_context and additional_context.strip():
            re_review_instruction += (
                f"Additional reviewer instructions from user:\n{additional_context}\n\n"
            )

        re_review_instruction += rereview_instruction_template

        input_messages = [
            {
                "role": "developer",
                "content": [
                    {
                        "type": "input_text",
                        "text": developer_message
                    }
                ]
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "output_text",
                        "text": previous_review.content
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": re_review_instruction
                    }
                ]
            }
        ]

        try:
            logger.info("Generating GPT re-review...")
            response = await self.client.responses.create(
                model=self.model,
                input=input_messages,
                text=self._build_text_config(),
                reasoning=self._build_reasoning_config(),
                tools=[],
                store=True,
                include=[
                    "reasoning.encrypted_content",
                    "web_search_call.action.sources"
                ],
                timeout=120.0
            )

            content = ""
            if hasattr(response, 'output') and response.output:
                for item in response.output:
                    if hasattr(item, 'content') and item.content:
                        for content_item in item.content:
                            if hasattr(content_item, 'text'):
                                content += content_item.text

            # Check for acceptance - must have ACCEPTED without MINOR/MAJOR REVISION
            declares_convergence = "ACCEPTED" in content.upper() and "MINOR REVISION" not in content.upper() and "MAJOR REVISION" not in content.upper()

            logger.info(f"GPT re-review generated (accepted: {declares_convergence})")

            return Response(
                provider=LLMProvider.OPENAI,
                content=content,
                timestamp=datetime.now(timezone.utc),
                is_critique=True,
                declares_convergence=declares_convergence
            )

        except APITimeoutError as e:
            logger.error(f"OpenAI API timeout during re-review: {e}")
            raise TimeoutError("OpenAI API request timed out") from e
        except APIError as e:
            logger.error(f"OpenAI API error during re-review: {e}")
            raise RuntimeError(f"OpenAI API error: {str(e)}") from e
        except Exception as e:
            logger.error(f"Unexpected error in GPT re-review: {e}")
            raise
