import json

from google import genai
from google.genai import types

from .base import AIProvider, Message


class GeminiProvider(AIProvider):
    """Google Gemini implementation of AIProvider using the google-genai SDK."""

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash-lite"):
        self.client = genai.Client(api_key=api_key)
        self.model = model

    def chat(
        self,
        system_prompt: str,
        history: list[Message],
        user_message: str,
    ) -> str:
        contents = [
            types.Content(
                role=msg.role,
                parts=[types.Part(text=msg.content)],
            )
            for msg in history
        ]
        contents.append(
            types.Content(role="user", parts=[types.Part(text=user_message)])
        )

        response = self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
            ),
        )
        return response.text

    def chat_json(self, system_prompt: str, user_message: str) -> dict:
        response = self.client.models.generate_content(
            model=self.model,
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
            ),
        )
        return json.loads(response.text)
