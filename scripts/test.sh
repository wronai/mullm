#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [ ! -d .venv-test ]; then
  python3 -m venv .venv-test
fi

.venv-test/bin/pip install -q pytest pytest-asyncio pydantic fastapi starlette httpx

export PYTHONPATH="${ROOT}/services/orchestrator"
.venv-test/bin/pytest tests/ -v "$@"
