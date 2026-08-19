#!/bin/bash
# Wrapper script that launchd calls daily. Loads your API keys/passwords
# from a .env file (keeps secrets out of the launchd plist itself) and
# runs the agent, logging output for debugging.

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

if [ -f "$PROJECT_DIR/.env" ]; then
  set -a
  source "$PROJECT_DIR/.env"
  set +a
else
  echo "Missing .env file at $PROJECT_DIR/.env -- copy .env.example and fill it in." >&2
  exit 1
fi

"$PROJECT_DIR/.venv/bin/python3" -m news_agent.main
