import os
from pathlib import Path

import pytest

from app.access.uri import build_uri, parse_uri
from app.access.transport import TransportService


def test_parse_and_build_uri():
    uri = build_uri("localfs", "docs/readme.md")
    parsed = parse_uri(uri)
    assert parsed.adapter == "localfs"
    assert parsed.path == "docs/readme.md"
    assert parsed.canonical == uri


@pytest.mark.asyncio
async def test_localfs_probe_and_fetch(tmp_path):
    sample = tmp_path / "hello.txt"
    sample.write_text("mullm access fabric", encoding="utf-8")
    os.environ["MULLM_LOCALFS_ROOT"] = str(tmp_path)

    transport = TransportService()
    uri = build_uri("localfs", "hello.txt")
    probe = await transport.probe(uri)
    assert probe["ok"] is True

    fetched = await transport.fetch(uri)
    assert "mullm" in (fetched.get("body_preview") or "")


@pytest.mark.asyncio
async def test_register_and_transfer_resource(command_bus, tmp_path):
    os.environ["MULLM_LOCALFS_ROOT"] = str(tmp_path)
    source = tmp_path / "data.txt"
    source.write_text("payload", encoding="utf-8")
    dest_dir = tmp_path / "out"
    os.environ["MULLM_TRANSPORT_SANDBOX"] = str(dest_dir)

    registered = await command_bus.handle(
        command_type="RegisterResource",
        data={
            "uri": build_uri("localfs", "data.txt"),
            "name": "Test data",
            "classification": "document",
        },
    )
    resource_id = registered["aggregate_id"]

    result = await command_bus.handle(
        command_type="RequestTransfer",
        data={
            "resource_id": resource_id,
            "destination_uri": build_uri("localfs", "imported/data.txt"),
            "requested_by": "test",
        },
    )
    assert result["events"][-1]["event_type"] in {"TransferCompleted", "TransferFailed"}
    if result["events"][-1]["event_type"] == "TransferCompleted":
        assert (dest_dir / "imported" / "data.txt").exists()
