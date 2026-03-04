# Behavioral Economics AI Interviewer

A console-based prototype for behavioral economics research. An AI interviewer asks participants structured questions, then extracts and visualizes their mental model as a directed acyclic graph (DAG) after each answer.

## How It Works

1. The AI interviewer (powered by Google Gemini) asks questions from `questionnaire.md`
2. After each answer, you confirm you're done (`J`) or continue with follow-up (`N`)
3. The app extracts your causal reasoning as a DAG and opens it in your browser
4. You accept the diagram (`J`) or explain what's missing (`N`)
5. Everything is saved instantly to a JSON session file — crash-safe and resumable

## Prerequisites

- **Python 3.11+**
- **uv** — fast Python package manager
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
- **Graphviz** — for rendering diagrams
  - macOS: `brew install graphviz`
  - Ubuntu/Debian: `sudo apt install graphviz`
  - Windows: Download from https://graphviz.org/download/ and add to PATH

## Setup

```bash
# 1. Clone the repository
git clone <repo-url>
cd behavioral_ai

# 2. Create your .env file
cp .env.example .env
# Edit .env and add your Gemini API key
# Get a free key at: https://aistudio.google.com/apikey

# 3. Install dependencies
uv sync

# 4. Run
uv run behavioral-ai
```

## Customizing the Questionnaire

Edit `questionnaire.md` to change the study title, researcher name, and questions:

```markdown
---
title: My_Study_Title
researcher: Your Name
---

## Frage 1
Your first question here?

## Frage 2
Your second question here?
```

- The `title` is used for the session filename
- Each `## Frage N` section becomes one interview question
- Questions can be in any language — just update the system prompts in `src/behavioral_ai/prompts.py` accordingly

## Session Files

All sessions are saved to `sessions/session_{title}_{timestamp}.json`. The format:

```json
{
  "title": "Mindestlohn_Studie",
  "researcher": "David",
  "started_at": "2026-03-04T14:30:00",
  "turns": [
    {
      "question_index": 1,
      "question_text": "...",
      "messages": [{"role": "model", "content": "..."}, {"role": "user", "content": "..."}],
      "answer_text": "concatenated user answers",
      "dag": {
        "nodes": ["Konzept A", "Konzept B"],
        "edges": [{"from": "Konzept A", "to": "Konzept B", "label": "führt zu"}]
      },
      "diagram_accepted": true,
      "user_correction": null
    }
  ]
}
```

If the application crashes or you quit mid-interview, the session is preserved. On next launch you'll be offered the option to resume.

## Switching AI Providers

The AI backend is abstracted in `src/behavioral_ai/ai/base.py`. To add a new provider (e.g. OpenAI):

1. Create `src/behavioral_ai/ai/openai.py` implementing `AIProvider`
2. Change the provider instantiation in `src/behavioral_ai/main.py`

## Project Structure

```
behavioral_ai/
├── questionnaire.md          # Edit this to change interview questions
├── .env                      # Your API keys (not committed)
├── .env.example              # Template for .env
├── pyproject.toml            # Python project config (uv/hatchling)
└── src/behavioral_ai/
    ├── main.py               # Entry point & interview orchestration
    ├── questionnaire.py      # Markdown questionnaire parser
    ├── session.py            # Session persistence & resume
    ├── prompts.py            # AI system prompts (edit to tune behavior)
    ├── ai/
    │   ├── base.py           # Abstract AIProvider interface
    │   └── gemini.py         # Google Gemini implementation
    └── agents/
        ├── interviewer.py    # Multi-turn interview agent
        └── diagram_creator.py # DAG extraction & visualization
```
