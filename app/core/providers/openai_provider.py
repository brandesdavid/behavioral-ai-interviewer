import json
import logging
from io import BytesIO
from base64 import b64decode

from openai import OpenAI
from core.providers.base import BaseProvider


class OpenAIProvider(BaseProvider):
    """LLM provider backed by OpenAI."""

    provider_name = "openai"

    def __init__(self, api_key: str, timeout: int = 30, max_retries: int = 3):
        self.client = OpenAI(api_key=api_key, timeout=timeout, max_retries=max_retries)
        logging.info("OpenAI client instantiated.")

    def complete(self, messages: list, model: str, max_tokens: int, temperature: float) -> str:
        response = self.client.chat.completions.create(
            messages=messages,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message.content.strip("\n\" '''")

    def complete_json(self, messages: list, model: str, max_tokens: int, temperature: float) -> dict:
        response = self.client.chat.completions.create(
            messages=messages,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            response_format={"type": "json_object"},
        )
        return json.loads(response.choices[0].message.content)

    def transcribe(self, audio: str) -> str:
        audio_file = BytesIO(b64decode(audio))
        audio_file.name = "audio.webm"
        response = self.client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language="en",
        )
        return response.text

    def moderate_text(self, text: str) -> bool:
        response = self.client.moderations.create(
            model="omni-moderation-latest",
            input=text,
        )
        return response.to_dict()["results"][0]["flagged"]
