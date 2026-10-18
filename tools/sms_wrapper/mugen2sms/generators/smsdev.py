"""Gerador SMSdev: artefatos dos converters -> headers C + manifest com SHA por simbolo.

Formato pensado para os gates do workspace:
- `#define <SYM>_SIZE <n>` sempre igual ao comprimento do array (`audit_symbol_size_sync.py`);
- header idempotente (guard `#ifndef`), ASCII, `const unsigned char` (sem float/malloc);
- manifest `{symbol, size_bytes, sha256_dos_bytes, source_sha256}` — insumo do
  `audit_rom_asset_binding.py` na S5+.

So viram artefato elementos `direct|approximate` do FidelityReport (S3);
`manual|unsupported` viram linha no relatorio de exclusao — nada silencioso.

Formato dos simbolos por pose (consumido pelo runtime do Plano 2):
  <S>_A<anim>F<frame>_TILES : pool de pares TALL 8x16 (64 B, topo+base), dedupado
                              por conteudo; espelhos H entram DEPOIS dos normais
                              (SMS nao tem flip de sprite — espelho e outro padrão)
  <S>_A<anim>F<frame>_META   : triplas (dx, dy, tile) + terminador 0x80, facing R;
  <S>_A<anim>F<frame>_METAL  : idem, facing L (tile = par espelhado, dx invertido).
                               Formato provado em ROM por MSSF2T fight.c:1095-1129;
                               tile de runtime = pool_idx*2 (indice par, SPRITEMODE_TALL)
  <S>_A<anim>F<frame>_PAL    : 16 palavras CRAM u8 (RGB r|g<<2|b<<4, SMSlib.h)
  <S>_A<anim>F<frame>_AXIS   : par int16 (x,y) do eixo MUGEN, compensado no runtime
  <S>_A<anim>F<frame>_CLSN   : quádruplas int16 em DUAS secoes (hit | hurt), cada uma terminada por sentinela -32767
"""
from __future__ import annotations

import hashlib
import json
import re
import struct
import sys
from dataclasses import dataclass, field
from pathlib import Path

from ..converters.sms_tiles import to_sms_pose
from ..converters.sms_clsn import to_clsn_tables
from ..converters.sms_cmd import serialize_pattern, to_patterns
from ..converters import sms_scale as SC
from .runtime_format import build_frames, pack_tiles_tall


@dataclass
class Artifact:
    symbol: str
    data: bytes
    source: str


@dataclass
class GenerationManifest:
    entries: list[dict] = field(default_factory=list)
    excluded: list[dict] = field(default_factory=list)
    stats: dict = field(default_factory=dict)
    generated_sha256: str = ""


def slug(name: str) -> str:
    s = re.sub(r"[^0-9a-z]+", "_", name.lower()).strip("_")
    return (s or "char").upper()


def render_header(artifacts: list[Artifact], guard: str,
                  bank_map: dict | None = None) -> str:
    lines = [f"#ifndef {guard}_H", f"#define {guard}_H", "",
             "/* gerado por mugen2sms.generators.smsdev - nao editar na mao */", ""]
    for a in artifacts:
        lines.append(f"#define {a.symbol}_SIZE {len(a.data)}")
        if bank_map and a.symbol in bank_map:
            b, off = bank_map[a.symbol]
            lines.append(f"#define {a.symbol}_BANK {b}")
            lines.append(f"#define {a.symbol}_OFF {off}")
        else:
            lines.append(f"const unsigned char {a.symbol}[{len(a.data)}] = {{")
            for i in range(0, len(a.data), 16):
                lines.append("    " + ", ".join(f"0x{b:02X}" for b in a.data[i:i + 16]) + ",")
            lines.append("};")
        lines.append("")
    lines.append(f"#endif /* {guard}_H */")
    return "\n".join(lines) + "\n"


BANK_PAGE = 16384   # slot 2 do Sega mapper (makesms -mbank ...:0:1:2)


