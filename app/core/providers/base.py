from abc import ABC, abstractmethod


class BaseProvider(ABC):
    """Abstract base class for LLM providers."""

    provider_name: str = "base"

    @abstractmethod
    def complete(self, messages: list, model: str, max_tokens: int, temperature: float) -> str:
        """Run a chat completion and return the response text."""

    @abstractmethod
    def complete_json(self, messages: list, model: str, max_tokens: int, temperature: float) -> dict:
        """Run a chat completion and return parsed JSON."""

    @abstractmethod
    def transcribe(self, audio: str) -> str:
        """Transcribe base64-encoded audio and return text."""

    @abstractmethod
    def moderate_text(self, text: str) -> bool:
        """Return True if the text should be flagged, False otherwise."""
