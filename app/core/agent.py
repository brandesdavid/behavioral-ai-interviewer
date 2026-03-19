import logging
from core.auxiliary import (
    execute_queries,
    fill_prompt_with_interview,
    chat_to_string,
)
from core.dag_agent import DAGAgent
from core.providers.base import BaseProvider


class LLMAgent(object):
    """Class to manage LLM-based agents via a pluggable provider."""

    def __init__(self, provider: BaseProvider):
        self.provider = provider

    def load_parameters(self, parameters: dict):
        """Load interview guidelines for prompt construction."""
        self.parameters = parameters

    def _model(self, task: str) -> str:
        """
        Return the model name for a task, preferring provider-specific overrides.
        E.g. parameters['probe']['model_gemini'] takes precedence over 'model'
        when the active provider is Gemini.
        """
        task_params = self.parameters[task]
        override_key = f"model_{self.provider.provider_name}"
        return task_params.get(override_key) or task_params.get("model", "gpt-4o-mini")

    def construct_query(self, tasks: list, history: list, user_message: str = None) -> dict:
        """
        Build provider-agnostic completion requests for the given tasks.
        Defaults: 300 max_tokens, temperature 0.
        """
        return {
            task: {
                "messages": [{
                    "role": "user",
                    "content": fill_prompt_with_interview(
                        self.parameters[task]["prompt"],
                        self.parameters["interview_plan"],
                        history,
                        user_message=user_message,
                    ),
                }],
                "model": self._model(task),
                "max_tokens": self.parameters[task].get("max_tokens", 300),
                "temperature": self.parameters[task].get("temperature", 0),
            }
            for task in tasks
        }

    def transcribe(self, audio) -> str:
        """Transcribe base64-encoded audio."""
        return self.provider.transcribe(audio)

    def review_answer(self, message: str, history: list) -> bool:
        """Moderate answers: are they on topic?"""
        response = execute_queries(
            self.provider,
            self.construct_query(["moderator"], history, message),
        )
        return "yes" in response["moderator"].lower()

    def review_question(self, next_question: str) -> bool:
        """Moderate questions via provider moderation."""
        return self.provider.moderate_text(next_question)

    def probe_within_topic(self, history: list) -> str:
        """Return next within-topic probing question."""
        response = execute_queries(
            self.provider,
            self.construct_query(["probe"], history),
        )
        return response["probe"]

    def transition_topic(self, history: list) -> tuple[str, str]:
        """
        Generate a topic transition question (and optional summary).
        Returns (transition_question, summary_text).
        """
        summarize = self.parameters.get("summarize")
        tasks = ["summary", "transition"] if summarize else ["transition"]
        response = execute_queries(
            self.provider,
            self.construct_query(tasks, history),
        )
        return response["transition"], response.get("summary", "")

    def extract_dag(self, topic: str, topic_idx: int, history: list) -> dict:
        """
        Extract a causal DAG from the completed topic's interview history.

        Args:
            topic: description of the topic just completed
            topic_idx: 1-based topic index used to filter history
            history: full interview history
        Returns:
            dict with 'nodes' and 'edges', or {} if dag not configured
        """
        if not self.parameters.get("dag"):
            return {}
        dag_params = self.parameters["dag"]
        override_key = f"model_{self.provider.provider_name}"
        model = dag_params.get(override_key) or dag_params.get("model", "gpt-4o")
        dag_agent = DAGAgent(self.provider)
        history_text = chat_to_string(history, only_topic=topic_idx)
        return dag_agent.extract_dag(
            topic=topic,
            history_text=history_text,
            model=model,
            max_tokens=dag_params.get("max_tokens", 1000),
        )