def generate(ch, fidelity, out_dir: Path, banked: bool = False,
             pre_scaled: bool = False,
             omit_blank_sprites: bool = False,
             controls=None) -> GenerationManifest:
    out_dir.mkdir(parents=True, exist_ok=True)
    s = slug(Path(ch.def_path).stem)
    artifacts: list[Artifact] = []
    man = GenerationManifest()
    cls_ok = {"direct", "approximate"}

    by_key = {(sp.group, sp.image): sp for sp in ch.sprites}
    clsn = to_clsn_tables(ch.anims)
    for n, action in sorted(ch.anims.items()):
        for i, fr in enumerate(action.frames):
            el = fidelity.by_id.get(f"anim:{n}.{i}")
            if el is None or el.classe not in cls_ok:
                man.excluded.append({"id": f"anim:{n}.{i}",
                                     "classe": el.classe if el else "ausente",
                                     "motivo": el.motivo if el else "sem registro"})
                continue
            sp = by_key.get((fr.group, fr.image))
            if sp is None:
                man.excluded.append({"id": f"anim:{n}.{i}", "classe": "unsupported",
                                     "motivo": "sprite-ausente"})
                continue
            if not pre_scaled and SC.needs_scale(sp.width, sp.height):
                # contrato de escala GDD: so o que nao cabe em 1:1 e reduzido 1:4
                pose = to_sms_pose(SC.downscale_indexed(sp))
            else:
                pose = to_sms_pose(sp)
            stem = f"{s}_A{n}F{i}"
            blob, _mirrors = pack_tiles_tall(pose)
            artifacts.append(Artifact(f"{stem}_TILES", blob, "sff"))
            artifacts.append(Artifact(f"{stem}_PAL", bytes(pose.palette), "sff+act"))
            artifacts.append(Artifact(f"{stem}_META", build_frames(
                pose, omit_blank_cells=omit_blank_sprites), "air"))
            artifacts.append(Artifact(f"{stem}_METAL", build_frames(
                pose, facing=1, omit_blank_cells=omit_blank_sprites), "air"))
            artifacts.append(Artifact(f"{stem}_AXIS", struct.pack("<2h", fr.x, fr.y), "air"))
            hit, hurt = clsn[n][i]
            if hit or hurt:
                # DUAS secoes terminadas por sentinela: hit (clsn1) primeiro,
                # hurt (clsn2) depois. Com uma so sentinela o runtime nao
                # distingue caixa de golpe de hurtbox — colisao exige isso.
                data = b"".join(struct.pack("<h", v) for v in hit) \
                    + struct.pack("<h", -32767) \
                    + b"".join(struct.pack("<h", v) for v in hurt) \
                    + struct.pack("<h", -32767)
                artifacts.append(Artifact(f"{stem}_CLSN", data, "air"))

    patterns, skipped = to_patterns(ch.commands, controls)
    for p in patterns:
        artifacts.append(Artifact(f"{s}_CMD_{re.sub(r'[^0-9a-zA-Z]+', '_', p.name).upper()}",
                                  serialize_pattern(p), "cmd"))
    for name, why in skipped.items():
        man.excluded.append({"id": f"cmd:{name}", "classe": "manual", "motivo": why})

    hdr_artifacts = artifacts
    bank_map: dict[str, tuple[int, int]] = {}
    if banked:
        page = bytearray(BANK_PAGE)
        off = 0
        for a in artifacts:
            if not a.symbol.endswith("_TILES"):
                continue
            if off + len(a.data) > BANK_PAGE:
                raise SystemExit(
                    f"[FAIL] banco de tiles estourou a pagina de {BANK_PAGE} B "
                    f"em {a.symbol} — corte quadros (nao truncar)")
            page[off:off + len(a.data)] = a.data
            bank_map[a.symbol] = (2, off)
            off += len(a.data)
        (out_dir / f"{s.lower()}_bank2.bin").write_bytes(bytes(page))

    hdr = render_header(hdr_artifacts, s.lower(), bank_map or None)
    (out_dir / f"{s.lower()}_art.h").write_text(hdr, encoding="ascii")
    hdr_bytes = hdr.encode("ascii")
    man.generated_sha256 = hashlib.sha256(hdr_bytes).hexdigest()
    for a in artifacts:
        e = {"symbol": a.symbol, "size_bytes": len(a.data),
             "sha256": hashlib.sha256(a.data).hexdigest(),
             "source": a.source, "source_sha256": ch.source_sha256,
             "blob": a.data}
        if a.symbol in bank_map:
            e["bank"], e["off"] = bank_map[a.symbol]
        man.entries.append(e)
    man.stats = {"artifacts": len(artifacts), "bytes": sum(len(a.data) for a in artifacts),
                 "excluded": len(man.excluded)}
    entries_json = [{k: v for k, v in e.items() if k != "blob"} for e in man.entries]
    (out_dir / f"{s.lower()}_manifest.json").write_text(
        json.dumps({"entries": entries_json, "excluded": man.excluded, "stats": man.stats,
                    "generated_sha256": man.generated_sha256}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    return man


def _worst_scene(ch, fid, size="8x8"):
    """Cena pior-frame: maior pose GERADA (pos-escala), ego + oponente colados no mesmo y.

    `size="8x8"` e deliberadamente pessimista: conta cada linha de 8 px como linha
    varrida; em SPRITEMODE_TALL cada entrada cobre 16 px, entao o pico real so pode
    ser menor que o medido aqui.
    """
    poses = []
    by_key = {(sp.group, sp.image): sp for sp in ch.sprites}
    for n, action in ch.anims.items():
        for i, fr in enumerate(action.frames):
            el = fid.by_id.get(f"anim:{n}.{i}")
            if el is None or el.classe not in ("direct", "approximate"):
                continue
            sp = by_key.get((fr.group, fr.image))
            if sp is None:
                continue
            w, h = (sp.width, sp.height)
            if SC.needs_scale(w, h):
                w, h = w // SC.SCALE, h // SC.SCALE
            tw, th = -(-w // 8), -(-h // 8)
            poses.append((tw * th, tw, th, n, i))
    if not poses:
        return None
    total, tw, th, n, i = max(poses)
    sprites = []
    for off, base in ((0, 0), (tw * 8, 256 - tw * 8)):     # dois lutadores, mesma linha
        for ty in range(th):
            for tx in range(tw):
                sprites.append({"y": 192 - th * 8 + ty * 8, "x": base + tx * 8, "tile": 0})
    return {"sprite_size": size, "zoomed": False, "sprites": sprites, "screen_h": 192,
            "pose_pior": f"anim {n} frame {i} ({tw}x{th} tiles)"}


def main(argv=None) -> int:
    import argparse
    import sys
    from pathlib import Path
    ap = argparse.ArgumentParser(description="gera artefatos SMS a partir de um pacote MUGEN")
    ap.add_argument("pacote", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--banked", action="store_true",
                    help="empacota _TILES em {slug}_bank2.bin (slot 2, 16 KB) e troca arrays inline por _BANK/_OFF")
    args = ap.parse_args(argv)
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from ..analysis.fidelity import classify_character
    from ..analysis.sms_budget import SmsLimits
    from ..character import load as ch_load
    from ..source import Source
    import audit_sprite_line_sim as sim
    ch = ch_load(Source(args.pacote))
    fid = classify_character(ch, SmsLimits())
    man = generate(ch, fid, args.out, banked=args.banked)
    scene = _worst_scene(ch, fid)
    (args.out / "worst_scene.json").write_text(json.dumps(scene, indent=2), encoding="utf-8")
    verdict = sim.simulate(scene)
    report = {"stats": man.stats, "excluded_by_classe":
              {c: sum(1 for e in man.excluded if e["classe"] == c) for c in
               ("approximate", "manual", "unsupported", "ausente")},
              "fidelity_totals": fid.totals, "generated_sha256": man.generated_sha256,
              "gate_scanline": {"peak_per_line": verdict["peak_per_line"],
                                "sat_entries": verdict["sprites"],
                                "violations": verdict["violations"][:6],
                                "veredito": "PASS" if not verdict["violations"] else "FAIL"}}
    (args.out / "s4_generation_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[{'GATE ' + report['gate_scanline']['veredito']}] {man.stats} "
          f"peak={verdict['peak_per_line']}/linha sat={verdict['sprites']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
