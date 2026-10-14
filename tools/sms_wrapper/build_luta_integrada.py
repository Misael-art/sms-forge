#!/usr/bin/env python3
"""Build the luta_mugen 72–88 integrated study.

Hand-written sources and headers live in SMS_projects/luta_mugen/integrada/
(tracked). Build generators and orchestration live in tools/sms_wrapper/.
Tile banks, the scene header and the ROM stay in out/local_study/luta_integrada/
because they are derived from restricted character data and are gitignored.
This recipe copies tracked sources into that tree, regenerates metadata,
builds via build_inner.py, then checks RAM layout and banks read by the runtime.

  python3 tools/sms_wrapper/build_luta_integrada.py [--check-only]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / "SMS_projects" / "luta_mugen"
CANON = PROJECT / "integrada"
STUDY = ROOT / "SMS_projects" / "luta_mugen" / "out" / "local_study" / "luta_integrada"
WRAPPER = ROOT / "tools" / "sms_wrapper"
HAND_HEADERS = ("fight.h", "input.h", "input_pad.h", "input_tier.h",
                "cpu_controller.h", "body.h",
                "luta.h", "stream.h", "stage.h", "hud.h", "audio.h",
                "trace_hooks.h")
BINDING = PROJECT / "doc" / "rom_asset_binding.json"
CUT_CONFIGS = (PROJECT / "data" / "ken_scale_pilot_80px.json",
               PROJECT / "data" / "ryu_scale_pilot_80px.json")


def run(cmd: list[str], cwd: Path | None = None) -> None:
    print("+", " ".join(cmd))
    r = subprocess.run(cmd, cwd=cwd)
    if r.returncode != 0:
        raise SystemExit(r.returncode)


def sync() -> None:
    if not (CANON / "src").is_dir():
        raise SystemExit(f"[FAIL] fontes canonicas ausentes: {CANON}")
    if not (STUDY / "inc" / "versus_scene_runtime_full_generated.h").is_file():
        raise SystemExit(f"[FAIL] header de cena ausente em {STUDY}/inc "
                         "(dado derivado local, nao versionado)")
    for src in sorted((CANON / "src").glob("*.c")):
        shutil.copy2(src, STUDY / "src" / src.name)
    for name in HAND_HEADERS:
        shutil.copy2(CANON / "inc" / name, STUDY / "inc" / name)
    tool_dst = STUDY / "tools"
    tool_dst.mkdir(parents=True, exist_ok=True)
    for src in sorted((CANON / "tools").glob("*.py")):
        shutil.copy2(src, tool_dst / src.name)
    shutil.copy2(CANON / ".mddev" / "project.json", STUDY / ".mddev" / "project.json")


def generate_assets() -> None:
    py = sys.executable
    inc = STUDY / "inc"
    run([py, str(WRAPPER / "luta_mugen_gen_stage_hud.py"),
         "--project", str(PROJECT),
         "--out-dir", str(inc), "--check-planta"])
    run([py, str(WRAPPER / "luta_mugen_gen_psg_blobs.py"),
         "--project", str(PROJECT),
         "--out", str(inc / "psg_blobs.h")])


def cmd_sources() -> tuple[Path, Path]:
    """As duas fontes MUGEN declaradas pelo manifesto de binding, com hash conferido.

    A receita nao conhece caminho de acervo: quem declara a fonte e
    `doc/rom_asset_binding.json`, e o sha256 e verificado antes de gerar
    qualquer padrao. Fonte ausente ou divergente falha fechado.
    """
    if not BINDING.is_file():
        raise SystemExit(f"[FAIL] manifesto de binding ausente: {BINDING}")
    binding = json.loads(BINDING.read_text())
    expected = binding["source_sha256"]
    if sorted(expected) != ["p1_ken", "p2_ryu"]:
        raise SystemExit(f"[FAIL] binding nao declara as duas fontes do corte: "
                         f"{sorted(expected)}")
    src = []
    for key in sorted(expected):
        path = next((e["source"] for e in binding["entries"]
                     if e["source_sha256"] == expected[key]), None)
        if path is None:
            raise SystemExit(f"[FAIL] binding sem entrada para a fonte {key}")
        p = Path(path)
        if not p.is_file():
            raise SystemExit(f"[FAIL] fonte {key} ausente: {p}")
        got = hashlib.sha256(p.read_bytes()).hexdigest()
        if got != expected[key]:
            raise SystemExit(f"[FAIL] sha256 divergente em {key}: {got[:12]} != "
                             f"{expected[key][:12]}")
        src.append(p)
    return src[0], src[1]


def generate_cmds() -> None:
    """Os oito padroes de golpe que o anel le, gerados da fonte MUGEN real.

    Nao toca a arte: o header de cena congelado continua a unica origem de
    tiles/metasprite da ROM (doc/23, secao 2 e 6.B).
    """
    src = cmd_sources()
    run([sys.executable, str(WRAPPER / "mugen2sms" / "generators" / "cmd_patterns.py"),
         "--p1-source", str(src[0]), "--p1-config", str(CUT_CONFIGS[0]),
         "--p2-source", str(src[1]), "--p2-config", str(CUT_CONFIGS[1]),
         "--out-header", str(STUDY / "inc" / "attack_cmds.h"),
         "--out-report", str(PROJECT / "out" / "local_study" / "lote_d_cast" /
                             "attack_cmds_base.json")])


def regenerate() -> None:
    py = sys.executable
    run([py, str(WRAPPER / "mugen2sms" / "generators" / "pose_table.py"),
         "--header", str(STUDY / "inc" / "versus_scene_runtime_full_generated.h"),
         "--banks", str(STUDY / "assets" / "banks" / "versus_scene_banks_02.bin"),
         "--out", str(STUDY / "inc" / "pose_table.h"),
         "--bank-out", str(STUDY / "assets" / "banks" / "pose_meta_37.bin")])
    source_banks = STUDY / "assets" / "banks" / "versus_scene_banks_02.bin"
    meta_blob = STUDY / "assets" / "banks" / "pose_meta_37.bin"
    source_pages = source_banks.stat().st_size // 16384
    meta_pages = meta_blob.stat().st_size // 16384
    first_data_bank = 2 + source_pages + meta_pages
    frame_data_blob = STUDY / "assets" / "banks" / f"frame_data_{first_data_bank}.bin"
    run([py, str(WRAPPER / "mugen2sms" / "generators" / "source_frame_data.py"),
         "--header", str(STUDY / "inc" / "versus_scene_runtime_full_generated.h"),
         "--first-bank", str(first_data_bank),
         "--out-header", str(STUDY / "inc" / "source_frame_data.h"),
         "--out-banks", str(frame_data_blob)])
    frame_pages = frame_data_blob.stat().st_size // 16384
    index_bank = first_data_bank + frame_pages
    pose_index_blob = STUDY / "assets" / "banks" / f"pose_index_{index_bank}.bin"
    run([py, str(WRAPPER / "mugen2sms" / "generators" / "pose_table.py"),
         "--header", str(STUDY / "inc" / "versus_scene_runtime_full_generated.h"),
         "--banks", str(source_banks), "--out", str(STUDY / "inc" / "pose_table.h"),
         "--bank-out", str(meta_blob), "--index-bank", str(index_bank),
         "--index-out", str(pose_index_blob)])
    run([py, str(CANON / "tools" / "trim_scene_header.py"),
         "--header", str(STUDY / "inc" / "versus_scene_runtime_full_generated.h"),
         "--out", str(STUDY / "inc" / "scene_trimmed.h")])
    parts = [
        source_banks, meta_blob, frame_data_blob, pose_index_blob,
    ]
    out = STUDY / "assets" / "banks" / "banks_integrada.bin"
    out.write_bytes(b"".join(p.read_bytes() for p in parts))
    project_json = STUDY / ".mddev" / "project.json"
    manifest = json.loads(project_json.read_text(encoding="utf-8"))
    extras = manifest["toolchain"].get("makesms_extra", [])
    kept = []
    index = 0
    while index < len(extras):
        arg = extras[index]
        if arg == "-mbank":
            index += 2
            continue
        if arg.startswith("assets/banks/banks_integrada.bin:"):
            index += 1
            continue
        kept.append(arg)
        index += 1
    pages = len(out.read_bytes()) // 16384
    kept.extend(["-mbank", f"assets/banks/banks_integrada.bin:0:{pages}:2"])
    manifest["toolchain"]["makesms_extra"] = kept
    project_json.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def frame_data_blob() -> Path:
    header = (STUDY / "inc" / "source_frame_data.h").read_text(encoding="utf-8")
    match = re.search(r"#define\s+KEN_FRAME_DATA_BANK\s+(\d+)u?", header)
    if not match:
        raise SystemExit("KEN_FRAME_DATA_BANK ausente")
    return STUDY / "assets" / "banks" / f"frame_data_{int(match.group(1))}.bin"


def pose_index_blob() -> Path:
    header = (STUDY / "inc" / "pose_table.h").read_text(encoding="utf-8")
    match = re.search(r"#define\s+KEN_POSE_INDEX_BANK\s+(\d+)u?", header)
    if not match:
        raise SystemExit("KEN_POSE_INDEX_BANK ausente")
    return STUDY / "assets" / "banks" / f"pose_index_{int(match.group(1))}.bin"


def measure() -> None:
    py = sys.executable
    rom = STUDY / "out" / "rom" / "scale_pilot_80px.sms"
    mp = STUDY / "out" / "obj" / "scale_pilot_80px.map"
    sources = sorted((STUDY / "src").glob("*.c"))
    run([py, str(CANON / "tools" / "check_ram_layout.py"),
         "--map", str(mp), "--rom", str(rom),
         "--sources", *[str(s) for s in sources],
         str(STUDY / "inc" / "source_frame_data.h"),
         str(STUDY / "inc" / "pose_table.h")])
    run([py, str(CANON / "tools" / "check_rom_binding.py"),
         "--rom", str(rom),
         "--image", str(STUDY / "assets" / "banks" / "banks_integrada.bin"),
         "--base-bank", "2",
         "--pose-header", str(STUDY / "inc" / "pose_table.h"),
         "--meta-blob", str(STUDY / "assets" / "banks" / "pose_meta_37.bin"),
         "--frame-data-blob", str(frame_data_blob()),
         "--frame-data-header", str(STUDY / "inc" / "source_frame_data.h"),
         "--pose-index-blob", str(pose_index_blob()),
         "--pose-index-header", str(STUDY / "inc" / "pose_table.h")])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check-only", action="store_true",
                    help="mede o mapa e a ROM ja gerados, sem recompilar")
    ap.add_argument("--self-check", action="store_true",
                    help="roda o self-check das duas medicoes usadas pela receita")
    args = ap.parse_args()
    py = sys.executable
    if args.self_check:
        run([py, str(CANON / "tools" / "check_ram_layout.py"), "--self-check"])
        run([py, str(CANON / "tools" / "check_rom_binding.py"), "--self-check"])
        run([py, str(WRAPPER / "mugen2sms" / "generators" / "pose_table.py"), "--self-check"])
        run([py, str(WRAPPER / "mugen2sms" / "generators" / "source_frame_data.py"), "--self-check"])
        print("[PASS] build_luta_integrada self-check")
        return 0
    sync()
    if args.check_only:
        measure()
        return 0
    generate_assets()
    regenerate()
    generate_cmds()
    run([py, str(ROOT / "tools" / "sms_wrapper" / "build_inner.py"),
         "--project", str(STUDY)])
    measure()
    return 0


if __name__ == "__main__":
    main()
