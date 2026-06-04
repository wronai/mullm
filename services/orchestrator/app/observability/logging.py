from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from app.observability.context import (
    get_chat_session_id,
    get_correlation_id,
    get_retrieval_trace_id,
)

logger = logging.getLogger("mullm.observability")


def log_event(
    *,
    severity: str,
    component: str,
    message: str,
    error_code: str | None = None,
    **fields: Any,
) -> None:
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "severity": severity,
        "service": "orchestrator",
        "component": component,
        "message": message,
        "correlation_id": get_correlation_id(),
        "retrieval_trace_id": get_retrieval_trace_id(),
        "chat_session_id": get_chat_session_id(),
        "error_code": error_code,
        **fields,
    }
    line = json.dumps(payload, default=str)
    if severity in {"error", "critical"}:
        logger.error(line)
    elif severity == "warning":
        logger.warning(line)
    else:
        logger.info(line)
