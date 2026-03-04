import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.box import Box, SQUARE
from rich.table import Table

from .ai.gemini import GeminiProvider
from .ai.mock import MockProvider
from .agents.diagram_creator import DiagramCreatorAgent
from .agents.interviewer import InterviewerAgent
from .questionnaire import QuestionnaireParser
from .session import SessionManager, TurnRecord

console = Console()

# src/behavioral_ai -> project root
PROJECT_ROOT = Path(__file__).parent.parent.parent


def _find_existing_sessions(sessions_dir: Path) -> list[Path]:
    if not sessions_dir.exists():
        return []
    return sorted(sessions_dir.glob("session_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)


def _prompt_resume(sessions_dir: Path) -> tuple[SessionManager | None, set[int]]:
    """
    If existing sessions exist, offer the user a choice to resume one.
    Returns (session_manager, completed_question_indices).
    """
    existing = _find_existing_sessions(sessions_dir)
    if not existing:
        return None, set()

    console.print("\n[bold yellow]Vorhandene Sessions gefunden:[/bold yellow]")
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("#", width=4)
    table.add_column("Datei")
    table.add_column("Fragen beantwortet", justify="right")

    for i, path in enumerate(existing, start=1):
        try:
            import json
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            turns_done = len(data.get("turns", []))
            table.add_row(str(i), path.name, str(turns_done))
        except Exception:
            table.add_row(str(i), path.name, "?")

    console.print(table)
    console.print(f"[dim]0 = Neu starten[/dim]")

    choice = console.input(
        "\n[bold green]Ihre Wahl (0 = Neu)[/bold green]: ").strip()
    try:
        idx = int(choice)
    except ValueError:
        idx = 0

    if idx == 0 or idx > len(existing):
        return None, set()

    selected = existing[idx - 1]
    console.print(f"[dim]Session wird geladen: {selected.name}[/dim]")
    manager, completed = SessionManager.load(selected)
    console.print(
        f"[bold green]Fortsetze Session mit {len(completed)} bereits beantworteten Frage(n).[/bold green]\n")
    return manager, completed


def main() -> None:
    demo_mode = "--demo" in sys.argv

    load_dotenv()

    if demo_mode:
        provider = MockProvider()
    else:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            console.print(
                "[bold red]Fehler: GEMINI_API_KEY ist nicht gesetzt.[/bold red]")
            console.print(
                "[dim]Erstelle eine .env Datei basierend auf .env.example[/dim]")
            console.print(
                "[dim]Oder starte mit --demo um den Flow ohne API-Key zu testen.[/dim]")
            sys.exit(1)
        provider = GeminiProvider(api_key=api_key)

    questionnaire_path = PROJECT_ROOT / "questionnaire.md"
    if not questionnaire_path.exists():
        console.print(
            f"[bold red]Fehler: questionnaire.md nicht gefunden unter {questionnaire_path}[/bold red]")
        sys.exit(1)

    sessions_dir = PROJECT_ROOT / "sessions"
    diagrams_dir = sessions_dir / "diagrams"

    parser = QuestionnaireParser(questionnaire_path)
    metadata = parser.metadata
    questions = parser.questions

    if not questions:
        console.print(
            "[bold red]Fehler: Keine Fragen in questionnaire.md gefunden.[/bold red]")
        sys.exit(1)

    demo_banner = "\n[bold yellow]⚠ DEMO MODE — Keine API-Aufrufe, vorgefertigtes Diagramm[/bold yellow]" if demo_mode else ""
    console.print(Panel(
        f"[bold]Behavioral Economics Forschungsinterview[/bold]{demo_banner}\n\n"
        f"Studie:    {metadata.get('title', 'N/A')}\n"
        f"Forscher:  {metadata.get('researcher', 'N/A')}\n"
        f"Fragen:    {len(questions)}\n\n"
        f"[dim]Nach jeder Antwort werden Sie gefragt ob Sie fertig sind (J/N).\n"
        f"Ein Diagramm Ihrer Gedanken wird dann zur Bestätigung angezeigt.[/dim]",
        border_style="yellow" if demo_mode else "green",
        title="Willkommen",
    ))

    # Resume or start fresh
    session, completed_indices = _prompt_resume(sessions_dir)

    if session is None:
        session = SessionManager(
            title=metadata.get("title", "interview"),
            researcher=metadata.get("researcher", "unknown"),
            sessions_dir=sessions_dir,
        )
        console.print(
            f"[dim]Session gespeichert unter: {session.filepath}[/dim]\n")

    interviewer = InterviewerAgent(provider=provider)
    diagram_creator = DiagramCreatorAgent(
        provider=provider, output_dir=diagrams_dir)

    # Main interview loop
    for i, question in enumerate(questions, start=1):
        if i in completed_indices:
            console.print(
                f"[dim]Frage {i} bereits beantwortet — überspringe.[/dim]")
            continue

        console.print(Panel.fit(
            f"[bold cyan]Frage {i} von {len(questions)}[/bold cyan]", box=SQUARE, border_style="bold cyan"))

        try:
            turn_messages = interviewer.conduct_question(question)
            answer_text = InterviewerAgent.get_answer_text(turn_messages)

            if not answer_text.strip():
                console.print(
                    "[dim]Keine Antwort erhalten — überspringe Diagramm.[/dim]")
                continue

            dag_data, accepted, correction = diagram_creator.create_and_show(
                question=question,
                answer_text=answer_text,
                question_index=i,
            )

            session.add_turn(TurnRecord(
                question_index=i,
                question_text=question,
                messages=[{"role": m.role, "content": m.content}
                          for m in turn_messages],
                answer_text=answer_text,
                dag=dag_data,
                diagram_accepted=accepted,
                user_correction=correction,
            ))

        except KeyboardInterrupt:
            console.print(
                "\n\n[bold yellow]Interview unterbrochen. Session wurde gespeichert.[/bold yellow]")
            console.print(f"[dim]{session.filepath}[/dim]")
            sys.exit(0)

    console.print(Panel(
        f"[bold green]Interview abgeschlossen![/bold green]\n\n"
        f"Alle {len(questions)} Fragen wurden beantwortet.\n"
        f"Session gespeichert unter:\n[dim]{session.filepath}[/dim]",
        border_style="green",
        title="Fertig",
    ))
