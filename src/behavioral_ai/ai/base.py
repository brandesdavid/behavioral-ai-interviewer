from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Message:
    role: str    # "user" or "model"
    content: str


class AIProvider(ABC):
    """Abstract base class for AI providers. Swap implementations to change the backend."""

    @abstractmethod
    def chat(
        self,
        system_prompt: str,
        history: list[Message],
        user_message: str,
    ) -> str:
        """Multi-turn completion with conversation history. Returns response text."""
        ...

    @abstractmethod
    def chat_json(
        self,
        system_prompt: str,
        user_message: str,
    ) -> dict:
        """Single-turn completion that enforces a JSON response. No history needed."""
        ...
