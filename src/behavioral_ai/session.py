import json
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path


@dataclass
class TurnRecord:
    question_index: int
    question_text: str
    messages: list[dict]       # [{"role": "user"|"model", "content": "..."}, ...]
    answer_text: str           # concatenated user messages
    dag: dict                  # {"nodes": [...], "edges": [...]}
    diagram_accepted: bool
    user_correction: str | None


@dataclass
class SessionData:
    title: str
    researcher: str
    started_at: str
    turns: list[TurnRecord] = field(default_factory=list)


class SessionManager:
    """Manages a single interview session with instant-write persistence."""

    def __init__(self, title: str, researcher: str, sessions_dir: Path):
        self.sessions_dir = sessions_dir
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = title.replace(" ", "_")
        self.filepath = sessions_dir / f"session_{safe_title}_{timestamp}.json"

        self.data = SessionData(
            title=title,
            researcher=researcher,
            started_at=datetime.now().isoformat(),
        )
        self._write()

    @classmethod
    def load(cls, filepath: Path) -> tuple["SessionManager", list[int]]:
        """Load an existing session file. Returns (manager, completed_question_indices)."""
        with open(filepath, encoding="utf-8") as f:
            raw = json.load(f)

        # Reconstruct a manager without creating a new file
        manager = object.__new__(cls)
        manager.sessions_dir = filepath.parent
        manager.filepath = filepath

        turns = [TurnRecord(**t) for t in raw.get("turns", [])]
        manager.data = SessionData(
            title=raw["title"],
            researcher=raw["researcher"],
            started_at=raw["started_at"],
            turns=turns,
        )

        completed_indices = {t.question_index for t in turns}
        return manager, completed_indices

    def add_turn(self, turn: TurnRecord) -> None:
        self.data.turns.append(turn)
        self._write()

    def _write(self) -> None:
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(asdict(self.data), f, ensure_ascii=False, indent=2)
