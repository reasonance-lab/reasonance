"""
Client registry for singleton LLM API clients.
Reuses HTTP connection pools for better performance.
"""
import threading
from typing import Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from anthropic import AsyncAnthropic
    from openai import AsyncOpenAI

_anthropic_clients: Dict[str, "AsyncAnthropic"] = {}
_openai_clients: Dict[str, "AsyncOpenAI"] = {}
_lock = threading.Lock()


def get_anthropic_client(api_key: str) -> "AsyncAnthropic":
    """Get or create Anthropic client for given API key (singleton per key)."""
    from anthropic import AsyncAnthropic

    with _lock:
        if api_key not in _anthropic_clients:
            _anthropic_clients[api_key] = AsyncAnthropic(api_key=api_key)
        return _anthropic_clients[api_key]


def get_openai_client(api_key: str) -> "AsyncOpenAI":
    """Get or create OpenAI client for given API key (singleton per key)."""
    from openai import AsyncOpenAI

    with _lock:
        if api_key not in _openai_clients:
            _openai_clients[api_key] = AsyncOpenAI(api_key=api_key)
        return _openai_clients[api_key]
