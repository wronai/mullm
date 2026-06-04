from pathlib import Path

import pytest

from app.evolution.catalog import ArchitectureCatalog
from app.evolution.policy_engine import PolicyEngine, PolicyViolation


@pytest.fixture
def catalog():
    root = Path(__file__).resolve().parents[1] / "catalog"
    return ArchitectureCatalog(root)


def test_catalog_loads_events(catalog):
    events = catalog.list_events()
    types = {e["type"] for e in events}
    assert "TaskCreated" in types
    assert "WorkflowVersionShadowed" in types
    assert "ChangeProposed" in types


def test_catalog_graph(catalog):
    graph = catalog.as_graph()
    assert "domains" in graph
    assert "ActivatePlugin" in graph["policy_rules"]


def test_policy_requires_plugin_manifest(catalog):
    engine = PolicyEngine(catalog)
    with pytest.raises(PolicyViolation):
        engine.validate_command(
            "ProposePlugin",
            {"plugin_id": "x", "version": "1.0.0", "capabilities": [], "manifest": {}},
        )


def test_policy_accepts_full_manifest(catalog):
    engine = PolicyEngine(catalog)
    engine.validate_command(
        "ProposePlugin",
        {
            "plugin_id": "x",
            "version": "1.0.0",
            "manifest": {
                "risk_level": "low",
                "inputs": {},
                "outputs": {},
                "health_check": "/health",
                "rollback_strategy": "disable",
            },
        },
    )


@pytest.mark.asyncio
async def test_shadow_workflow(command_bus):
    await command_bus.handle(
        command_type="ProposeWorkflowVersion",
        data={
            "workflow_id": "wf-shadow",
            "version": 2,
            "definition": {"steps": ["a"]},
        },
    )
    await command_bus.handle(
        command_type="ValidateWorkflowVersion",
        data={"workflow_id": "wf-shadow"},
    )
    result = await command_bus.handle(
        command_type="ShadowWorkflowVersion",
        data={"workflow_id": "wf-shadow", "traffic_percent": 15},
    )
    assert result["events"][-1]["event_type"] == "WorkflowVersionShadowed"
    assert "experiment_id" in result


@pytest.mark.asyncio
async def test_propose_change(command_bus):
    result = await command_bus.handle(
        command_type="ProposeChange",
        data={
            "change_type": "workflow",
            "target_id": "wf-1",
            "hypothesis": "Reduce retries",
            "proposed_by": "evolution-agent",
        },
    )
    assert result["events"][0]["event_type"] == "ChangeProposed"
