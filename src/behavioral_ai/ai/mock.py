from .base import AIProvider, Message

_INTERVIEWER_RESPONSES = [
    "Vielen Dank für Ihre Antwort! Können Sie etwas mehr darüber erzählen, "
    "welche konkreten Auswirkungen Sie sich vorstellen?",
    "Das ist sehr interessant. Gibt es noch andere Gedanken oder Gefühle, "
    "die Ihnen dazu kommen?",
    "Ich verstehe. Was denken Sie, wie wahrscheinlich ist dieses Szenario Ihrer Meinung nach?",
]

_DEMO_DAG = {
    "nodes": [
        "Mindestlohnsteigerung",
        "Mehr Menschen verdienen Geld",
        "Bessere Lebensqualität",
        "Angst vor Staatskollaps",
        "Höhere Unternehmenskosten",
        "Entlassungen möglich",
    ],
    "edges": [
        {"from": "Mindestlohnsteigerung", "to": "Mehr Menschen verdienen Geld", "label": "führt zu"},
        {"from": "Mehr Menschen verdienen Geld", "to": "Bessere Lebensqualität", "label": "bewirkt"},
        {"from": "Mindestlohnsteigerung", "to": "Angst vor Staatskollaps", "label": "erzeugt"},
        {"from": "Mindestlohnsteigerung", "to": "Höhere Unternehmenskosten", "label": "verursacht"},
        {"from": "Höhere Unternehmenskosten", "to": "Entlassungen möglich", "label": "kann führen zu"},
    ],
}


class MockProvider(AIProvider):
    """Demo provider — no API calls. Returns hardcoded responses for flow testing."""

    _QUESTION_INTROS = [
        "Herzlich willkommen! Meine erste Frage an Sie: {question}",
        "Danke. Kommen wir zur nächsten Frage: {question}",
        "Sehr gut. Weiter zur dritten Frage: {question}",
        "Fast geschafft! Letzte Frage: {question}",
    ]

    def __init__(self) -> None:
        self._call_count = 0
        self._question_count = 0

    def chat(self, system_prompt: str, history: list[Message], user_message: str) -> str:
        if user_message.startswith("[Bitte stelle die folgende Forschungsfrage]"):
            question = user_message.split("]: ", 1)[-1]
            intro = self._QUESTION_INTROS[self._question_count % len(self._QUESTION_INTROS)]
            self._question_count += 1
            return intro.format(question=question)

        if user_message.startswith("[Teilnehmer hat die Frage abgeschlossen"):
            return "Vielen Dank für Ihre Antwort! Ich erstelle nun ein Diagramm Ihrer Gedanken."

        response = _INTERVIEWER_RESPONSES[self._call_count % len(_INTERVIEWER_RESPONSES)]
        self._call_count += 1
        return response

    def chat_json(self, system_prompt: str, user_message: str) -> dict:
        return _DEMO_DAG
