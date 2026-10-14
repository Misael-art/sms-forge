"""Estudo local: parseia um personagem MUGEN real de ponta a ponta e mede o IR.

Somente-leitura sobre o acervo; escreve apenas no --out (gitignored).
Uso: python3 -m mugen2sms.ken_full_parse <zip|pasta> [--out ken_ir.json]
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from . import character as CH
from .source import Source

# avisos do parser que sao defeitos de leitura, nao escolhas de design
_ERROR_MARKERS = ("nao suportado", "truncado", "inexistente", "fora do arquivo",
                  "invalido", "sem frames", "interrompida")


def summarize(ch: CH.Character) -> dict:
    n_clsn = sum(len(f.clsn1) + len(f.clsn2) for a in ch.anims.values() for f in a.frames)
    parse_erros = [w for w in ch.warnings if any(m in w for m in _ERROR_MARKERS)]
    return {
        "personagem": ch.name,
        "author": ch.author,
        "def": ch.def_path,
        "source_sha256": ch.source_sha256,
        "n_sprites": len(ch.sprites),
        "n_palettes": len(ch.palettes),
        "n_animations": len(ch.anims),
        "n_frames": sum(len(a.frames) for a in ch.anims.values()),
        "n_clsn_entries": n_clsn,
        "n_commands": len(ch.commands),
        "n_sounds": len(ch.sounds),
        "n_states": len(ch.states),
        "origens_states": dict(Counter(s.origin for s in ch.states.values())),
        "fidelidade_controladores": ch.report["controller_fidelity"],
        "controller_total": sum(ch.report["controllers"].values()),
        "missing_refs": ch.report["missing_refs"],
        # refs com "resolution" sao substituicoes intencionais do design (ex.: stcommon -> common_forge)
        "missing_refs_reais": [m for m in ch.report["missing_refs"] if "resolution" not in m],
        "anims_missing_sprites": ch.report["anims"]["missing_sprites"],
        "parse_erros": parse_erros,
        "outros_avisos": [w for w in ch.warnings if w not in parse_erros],
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pacote", type=Path, help=".zip ou pasta do personagem MUGEN")
    ap.add_argument("--out", type=Path, default=Path("ken_ir.json"))
    args = ap.parse_args(argv)
    ch = character_load(args.pacote)
    s = summarize(ch)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")
    ok = not s["parse_erros"] and not s["missing_refs_reais"] and all(
        s[k] > 0 for k in ("n_sprites", "n_animations", "n_frames", "n_clsn_entries",
                           "n_commands", "n_states"))
    print(f"[{'OK' if ok else 'FALHA'}] {args.pacote.name}: "
          f"{s['n_sprites']} sprites, {s['n_animations']} anims ({s['n_frames']} frames, "
          f"{s['n_clsn_entries']} clsn), {s['n_commands']} comandos, {s['n_states']} estados, "
          f"{s['n_sounds']} sons -> {args.out}")
    for e in s["parse_erros"]:
        print("  erro:", e)
    for m in s["missing_refs_reais"]:
        print("  referencia ausente:", m)
    return 0 if ok else 1


def character_load(pacote: Path) -> CH.Character:
    return CH.load(Source(pacote))


if __name__ == "__main__":
    sys.exit(main())
