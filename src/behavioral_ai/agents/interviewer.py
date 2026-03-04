from rich.console import Console
from rich.panel import Panel

from ..ai.base import AIProvider, Message
from ..prompts import format_interviewer_prompt

console = Console()


class InterviewerAgent:
    """Conducts a multi-turn interview for a single question using an AI provider."""

    def __init__(self, provider: AIProvider):
        self.provider = provider
        self.history: list[Message] = []  # spans entire session for cross-question memory

    def conduct_question(self, question: str) -> list[Message]:
        """
        Runs the multi-turn interview loop for one question.

        After each user message, asks "Sind Sie fertig mit Ihrer Antwort? (J/N)".
        If J → moves to diagram creation. If N → AI responds with follow-up.

        Returns the list of messages for this question turn.
        """
        system_prompt = format_interviewer_prompt(question)
        turn_messages: list[Message] = []

        # AI opens with the question
        opening = self.provider.chat(
            system_prompt=system_prompt,
            history=self.history,
            user_message=f"[Bitte stelle die folgende Forschungsfrage]: {question}",
        )
        console.print(Panel(opening, title="[bold blue]Interviewer[/bold blue]", border_style="blue"))

        interviewer_opening = Message(role="model", content=opening)
        self.history.append(interviewer_opening)
        turn_messages.append(interviewer_opening)

        while True:
            user_input = console.input("\n[bold green]Sie[/bold green]: ").strip()
            if not user_input:
                continue

            user_msg = Message(role="user", content=user_input)
            self.history.append(user_msg)
            turn_messages.append(user_msg)

            fertig = console.input(
                "[dim]Sind Sie fertig mit Ihrer Antwort? (J/N)[/dim]: "
            ).strip().upper()

            if fertig == "J":
                # AI acknowledges and wraps up the question
                closing = self.provider.chat(
                    system_prompt=system_prompt,
                    history=self.history,
                    user_message="[Teilnehmer hat die Frage abgeschlossen. Bedanke dich kurz.]",
                )
                console.print(Panel(closing, title="[bold blue]Interviewer[/bold blue]", border_style="blue"))
                closing_msg = Message(role="model", content=closing)
                self.history.append(closing_msg)
                turn_messages.append(closing_msg)
                break
            # N = not finished yet, just loop back so user can keep typing

        return turn_messages

    @staticmethod
    def get_answer_text(turn_messages: list[Message]) -> str:
        """Concatenates all user messages from a turn into one text block."""
        parts = [m.content for m in turn_messages if m.role == "user"]
        return " ".join(parts)
