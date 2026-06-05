"""Drzewo decyzji routingu — explain API i dopasowanie tras."""

from __future__ import annotations

import pytest

from app import routing_trace


@pytest.mark.asyncio
async def test_explain_file_list_usera_selects_orient(monkeypatch):
    monkeypatch.setenv("PROMPT_ROUTER_MODE", "rules")
    tree = await routing_trace.explain_pipeline(
        "lista plikow usera",
        chat_mode="discuss",
        use_rag=True,
    )
    orient = next(s for s in tree["steps"] if s["step"] == "nlp2dsl_orient")
    assert orient["status"] == "selected"
    assert tree["final_route"] == "nlp2cmd_shell"
    assert tree["selected_step"] == "nlp2dsl_orient"
    rules = next(s for s in tree["steps"] if s["step"] == "rules")
    assert rules["status"] == "skipped"
    assert tree["matched_expectations"]
    assert tree["matched_expectations"][0]["id"] == "shell_host_user_files"


@pytest.mark.asyncio
async def test_explain_disk_space_orient_first():
    tree = await routing_trace.explain_pipeline(
        "sprawdz miejsce na dysku",
        chat_mode="discuss",
        use_rag=True,
    )
    orient = next(s for s in tree["steps"] if s["step"] == "nlp2dsl_orient")
    assert orient["status"] == "selected"
    aligned = routing_trace.align_tree_to_route(
        tree, "nlp2cmd_shell", ingress_step="nlp2dsl_orient"
    )
    assert aligned["selected_step"] == "nlp2dsl_orient"


@pytest.mark.asyncio
async def test_align_registry_file_list_route():
    tree = await routing_trace.explain_pipeline("lista plikow usera z rejestru")
    aligned = routing_trace.align_tree_to_route(
        tree, "mullm_file_list", ingress_step="nlp2dsl_orient"
    )
    assert aligned["selected_step"] == "nlp2dsl_orient"
    orient = next(s for s in aligned["steps"] if s["step"] == "nlp2dsl_orient")
    assert orient["status"] == "selected"
