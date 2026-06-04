from __future__ import annotations

import os

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api_routes import router as api_router

ORCHESTRATOR_URL = os.getenv(
    "ORCHESTRATOR_URL",
    os.getenv("MULLM_ORCHESTRATOR_URL", "http://orchestrator:8000"),
)
PROJECTOR_URL = os.getenv(
    "PROJECTOR_URL",
    os.getenv("MULLM_PROJECTOR_URL", "http://projector:8000"),
)

app = FastAPI(title="mullm-web")
app.include_router(api_router, prefix="/api")
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))


@app.get("/health")
async def health():
    return {"status": "ok", "service": "mullm-web"}


@app.get("/", response_class=HTMLResponse)
async def workspace(request: Request):
    return templates.TemplateResponse(
        "workspace.html",
        {"request": request},
    )


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    tasks: list = []
    feed: list = []
    agents: list = []
    approvals: list = []
    plugins: list = []
    resources: list = []
    rag_documents: list = []
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
        resources = await _fetch("/projections/resources")
        rag_documents = await _fetch("/projections/rag/documents")
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "tasks": tasks,
            "feed": feed,
            "agents": agents,
            "approvals": approvals,
            "plugins": plugins,
            "resources": resources,
            "rag_documents": rag_documents,
        },
    )
