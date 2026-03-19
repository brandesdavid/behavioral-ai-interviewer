import logging
from core.auxiliary import (
    execute_queries,
    fill_prompt_with_interview,
    chat_to_string
)
from core.dag_agent import DAGAgent
from io import BytesIO
from base64 import b64decode
from openai import OpenAI


class LLMAgent(object):
    """ Class to manage LLM-based agents. """

    def __init__(self, api_key, timeout: int = 30, max_retries: int = 3):
        self.client = OpenAI(
            api_key=api_key, timeout=timeout, max_retries=max_retries)
        logging.info("OpenAI client instantiated. Should happen only once!")

    def load_parameters(self, parameters: dict):
        """ Load interview guidelines for prompt construction. """
        self.parameters = parameters

    def transcribe(self, audio) -> str:
        """ Transcribe audio file. """
        audio_file = BytesIO(b64decode(audio))
        audio_file.name = "audio.webm"

        response = self.client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language="en"  # English language input
        )
        return response.text

    def construct_query(self, tasks: list, history: list, user_message: str = None) -> dict:
        """ 
        Construct OpenAI API completions query, 
        defaults to `gpt-4o-mini` model, 300 token answer limit, and temperature of 0. 
        For details see https://platform.openai.com/docs/api-reference/completions.
        """
        return {
            task: {
                "messages": [{
                    "role": "user",
                    "content": fill_prompt_with_interview(
                        self.parameters[task]['prompt'],
                        self.parameters['interview_plan'],
                        history,
                        user_message=user_message
                    )
                }],
                "model": self.parameters[task].get('model', 'gpt-4o-mini'),
                "max_tokens": self.parameters[task].get('max_tokens', 300),
                "temperature": self.parameters[task].get('temperature', 0)
            } for task in tasks
        }

    def review_answer(self, message: str, history: list) -> bool:
        """ Moderate answers: Are they on topic? """
        response = execute_queries(
            self.client.chat.completions.create,
            self.construct_query(['moderator'], history, message)
        )
        return "yes" in response["moderator"].lower()

    def review_question(self, next_question: str) -> bool:
        """ Moderate questions: Are they flagged by the moderation endpoint? """
        response = self.client.moderations.create(
            model="omni-moderation-latest",
            input=next_question,
        )
        return response.to_dict()["results"][0]["flagged"]

    def probe_within_topic(self, history: list) -> str:
        """ Return next 'within-topic' probing question. """
        response = execute_queries(
            self.client.chat.completions.create,
            self.construct_query(['probe'], history)
        )
        return response['probe']

    def transition_topic(self, history: list) -> tuple[str, str]:
        """
        Determine next interview question transition from one topic
        cluster to the next. If have defined `summarize` model in parameters
        will also get summarization of interview thus far.
        """
        summarize = self.parameters.get('summarize')
        tasks = ['summary', 'transition'] if summarize else ['transition']
        response = execute_queries(
            self.client.chat.completions.create,
            self.construct_query(tasks, history)
        )
        return response['transition'], response.get('summary', '')

    def extract_dag(self, topic: str, topic_idx: int, history: list) -> dict:
        """
        Extract a causal DAG from the completed topic's interview history.

        Args:
            topic: Description of the topic just completed
            topic_idx: Index of the topic (1-based) to extract history for
            history: Full interview history

        Returns:
            dict with 'nodes' and 'edges', or empty dict if dag not configured
        """
        if not self.parameters.get('dag'):
            return {}
        dag_params = self.parameters['dag']
        dag_agent = DAGAgent(self.client)
        history_text = chat_to_string(history, only_topic=topic_idx)
        return dag_agent.extract_dag(
            topic=topic,
            history_text=history_text,
            model=dag_params.get('model', 'gpt-4o'),
            max_tokens=dag_params.get('max_tokens', 1000),
        )
