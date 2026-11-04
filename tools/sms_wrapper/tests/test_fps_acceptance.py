"""Owner floor58: raw ROM windows and final axis, not emulator title or mean."""
import hashlib
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from measure_runtime_probe import target_fps_verdict, runtime_fps_verdict
from reconcile_claims import axis_support


def metrics(rates):
    return {"region": "NTSC", "fps_janelas": rates,
            "fps_measured": rates[0], "fps_constante": True,
            "frame_advance_proved": True, "frames_delta_total": 960}


@pytest.mark.parametrize("rates,expected", [
    ([58.0, 58.0], True), ([58.0, 60.0], True),
    ([59.67, 59.81], True), ([60.0, 60.0], True),
    ([57.999999, 59.0], False), ([57.0, 61.0], False),
    ([60.0, 62.0], False), ([True, 60.0], False),
    ([float("nan"), 60.0], False), ([float("inf"), 60.0], False),
    ([60.0], False), ([], False),
])
def test_owner_window_boundaries(rates, expected):
    assert target_fps_verdict(rates, "NTSC")["passed"] is expected


def test_pal_region_diagnostic_does_not_pay_60_target():
    result = target_fps_verdict([50.0, 50.0], "PAL")
    assert result["regional_diagnostic_passed"]
    assert not result["passed"]


@pytest.mark.parametrize("change", [
    {"fps_janelas": [57.999999, 60.0]},
    {"fps_measured": 57.999999}, {"fps_constante": False},
    {"frame_advance_proved": False}, {"frames_delta_total": 0},
])
def test_raw_or_stopped_execution_cannot_inherit_positive_axis(change):
    doc = metrics([60.0, 60.0])
    doc.update(change)
    assert not runtime_fps_verdict(doc)["passed"]


def test_reconciliation_binds_rates_and_current_rom(tmp_path, monkeypatch):
    rom_dir = tmp_path / "out/rom"
    evidence = tmp_path / "out/evidence"
    rom_dir.mkdir(parents=True)
    evidence.mkdir()
    raw = b"synthetic ROM identity only, not emulator evidence"
    (rom_dir / "test.sms").write_bytes(raw)
    sha = hashlib.sha256(raw).hexdigest()
    (tmp_path / ".mddev").mkdir()
    (tmp_path / ".mddev/project.json").write_text(json.dumps({"name": "test"}))
    (tmp_path / "out/build_record.json").write_text(json.dumps({"rom_sha256": sha}))
    from session_bridge import isolated
    sid = "f" * 32
    sessions = tmp_path / "sessions"
    session = sessions / sid
    (session / "emulator").mkdir(parents=True)
    (session / "emulator/rom.sms").write_bytes(raw)
    (session / "session.json").write_text(json.dumps({"session_id": sid, "root": str(session),
                                                     "rom_sha256": sha, "created_at": 0}))
    monkeypatch.setattr(isolated, "DEFAULT_ROOT", sessions)
    path = evidence / "fps.json"
    for rates, digest, expected in [([58.0, 60.0], sha, True),
                                    ([57.999999, 59.0], sha, False),
                                    ([60.0, 60.0], "other-ROM", False)]:
        path.write_text(json.dumps(dict(metrics(rates), rom_sha256=digest, session_id=sid)))
        assert axis_support(str(tmp_path))["fps_constante"][0] is expected
    path.write_text(json.dumps({"constante_50_60": True, "rom_sha256": sha}))
    assert not axis_support(str(tmp_path))["fps_constante"][0]
