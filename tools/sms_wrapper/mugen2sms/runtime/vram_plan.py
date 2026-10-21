"""Planta de VRAM do SMS para o runtime (Lote B): fonte unica por consumidor.

Uma ROM de luta disputa os 16 KiB do VDP entre pool de patterns de sprite,
patterns de BG, PNT, SAT e espaco de FX. Este modulo valida a planta
DECLARADA e aponta: sobreposicao, regiao fora de 0x0000..0x3FFF, pool de
sprites fora da janela do reg6 e o risco de o tile de reserva da PNT morar
dentro de uma regiao reescrita em runtime (o caso concreto deste workspace:
PNT preenchida com tile 255, cujo pattern mora em 0x1FE0 dentro do pool de
sprites 0x0000..0x1FFF quando POOL_PAIRS=128 — pintar o pool apaga o "preto"
inteiro do BG).

Fatos com fonte (L001: numero sem fonte nao vira lei):
- VRAM do VDP = 16 KiB; tile = 32 B: SMSlib.h:121
  ``TILEtoADDR(tile) = (tile)*32`` (sdk/devkitSMS-upstream).
- PNT em 0x3800: SMSlib.c ``VDPReg_init`` reg2 ("PNT is at address 0x3800");
  768 entradas de 16 bits (§6 SMS_GLOBAL) = 1536 B.
- SAT em 0x3F00: SMSlib.c ``VDPReg_init`` reg5; 64 entradas x 4 B
  (AGENTS.md ">64 sprites na SAT" e MAXSPRITES=64).
- Sprites na primeira metade (reg6=0xFB via
  ``SMS_useFirstHalfTilesforSprites(1)``, SMSlib.c:184-186): patterns de
  sprite saem de 0x0000..0x1FFF; o fetch soma a base do reg6
  (BlastEm 1.0.0 vdp.c:754-755).
- BG le o pattern em tile*32 sem termo do reg4 (BlastEm vdp.c:1581/2048);
  indices uteis 0..447 — 448*32 = 0x3800 encosta na PNT
  (skill sms-vdp-tiles.md).

Uso:
    python -m mugen2sms.runtime.vram_plan plan.json [--json saida.json]
    python -m mugen2sms.runtime.vram_plan --self-check

Exit: 0 planta limpa | 1 violacao/risco | 3 uso.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

VRAM_BYTES = 16384
TILE_BYTES = 32                     # SMSlib.h:121
PNT_ADDR = 0x3800                   # SMSlib.c VDPReg_init reg2
PNT_ENTRIES = 768                   # 32x24 (§6 SMS_GLOBAL)
PNT_BYTES = PNT_ENTRIES * 2
SAT_ADDR = 0x3F00                   # SMSlib.c VDPReg_init reg5
SAT_ENTRIES = 64                    # MAXSPRITES=64 (SMSlib_common.c:21)
SAT_BYTES = SAT_ENTRIES * 4
SPRITE_FIRST_HALF_BYTES = 0x2000    # 256 tiles com reg6=0xFB
BG_TILES_MAX = 448                  # 448*32 = 0x3800 (skill sms-vdp-tiles)

KINDS = ("sprite_patterns", "bg_patterns", "hud_patterns", "fx_patterns",
         "pnt", "sat", "free")


@dataclass(frozen=True)
class Region:
    """Regiao de VRAM declarada por um consumidor."""
    name: str
    start: int
    size: int
    kind: str = "bg_patterns"
    writable: bool = False          # reescrita depois do boot (stream/upload)
    note: str = ""

    @property
    def end(self) -> int:
        return self.start + self.size

    def overlaps(self, other: "Region") -> bool:
        return self.start < other.end and other.start < self.end

    def as_dict(self) -> dict:
        d = {"name": self.name, "kind": self.kind, "start": self.start,
             "end": self.end, "size": self.size, "writable": self.writable}
        if self.note:
            d["note"] = self.note
        return d


@dataclass
class Plan:
    regions: list[Region] = field(default_factory=list)
    blank_tile: int | None = None    # tile de reserva usado para preencher a PNT
    sprite_first_half: bool = True   # reg6=0xFB

    def by_kind(self, kind: str) -> list[Region]:
        return [r for r in self.regions if r.kind == kind]


def _overlap_span(region: Region, start: int, end: int) -> bool:
    return region.start < end and start < region.end


def validate(plan: Plan) -> list[str]:
    """Violacoes da planta declarada (vazio = limpa)."""
    problems: list[str] = []
    for r in plan.regions:
        if r.kind not in KINDS:
            problems.append(
                "%s: kind desconhecido %r (use um de %s)"
                % (r.name, r.kind, ", ".join(KINDS)))
        if r.size <= 0:
            problems.append("%s: size %d <= 0" % (r.name, r.size))
        if r.start < 0 or r.end > VRAM_BYTES:
            problems.append(
                "%s: 0x%04X..0x%04X fora da VRAM 0x0000..0x%04X"
                % (r.name, r.start, r.end, VRAM_BYTES - 1))
        if r.kind in ("sprite_patterns", "bg_patterns", "hud_patterns",
                      "fx_patterns"):
            if r.start % TILE_BYTES or r.size % TILE_BYTES:
                problems.append(
                    "%s: regiao de pattern nao alinhada a tile (32 B): "
                    "0x%04X+%d" % (r.name, r.start, r.size))
        if r.kind == "pnt" and (r.start != PNT_ADDR or r.size != PNT_BYTES):
            problems.append(
                "%s: PNT declarada em 0x%04X+%d; SMSlib init deixa a PNT em "
                "0x%04X+%d (VDPReg_init reg2)" % (r.name, r.start, r.size,
                                                  PNT_ADDR, PNT_BYTES))
        if r.kind == "sat" and (r.start != SAT_ADDR or r.size != SAT_BYTES):
            problems.append(
                "%s: SAT declarada em 0x%04X+%d; SMSlib init deixa a SAT em "
                "0x%04X+%d (VDPReg_init reg5)" % (r.name, r.start, r.size,
                                                  SAT_ADDR, SAT_BYTES))
        if plan.sprite_first_half and r.kind == "sprite_patterns" \
                and r.end > SPRITE_FIRST_HALF_BYTES:
            problems.append(
                "%s: pool de sprites 0x%04X..0x%04X cruza 0x%04X — com "
                "reg6=0xFB (SMS_useFirstHalfTilesforSprites) os VDP so "
                "busca patterns de sprite em 0x0000..0x%04X"
                % (r.name, r.start, r.end, SPRITE_FIRST_HALF_BYTES,
                   SPRITE_FIRST_HALF_BYTES - 1))
        if r.kind == "bg_patterns" and r.end > BG_TILES_MAX * TILE_BYTES:
            problems.append(
                "%s: BG alem do tile %d (0x%04X) colide com a PNT em 0x%04X "
                "(448 tiles uteis: 448*32 = 0x3800)"
                % (r.name, BG_TILES_MAX - 1, BG_TILES_MAX * TILE_BYTES - 1,
                   PNT_ADDR))
    for i, a in enumerate(plan.regions):
        for b in plan.regions[i + 1:]:
            if a.kind == "free" or b.kind == "free":
                continue
            if a.overlaps(b):
                problems.append(
                    "sobreposicao: %s 0x%04X..0x%04X x %s 0x%04X..0x%04X"
                    % (a.name, a.start, a.end, b.name, b.start, b.end))
    return problems


def blank_tile_hazards(plan: Plan) -> list[str]:
    """Riscos do tile de reserva (o "preto" que a PNT usa como fundo)."""
    if plan.blank_tile is None:
        return []
    t = plan.blank_tile
    problems: list[str] = []
    if not (0 <= t <= 0x1FF):
        problems.append(
            "tile de reserva %d fora do indice de 9 bits da PNT (0..511)" % t)
        return problems
    span = (t * TILE_BYTES, t * TILE_BYTES + TILE_BYTES)
    if span[1] > VRAM_BYTES:
        problems.append(
            "tile de reserva %d: pattern 0x%04X..0x%04X passa da VRAM"
            % (t, span[0], span[1]))
        return problems
    for r in plan.regions:
        if not _overlap_span(r, *span):
            continue
        if r.writable:
            problems.append(
                "tile de reserva %d (0x%04X..0x%04X) cai dentro de %s "
                "(kind=%s, reescrita em runtime): o fundo da PNT inteira "
                "muda de aparencia quando essa regiao for escrita"
                % (t, span[0], span[1] - 1, r.name, r.kind))
        elif r.kind in ("pnt", "sat"):
            problems.append(
                "tile de reserva %d (0x%04X..0x%04X) cai dentro de %s "
                "(kind=%s): o 'pattern' de reserva e' bytes de PNT/SAT ao "
                "vivo" % (t, span[0], span[1] - 1, r.name, r.kind))
    return problems


def gaps(plan: Plan) -> list[tuple[int, int]]:
    """Trechos de VRAM sem dono (start, size), ordenados."""
    used = sorted((r.start, r.end) for r in plan.regions if r.kind != "free")
    out, cursor = [], 0
    for start, end in used:
        if start > cursor:
            out.append((cursor, start - cursor))
        cursor = max(cursor, end)
    if cursor < VRAM_BYTES:
        out.append((cursor, VRAM_BYTES - cursor))
    return out


def report(plan: Plan) -> dict:
    v = validate(plan)
    h = blank_tile_hazards(plan)
    return {
        "schema": "mugen2sms.vram-plan/v1",
        "ok": not v and not h,
        "violations": v,
        "blank_tile_hazards": h,
        "gaps": [{"start": s, "size": n} for s, n in gaps(plan)],
        "map": [r.as_dict() for r in sorted(plan.regions,
                                            key=lambda r: r.start)],
    }


def _int(value) -> int:
    if isinstance(value, int):
        return value
    return int(str(value), 0)


def load_plan(path: Path) -> Plan:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    regions = []
    for item in raw.get("regions", []):
        regions.append(Region(
            name=str(item["name"]),
            start=_int(item["start"]),
            size=_int(item["size"]),
            kind=str(item.get("kind", "bg_patterns")),
            writable=bool(item.get("writable", False)),
            note=str(item.get("note", "")),
        ))
    return Plan(
        regions=regions,
        blank_tile=(None if raw.get("blank_tile") is None
                    else _int(raw["blank_tile"])),
        sprite_first_half=bool(raw.get("sprite_first_half", True)),
    )


def plan_luta_mugem_rev2(pairs: int = 128, blank_tile: int = 255) -> Plan:
    """Planta do consumidor luta_mugem_rev2 (v033): pool de pares TALL 64 B.

    ``pairs`` = POOL_PAIRS do main.c; o pool ocupa pairs*64 bytes a partir de
    0x0000. A PNT e' preenchida com ``blank_tile`` (SMS_VRAMmemsetW(0x3800,
    0x00ff, 1536) = tile 255 sem flags) e o fundo e' o pattern zerado desse
    tile — que mora DENTRO do pool enquanto pairs=128 (tile 255 -> 0x1FE0).
    """
    regions = [
        Region("sprite_pool", 0x0000, pairs * 64, kind="sprite_patterns",
               writable=True,
               note="POOL_PAIRS=%d pares TALL de 64 B (main.c:42)" % pairs),
        Region("pnt", PNT_ADDR, PNT_BYTES, kind="pnt"),
        Region("sat", SAT_ADDR, SAT_BYTES, kind="sat"),
    ]
    return Plan(regions=regions, blank_tile=blank_tile,
                sprite_first_half=True)


def self_check() -> int:
    ok = True

    # 1. Planta do consumidor com pool de 128 pares: o tile 255 cai no pool.
    p128 = plan_luta_mugem_rev2(pairs=128, blank_tile=255)
    rep = report(p128)
    ok &= rep["violations"] == []
    ok &= any("tile de reserva 255" in h for h in rep["blank_tile_hazards"])

    # 2. Pool reduzido e reserva fora: planta limpa.
    p126 = plan_luta_mugem_rev2(pairs=126, blank_tile=254)
    p126.regions.append(Region("blank", 254 * 32, 32, kind="bg_patterns",
                               note="pattern zerado do tile de reserva"))
    rep = report(p126)
    ok &= rep["ok"]
    # 2b. Mesmo pool grande + reserva AINDA no pool: risco detectado.
    p128b = plan_luta_mugem_rev2(pairs=128, blank_tile=254)
    ok &= report(p128b)["blank_tile_hazards"] != []

    # 3. Sobreposicao PNT x pool nao passa (pool passa do inicio da PNT).
    bad = Plan(regions=[
        Region("pool", 0x0000, 0x3900, kind="sprite_patterns", writable=True),
        Region("pnt", PNT_ADDR, PNT_BYTES, kind="pnt"),
    ], blank_tile=None)
    ok &= any("sobreposicao" in p for p in validate(bad))

    # 4. Pool de sprite cruzando a janela do reg6 nao passa.
    bad = Plan(regions=[
        Region("pool", 0x1000, 0x2000, kind="sprite_patterns", writable=True),
    ])
    ok &= any("reg6" in p for p in validate(bad))

    # 5. BG alem do tile 447 nao passa.
    bad = Plan(regions=[
        Region("bg", 0x1000, 0x2900, kind="bg_patterns"),
    ])
    ok &= any("448 tiles" in p for p in validate(bad))

    # 6. PNT/SAT fora do canonico nao passam.
    bad = Plan(regions=[
        Region("pnt", 0x3A00, PNT_BYTES, kind="pnt"),
        Region("sat", SAT_ADDR, SAT_BYTES, kind="sat"),
    ])
    ok &= any("PNT declarada" in p for p in validate(bad))

    # 7. gaps: com pool 0..0x1FE0, PNT e SAT, o unico buraco e' 0x3E00..0x3F00.
    p = plan_luta_mugem_rev2(pairs=127, blank_tile=254)
    ok &= gaps(p) == [(0x1FC0, 0x3800 - 0x1FC0), (0x3E00, 0x100)]

    print("self-check vram_plan:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("plan", type=Path, nargs="?")
    ap.add_argument("--json", type=Path, default=None)
    ap.add_argument("--self-check", action="store_true")
    args = ap.parse_args(argv)
    if args.self_check:
        return self_check()
    if args.plan is None:
        ap.error("informe plan.json ou use --self-check")
    rep = report(load_plan(args.plan))
    if args.json:
        args.json.write_text(json.dumps(rep, indent=1) + "\n",
                             encoding="utf-8")
    for item in rep["map"]:
        print("  %-14s %-16s 0x%04X..0x%04X %s"
              % (item["name"], item["kind"], item["start"], item["end"] - 1,
                 "writable" if item["writable"] else ""))
    for s, n in rep["gaps"]:
        print("  (vago)         0x%04X..0x%04X" % (s, s + n - 1))
    for p in rep["violations"]:
        print("[VIOLACAO] " + p)
    for h in rep["blank_tile_hazards"]:
        print("[RISCO]    " + h)
    print("[vram-plan] %s" % ("ok" if rep["ok"] else "REPROVADO"))
    return 0 if rep["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
