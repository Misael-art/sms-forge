#!/usr/bin/env python3
"""Emite psg_blobs.h a partir dos .psg já hasheados no manifesto.

Não reautora. Falha se o SHA-256 ou o tamanho divergir do manifesto.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

DEFAULT_PROJECT = (Path(__file__).resolve().parents[2] / "SMS_projects" /
                   "luta_mugen")
# SFX deste corte: round, soco aceito, contato, KO. Chute e especial
# permanecem no disco; B2 é guarda e o especial não é entrada aceita.
WANTED = ("music_battle", "sfx_round", "sfx_shot", "sfx_hit", "sfx_down")


def _c_array(name: str, data: bytes) -> str:
    lines = [f"static const unsigned char {name}[{len(data)}] = {{"]
    for i in range(0, len(data), 16):
        chunk = ", ".join(f"0x{b:02X}" for b in data[i:i + 16])
        lines.append(f"    {chunk},")
    lines.append("};")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--project", type=Path, default=DEFAULT_PROJECT)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    project = args.project.resolve()
    manifest = project / "doc" / "audio_provenance_manifest.json"
    man = json.loads(manifest.read_text(encoding="utf-8"))
    by_stem = {}
    for asset in man["assets"]:
        stem = Path(asset["file"]).stem
        by_stem[stem] = asset
    parts = [
        "/* gerado por luta_mugen_gen_psg_blobs.py; bytes dos .psg do manifesto */",
        "#ifndef PSG_BLOBS_H",
        "#define PSG_BLOBS_H",
    ]
    for stem in WANTED:
        asset = by_stem[stem]
        path = project / asset["file"]
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        if digest != asset["sha256"] or len(data) != asset["bytes"]:
            raise SystemExit(
                f"{stem}: sha/tamanho {digest}/{len(data)} "
                f"!= {asset['sha256']}/{asset['bytes']}")
        parts.append(_c_array(stem, data))
    parts.append("#endif")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(parts) + "\n", encoding="utf-8")
    print(f"[OK] psg_blobs {len(WANTED)} streams -> {args.out}")
    return 0


if __name__ == "__main__":
    main()
