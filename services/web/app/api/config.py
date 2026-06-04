from __future__ import annotations

import os

from app import chat as chat_service

ORCHESTRATOR_URL = os.getenv(
    "ORCHESTRATOR_URL",
    os.getenv("MULLM_ORCHESTRATOR_URL", "http://orchestrator:8000"),
)
PROJECTOR_URL = os.getenv(
    "PROJECTOR_URL",
    os.getenv("MULLM_PROJECTOR_URL", "http://projector:8000"),
)

chat_service.ORCHESTRATOR_URL = ORCHESTRATOR_URL
