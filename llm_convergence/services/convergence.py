import logging
from typing import List
from ..domain.models import Round, Response
from ..domain.enums import ConvergenceStatus

logger = logging.getLogger(__name__)


class ConvergenceDetector:
    """
    Detects convergence between LLM responses.
    Uses explicit convergence declarations from both LLMs.
    """

    # Expanded list of convergence signal phrases
    AGREEMENT_PHRASES = [
        "i agree",
        "i concur",
        "no significant differences",
        "we have converged",
        "same conclusion",
        "aligned",
        "in agreement",
        "convergence declared",
        "completely agree",
        "fully agree",
        "entirely agree",
        "no disagreement",
        "no further critique",
        "nothing to add",
        "well said",
        "perfectly stated",
        "accurate assessment",
        "comprehensive answer",
        "thorough response",
    ]

    @staticmethod
    def evaluate_round(current_round: Round) -> ConvergenceStatus:
        """
        Evaluate if a round shows convergence.

        Args:
            current_round: The round to evaluate

        Returns:
            ConvergenceStatus indicating the convergence state
        """
        # First round has no critiques yet
        if current_round.round_number == 1:
            logger.debug("Round 1 has no critiques, returning PENDING")
            return ConvergenceStatus.PENDING

        # Both critiques must exist to evaluate convergence
        if not current_round.claude_critique or not current_round.openai_critique:
            logger.warning("Missing critique in round, cannot evaluate convergence")
            return ConvergenceStatus.PENDING

        # Check if both LLMs have declared convergence
        claude_converged = current_round.claude_critique.declares_convergence
        openai_converged = current_round.openai_critique.declares_convergence

        logger.info(f"Round {current_round.round_number}: Claude converged={claude_converged}, GPT converged={openai_converged}")

        if claude_converged and openai_converged:
            logger.info("Both LLMs declared convergence")
            return ConvergenceStatus.CONVERGED
        elif not claude_converged and not openai_converged:
            # Both still critiquing, continue discussion
            logger.debug("Both LLMs still critiquing, continuing discussion")
            return ConvergenceStatus.PENDING
        else:
            # One converged but not the other - diverged opinions
            converged_llm = "Claude" if claude_converged else "GPT"
            logger.warning(f"Diverged: Only {converged_llm} declared convergence")
            return ConvergenceStatus.DIVERGED

    @staticmethod
    def evaluate_conversation(rounds: List[Round]) -> ConvergenceStatus:
        """
        Evaluate the overall convergence status of a conversation.

        Args:
            rounds: List of all rounds in the conversation

        Returns:
            ConvergenceStatus of the conversation
        """
        if not rounds:
            logger.warning("No rounds to evaluate")
            return ConvergenceStatus.PENDING

        # Check the latest round
        latest_round = rounds[-1]
        status = ConvergenceDetector.evaluate_round(latest_round)
        logger.info(f"Conversation status after {len(rounds)} rounds: {status}")
        return status

    @staticmethod
    def check_agreement_signals(response: Response) -> bool:
        """
        Check for agreement signals in a response.

        Args:
            response: The response to check

        Returns:
            True if agreement signals are found
        """
        if not response or not response.content:
            return False

        content_lower = response.content.lower()
        found_signals = [
            phrase for phrase in ConvergenceDetector.AGREEMENT_PHRASES
            if phrase in content_lower
        ]

        if found_signals:
            logger.debug(f"Found agreement signals: {found_signals[:3]}")  # Log first 3
            return True

        return False

    @staticmethod
    def detect_explicit_declaration(content: str) -> bool:
        """
        Detect explicit convergence declarations in text.

        Args:
            content: The text content to check

        Returns:
            True if explicit convergence declaration found
        """
        explicit_markers = [
            "convergence declared",
            "declare convergence",
            "i declare convergence",
            "we have converged",
        ]

        content_lower = content.lower() if content else ""
        return any(marker in content_lower for marker in explicit_markers)
