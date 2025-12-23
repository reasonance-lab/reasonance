from dataclasses import dataclass, field, asdict
from typing import Optional, Any, Dict
from datetime import datetime, timezone
from .enums import LLMProvider, ConvergenceStatus, ConversationMode


@dataclass
class Response:
    """Represents a single LLM response or critique."""
    provider: LLMProvider
    content: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    is_critique: bool = False
    declares_convergence: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "provider": self.provider.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "is_critique": self.is_critique,
            "declares_convergence": self.declares_convergence
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Response":
        """Create from dictionary."""
        return cls(
            provider=LLMProvider(data["provider"]),
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            is_critique=data.get("is_critique", False),
            declares_convergence=data.get("declares_convergence", False)
        )


@dataclass
class Round:
    """Represents a single round of conversation between both LLMs."""
    round_number: int
    claude_response: Optional[Response] = None
    openai_response: Optional[Response] = None
    claude_critique: Optional[Response] = None
    openai_critique: Optional[Response] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "round_number": self.round_number,
            "claude_response": self.claude_response.to_dict() if self.claude_response else None,
            "openai_response": self.openai_response.to_dict() if self.openai_response else None,
            "claude_critique": self.claude_critique.to_dict() if self.claude_critique else None,
            "openai_critique": self.openai_critique.to_dict() if self.openai_critique else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Round":
        """Create from dictionary."""
        return cls(
            round_number=data["round_number"],
            claude_response=Response.from_dict(data["claude_response"]) if data.get("claude_response") else None,
            openai_response=Response.from_dict(data["openai_response"]) if data.get("openai_response") else None,
            claude_critique=Response.from_dict(data["claude_critique"]) if data.get("claude_critique") else None,
            openai_critique=Response.from_dict(data["openai_critique"]) if data.get("openai_critique") else None
        )


@dataclass
class Conversation:
    """Represents the complete conversation session."""
    id: str
    user_prompt: str
    rounds: list[Round] = field(default_factory=list)
    status: ConvergenceStatus = ConvergenceStatus.PENDING
    mode: ConversationMode = ConversationMode.CONVERGENCE
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "user_prompt": self.user_prompt,
            "rounds": [r.to_dict() for r in self.rounds],
            "status": self.status.value,
            "mode": self.mode.value,
            "created_at": self.created_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Conversation":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            user_prompt=data["user_prompt"],
            rounds=[Round.from_dict(r) for r in data.get("rounds", [])],
            status=ConvergenceStatus(data.get("status", "pending")),
            mode=ConversationMode(data.get("mode", "convergence")),
            created_at=datetime.fromisoformat(data["created_at"])
        )
