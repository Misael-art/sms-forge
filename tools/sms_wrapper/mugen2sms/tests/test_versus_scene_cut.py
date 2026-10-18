"""P1/P2 artifacts remain distinct when both slots use the same character."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PKG_ROOT = Path(__file__).resolve().parents[1]


def test_same_character_mirror_header_namespaces_artifacts_and_pose_refs():
    result = subprocess.run(
        [sys.executable, "-m", "mugen2sms.generators.versus_scene_cut", "--self-check"],
        cwd=PKG_ROOT.parent,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "[PASS] versus scene cut self-check" in result.stdout
