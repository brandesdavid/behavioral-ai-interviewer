# AI Interviewer with DAG-based Mental Model Extraction

This project extends the AI interviewer framework by Chopra & Haaland (2023) with a **DAG Agent** that automatically extracts causal Directed Acyclic Graphs (DAGs) from interview transcripts. After each interview topic is completed, the DAG Agent maps the interviewee's stated reasoning into a structured mental model — capturing concepts and causal relationships as a graph that can be stored, compared, and analyzed across participants.

## Building on Prior Work

This codebase builds on the paper:

> Chopra, Felix and Haaland, Ingar, *Conducting Qualitative Interviews with AI* (2023). CESifo Working Paper No. 10666.
> Available at SSRN: https://ssrn.com/abstract=4583756

The original framework provides a scalable AI interviewer system supporting multi-topic interview plans, LLM-based probing and topic transition agents, answer moderation, and deployment via Flask or AWS Lambda. We extend this with a DAG extraction layer that turns qualitative interview responses into structured causal graphs — enabling quantitative analysis of mental models at scale.

The original code is licensed under [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/). Uses and distribution should cite the paper above.

---

## What's New: DAG Agent

The `DAGAgent` (`app/core/dag_agent.py`) extracts a causal DAG from the interview transcript at each topic transition. It uses GPT-4o with a structured JSON output to identify:

- **Nodes**: key concepts explicitly mentioned by the interviewee (2–5 words each, max 10)
- **Edges**: directed causal relationships between concepts (max 12), labelled (e.g. "leads to", "causes", "increases")

The DAG is stored in the session history under `topic_dags` and returned in the API response as `dag` when a topic transition occurs.

### Enabling DAG extraction

Add a `"dag"` key to your interview configuration in `app/parameters.py`:

```python
"dag": {
    "model": "gpt-4o",
    "max_tokens": 1000
}
```

If `"dag"` is absent from the config, extraction is skipped and behaviour is identical to the original framework.

### API response with DAG

When a topic transition occurs and DAG extraction is enabled, the `/next` response includes:

```json
{
  "session_id": "...",
  "message": "transition question from interviewer",
  "dag": {
    "nodes": [
      {"id": "1", "label": "lack of affordable housing"},
      {"id": "2", "label": "rising rents"}
    ],
    "edges": [
      {"source": "2", "target": "1", "label": "causes"}
    ]
  }
}
```

---

## Interview Configurations

### STOCK_MARKET
Investigates reasons for non-participation in the stock market (original configuration from Chopra & Haaland 2023).

### HOMELESS_BERLIN
Explores interviewees' causal beliefs about homelessness in Berlin — what causes it, what keeps people homeless, and what solutions exist. DAG extraction is enabled, producing one mental-model graph per completed topic.

Opening question:
> *"I am interested in learning more about what you think about homelessness in Berlin. Can you help me understand what you think are the main factors or reasons why people become homeless and what keeps them homeless?"*

Topics:
1. Reasons behind becoming and staying homeless
2. Structural and systemic barriers to leaving homelessness
3. Potential solutions, support systems, and policy changes

---

## Setup & Deployment

Three deployment options are supported: local testing, Flask server, and AWS Lambda (preferred for scale). See sections below.

The application requires an OpenAI API key. Set it via environment variable:

```bash
export OPENAI_API_KEY=your_key_here
```

Or edit `OPENAI_API_KEY` directly in `app/parameters.py`.


## Option 1: Running locally (Docker)

```bash
docker compose up --build --detach
```

Then navigate to `http://127.0.0.1:8000/HOMELESS_BERLIN/TEST-SESSION-123` to start a test interview.


## Option 2: Deploy as Flask app

```bash
scp -r <LOCAL_DIRECTORY> <REMOTE_DIRECTORY>
docker compose up --build --detach
```


## Option 3: Deploy as AWS Lambda (preferred)

```bash
./aws_setup.sh <AWS_PUBLIC_KEY> <AWS_SECRET_KEY> <AWS_REGION> <S3_BUCKET>
./aws_deploy.sh <S3_BUCKET>
```

The deploy script returns a public endpoint URL. Test it:

```bash
curl -X POST \
  -d '{"route":"next","payload":{"session_id":"test","interview_id":"HOMELESS_BERLIN","user_message":"test"}}' \
  https://<YOUR_ENDPOINT>.amazonaws.com/Prod/
```


## Qualtrics Integration

Embed the interview in a Qualtrics survey using the files in `/Qualtrics`. Add embedded variables `user_id`, `interview_id`, `interview_endpoint`, and `first_question` to your survey flow, then copy the HTML/JS from `/Qualtrics` into a Text/Graphic question.


## Retrieving Stored Interviews

**Local / Flask**: sessions are stored in `app/data/`. Retrieve via:
```bash
curl -X POST -d '{"route":"retrieve","payload":{}}' http://127.0.0.1:8000/retrieve
```

**AWS Lambda**: export all sessions to CSV:
```bash
python aws_retrieve.py --table_name=interview-sessions --output_path=data.csv
```

The exported data includes `topic_dags` per session entry, allowing offline analysis of extracted mental models.


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
