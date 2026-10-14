"""Host tests for the product runtime's CMD-v3/v4 ring and per-slot tier state."""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]
PROJECT = ROOT / "SMS_projects/luta_mugen"
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from mugen2sms.converters import sms_cmd  # noqa: E402
from mugen2sms.converters.sms_controls import ControlMap  # noqa: E402
from mugen2sms.parsers import cmd as cmdmod  # noqa: E402

pytestmark = pytest.mark.skipif(shutil.which("gcc") is None, reason="gcc ausente")

K1, K2 = 0x10, 0x20
PATTERNS = ("LP", "HP", "LK", "HK", "QCF_LP", "FF", "OLD", "TIER3",
            "HOLD", "RELEASE", "FLEX_D", "FLEX_F", "HOLD_FLEX_F",
            "BAD_FLAGS", "BAD_WANT", "RISING", "RISING_TERRY_Y",
            "RISING_TERRY_X255", "LEGACY_V3", "RISING_EXACT")
COMMANDS = {"LP": "x", "HP": "z", "LK": "a", "HK": "c",
            "QCF_LP": "D, DF, F, x", "FF": "F, F",
            "FLEX_D": "$D", "FLEX_F": "$F", "HOLD_FLEX_F": "/$F",
            "RISING": "~15$D, U, x", "RISING_EXACT": "~15D, U, x"}
CONTROLS = ControlMap({"1": ["x", "z"], "2": ["a", "c"]},
                      {"1": [6], "2": [6]})


def _blobs() -> dict[str, bytes]:
    commands = []
    for name, text in COMMANDS.items():
        steps, errors = cmdmod.parse_command_string(text)
        commands.append(cmdmod.Command(name, steps, 15, 1, 1, text, errors))
    patterns, skipped = sms_cmd.to_patterns(commands, CONTROLS)
    assert skipped == {}, skipped
    result = {p.name.upper(): sms_cmd.serialize_pattern(p) for p in patterns}
    result["OLD"] = bytes([1, 1, 15, 1, 0x10, 0x00])
    result["LEGACY_V3"] = bytes([3, 1, 15, 1, 0x10, 0x00])
    result["TIER3"] = bytes([sms_cmd.BLOB_FMT_VERSION, 1, 15, 1, 0x10, 0x0C, 0])
    result["HOLD"] = bytes([sms_cmd.BLOB_FMT_VERSION, 1, 1, 1, 0x10, 0x01, 0])
    result["RELEASE"] = bytes([sms_cmd.BLOB_FMT_VERSION, 1, 1, 1, 0x10, 0x02, 0])
    result["BAD_FLAGS"] = bytes([sms_cmd.BLOB_FMT_VERSION, 1, 15, 1, 0x10, 0x20, 0])
    result["BAD_WANT"] = bytes([sms_cmd.BLOB_FMT_VERSION, 1, 15, 1, 0x40, 0x00, 0])
    terry_controls = ControlMap({"1": ["x", "y"], "2": ["a", "b"]},
                                {"1": [6], "2": [6]})
    command_steps, errors = cmdmod.parse_command_string("~15$D, U, y")
    command = cmdmod.Command("RISING_TERRY_Y", command_steps, 10, 1, 1,
                             "~15$D, U, y", errors)
    strong_patterns, skipped = sms_cmd.to_patterns([command], terry_controls)
    assert skipped == {}, skipped
    result["RISING_TERRY_Y"] = sms_cmd.serialize_pattern(strong_patterns[0])
    command_steps, errors = cmdmod.parse_command_string("~255$D, U, x")
    command = cmdmod.Command("RISING_TERRY_X255", command_steps, 10, 1, 1,
                             "~255$D, U, x", errors)
    max_patterns, skipped = sms_cmd.to_patterns([command], terry_controls)
    assert skipped == {}, skipped
    result["RISING_TERRY_X255"] = sms_cmd.serialize_pattern(max_patterns[0])
    return result


