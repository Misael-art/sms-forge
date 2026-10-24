"""Classificacao de fidelidade por recurso: Character MUGEN -> VDP do Master System.

Um registro por sprite/pose/clsn/comando/som/controlador de estado, classe em
`direct|approximate|manual|unsupported` e motivo curto. O veredito e o dado de
entrada do Plano 2 (runtime); nao e negociavel, e medicao.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from . import sms_budget as B
from mugen2sms.converters import sms_scale as SC


@dataclass
class Element:
    id: str
    classe: str
    motivo: str = ""


@dataclass
class FidelityReport:
    per_element: list[Element] = field(default_factory=list)
    by_id: dict[str, Element] = field(default_factory=dict)
    totals: dict[str, int] = field(default_factory=dict)

    def add(self, el: Element) -> None:
        self.per_element.append(el)
        self.by_id[el.id] = el


# conjunto LEGADO de botoes sem mapa por tempo de pressao (a=KEY_1, s=KEY_2 no input.c); o pad tem
# KEY_1+KEY_2 (SMSlib.h:296-302) e o mapa vigente esta em converters/sms_controls.py (L093). Convencao MUGEN: maiusculas sao direcoes
# (F/B/U/D/DF..), minusculas de 1 caractere sao botoes (a,b,c,x,y,z; 's'=start, 'n'=nenhum).
_PAD_BUTTONS = {"a", "s", "n"}


def classify_character(ch, limits: B.SmsLimits, scale_label: str | None = None) -> FidelityReport:
    rep = FidelityReport()
    by_key = {(s.group, s.image): s for s in ch.sprites}

    for sp in ch.sprites:
        colors = B.used_colors(sp)
        if colors > limits.subpalette_colors:
            classe, motivo = "manual", f"paleta>15uteis:{colors}"
        else:
            classe, motivo = "direct", ""
        rep.add(Element(f"sprite:{sp.group},{sp.image}", classe, motivo))

    for n, action in ch.anims.items():
        for i, fr in enumerate(action.frames):
            sp = by_key.get((fr.group, fr.image))
            if sp is None:
                rep.add(Element(f"anim:{n}.{i}", "unsupported", "sprite-ausente"))
                continue
            entries = B.sat_entries(sp.width, sp.height)
            if entries > limits.sat_max:
                classe, motivo = "unsupported", f"sat>{limits.sat_max}:{entries}"
            elif scale_label:
                # Arte já no tamanho do pose_budget. O motivo nomeia a fração
                # que rodou. `downscale1:4` fica no caminho histórico.
                classe, motivo = "approximate", scale_label
            elif SC.exceeds_budget(sp.width, sp.height):
                # contrato de escala do GDD (2026-09-25): nem 1:4 salva -> reautoria
                classe, motivo = "manual", "estourou-apos-escala"
            elif SC.needs_scale(sp.width, sp.height):
                classe, motivo = "approximate", "downscale1:4"
            else:
                classe, motivo = "direct", ""
            rep.add(Element(f"anim:{n}.{i}", classe, motivo))
            if fr.clsn1 or fr.clsn2:
                rep.add(Element(f"clsn:{n}.{i}", "direct", "colisao-em-software-z80"))

    for c in ch.commands:
        buttons = sorted({k.key for step in c.steps for k in step.keys
                          if len(k.key) == 1 and k.key.islower() and k.key not in _PAD_BUTTONS})
        if buttons:
            rep.add(Element(f"cmd:{c.name}", "manual", "botao>pad:" + "/".join(buttons)))
        else:
            rep.add(Element(f"cmd:{c.name}", "direct", ""))

    for s in ch.sounds:
        rep.add(Element(f"sound:{s.group},{s.sample}", "unsupported", "pcm>psg"))

    for n, st in ch.states.items():
        for i, cc in enumerate(st.controllers):
            motivo = cc.notes[0][:120] if cc.notes else ""
            rep.add(Element(f"state:{n}:{i}", cc.fidelity, motivo))

    # pool de VRAM: todos os tiles do personagem residindo ao mesmo tempo (sem BG)
    uniq, total = B.dedup_tiles(ch.sprites)
    fits = uniq * limits.tile_bytes <= limits.vram_bytes
    rep.add(Element("vram:tiles-dedup", "direct" if fits else "approximate",
                    f"{uniq} tiles unicos de {total} = {uniq * limits.tile_bytes} B; "
                    + ("cabe na VRAM inteira" if fits else "streaming por pose obrigatorio")))
    rep.totals = dict(Counter(e.classe for e in rep.per_element))
    return rep


def _self_check() -> int:
    """Caso-limite embutido: pose de 9 colunas (cabe apos 1:4) e som PCM devem
    aparecer com as classes certas; `downscale1:4` e o motivo do contrato de escala."""
    from mugen2sms.character import CState
    from mugen2sms.ir import controllers as C
    from mugen2sms.parsers import air, snd, sff

    class Ch:
        pass
    ch = Ch()
    ch.sprites = [sff.Sprite(1, 0, 0, 0, 72, 64, bytes([1] * (72 * 64)), [(0, 0, 0)] * 256,
                             False, None, 0)]
    ch.anims = {0: air.Action(0, [air.Frame(1, 0, 0, 0, 1)])}
    ch.commands, ch.sounds = [], [snd.Sound(1, 0, b"x", 1, 1, 1, 1, None)]
    ch.states = {}
    rep = classify_character(ch, B.SmsLimits())
    fails = []
    if rep.by_id["anim:0.0"].classe != "approximate":
        fails.append("pose larga nao virou approximate")
    if not rep.by_id["anim:0.0"].motivo.startswith("downscale"):
        fails.append("motivo de downscale obrigatorio ausente")
    if rep.by_id["sound:1,0"].classe != "unsupported":
        fails.append("PCM nao virou unsupported")
    if sum(rep.totals.values()) != len(rep.per_element):
        fails.append("totals nao fecham com per_element")
    if fails:
        for f in fails:
            print("[SELF-CHECK FALHOU]", f)
        return 1
    print("[SELF-CHECK OK] analysis.fidelity")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pacote", nargs="?", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--self-check", action="store_true")
    args = ap.parse_args(argv)
    if args.self_check:
        return _self_check()
    if not args.pacote or not args.out:
        ap.error("pacote e --out obrigatorios (ou --self-check)")
    from mugen2sms import character as CH
    from mugen2sms.source import Source
    ch = CH.load(Source(args.pacote))
    rep = classify_character(ch, B.SmsLimits())
    out = {
        "personagem": ch.name,
        "limits": {f: getattr(B.SmsLimits(), f) for f in
                   ("sprites_per_line", "sat_max", "tiles_visible_per_frame",
                    "tile_bytes", "subpalette_colors", "vram_bytes", "ram_bytes")},
        "totals": rep.totals,
        "por_categoria": {},
        "elements": [{"id": e.id, "classe": e.classe, "motivo": e.motivo} for e in rep.per_element],
    }
    for e in rep.per_element:
        cat = e.id.split(":")[0]
        d = out["por_categoria"].setdefault(cat, Counter())
        d[e.classe] += 1
    out["por_categoria"] = {k: dict(v) for k, v in out["por_categoria"].items()}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] {ch.name}: {out['totals']} -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
