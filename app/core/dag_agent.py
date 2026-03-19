import json
import logging

from openai import OpenAI


DAG_SYSTEM_PROMPT = """You are an expert in cognitive mapping and causal reasoning for qualitative research.
Extract a causal Directed Acyclic Graph (DAG) from the interview transcript provided, representing the interviewee's mental model about the given topic.

Rules:
- Extract only concepts and relationships explicitly expressed by the interviewee (not the interviewer)
- Each node should be a concise concept (2-5 words)
- Edges represent causal or associative relationships between concepts
- Maximum 10 nodes and 12 edges
- The graph must be acyclic (no cycles)
- Edge labels should briefly describe the relationship (e.g., "leads to", "increases", "causes", "results in")

Return ONLY valid JSON in this exact format, no other text:
{
  "nodes": [
    {"id": "1", "label": "concept name"}
  ],
  "edges": [
    {"source": "1", "target": "2", "label": "relationship type"}
  ]
}"""


class DAGAgent:
    """
    Agent that extracts a causal Directed Acyclic Graph (DAG) from an
    interview transcript, capturing the interviewee's mental model about
    a given topic.
    """

    def __init__(self, client: OpenAI):
        self.client = client

    def extract_dag(
        self,
        topic: str,
        history_text: str,
        model: str = "gpt-4o",
        max_tokens: int = 1000,
    ) -> dict:
        """
        Extract a DAG from the interview transcript for a given topic.

        Args:
            topic: Description of the interview topic
            history_text: Formatted interview transcript (Interviewer/Interviewee turns)
            model: OpenAI model to use
            max_tokens: Maximum tokens for the response

        Returns:
            dict with 'nodes' and 'edges' lists, or empty dict on failure
        """
        user_message = f"Topic: {topic}\n\nInterview transcript:\n{history_text}"

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": DAG_SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                response_format={"type": "json_object"},
                max_tokens=max_tokens,
                temperature=0,
            )
            dag = json.loads(response.choices[0].message.content)
            logging.info(
                f"DAG extracted: {len(dag.get('nodes', []))} nodes, "
                f"{len(dag.get('edges', []))} edges"
            )
            return dag
        except Exception as e:
            logging.error(f"DAG extraction failed: {e}")
            return {"nodes": [], "edges": []}
