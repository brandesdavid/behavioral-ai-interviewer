import os
import logging
from core.providers.base import BaseProvider


def get_provider() -> BaseProvider:
    """
    Factory: return the configured LLM provider.

    Set the environment variable LLM_PROVIDER to select the backend:
        LLM_PROVIDER=openai   (default) — requires OPENAI_API_KEY
        LLM_PROVIDER=gemini            — requires GEMINI_API_KEY
    """
    provider_name = os.getenv("LLM_PROVIDER", "openai").lower()
    logging.info(f"Using LLM provider: '{provider_name}'")

    if provider_name == "gemini":
        from core.providers.gemini_provider import GeminiProvider
        api_key = os.getenv("GEMINI_API_KEY", "")
        return GeminiProvider(api_key=api_key)

    # Default: OpenAI
    from core.providers.openai_provider import OpenAIProvider
    from parameters import OPENAI_API_KEY
    return OpenAIProvider(api_key=OPENAI_API_KEY)
