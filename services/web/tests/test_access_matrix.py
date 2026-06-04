import tempfile
from pathlib import Path

import pytest

from app import access_matrix as am


@pytest.fixture
def matrix_file(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "matrices.yaml"
        monkeypatch.setenv("MULLM_ACCESS_MATRIX_PATH", str(path))
        yield path


def test_default_all_checked(matrix_file):
    state = am.default_state()
    assert state["default_all"] is True
    rid = state["resources"][0]["id"]
    aid = state["agents"][0]["id"]
    assert state["agent_resource"][rid][aid] is True


def test_save_and_deny(matrix_file):
    state = am.default_state()
    rid = "filesystem:user"
    state["agent_resource"][rid]["shell_agent"] = False
    am.save_state(state)
    assert am.agent_may_access_resource("shell_agent", rid) is False
    assert am.agent_may_access_resource("files_agent", rid) is True


def test_diagnose_file_list_no_shell():
    d = am.diagnose_file_list_command()
    assert d["uses_shell_agent"] is False
    assert "projector" in d["data_sources"][0]
