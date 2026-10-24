"""Regressao das quatro ferramentas de medicao propostas no fechamento PB-13–PB-18.

Os testes de projeto usam o corte `pose_budget_pair_20261023` como fixture
historica. Eles nao promovem os numeros a lei: apenas impedem que a ferramenta
canonica derive do artefato que ja foi medido.
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).resolve().parent
TOOLS_DIR = TESTS_DIR.parents[1]          # .../tools/sms_wrapper
WORKSPACE = TESTS_DIR.parents[3]          # .../SMSForge
_fixture = os.environ.get("SMSFORGE_REV2_FIXTURE_ROOT")
REV2 = Path(_fixture).resolve() if _fixture else WORKSPACE / "SMS_projects" / "luta_mugem_rev2"
if _fixture and not REV2.is_dir():
    raise ValueError("SMSFORGE_REV2_FIXTURE_ROOT must name an existing restored project")
CUT = REV2 / "out" / "generated" / "pose_budget_pair_20261023"
HEADER = CUT / "versus_scene_runtime.h"
POSE_ROOT = REV2 / "out" / "display_fit" / "pose_budget_8"


def load_tool(name: str):
    module_name = "smsforge_tool_" + name
    if module_name in sys.modules:
        return sys.modules[module_name]
    if str(TOOLS_DIR) not in sys.path:
        sys.path.insert(0, str(TOOLS_DIR))
    spec = importlib.util.spec_from_file_location(module_name, TOOLS_DIR / f"{name}.py")
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("script", [
    "audit_composition_gate.py",
    "audit_sole_alignment.py",
    "audit_sprite_line_sim.py",
    "measure_worst_frame.py",
])
def test_tool_self_checks(script):
    result = subprocess.run(
        [sys.executable, str(TOOLS_DIR / script), "--self-check"],
        cwd=TOOLS_DIR,
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "SELF-CHECK OK" in result.stdout + result.stderr


@pytest.mark.rev2
def test_composition_gate_reproduces_pose_budget_cut():
    if not HEADER.is_file():
        pytest.skip("pose_budget_pair cut ausente")
    gate = load_tool("audit_composition_gate")
    result, generated = gate.build_gate(
        HEADER.read_text(encoding="ascii"),
        source_label=str(HEADER),
        anim_count=12,
    )
    assert result["dropped_pose_count"] == 25
    assert result["dropped_pose_total"] == 93
    assert result["dropped_anim_by_side"] == {
        "p1": [6, 7, 8, 9],
        "p2": [6, 7, 8, 9, 10, 11],
    }
    assert result["max_cells_by_side"] == {
        "p1": [4, 4, 4, 4, 4, 4, 5, 6, 6, 6, 4, 4],
        "p2": [4, 4, 4, 4, 4, 4, 6, 7, 6, 6, 6, 8],
    }
    assert "VERSUS_COMPOSITION_IDLE_COLUMNS 4u" in generated
    assert "VERSUS_ANIM_LEGAL" in generated


@pytest.mark.rev2
def test_sole_alignment_reproduces_four_reference_frames():
    if not HEADER.is_file() or not (POSE_ROOT / "ryu").is_dir():
        pytest.skip("corte ou display_fit ausente")
    sole = load_tool("audit_sole_alignment")
    result = sole.measure_text(
        HEADER.read_text(encoding="ascii"),
        source_label=str(HEADER),
        pose_dirs={"p1": POSE_ROOT / "ryu", "p2": POSE_ROOT / "ken"},
        symbols=[
            "P1_RYU_A0F0",
            "P1_RYU_A260F0",
            "P2_KEN8_A0F0",
            "P2_KEN8_A250F0",
        ],
        require_hurt=True,
    )
    measured = {
        frame["symbol"]: (
            frame["sole_offset"],
            frame["hurt_bottom"],
            frame["hurt_minus_sole"],
        )
        for frame in result["frames"]
    }
    assert measured == {
        "P1_RYU_A0F0": (0, 1, 1),
        "P1_RYU_A260F0": (3, 0, -3),
        "P2_KEN8_A0F0": (0, -1, -1),
        "P2_KEN8_A250F0": (3, 1, -2),
    }
    assert result["summary"]["max_abs_delta"] == 3


def test_worst_frame_schema_separates_snapshot_from_sealed_min():
    worst = load_tool("measure_worst_frame")
    result = worst.analyze_snapshot(4, 1740, 1, 4079, 45.0)
    assert result["verdicto"] == "derramou"
    assert result["vline_min"] == 4
    assert result["sealed_field"] == "vline_min"
    assert result["vline_kind"] == "sealed_min"
    assert result["schema"] == "smsforge.worst_frame/v2"

    sample = worst.snapshot_sample(144, 4, 1740, 2, "ROUND", 4079, 1)
    assert sample["vline"] == 144
    assert sample["vline_kind"] == "snapshot"
    assert sample["vline_min"] == 4
    assert sample["vline_sealed_min"] == 4


def test_sprite_line_sim_rejects_self_duel_only_on_request():
    sim = load_tool("audit_sprite_line_sim")
    base = {"sprite_size": "8x16", "screen_h": 192, "sprites": []}
    distinct = dict(base, composition=[
        {"side": "p1", "fighter": "Ryu"},
        {"side": "p2", "fighter": "Ken"},
    ])
    same = dict(base, composition=[
        {"side": "p1", "fighter": "Ryu"},
        {"side": "p2", "fighter": "RYU"},
    ])
    assert not sim.simulate(distinct, require_distinct_fighters=True)["violations"]
    assert any("mesmo lutador" in v for v in sim.simulate(
        same, require_distinct_fighters=True)["violations"])
    # Sem opt-in, um espelho tecnico continua sendo um manifesto valido.
    assert not sim.simulate(same)["violations"]
    assert any("exatamente 2" in v for v in sim.simulate(
        dict(base, composition=[]), require_distinct_fighters=True)["violations"])


def test_composition_counts_overlapping_vertical_intervals():
    gate = load_tool("audit_composition_gate")
    assert gate.peak_scanline([(0, 0, 0)] * 3 + [(8, 8, 0)] * 3) == 6
    assert gate.peak_scanline([(0, -8, 0)] * 3 + [(8, 0, 0)] * 3) == 6
    assert gate.peak_scanline([(0, 0, 0)] * 3 + [(8, 16, 0)] * 3) == 3
    text = gate.SYNTHETIC_HEADER.replace(
        "0x10, 0x00,", "0x10, 0x08,", 1)
    result, _ = gate.build_gate(text, source_label="fixture")
    assert result["max_cells_by_side"]["p2"][0] == 5


@pytest.mark.parametrize("value", ["-1", "256", "1 << 3", "0+1"])
def test_composition_refuses_nonbyte_initializers(value):
    gate = load_tool("audit_composition_gate")
    with pytest.raises(gate.GateError):
        gate.parse_arrays(f"const unsigned char M[1] = {{ {value} }};")


def test_composition_uses_signed_dy_and_rejects_other_payloads():
    gate = load_tool("audit_composition_gate")
    assert gate.cells("M", {"M": bytes([0, 248, 0, 128])}, {}) == [(0, -8, 0)]
    with pytest.raises(gate.GateError, match="early"):
        gate.cells("M", {"M": bytes([128, 0, 0, 128])}, {})
    with pytest.raises(gate.GateError, match="field"):
        gate.build_gate(gate.SYNTHETIC_HEADER, source_label="fixture", p2_field="clsn")


def test_candidate_outputs_preserve_existing_files_and_aliases(tmp_path):
    gate = load_tool("audit_composition_gate")
    source = tmp_path / "source.h"
    source.write_text("preserve")
    for kind in ("source", "symlink", "hardlink"):
        target = source if kind == "source" else tmp_path / kind
        if kind == "symlink":
            target.symlink_to(source)
        elif kind == "hardlink":
            target.hardlink_to(source)
        fresh = tmp_path / (kind + ".json")
        with pytest.raises(FileExistsError):
            gate.publish_outputs(target, fresh, "new", {})
        assert source.read_text() == "preserve"
        assert not fresh.exists()
    with pytest.raises(OSError):
        gate.publish_outputs(tmp_path / "same", tmp_path / "same", "new", {})
    gate.publish_outputs(tmp_path / "new.h", tmp_path / "new.json", "new", {"ok": True})
    assert json.loads((tmp_path / "new.json").read_text()) == {"ok": True}


def test_sole_decodes_alpha_values_by_palette_index():
    import struct
    sole = load_tool("audit_sole_alignment")
    def png_alpha(values):
        return b"\x89PNG\r\n\x1a\n" + struct.pack(">I", len(values)) + b"tRNS" + bytes(values) + b"\0" * 4
    assert sole.transparent_indices(png_alpha([0, 0, 255])) == {0, 1}
    assert sole.bottom_opaque_row([[0, 1], [0, 255]], {0, 1}) == 1
    with pytest.raises(sole.SoleError, match="partial"):
        sole.transparent_indices(png_alpha([0, 127, 255]))
    with pytest.raises(sole.SoleError, match="index 0"):
        sole.transparent_indices(png_alpha([255, 0]))
