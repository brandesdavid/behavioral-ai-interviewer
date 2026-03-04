import webbrowser
from pathlib import Path

import graphviz
from rich.console import Console

from ..ai.base import AIProvider
from ..prompts import DIAGRAM_EXTRACTOR_SYSTEM_PROMPT

console = Console()


class DiagramCreatorAgent:
    """Extracts a mental model DAG from an interview answer and shows it to the user."""

    def __init__(self, provider: AIProvider, output_dir: Path):
        self.provider = provider
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def create_and_show(
        self,
        question: str,
        answer_text: str,
        question_index: int,
    ) -> tuple[dict, bool, str | None]:
        """
        Extracts a DAG from the answer, renders it as SVG, opens it in the browser,
        and asks the user to accept or reject it.

        Returns: (dag_data, accepted, correction_text)
        """
        console.print("\n[bold yellow]Diagramm wird erstellt...[/bold yellow]")

        dag_data = self._extract_dag(question, answer_text)
        svg_path = self._render_dag(dag_data, question_index)

        console.print("[bold yellow]Das Diagramm wird jetzt in Ihrem Browser geöffnet.[/bold yellow]\n")
        webbrowser.open(f"file://{svg_path}")

        console.print("[bold]Repräsentiert dieses Diagramm Ihr mentales Modell?[/bold]")
        response = console.input("[bold green](J/N)[/bold green]: ").strip().upper()
        accepted = response == "J"

        correction: str | None = None
        if not accepted:
            correction = console.input(
                "[bold green]Bitte erläutere wieso der Graph dir nicht passt[/bold green]: "
            ).strip()
            console.print("[dim]Danke für Ihr Feedback. Wir gehen zur nächsten Frage über.[/dim]\n")
        else:
            console.print("[dim]Danke! Wir gehen zur nächsten Frage über.[/dim]\n")

        return dag_data, accepted, correction

    def _extract_dag(self, question: str, answer: str) -> dict:
        user_message = f"Frage: {question}\n\nAntwort des Teilnehmers: {answer}"
        return self.provider.chat_json(
            system_prompt=DIAGRAM_EXTRACTOR_SYSTEM_PROMPT,
            user_message=user_message,
        )

    def _render_dag(self, dag_data: dict, question_index: int) -> str:
        dot = graphviz.Digraph(
            name=f"question_{question_index}",
            format="svg",
            graph_attr={
                "rankdir": "LR",
                "bgcolor": "white",
                "fontname": "Helvetica",
                "pad": "0.5",
                "splines": "ortho",
            },
            node_attr={
                "shape": "box",
                "style": "rounded,filled",
                "fillcolor": "#E8F4FD",
                "color": "#2E86C1",
                "fontname": "Helvetica",
                "fontsize": "11",
            },
            edge_attr={
                "fontname": "Helvetica",
                "fontsize": "9",
                "color": "#555555",
                "arrowsize": "0.8",
            },
        )

        nodes = dag_data.get("nodes", [])
        edges = dag_data.get("edges", [])

        # First node gets a distinct style as the root concept
        for i, node in enumerate(nodes):
            if i == 0:
                dot.node(node, node, fillcolor="#2E86C1", fontcolor="white", style="rounded,filled")
            else:
                dot.node(node, node)

        for edge in edges:
            src = edge.get("from", "")
            dst = edge.get("to", "")
            label = edge.get("label", "")
            if src and dst:
                dot.edge(src, dst, label=label)

        output_path = self.output_dir / f"diagram_q{question_index}"
        rendered = dot.render(str(output_path), cleanup=True)
        return str(Path(rendered).resolve())
