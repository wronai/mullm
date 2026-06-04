"""Smoke: kontrakty intract routingu (opcjonalny subprocess)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

MULLM_ROOT = Path(__file__).resolve().parents[3]
INTRACT_SRC = Path(
    os.environ.get("INTRACT_ROOT", "/home/tom/github/semcod/intract")
) / "src"


@pytest.mark.skipif(
    not (INTRACT_SRC / "intract").is_dir(),
    reason="Intract not found (set INTRACT_ROOT)",
)
def test_intract_validate_routing_contracts() -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(INTRACT_SRC) + (
        f":{env['PYTHONPATH']}" if env.get("PYTHONPATH") else ""
    )
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "intract",
            "validate",
            ".",
            "--manifest",
            "intract.yaml",
        ],
        cwd=MULLM_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    combined = proc.stdout + proc.stderr
    assert "violation" not in combined.lower() or "Status: pass" in combined
