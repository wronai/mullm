from __future__ import annotations

import os

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

ORCHESTRATOR_URL = os.getenv("ORCHESTRATOR_URL", "http://orchestrator:8000")
PROJECTOR_URL = os.getenv("PROJECTOR_URL", "http://projector:8000")

app = FastAPI(title="mullm-web")
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))


@app.get("/health")
async def health():
    return {"status": "ok", "service": "mullm-web"}


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    tasks: list = []
    feed: list = []
    agents: list = []
    approvals: list = []
    plugins: list = []
    async with httpx.AsyncClient(timeout=5.0) as client:
        async def _fetch(path: str, *, limit: int | None = None) -> list:
            try:
                params = {"limit": limit} if limit else None
                return (await client.get(f"{PROJECTOR_URL}{path}", params=params)).json().get(
                    "items", []
                )
            except httpx.HTTPError:
                return []

        tasks = await _fetch("/projections/tasks")
        feed = await _fetch("/projections/feed", limit=20)
        agents = await _fetch("/projections/agents")
        approvals = await _fetch("/projections/approvals")
        plugins = await _fetch("/projections/plugins")
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "tasks": tasks,
            "feed": feed,
            "agents": agents,
            "approvals": approvals,
            "plugins": plugins,
        },
    )
