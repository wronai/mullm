from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.observability.context import new_correlation_id, observability_context


class CorrelationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        cid = (
            request.headers.get("x-correlation-id")
            or request.headers.get("X-Correlation-ID")
            or new_correlation_id()
        )
        with observability_context(correlation_id=cid):
            response = await call_next(request)
            response.headers["X-Correlation-ID"] = cid
            return response
