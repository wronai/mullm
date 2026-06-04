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
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            tasks = (await client.get(f"{PROJECTOR_URL}/projections/tasks")).json().get("items", [])
        except httpx.HTTPError:
            pass
        try:
            feed = (await client.get(f"{PROJECTOR_URL}/projections/feed", params={"limit": 20})).json().get(
                "items", []
            )
        except httpx.HTTPError:
            pass
        try:
            agents = (await client.get(f"{PROJECTOR_URL}/projections/agents")).json().get("items", [])
        except httpx.HTTPError:
            pass
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {"tasks": tasks, "feed": feed, "agents": agents},
    )
