import os
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


def get_configured_llm_provider() -> str:
    """
    Returns the active LLM provider from environment variables.
    Defaults to 'gemini' as PRIMARY source for analysis. Switchable to 'ollama'.
    """
    provider = os.getenv("LLM_PROVIDER", "gemini").strip().lower()
    if provider in ["ollama", "local"]:
        return "ollama"
    return "gemini"
