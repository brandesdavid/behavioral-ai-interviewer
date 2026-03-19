# AI Interviewer — common dev commands
# Usage: just <command>

set dotenv-load  # automatically load .env from repo root

# show available commands
default:
    @just --list

# ── Local dev ────────────────────────────────────────────────────────────────

# create venv and install dependencies
setup:
    python3 -m venv venv
    venv/bin/pip3 install -r local_requirements.txt
    @echo "Done. Activate with: source venv/bin/activate"

# run Flask app locally (requires activated venv or env/)
run:
    cd app && ../venv/bin/python app.py

# run with a specific provider (openai | gemini)
run-openai:
    cd app && LLM_PROVIDER=openai ../venv/bin/python app.py

run-gemini:
    cd app && LLM_PROVIDER=gemini ../venv/bin/python app.py

# ── Docker ───────────────────────────────────────────────────────────────────

# build and start via docker compose
up:
    docker compose up --build

# start without rebuilding
start:
    docker compose up

# stop containers
stop:
    docker compose down

# view live logs
logs:
    docker compose logs -f

# ── Health checks ────────────────────────────────────────────────────────────

# check if the server is running
ping:
    curl -s http://localhost:8000/ && echo

healthcheck:
    curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/healthcheck

# send a test interview request (starts a new session)
test-request:
    curl -s -X POST http://localhost:8000/ \
      -H "Content-Type: application/json" \
      -d '{"route":"next","payload":{"session_id":"test-123","interview_id":"HOMELESS_BERLIN","user_message":""}}' \
      | python -m json.tool

# ── Test UI ──────────────────────────────────────────────────────────────────

# open the local test page (demo + live mode) in the browser
test-ui:
    open test/index.html

# ── Data ─────────────────────────────────────────────────────────────────────

# export all sessions to CSV
export output="data.csv":
    python retrieve.py --data_dir=app/data --output_path={{output}}
    @echo "Exported to {{output}}"

# export and print transcripts to stdout
export-print output="data.csv":
    python retrieve.py --data_dir=app/data --output_path={{output}} --print_chats

# list stored session files
sessions:
    @ls -lh app/data/*.json 2>/dev/null || echo "No sessions found in app/data/"

# delete all stored sessions (asks for confirmation)
clean-data:
    @echo "This will delete all files in app/data/. Press Ctrl-C to cancel."
    @sleep 2
    rm -f app/data/*.json
    @echo "Cleared."
