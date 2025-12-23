"""LLM Convergence Application."""
from dotenv import load_dotenv

# Load environment variables once at app startup
load_dotenv()

from .llm_convergence import app
