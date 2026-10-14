from __future__ import annotations

import json
from pathlib import Path

import pytest

from mugen2sms.analysis.control_adapter import load_trigger, resolve_trigger

ROOT = Path(__file__).resolve().parents[4]
PROFILE = ROOT / "SMS_projects/luta_mugen/out/local_study/lote0_20261004/control_profile_ffspRyo_20261005.json"
RYO_SHA = "7272abcf787c0946fd388be84010b720579be5d301590b0eec8e7f22f0f32133"


def test_ryo_z_resolves_to_physical_button1_and_six_frame_hold():
    profile = json.loads(PROFILE.read_text())
    trigger = resolve_trigger(profile, RYO_SHA, "z")
    assert trigger["physical_button"] == 1
    assert trigger["activation"] == "hold"
    assert trigger["threshold_frames"] == 6


def test_ryo_quick_punch_releases_on_button1_and_kick_uses_button2():
    profile = json.loads(PROFILE.read_text())
    quick = resolve_trigger(profile, RYO_SHA, "x")
    kick = resolve_trigger(profile, RYO_SHA, "c")
    assert (quick["physical_button"], quick["activation"]) == (1, "release")
    assert (kick["physical_button"], kick["activation"]) == (2, "hold")


@pytest.mark.parametrize(
    ("profile_change", "source_sha", "command"),
    [
        ({}, "b" * 64, "z"),
        ({"dropped": ["z"]}, RYO_SHA, "z"),
        ({"families": {"1": ["z", "x"], "2": ["z", "c"]}}, RYO_SHA, "z"),
        ({"families": {"1": ["z"], "2": ["a", "c"]}}, RYO_SHA, "z"),
        ({"thresholds": {"1": [0], "2": [6]}}, RYO_SHA, "z"),
    ],
)
def test_unsupported_or_unbound_profile_fails_closed(profile_change, source_sha, command):
    profile = json.loads(PROFILE.read_text())
    profile.update(profile_change)
    with pytest.raises(ValueError):
        resolve_trigger(profile, source_sha, command)


def test_loader_binds_control_profile_file_hash_and_package_hash():
    trigger = load_trigger(PROFILE, RYO_SHA, "z")
    assert trigger["profile_path"] == str(PROFILE.resolve())
    assert len(trigger["profile_sha256"]) == 64
    with pytest.raises(ValueError, match="source SHA"):
        load_trigger(PROFILE, "0" * 64, "z")
