from enum import Enum


class LLMProvider(Enum):
    """Enumeration of supported LLM providers."""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"


class ConvergenceStatus(Enum):
    """Status of conversation convergence."""
    PENDING = "pending"
    CONVERGED = "converged"
    DIVERGED = "diverged"
    USER_DECIDED = "user_decided"


class ConversationMode(Enum):
    """Mode of conversation."""
    CONVERGENCE = "convergence"  # Both LLMs respond and critique each other
    PEER_REVIEW = "peer_review"  # Claude submits, GPT reviews
