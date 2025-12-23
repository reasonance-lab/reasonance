import asyncio
import uuid
import logging
from typing import Tuple
from .anthropic_service import AnthropicService
from .openai_service import OpenAIService
from .convergence import ConvergenceDetector
from ..domain.models import Conversation, Round, Response
from ..domain.enums import ConvergenceStatus

logger = logging.getLogger(__name__)


class Orchestrator:
    """
    Orchestrates the conversation between Claude and GPT.
    Manages rounds, parallel execution, and convergence checking.
    """

    def __init__(
        self,
        anthropic_service: AnthropicService,
        openai_service: OpenAIService
    ):
        """
        Initialize orchestrator with LLM services.

        Args:
            anthropic_service: Anthropic Claude service instance
            openai_service: OpenAI GPT service instance
        """
        self.anthropic = anthropic_service
        self.openai = openai_service
        self.convergence_detector = ConvergenceDetector()
        logger.info("Orchestrator initialized")

    async def start_conversation(self, prompt: str) -> Conversation:
        """
        Start a new conversation with initial responses from both LLMs.

        Args:
            prompt: The user's prompt

        Returns:
            Conversation object with the first round completed
        """
        conversation = Conversation(
            id=str(uuid.uuid4()),
            user_prompt=prompt,
            rounds=[],
            status=ConvergenceStatus.PENDING
        )

        logger.info(f"Starting conversation {conversation.id} with prompt: {prompt[:50]}...")

        try:
            # Execute initial responses in parallel
            logger.info("Fetching initial responses from both LLMs in parallel...")
            claude_response, openai_response = await asyncio.gather(
                self.anthropic.generate_response(prompt),
                self.openai.generate_response(prompt)
            )

            # Create first round
            first_round = Round(
                round_number=1,
                claude_response=claude_response,
                openai_response=openai_response
            )

            conversation.rounds.append(first_round)
            logger.info(f"First round completed for conversation {conversation.id}")

            return conversation

        except Exception as e:
            logger.error(f"Error starting conversation {conversation.id}: {e}", exc_info=True)
            raise

    async def continue_round(self, conversation: Conversation) -> Round:
        """
        Continue the conversation with a new round of critiques.

        Args:
            conversation: The conversation to continue

        Returns:
            The new round with critiques from both LLMs
        """
        if not conversation.rounds:
            raise ValueError("Cannot continue conversation with no existing rounds")

        previous_round = conversation.rounds[-1]
        round_number = len(conversation.rounds) + 1

        # Ensure previous round has responses
        if not previous_round.claude_response or not previous_round.openai_response:
            raise ValueError("Previous round must have both responses")

        logger.info(f"Starting round {round_number} for conversation {conversation.id}")

        try:
            # Generate critiques in parallel
            # Claude critiques OpenAI's response, OpenAI critiques Claude's
            logger.info("Fetching critiques from both LLMs in parallel...")
            claude_critique, openai_critique = await asyncio.gather(
                self.anthropic.generate_critique(
                    original_prompt=conversation.user_prompt,
                    other_response=previous_round.openai_response,
                    own_previous=previous_round.claude_response
                ),
                self.openai.generate_critique(
                    original_prompt=conversation.user_prompt,
                    other_response=previous_round.claude_response,
                    own_previous=previous_round.openai_response
                )
            )

            # Create new round with critiques
            new_round = Round(
                round_number=round_number,
                claude_response=previous_round.claude_response,
                openai_response=previous_round.openai_response,
                claude_critique=claude_critique,
                openai_critique=openai_critique
            )

            conversation.rounds.append(new_round)

            # Update conversation status based on convergence
            conversation.status = self.convergence_detector.evaluate_round(new_round)
            logger.info(f"Round {round_number} completed. Status: {conversation.status}")

            return new_round

        except Exception as e:
            logger.error(f"Error in round {round_number} for conversation {conversation.id}: {e}", exc_info=True)
            raise

    def check_convergence(
        self,
        conversation: Conversation,
        auto_mode: bool = True
    ) -> ConvergenceStatus:
        """
        Check convergence status of the conversation.

        Args:
            conversation: The conversation to check
            auto_mode: If True, automatically detect convergence. If False, wait for user decision.

        Returns:
            ConvergenceStatus
        """
        if not auto_mode:
            return ConvergenceStatus.PENDING

        status = self.convergence_detector.evaluate_conversation(conversation.rounds)
        logger.info(f"Convergence check for conversation {conversation.id}: {status}")
        return status

    async def run_until_convergence(
        self,
        prompt: str,
        max_rounds: int = 10
    ) -> Conversation:
        """
        Run a conversation until convergence or max rounds reached.

        Args:
            prompt: The user's prompt
            max_rounds: Maximum number of rounds to run

        Returns:
            The completed conversation
        """
        logger.info(f"Running until convergence (max {max_rounds} rounds)...")
        conversation = await self.start_conversation(prompt)

        for i in range(max_rounds - 1):
            await self.continue_round(conversation)

            status = self.check_convergence(conversation, auto_mode=True)

            if status == ConvergenceStatus.CONVERGED:
                logger.info(f"Convergence achieved after {i + 2} rounds")
                break

        return conversation
