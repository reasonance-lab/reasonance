import reflex as rx
from typing import List, Optional, Dict, Any
import logging
import uuid
from .domain.models import Conversation, Round
from .domain.enums import ConvergenceStatus, ConversationMode
from .services.anthropic_service import AnthropicService
from .services.openai_service import OpenAIService
from .services.convergence import ConvergenceDetector
from .storage.session_storage import SessionStorage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AppState(rx.State):
    """Main application state managing the LLM convergence conversation."""

    # User input
    user_prompt: str = ""

    # Current conversation (stored as dict for Reflex serialization)
    conversation_data: Dict[str, Any] = {}
    is_loading: bool = False
    error_message: str = ""
    loading_status: str = ""  # Shows which LLM is currently responding

    # Settings
    auto_convergence: bool = True
    max_rounds: int = 10
    selected_round: str = "1"  # For tabbed round display
    conversation_mode: str = "convergence"  # "convergence" or "peer_review"

    # Manual review mode (peer review with Auto OFF)
    review_additional_prompt: str = ""  # User's additional context for review
    awaiting_manual_review: bool = False  # True when waiting for user to trigger review

    # OpenAI Model Settings
    openai_model: str = "gpt-5.2"  # Options: "gpt-5.2", "gpt-5.2-pro"
    openai_effort: str = "high"  # Options: "high", "xhigh" (only for gpt-5.2)
    gpt_pro_confirmed: bool = False  # Confirmation checkbox for expensive model

    # Anthropic Model Settings
    anthropic_model: str = "claude-opus-4-5-20251101"
    anthropic_thinking_enabled: bool = True
    anthropic_thinking_budget: int = 16000

    # Settings dialog state
    settings_dialog_open: bool = False

    # API Keys (stored as text for user to paste)
    api_keys_text: str = "OPENAI_API_KEY=\nANTHROPIC_API_KEY="

    # Convergence mode prompts
    conv_claude_system: str = (
        "You are participating in a collaborative reasoning exercise. "
        "Another AI will also respond to this prompt independently. "
        "After initial responses, you will critique each other's outputs "
        "until you converge on a shared conclusion."
    )
    conv_gpt_system: str = (
        "You are participating in a collaborative reasoning exercise. "
        "Another AI will also respond to this prompt independently. "
        "After initial responses, you will critique each other's outputs "
        "until you converge on a shared conclusion."
    )
    conv_claude_critique_system: str = "You are continuing a collaborative reasoning exercise."
    conv_claude_critique_instruction: str = (
        "Critique the other AI's response. Identify agreements, disagreements, "
        "and suggest refinements. If you believe you have converged on a shared "
        "conclusion, explicitly state: 'CONVERGENCE DECLARED' at the end of your response."
    )
    conv_gpt_critique_system: str = "You are continuing a collaborative reasoning exercise."
    conv_gpt_critique_instruction: str = (
        "Critique the other AI's response. Identify agreements, disagreements, "
        "and suggest refinements. If you believe you have converged on a shared "
        "conclusion, explicitly state: 'CONVERGENCE DECLARED' at the end of your response."
    )

    # Peer review mode prompts
    pr_claude_system: str = (
        "You are developing a comprehensive response to the following user prompt. "
        "Focus on clarity, accuracy, and thoroughness of your response."
    )
    pr_claude_revision_system: str = (
        "You are revising your response based on feedback received. "
        "Address each point thoughtfully and improve your response where appropriate."
    )
    pr_claude_revision_instruction: str = (
        "Review the feedback provided. Respond in two parts:\n\n"
        "**Part 1 - Response to Feedback:**\n"
        "Address each numbered point (M1, M2, m1, Q1, etc.):\n"
        "- State whether you: ACCEPT, PARTIALLY ACCEPT, or RESPECTFULLY DISAGREE\n"
        "- Provide brief reasoning\n"
        "- Note what changes you will make (if any)\n\n"
        "**Part 2 - Revised Response:**\n"
        "Provide your improved response incorporating accepted feedback."
    )
    pr_gpt_review_system: str = (
        "You are evaluating a response for quality, accuracy, completeness, "
        "and relevance to the user prompt."
    )
    pr_gpt_review_instruction: str = (
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
    pr_gpt_rereview_system: str = (
        "You are re-evaluating a response after the author has addressed your feedback."
    )
    pr_gpt_rereview_instruction: str = (
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

    # Note: Services are NOT stored as instance variables to avoid pickle/serialization errors
    # They are created on-demand in methods that need them

    def _create_anthropic_service(self) -> AnthropicService:
        """Create Anthropic service with current settings."""
        return AnthropicService(
            api_key=self.get_anthropic_api_key(),
            model=self.anthropic_model,
            thinking_enabled=self.anthropic_thinking_enabled,
            thinking_budget=self.anthropic_thinking_budget
        )

    def _create_openai_service(self) -> OpenAIService:
        """Create OpenAI service with current settings."""
        return OpenAIService(
            api_key=self.get_openai_api_key(),
            model=self.openai_model,
            effort=self.openai_effort if self.openai_model == "gpt-5.2" else None
        )

    def _create_storage(self) -> SessionStorage:
        """Create storage instance."""
        return SessionStorage()

    @property
    def conversation(self) -> Optional[Conversation]:
        """Get conversation object from dict."""
        if not self.conversation_data:
            return None
        try:
            return Conversation.from_dict(self.conversation_data)
        except Exception as e:
            logger.error(f"Failed to deserialize conversation: {e}")
            return None

    @rx.var
    def has_conversation(self) -> bool:
        """Check if there is an active conversation."""
        return bool(self.conversation_data and "rounds" in self.conversation_data and len(self.conversation_data["rounds"]) > 0)

    @rx.var
    def current_round_number(self) -> int:
        """Get the current round number."""
        if self.conversation_data and "rounds" in self.conversation_data:
            return len(self.conversation_data["rounds"])
        return 0

    @rx.var(cache=True)
    def rounds_display(self) -> List[Dict[str, str]]:
        """Get rounds list formatted for display. Cached to prevent unnecessary recomputation."""
        if not self.conversation_data or "rounds" not in self.conversation_data:
            return []

        return [
            {
                "round_number": str(r.get("round_number", 1)),
                "claude_response": (r.get("claude_response") or {}).get("content", ""),
                "openai_response": (r.get("openai_response") or {}).get("content", ""),
                "claude_critique": (r.get("claude_critique") or {}).get("content", ""),
                "openai_critique": (r.get("openai_critique") or {}).get("content", ""),
            }
            for r in self.conversation_data["rounds"]
        ]

    @rx.var
    def user_prompt_display(self) -> str:
        """Get user prompt for display."""
        if self.conversation_data and "user_prompt" in self.conversation_data:
            return self.conversation_data["user_prompt"]
        return ""

    @rx.var
    def status_display(self) -> str:
        """Get human-readable status display."""
        if not self.conversation_data:
            return "No conversation started"

        status_map = {
            "pending": "In Progress",
            "converged": "Converged ✓",
            "diverged": "Diverged",
            "user_decided": "User Decided"
        }
        status = self.conversation_data.get("status", "pending")
        return status_map.get(status, "Unknown")

    @rx.var
    def can_continue(self) -> bool:
        """Check if conversation can continue."""
        if not self.conversation_data or self.is_loading:
            return False

        status = self.conversation_data.get("status", "pending")
        if status == "converged":
            return False

        if self.current_round_number >= self.max_rounds:
            return False

        return True

    def set_prompt(self, prompt: str):
        """Set the user prompt."""
        self.user_prompt = prompt

    def set_selected_round(self, round_num: str):
        """Set the selected round for tab display."""
        self.selected_round = round_num

    def toggle_auto_convergence(self):
        """Toggle auto-convergence mode."""
        self.auto_convergence = not self.auto_convergence

    def set_openai_model(self, model: str):
        """Set the OpenAI model."""
        self.openai_model = model
        # Reset confirmation when switching away from pro model
        if model != "gpt-5.2-pro":
            self.gpt_pro_confirmed = False

    def set_openai_effort(self, effort: str):
        """Set the OpenAI effort level (only for gpt-5.2)."""
        self.openai_effort = effort

    def toggle_gpt_pro_confirmation(self):
        """Toggle the GPT Pro confirmation checkbox."""
        self.gpt_pro_confirmed = not self.gpt_pro_confirmed

    def toggle_anthropic_thinking(self):
        """Toggle Anthropic thinking mode."""
        self.anthropic_thinking_enabled = not self.anthropic_thinking_enabled

    # Settings dialog methods
    def open_settings_dialog(self):
        """Open the settings dialog."""
        self.settings_dialog_open = True

    def close_settings_dialog(self):
        """Close the settings dialog."""
        self.settings_dialog_open = False

    def set_settings_dialog_open(self, is_open: bool):
        """Set the settings dialog open state."""
        self.settings_dialog_open = is_open

    def set_api_keys_text(self, value: str):
        """Set the API keys text."""
        self.api_keys_text = value

    def _get_api_key_from_settings(self, key_name: str) -> Optional[str]:
        """Parse API key from settings text.

        Args:
            key_name: The key name to look for (e.g., 'OPENAI_API_KEY')

        Returns:
            The API key value if found and non-empty, None otherwise
        """
        if not self.api_keys_text:
            return None

        for line in self.api_keys_text.strip().split('\n'):
            line = line.strip()
            if line.startswith(f"{key_name}="):
                value = line[len(f"{key_name}="):].strip()
                if value:
                    return value
        return None

    def get_openai_api_key(self) -> Optional[str]:
        """Get OpenAI API key - checks env first, then settings."""
        import os
        env_key = os.getenv("OPENAI_API_KEY")
        if env_key:
            return env_key
        return self._get_api_key_from_settings("OPENAI_API_KEY")

    def get_anthropic_api_key(self) -> Optional[str]:
        """Get Anthropic API key - checks env first, then settings."""
        import os
        env_key = os.getenv("ANTHROPIC_API_KEY")
        if env_key:
            return env_key
        return self._get_api_key_from_settings("ANTHROPIC_API_KEY")

    def reset_prompts_to_defaults(self):
        """Reset all prompts to default values."""
        # Convergence mode defaults
        self.conv_claude_system = (
            "You are participating in a collaborative reasoning exercise. "
            "Another AI will also respond to this prompt independently. "
            "After initial responses, you will critique each other's outputs "
            "until you converge on a shared conclusion."
        )
        self.conv_gpt_system = (
            "You are participating in a collaborative reasoning exercise. "
            "Another AI will also respond to this prompt independently. "
            "After initial responses, you will critique each other's outputs "
            "until you converge on a shared conclusion."
        )
        self.conv_claude_critique_system = "You are continuing a collaborative reasoning exercise."
        self.conv_claude_critique_instruction = (
            "Critique the other AI's response. Identify agreements, disagreements, "
            "and suggest refinements. If you believe you have converged on a shared "
            "conclusion, explicitly state: 'CONVERGENCE DECLARED' at the end of your response."
        )
        self.conv_gpt_critique_system = "You are continuing a collaborative reasoning exercise."
        self.conv_gpt_critique_instruction = (
            "Critique the other AI's response. Identify agreements, disagreements, "
            "and suggest refinements. If you believe you have converged on a shared "
            "conclusion, explicitly state: 'CONVERGENCE DECLARED' at the end of your response."
        )
        # Peer review mode defaults
        self.pr_claude_system = (
            "You are developing a comprehensive response to the following user prompt. "
            "Focus on clarity, accuracy, and thoroughness of your response."
        )
        self.pr_claude_revision_system = (
            "You are revising your response based on feedback received. "
            "Address each point thoughtfully and improve your response where appropriate."
        )
        self.pr_claude_revision_instruction = (
            "Review the feedback provided. Respond in two parts:\n\n"
            "**Part 1 - Response to Feedback:**\n"
            "Address each numbered point (M1, M2, m1, Q1, etc.):\n"
            "- State whether you: ACCEPT, PARTIALLY ACCEPT, or RESPECTFULLY DISAGREE\n"
            "- Provide brief reasoning\n"
            "- Note what changes you will make (if any)\n\n"
            "**Part 2 - Revised Response:**\n"
            "Provide your improved response incorporating accepted feedback."
        )
        self.pr_gpt_review_system = (
            "You are evaluating a response for quality, accuracy, completeness, "
            "and relevance to the user prompt."
        )
        self.pr_gpt_review_instruction = (
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
        self.pr_gpt_rereview_system = (
            "You are re-evaluating a response after the author has addressed your feedback."
        )
        self.pr_gpt_rereview_instruction = (
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

    # Prompt setters (for individual prompt updates)
    def set_conv_claude_system(self, value: str):
        self.conv_claude_system = value

    def set_conv_gpt_system(self, value: str):
        self.conv_gpt_system = value

    def set_conv_claude_critique_system(self, value: str):
        self.conv_claude_critique_system = value

    def set_conv_claude_critique_instruction(self, value: str):
        self.conv_claude_critique_instruction = value

    def set_conv_gpt_critique_system(self, value: str):
        self.conv_gpt_critique_system = value

    def set_conv_gpt_critique_instruction(self, value: str):
        self.conv_gpt_critique_instruction = value

    def set_pr_claude_system(self, value: str):
        self.pr_claude_system = value

    def set_pr_claude_revision_system(self, value: str):
        self.pr_claude_revision_system = value

    def set_pr_claude_revision_instruction(self, value: str):
        self.pr_claude_revision_instruction = value

    def set_pr_gpt_review_system(self, value: str):
        self.pr_gpt_review_system = value

    def set_pr_gpt_review_instruction(self, value: str):
        self.pr_gpt_review_instruction = value

    def set_pr_gpt_rereview_system(self, value: str):
        self.pr_gpt_rereview_system = value

    def set_pr_gpt_rereview_instruction(self, value: str):
        self.pr_gpt_rereview_instruction = value

    def set_conversation_mode(self, mode: str):
        """Set the conversation mode."""
        self.conversation_mode = mode

    def set_review_additional_prompt(self, text: str):
        """Set additional context for manual review."""
        self.review_additional_prompt = text

    @rx.var
    def show_manual_review_input(self) -> bool:
        """Show manual review input when awaiting and in peer review mode."""
        return (
            self.awaiting_manual_review
            and self.conversation_is_peer_review
            and not self.is_loading
        )

    @rx.var
    def is_peer_review_mode(self) -> bool:
        """Check if current mode is peer review."""
        return self.conversation_mode == "peer_review"

    @rx.var
    def current_mode_display(self) -> str:
        """Get display name for current mode."""
        if self.conversation_data and "mode" in self.conversation_data:
            mode = self.conversation_data.get("mode", "convergence")
            return "Peer Review" if mode == "peer_review" else "Convergence"
        return "Peer Review" if self.conversation_mode == "peer_review" else "Convergence"

    @rx.var
    def conversation_is_peer_review(self) -> bool:
        """Check if current conversation is in peer review mode."""
        if self.conversation_data and "mode" in self.conversation_data:
            return self.conversation_data.get("mode", "convergence") == "peer_review"
        return False

    @rx.var
    def can_start_conversation(self) -> bool:
        """Check if conversation can be started based on model settings."""
        if self.is_loading:
            return False
        if not self.user_prompt.strip():
            return False
        # If gpt-5.2-pro is selected, require confirmation
        if self.openai_model == "gpt-5.2-pro" and not self.gpt_pro_confirmed:
            return False
        return True

    @rx.var
    def show_effort_selector(self) -> bool:
        """Show effort selector only for gpt-5.2 model."""
        return self.openai_model == "gpt-5.2"

    @rx.var
    def show_pro_confirmation(self) -> bool:
        """Show confirmation checkbox for gpt-5.2-pro model."""
        return self.openai_model == "gpt-5.2-pro"

    async def start_conversation(self):
        """Start a new conversation - routes to appropriate mode."""
        if not self.user_prompt.strip():
            self.error_message = "Please enter a prompt"
            logger.warning("Attempted to start conversation with empty prompt")
            return

        if self.conversation_mode == "peer_review":
            async for _ in self._start_peer_review():
                yield
        else:
            async for _ in self._start_convergence():
                yield

    async def _start_convergence(self):
        """Start convergence mode: Both LLMs respond independently."""
        self.is_loading = True
        self.error_message = ""
        self.loading_status = "Waiting for Claude..."
        logger.info(f"Starting convergence conversation with prompt: {self.user_prompt[:50]}...")
        yield

        try:
            conversation = Conversation(
                id=str(uuid.uuid4()),
                user_prompt=self.user_prompt,
                rounds=[],
                status=ConvergenceStatus.PENDING,
                mode=ConversationMode.CONVERGENCE
            )

            first_round = Round(round_number=1)

            # Step 1: Get Claude response
            logger.info("Fetching Claude response...")
            anthropic_service = self._create_anthropic_service()
            claude_response = await anthropic_service.generate_response(
                self.user_prompt,
                system_prompt=self.conv_claude_system
            )
            first_round.claude_response = claude_response

            conversation.rounds = [first_round]
            self.conversation_data = conversation.to_dict()
            self.selected_round = "1"
            logger.info(f"Claude response received ({len(claude_response.content)} chars)")
            yield

            # Step 2: Get GPT response
            self.loading_status = "Waiting for GPT..."
            logger.info("Fetching GPT response...")
            openai_service = self._create_openai_service()
            openai_response = await openai_service.generate_response(
                self.user_prompt,
                developer_message=self.conv_gpt_system
            )
            first_round.openai_response = openai_response

            conversation.rounds = [first_round]
            self.conversation_data = conversation.to_dict()
            logger.info(f"GPT response received ({len(openai_response.content)} chars)")

            storage = self._create_storage()
            await storage.save(conversation)
            logger.info(f"Convergence conversation started: {conversation.id}")

        except Exception as e:
            logger.error(f"Error starting convergence conversation: {e}", exc_info=True)
            self.error_message = f"Error: {str(e)}"
            self.conversation_data = {}

        finally:
            self.is_loading = False
            self.loading_status = ""

    async def _start_peer_review(self):
        """Start peer review mode: Claude submits, GPT reviews."""
        self.is_loading = True
        self.error_message = ""
        self.loading_status = "Claude generating response..."
        logger.info(f"Starting peer review with prompt: {self.user_prompt[:50]}...")
        yield

        try:
            conversation = Conversation(
                id=str(uuid.uuid4()),
                user_prompt=self.user_prompt,
                rounds=[],
                status=ConvergenceStatus.PENDING,
                mode=ConversationMode.PEER_REVIEW
            )

            first_round = Round(round_number=1)

            # Step 1: Claude generates initial response
            logger.info("Fetching Claude's initial response...")
            anthropic_service = self._create_anthropic_service()
            claude_response = await anthropic_service.generate_peer_review_response(
                self.user_prompt,
                system_prompt=self.pr_claude_system
            )
            first_round.claude_response = claude_response

            conversation.rounds = [first_round]
            self.conversation_data = conversation.to_dict()
            self.selected_round = "1"
            logger.info(f"Claude response received ({len(claude_response.content)} chars)")

            # Save conversation after Claude's response
            storage = self._create_storage()
            await storage.save(conversation)
            yield

            # Check if manual mode (Auto OFF) - stop here and wait for user
            if not self.auto_convergence:
                self.awaiting_manual_review = True
                self.is_loading = False
                self.loading_status = ""
                logger.info("Manual review mode: waiting for user to trigger review")
                return

            # Step 2: GPT reviews Claude's response (Auto mode)
            self.loading_status = "GPT reviewing response..."
            logger.info("Fetching GPT's review...")
            openai_service = self._create_openai_service()
            gpt_review = await openai_service.generate_review(
                original_prompt=self.user_prompt,
                response_to_review=claude_response,
                developer_message=self.pr_gpt_review_system,
                review_instruction_template=self.pr_gpt_review_instruction
            )
            first_round.openai_critique = gpt_review  # Store review in openai_critique field

            conversation.rounds = [first_round]
            self.conversation_data = conversation.to_dict()
            logger.info(f"GPT review received ({len(gpt_review.content)} chars)")

            # Check if accepted on first review
            if gpt_review.declares_convergence:
                conversation.status = ConvergenceStatus.CONVERGED
                self.conversation_data = conversation.to_dict()
                logger.info("Response accepted on first review!")

            await storage.save(conversation)
            logger.info(f"Peer review conversation started: {conversation.id}")

        except Exception as e:
            logger.error(f"Error starting peer review: {e}", exc_info=True)
            self.error_message = f"Error: {str(e)}"
            self.conversation_data = {}

        finally:
            self.is_loading = False
            self.loading_status = ""

    async def continue_conversation(self):
        """Continue the conversation - routes to appropriate mode."""
        if not self.conversation_data or not self.can_continue:
            logger.warning("Cannot continue conversation - invalid state")
            return

        # Get mode from conversation data
        mode = self.conversation_data.get("mode", "convergence")

        if mode == "peer_review":
            async for _ in self._continue_peer_review():
                yield
        else:
            async for _ in self._continue_convergence():
                yield

    async def _continue_convergence(self):
        """Continue convergence mode: Both LLMs critique each other."""
        self.is_loading = True
        self.error_message = ""
        self.loading_status = "Waiting for Claude's critique..."
        yield

        try:
            conversation = self.conversation
            if not conversation:
                raise ValueError("Failed to deserialize conversation")

            previous_round = conversation.rounds[-1]
            round_number = len(conversation.rounds) + 1

            if not previous_round.claude_response or not previous_round.openai_response:
                raise ValueError("Previous round must have both responses")

            logger.info(f"Continuing convergence {conversation.id}, round {round_number}")

            new_round = Round(
                round_number=round_number,
                claude_response=previous_round.claude_response,
                openai_response=previous_round.openai_response
            )

            # Step 1: Claude's critique
            logger.info("Fetching Claude critique...")
            anthropic_service = self._create_anthropic_service()
            claude_critique = await anthropic_service.generate_critique(
                original_prompt=conversation.user_prompt,
                other_response=previous_round.openai_response,
                own_previous=previous_round.claude_response,
                system_prompt=self.conv_claude_critique_system,
                critique_instruction=self.conv_claude_critique_instruction
            )
            new_round.claude_critique = claude_critique

            conversation.rounds.append(new_round)
            self.conversation_data = conversation.to_dict()
            self.selected_round = str(round_number)
            logger.info(f"Claude critique received ({len(claude_critique.content)} chars)")
            yield

            # Step 2: GPT's critique
            self.loading_status = "Waiting for GPT's critique..."
            logger.info("Fetching GPT critique...")
            openai_service = self._create_openai_service()
            openai_critique = await openai_service.generate_critique(
                original_prompt=conversation.user_prompt,
                other_response=previous_round.claude_response,
                own_previous=previous_round.openai_response,
                developer_message=self.conv_gpt_critique_system,
                critique_instruction=self.conv_gpt_critique_instruction
            )
            new_round.openai_critique = openai_critique

            conversation.rounds[-1] = new_round
            self.conversation_data = conversation.to_dict()
            logger.info(f"GPT critique received ({len(openai_critique.content)} chars)")

            if self.auto_convergence:
                convergence_detector = ConvergenceDetector()
                status = convergence_detector.evaluate_round(new_round)
                conversation.status = status
                self.conversation_data = conversation.to_dict()
                logger.info(f"Convergence status: {status}")

            storage = self._create_storage()
            await storage.save(conversation)

        except Exception as e:
            logger.error(f"Error continuing convergence: {e}", exc_info=True)
            self.error_message = f"Error: {str(e)}"

        finally:
            self.is_loading = False
            self.loading_status = ""

    async def _continue_peer_review(self):
        """Continue peer review mode: Claude revises, GPT re-reviews."""
        self.is_loading = True
        self.error_message = ""
        self.loading_status = "Claude preparing rebuttal & revision..."
        yield

        try:
            conversation = self.conversation
            if not conversation:
                raise ValueError("Failed to deserialize conversation")

            previous_round = conversation.rounds[-1]
            round_number = len(conversation.rounds) + 1

            # Get previous response and review
            previous_response = previous_round.claude_response
            previous_review = previous_round.openai_critique

            if not previous_response or not previous_review:
                raise ValueError("Previous round must have response and review")

            logger.info(f"Continuing peer review {conversation.id}, round {round_number}")

            new_round = Round(round_number=round_number)

            # Step 1: Claude generates rebuttal and revision
            logger.info("Fetching Claude's rebuttal and revision...")
            anthropic_service = self._create_anthropic_service()
            revision = await anthropic_service.generate_revision(
                original_prompt=conversation.user_prompt,
                previous_response=previous_response,
                review_feedback=previous_review,
                system_prompt=self.pr_claude_revision_system,
                revision_instruction=self.pr_claude_revision_instruction
            )
            new_round.claude_response = revision  # Store revision as claude_response

            conversation.rounds.append(new_round)
            self.conversation_data = conversation.to_dict()
            self.selected_round = str(round_number)
            logger.info(f"Claude revision received ({len(revision.content)} chars)")

            # Save conversation after Claude's revision
            storage = self._create_storage()
            await storage.save(conversation)
            yield

            # Check if manual mode (Auto OFF) - stop here and wait for user
            if not self.auto_convergence:
                self.awaiting_manual_review = True
                self.is_loading = False
                self.loading_status = ""
                logger.info("Manual review mode: waiting for user to trigger re-review")
                return

            # Step 2: GPT re-reviews the revision (Auto mode)
            self.loading_status = "GPT evaluating revision..."
            logger.info("Fetching GPT's re-review...")
            openai_service = self._create_openai_service()
            re_review = await openai_service.generate_re_review(
                original_prompt=conversation.user_prompt,
                previous_review=previous_review,
                rebuttal_and_revision=revision,
                developer_message=self.pr_gpt_rereview_system,
                rereview_instruction_template=self.pr_gpt_rereview_instruction
            )
            new_round.openai_critique = re_review  # Store re-review as openai_critique

            conversation.rounds[-1] = new_round
            self.conversation_data = conversation.to_dict()
            logger.info(f"GPT re-review received ({len(re_review.content)} chars)")

            # Check if accepted
            if re_review.declares_convergence:
                conversation.status = ConvergenceStatus.CONVERGED
                self.conversation_data = conversation.to_dict()
                logger.info("Revision accepted!")

            await storage.save(conversation)

        except Exception as e:
            logger.error(f"Error continuing peer review: {e}", exc_info=True)
            self.error_message = f"Error: {str(e)}"

        finally:
            self.is_loading = False
            self.loading_status = ""

    async def trigger_manual_review(self):
        """Trigger GPT review manually with optional additional context.

        Handles both initial reviews (round 1) and re-reviews (subsequent rounds).
        """
        if not self.awaiting_manual_review:
            return

        self.awaiting_manual_review = False
        self.is_loading = True
        self.loading_status = "GPT reviewing response..."
        yield

        try:
            conversation = self.conversation
            if not conversation:
                raise ValueError("No conversation found")

            current_round = conversation.rounds[-1]
            claude_response = current_round.claude_response

            if not claude_response:
                raise ValueError("No Claude response to review")

            openai_service = self._create_openai_service()
            additional_context = self.review_additional_prompt if self.review_additional_prompt.strip() else None

            # Check if this is the first round (initial review) or subsequent (re-review)
            if current_round.round_number == 1:
                # Initial review
                logger.info("Triggering manual GPT initial review...")
                gpt_review = await openai_service.generate_review(
                    original_prompt=conversation.user_prompt,
                    response_to_review=claude_response,
                    additional_context=additional_context,
                    developer_message=self.pr_gpt_review_system,
                    review_instruction_template=self.pr_gpt_review_instruction
                )
            else:
                # Re-review - need previous review from the previous round
                previous_round = conversation.rounds[-2] if len(conversation.rounds) > 1 else None
                previous_review = previous_round.openai_critique if previous_round else None

                if not previous_review:
                    raise ValueError("No previous review found for re-review")

                logger.info("Triggering manual GPT re-review...")
                gpt_review = await openai_service.generate_re_review(
                    original_prompt=conversation.user_prompt,
                    previous_review=previous_review,
                    rebuttal_and_revision=claude_response,
                    additional_context=additional_context,
                    developer_message=self.pr_gpt_rereview_system,
                    rereview_instruction_template=self.pr_gpt_rereview_instruction
                )

            current_round.openai_critique = gpt_review
            conversation.rounds[-1] = current_round
            self.conversation_data = conversation.to_dict()
            logger.info(f"GPT review received ({len(gpt_review.content)} chars)")

            # Clear the additional prompt for next use
            self.review_additional_prompt = ""

            # Check if accepted
            if gpt_review.declares_convergence:
                conversation.status = ConvergenceStatus.CONVERGED
                self.conversation_data = conversation.to_dict()
                logger.info("Response accepted on review!")

            storage = self._create_storage()
            await storage.save(conversation)

        except Exception as e:
            logger.error(f"Error in manual review: {e}", exc_info=True)
            self.error_message = f"Error: {str(e)}"

        finally:
            self.is_loading = False
            self.loading_status = ""

    def reset_conversation(self):
        """Reset the conversation to start fresh."""
        logger.info("Resetting conversation")

        if self.conversation_data:
            conv_id = self.conversation_data.get("id")
            if conv_id:
                # Note: This is sync, storage.delete is async - should be handled properly
                try:
                    import asyncio
                    storage = self._create_storage()
                    asyncio.create_task(storage.delete(conv_id))
                except Exception as e:
                    logger.error(f"Error deleting conversation: {e}")

        self.conversation_data = {}
        self.user_prompt = ""
        self.error_message = ""
        self.loading_status = ""
        self.is_loading = False
        self.gpt_pro_confirmed = False  # Reset confirmation for safety
        self.awaiting_manual_review = False  # Reset manual review state
        self.review_additional_prompt = ""  # Clear additional prompt

    def mark_user_decided(self):
        """Mark the conversation as user-decided (manual convergence)."""
        if self.conversation_data:
            self.conversation_data["status"] = "user_decided"
            logger.info("Conversation marked as user decided")

    # Export functionality - regular methods (not reactive) for on-demand generation
    def _get_conversation_markdown(self) -> str:
        """Generate markdown content for current conversation. Called on-demand during export."""
        if not self.conversation_data:
            return ""

        from datetime import datetime

        parts = [
            "# LLM Convergence Conversation\n\n",
            f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
            f"**Mode:** {self.current_mode_display}\n",
            f"**Status:** {self.status_display}\n\n",
            "---\n\n",
            f"## User Prompt\n\n{self.user_prompt_display}\n\n",
            "---\n\n",
        ]

        mode = self.conversation_data.get("mode", "convergence")

        for round_data in self.rounds_display:
            parts.append(f"## Round {round_data['round_number']}\n\n")

            if mode == "peer_review":
                # Peer review format
                if round_data.get('claude_response'):
                    label = "Claude Response" if round_data['round_number'] == "1" else "Claude Revision"
                    parts.append(f"### {label}\n\n{round_data['claude_response']}\n\n")
                if round_data.get('openai_critique'):
                    label = "GPT Review" if round_data['round_number'] == "1" else "GPT Re-review"
                    parts.append(f"### {label}\n\n{round_data['openai_critique']}\n\n")
            else:
                # Convergence format
                if round_data.get('claude_response'):
                    parts.append(f"### Claude Response\n\n{round_data['claude_response']}\n\n")
                if round_data.get('openai_response'):
                    parts.append(f"### GPT Response\n\n{round_data['openai_response']}\n\n")
                if round_data.get('claude_critique'):
                    parts.append(f"### Claude Critique\n\n{round_data['claude_critique']}\n\n")
                if round_data.get('openai_critique'):
                    parts.append(f"### GPT Critique\n\n{round_data['openai_critique']}\n\n")

            parts.append("---\n\n")

        return "".join(parts)

    def _get_settings_markdown(self) -> str:
        """Generate markdown content for current prompt settings. Called on-demand during export."""
        from datetime import datetime

        parts = [
            "# Prompt Settings Export\n\n",
            f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n",
            "---\n\n## Convergence Mode\n\n",
            f"### Claude System Prompt\n```\n{self.conv_claude_system}\n```\n\n",
            f"### GPT System Prompt\n```\n{self.conv_gpt_system}\n```\n\n",
            f"### Claude Critique System\n```\n{self.conv_claude_critique_system}\n```\n\n",
            f"### Claude Critique Instruction\n```\n{self.conv_claude_critique_instruction}\n```\n\n",
            f"### GPT Critique System\n```\n{self.conv_gpt_critique_system}\n```\n\n",
            f"### GPT Critique Instruction\n```\n{self.conv_gpt_critique_instruction}\n```\n\n",
            "---\n\n## Peer Review Mode\n\n",
            f"### Claude System Prompt\n```\n{self.pr_claude_system}\n```\n\n",
            f"### Claude Revision System\n```\n{self.pr_claude_revision_system}\n```\n\n",
            f"### Claude Revision Instruction\n```\n{self.pr_claude_revision_instruction}\n```\n\n",
            f"### GPT Review System\n```\n{self.pr_gpt_review_system}\n```\n\n",
            f"### GPT Review Instruction\n```\n{self.pr_gpt_review_instruction}\n```\n\n",
            f"### GPT Re-review System\n```\n{self.pr_gpt_rereview_system}\n```\n\n",
            f"### GPT Re-review Instruction\n```\n{self.pr_gpt_rereview_instruction}\n```\n\n",
        ]

        return "".join(parts)

    def download_conversation(self):
        """Trigger download of conversation as markdown file."""
        if not self.conversation_data:
            return

        from datetime import datetime
        filename = f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        return rx.download(data=self._get_conversation_markdown(), filename=filename)

    def download_settings(self):
        """Trigger download of settings as markdown file."""
        from datetime import datetime
        filename = f"prompt_settings_{datetime.now().strftime('%Y%m%d')}.md"
        return rx.download(data=self._get_settings_markdown(), filename=filename)
