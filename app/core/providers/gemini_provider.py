import json
import logging
from base64 import b64decode

from google import genai
from google.genai import types
from core.providers.base import BaseProvider


class GeminiProvider(BaseProvider):
    """LLM provider backed by Google Gemini."""

    provider_name = "gemini"

    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        logging.info("Gemini client instantiated.")

    def _build_config(self, max_tokens: int, temperature: float, system: str = None, json_mode: bool = False):
        return types.GenerateContentConfig(
            max_output_tokens=max_tokens,
            temperature=temperature,
            system_instruction=system,
            response_mime_type="application/json" if json_mode else None,
        )

    def _split_messages(self, messages: list) -> tuple[str | None, list]:
        """Separate system prompt from user/assistant turns."""
        system = None
        contents = []
        for msg in messages:
            role = msg["role"]
            text = msg["content"]
            if role == "system":
                system = text
            elif role == "user":
                contents.append(types.Content(role="user", parts=[types.Part(text=text)]))
            elif role in ("assistant", "model"):
                contents.append(types.Content(role="model", parts=[types.Part(text=text)]))
        return system, contents

    def complete(self, messages: list, model: str, max_tokens: int, temperature: float) -> str:
        system, contents = self._split_messages(messages)
        response = self.client.models.generate_content(
            model=model,
            contents=contents,
            config=self._build_config(max_tokens, temperature, system),
        )
        return response.text.strip()

    def complete_json(self, messages: list, model: str, max_tokens: int, temperature: float) -> dict:
        system, contents = self._split_messages(messages)
        response = self.client.models.generate_content(
            model=model,
            contents=contents,
            config=self._build_config(max_tokens, temperature, system, json_mode=True),
        )
        return json.loads(response.text)

    def transcribe(self, audio: str) -> str:
        audio_bytes = b64decode(audio)
        response = self.client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=[types.Content(parts=[
                types.Part(inline_data=types.Blob(mime_type="audio/webm", data=audio_bytes)),
                types.Part(text="Transcribe the audio. Return only the transcription text, nothing else."),
            ])],
        )
        return response.text.strip()

    def moderate_text(self, text: str) -> bool:
        # Gemini applies safety filters at the API level; no dedicated moderation endpoint.
        logging.debug("Gemini provider: moderate_text always returns False (safety handled by API).")
        return False
