import re
from pathlib import Path


class QuestionnaireParser:
    """Parses a markdown questionnaire with YAML front matter and ## headings."""

    def __init__(self, path: Path):
        text = path.read_text(encoding="utf-8")
        self.metadata = self._parse_frontmatter(text)
        self.questions = self._parse_questions(text)

    def _parse_frontmatter(self, text: str) -> dict:
        metadata: dict[str, str] = {}
        match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
        if match:
            for line in match.group(1).splitlines():
                if ":" in line:
                    key, _, value = line.partition(":")
                    metadata[key.strip()] = value.strip()
        return metadata

    def _parse_questions(self, text: str) -> list[str]:
        # Remove front matter block
        text = re.sub(r"^---\n.*?\n---\n", "", text, flags=re.DOTALL)
        questions = []
        # Split on ## headings; content after each heading is the question
        sections = re.split(r"^## .+$", text, flags=re.MULTILINE)
        for section in sections[1:]:
            q = section.strip()
            if q:
                questions.append(q)
        return questions
