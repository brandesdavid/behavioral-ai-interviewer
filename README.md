# AI Interviewer with DAG-based Mental Model Extraction

This project extends the AI interviewer framework by Chopra & Haaland (2023) with a **DAG Agent** that automatically extracts causal Directed Acyclic Graphs (DAGs) from interview transcripts. After each interview topic is completed, the DAG Agent maps the interviewee's stated reasoning into a structured mental model — capturing concepts and causal relationships as a graph that can be stored, compared, and analyzed across participants.

## Building on Prior Work

This codebase builds on the paper:

> Chopra, Felix and Haaland, Ingar, *Conducting Qualitative Interviews with AI* (2023). CESifo Working Paper No. 10666.
> Available at SSRN: <https://ssrn.com/abstract=4583756>

The original framework provides a scalable AI interviewer system supporting multi-topic interview plans, LLM-based probing and topic transition agents, answer moderation, and deployment via Flask. We extend this with a DAG extraction layer that turns qualitative interview responses into structured causal graphs — enabling quantitative analysis of mental models at scale.

The original code is licensed under [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/). Uses and distribution should cite the paper above.

---

## What's New: DAG Agent

The `DAGAgent` (`app/core/dag_agent.py`) extracts a causal DAG from the interview transcript at each topic transition. It uses the configured LLM with structured JSON output to identify:

- **Nodes**: key concepts explicitly mentioned by the interviewee (2–5 words each, max 10)
- **Edges**: directed causal relationships between concepts (max 12), labelled (e.g. "leads to", "causes")

The DAG is stored in the session history under `topic_dags` and returned in the API response as `dag` when a topic transition occurs.

Enable DAG extraction by adding a `"dag"` key to your interview config in `app/parameters.py`:

```python
"dag": {
    "model": "gpt-4o",
    "model_gemini": "gemini-2.0-flash",
    "max_tokens": 1000
}
```

---

## LLM Provider

Switch between OpenAI and Gemini via environment variable:

```bash
# OpenAI (default)
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...

# Gemini
LLM_PROVIDER=gemini
GEMINI_API_KEY=AIza...
```

Each agent config in `app/parameters.py` supports `model` (OpenAI) and `model_gemini` (Gemini) fields.

---

## Interview Configurations

### STOCK_MARKET
Investigates reasons for non-participation in the stock market (original configuration from Chopra & Haaland 2023).

### HOMELESS_BERLIN
Explores interviewees' causal beliefs about homelessness in Berlin — what causes it, what keeps people homeless, and what solutions exist. DAG extraction is enabled.

Opening question:
> *"I am interested in learning more about what you think about homelessness in Berlin. Can you help me understand what you think are the main factors or reasons why people become homeless and what keeps them homeless?"*

---

## Setup

The application requires an OpenAI or Gemini API key. Set it via environment variable or edit `app/parameters.py` directly.


## Option 1: Local development (without Docker)

```bash
python -m venv env && source env/bin/activate
pip install -r local_requirements.txt
python app/app.py
```

The app runs on `http://127.0.0.1:8000`. Test it:
```bash
curl http://127.0.0.1:8000/
# → Running!
```


## Option 2: Docker (local or server)

```bash
docker compose up --build
```

The container exposes port `8000`. Set env vars in a `.env` file next to `docker-compose.yml`:

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
LOG_LEVEL=ERROR
```

Session data is persisted in `./app/data` via a volume mount.


## Option 3: Coolify (production, recommended)

1. Push this repo to your Git provider.
2. In Coolify, create a new **Dockerfile**-based service pointing to the repo.
3. Set the following environment variables in Coolify:

| Variable | Value |
|----------|-------|
| `LLM_PROVIDER` | `openai` or `gemini` |
| `OPENAI_API_KEY` | your key |
| `GEMINI_API_KEY` | your key (if using Gemini) |
| `LOG_LEVEL` | `ERROR` |

4. Set the exposed port to `8000`.
5. Mount a persistent volume to `/app/data` to preserve session data across deploys.
6. Deploy. Coolify handles HTTPS and the reverse proxy automatically.

---

## Qualtrics Integration

Once deployed, embed the interview directly in a Qualtrics survey.

**Step 1:** In Qualtrics, add these embedded variables to the beginning of your survey flow:

| Variable | Value |
|----------|-------|
| `user_id` | unique respondent identifier |
| `interview_id` | e.g. `HOMELESS_BERLIN` (must match a key in `app/parameters.py`) |
| `interview_endpoint` | your server URL, e.g. `https://interviews.your-domain.com/` |

**Step 2:** Create a `Text/Graphic` question. Copy the HTML from `Qualtrics/without_voice/Qualtrics.html` (or `with_voice/` for audio input) into the HTML field, and the JS into the JavaScript field.

**Step 3:** Done. The survey will call your server at `interview_endpoint` automatically.

> **Note:** The Qualtrics JS sends requests in the format `{"route": "...", "payload": {...}}` to the root endpoint `/`. The Flask app handles this via a built-in dispatcher — no additional configuration needed.


## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check — returns `Running!` |
| `/healthcheck` | GET | Returns `200` |
| `/` | POST | Qualtrics dispatcher — accepts `{route, payload}` |
| `/<interview_id>/<session_id>` | GET | Browser-based test interview |
| `/next` | POST | Next question — `{session_id, interview_id, user_message}` |
| `/transcribe` | POST | Transcribe audio — `{audio: base64}` |
| `/load/<session_id>` | GET | Load session history |
| `/delete/<session_id>` | GET | Delete session |
| `/retrieve` | GET | Retrieve all sessions |


## Retrieving Stored Interviews

Sessions are stored as JSON files in `app/data/`. Export to CSV:

```bash
python retrieve.py --data_dir=app/data --output_path=data.csv
```

To also print the transcripts to stdout:
```bash
python retrieve.py --data_dir=app/data --output_path=data.csv --print_chats
```


## Citation

```
@article{ChopraHaaland2023,
  title={Conducting Qualitative Interviews with AI},
  author={Chopra, Felix and Haaland, Ingar},
  journal={CESifo Working Paper No. 10666},
  url={https://ssrn.com/abstract=4583756},
  year={2023}
}
```