def _build(tmp_path: Path) -> Path:
    blobs = _blobs()
    lines = ["#include <stdio.h>", '#include "input.h"',
             "static const unsigned char *patterns[] = {"]
    for name in PATTERNS:
        data = blobs[name]
        lines.append("(const unsigned char[]){" +
                     ",".join(str(value) for value in data) + "},")
    lines += ["};", "int main(void) {", "char op; unsigned s,a,b; input_init();",
              "while (scanf(\" %c\", &op) == 1) {",
              "if(op=='t'){ if(scanf(\"%u%u%u\",&s,&a,&b)!=3)return 2; input_tick(s,a,b); }",
              "else if(op=='q'){ if(scanf(\"%u%u\",&s,&a)!=2)return 2; printf(\"%u\\n\",input_pattern_hit(s,patterns[a])); }",
              "else if(op=='d'){ if(scanf(\"%u\",&s)!=1)return 2; printf(\"%u\\n\",input_take_command_dirty(s)); }",
              "else if(op=='s'){ if(scanf(\"%u%u%u\",&s,&a,&b)!=3)return 2; input_set_thresholds(s,a,b); }",
              "else return 3; } return 0; }"]
    harness = tmp_path / "input_harness.c"
    harness.write_text("\n".join(lines) + "\n", encoding="ascii")
    exe = tmp_path / "input_harness"
    result = subprocess.run(["gcc", "-Wall", "-Werror", "-std=c99",
                             "-I", str(PROJECT / "inc"), str(harness),
                             str(PROJECT / "src/input.c"),
                             str(PROJECT / "src/input_tier.c"), "-o", str(exe)],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    return exe


def _run(exe: Path, lines: list[str]) -> list[int]:
    result = subprocess.run([str(exe)], input="\n".join(lines) + "\n",
                            capture_output=True, text=True, check=True)
    return [int(value) for value in result.stdout.split()]


def _idx(name: str) -> int:
    return PATTERNS.index(name)


def test_root_ring_matches_light_strong_and_other_physical_family(tmp_path):
    exe = _build(tmp_path)
    script = ["t 0 16 0", "q 0 0", "t 0 0 0", "q 0 0", "q 0 1",
              "t 0 16 0", "t 0 16 0", "t 0 16 0", "t 0 16 0",
              "t 0 16 0", "t 0 16 0", "q 0 0", "q 0 1", "t 0 0 0", "q 0 0",
              "t 1 32 0", "t 1 0 0", "q 1 2"]
    assert _run(exe, script) == [0, 1, 0, 0, 1, 0, 1]


def test_root_ring_recognizes_motion_and_facing_relative_direction(tmp_path):
    exe = _build(tmp_path)
    script = ["t 0 2 0", "t 0 10 0", "t 0 8 0", "t 0 24 0",
              "t 0 8 0", "q 0 4", "q 0 0",  # motion and terminal LP pulse
              "t 1 4 1", "t 1 4 1", "q 1 5"]  # left is forward for facing left
    assert _run(exe, script) == [1, 0, 1]


def test_root_ring_matches_four_way_cardinals_with_neighbor_diagonals(tmp_path):
    exe = _build(tmp_path)
    down = []
    for sample in (2, 10, 6):
        down += [f"t 0 {sample} 0", "q 0 10"]
    forward = ["t 0 4 0", "q 0 11"]
    for sample in (8, 9, 10):
        forward += [f"t 0 {sample} 0", "q 0 11"]
    held_forward = []
    for sample in (8, 9, 10):
        held_forward += [f"t 0 {sample} 0", "q 0 12"]
    assert _run(exe, down) == [1, 1, 1]
    assert _run(exe, forward) == [0, 1, 1, 1]
    assert _run(exe, held_forward) == [1, 1, 1]


def test_root_ring_rejects_old_and_unrepresentable_tier_blobs(tmp_path):
    exe = _build(tmp_path)
    script = ["t 0 16 0", "t 0 0 0", "q 0 6", "q 0 7"]
    assert _run(exe, script) == [0, 0]


def test_root_ring_rejects_reserved_cmd_v3_bits(tmp_path):
    exe = _build(tmp_path)
    script = ["t 0 16 0", "t 0 0 0", "q 0 13", "q 0 14"]
    assert _run(exe, script) == [0, 0]


def test_root_ring_uses_independent_slot_thresholds(tmp_path):
    exe = _build(tmp_path)
    script = ["s 0 3 6", "s 1 6 6", "t 0 16 0", "t 0 16 0",
              "t 1 16 0", "t 0 16 0", "q 0 1", "q 1 1",
              "t 0 0 0", "q 0 0"]
    assert _run(exe, script) == [1, 0, 0]


def test_root_ring_applies_hold_and_release_flags_to_current_sample(tmp_path):
    exe = _build(tmp_path)
    script = ["t 0 16 0", "q 0 8", "q 0 9", "t 0 0 0",
              "q 0 8", "q 0 9"]
    assert _run(exe, script) == [1, 0, 0, 1]


def test_root_ring_command_dirty_tracks_normalized_timeline_changes(tmp_path):
    exe = _build(tmp_path)
    script = ["d 0", "t 0 8 0", "d 0", "d 0",
              "t 0 8 0", "d 0", "q 0 5"]
    for _ in range(14):
        script.extend(["t 0 8 0", "d 0"])
    script.extend(["t 0 8 0", "d 0"])
    values = _run(exe, script)
    assert values[:5] == [0, 1, 0, 1, 1]
    assert values[5:-1] == [1] * 14
    assert values[-1] == 0  # wrap substitui um sample pelo mesmo valor


def test_root_ring_live_dispatch_distinguishes_families_and_tiers(tmp_path):
    """Model slot_command's per-frame priority and pulse consumption."""
    exe = _build(tmp_path)
    order = [4, 0, 1, 2, 3]  # special, LP, HP, LK, HK

    def trace(samples):
        script = ["s 0 6 6"]
        for sample in samples:
            script.append(f"t 0 {sample} 0")
            script.extend(f"q 0 {index}" for index in order)
        values = _run(exe, script)
        return [values[i:i + len(order)]
                for i in range(0, len(values), len(order))]

    assert trace([16, 16, 0, 0]) == [
        [0, 0, 0, 0, 0], [0, 0, 0, 0, 0],
        [0, 1, 0, 0, 0], [0, 0, 0, 0, 0],
    ]
    assert trace([16, 16, 16, 16, 16, 16, 0, 0]) == [
        [0, 0, 0, 0, 0], [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0], [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0], [0, 0, 1, 0, 0],
        [0, 0, 0, 0, 0], [0, 0, 0, 0, 0],
    ]
    assert trace([32, 32, 0, 0]) == [
        [0, 0, 0, 0, 0], [0, 0, 0, 0, 0],
        [0, 0, 0, 1, 0], [0, 0, 0, 0, 0],
    ]


def test_root_ring_live_dispatch_prioritizes_qcf_before_weak_button(tmp_path):
    exe = _build(tmp_path)
    script = ["s 0 6 6"]
    for sample in [2, 10, 8, 24, 24, 8, 0, 0]:
        script.append(f"t 0 {sample} 0")
        script.extend(f"q 0 {index}" for index in [4, 0, 1, 2, 3])
    values = _run(exe, script)
    rows = [values[i:i + 5] for i in range(0, len(values), 5)]
    assert rows[5] == [1, 0, 0, 0, 0]


def test_root_ring_matches_timed_four_way_release_after_fifteen_ticks(tmp_path):
    exe = _build(tmp_path)
    short = [f"t 0 {2 | 4} 0" for _ in range(14)]
    for sample in (4, 1, K1, 0):
        short.append(f"t 0 {sample} 0")
    short.append(f"q 0 {_idx('RISING')}")
    assert _run(exe, short) == [0]

    script = [f"t 0 {2 | 4} 0" for _ in range(15)]
    for sample in (4, 1, K1, 0):
        script.append(f"t 0 {sample} 0")
    script.extend([f"q 0 {_idx('RISING')}", f"q 0 {_idx('RISING')}"])
    assert _run(exe, script) == [1, 0]


def test_root_ring_matches_terry_rising_tackle_y_on_strong_release_tier(tmp_path):
    exe = _build(tmp_path)
    script = ["s 0 6 6"] + ["t 0 2 0" for _ in range(15)]
    script.extend(["t 0 0 0", "t 0 1 0"])
    for _ in range(6):
        script.extend(["t 0 16 0", f"q 0 {_idx('RISING_TERRY_Y')}"])
    assert _run(exe, script) == [0, 0, 0, 0, 0, 1]


def test_root_ring_saturates_timed_release_at_uint8_boundary(tmp_path):
    exe = _build(tmp_path)

    def probe(charge_ticks: int) -> list[int]:
        script = ["s 0 6 6"] + ["t 0 2 0" for _ in range(charge_ticks)]
        script.extend(["t 0 0 0", "t 0 1 0", "t 0 16 0", "t 0 0 0",
                       f"q 0 {_idx('RISING_TERRY_X255')}"])
        return _run(exe, script)

    assert probe(254) == [0]
    assert probe(255) == [1]


def test_root_ring_keeps_legacy_v3_blob_readable(tmp_path):
    exe = _build(tmp_path)
    assert _run(exe, ["t 0 16 0", "t 0 0 0",
                      f"q 0 {_idx('LEGACY_V3')}"]) == [1]


def test_root_ring_requires_pure_cardinal_for_timed_release_without_dollar(tmp_path):
    exe = _build(tmp_path)
    script = [f"t 0 {2 | 4} 0" for _ in range(15)]
    for sample in (4, 1, K1, 0):
        script.append(f"t 0 {sample} 0")
    script.append(f"q 0 {_idx('RISING_EXACT')}")
    assert _run(exe, script) == [0]
