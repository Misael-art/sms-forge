"""Selected PSG generation must preserve unrelated project audio and provenance."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]
GENERATOR = ROOT / "tools/sms_wrapper/make_psg_assets.py"
pytestmark = pytest.mark.rev2


def test_selected_psg_regeneration_preserves_other_assets_and_manifest(tmp_path):
    project = tmp_path / "fixture"
    (project / "doc").mkdir(parents=True)
    (project / "res/audio").mkdir(parents=True)
    (project / "inc").mkdir()
    untouched = project / "res/audio/sfx_hurt.psg"
    untouched.write_bytes(b"existing unrelated stream")
    existing = {"file": "res/audio/sfx_hurt.psg", "role": "existing",
                "sha256": hashlib.sha256(untouched.read_bytes()).hexdigest(),
                "bytes": len(untouched.read_bytes())}
    manifest = project / "doc/audio_provenance_manifest.json"
    manifest.write_text(json.dumps({"assets": [existing]}), encoding="utf-8")
    command = [sys.executable, str(GENERATOR), "--project", str(project),
               "--only", "sfx_hit", "--role", "sfx_hit=diagnostic hit"]

    for _ in range(2):
        result = subprocess.run(command, capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        entries = json.loads(manifest.read_text(encoding="utf-8"))["assets"]
        assert entries[0] == existing
        assert len(entries) == 2 and entries[1]["role"] == "diagnostic hit"
        blob = (project / "res/audio/sfx_hit.psg").read_bytes()
        assert entries[1]["sha256"] == hashlib.sha256(blob).hexdigest()
        assert entries[1]["channels"] == "SFX_CHANNELS2AND3"
        assert untouched.read_bytes() == b"existing unrelated stream"
        assert not (project / "res/audio/music_battle.psg").exists()
        if _ == 0:
            first = (manifest.read_bytes(), blob, (project / "inc/sfx_hit.h").read_bytes())
        else:
            assert first == (manifest.read_bytes(), blob, (project / "inc/sfx_hit.h").read_bytes())

    before = manifest.read_bytes()
    bad = subprocess.run(command + ["--role", "sfx_hurt=not selected"],
                         capture_output=True, text=True)
    assert bad.returncode != 0 and manifest.read_bytes() == before
