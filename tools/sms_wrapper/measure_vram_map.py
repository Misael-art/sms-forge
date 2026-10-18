#!/usr/bin/env python3
"""measure_vram_map.py — mapa de VRAM SMS: janelas, colisoes e sobras legais (L133, SMS_GLOBAL §124).

Lei (corpus smspower.org/Development/VRAMMemoryMap, Tier 1): layout corrente
$0000-$1FFF tiles 0-255, $2000-$37FF tiles 256-447, $3800-$3EFF tilemap,
$3F00-$3FFF SAT. A SAT da 1 byte ao indice do sprite: sprite so alcanca a
janela de 256 tiles escolhida pelo reg6 — $FB = base $0000 (256 tiles
unicos), $FF = base $2000 (192 unicos; default da SMSlib, SMSlib.c
VDPReg_init e SMS_useFirstHalfTilesforSprites em SMSlib.h:53). BG usa
indices 0-511 e alcancar qualquer tile antes da name table.

Sobras legais (cada uma com condicao de guarda, do proprio corpus):
  gap_sat            $3F40-$3F7F  2 tiles  — stretch de 64 bytes nao usado
                                        pela SAT quando o jogo ocupa 32
                                        entradas (sprite idx 250 / tilemap
                                        idx 506)
  tilemap_bottom     $3E00-$3EFF  8 tiles  — exige SEM scroll vertical e
                                        modo 192 (idx 240 / 496)
  sat_tail           $3F20-$3F3F + $3FC0-$3FFF  3 tiles — exige <=31 sprites
                                        com terminador $D0 na 32a entrada,
                                        valido so em modo 192 (§118/L128)

Modos:
  --plan PLAN.json    plano de carga (schema sms_vram_plan_v1): julga
                      colisoes entre regioes, janela do reg6, name table
                      extra com motivo, e oferta de sobras.
  --snapshots DIR     vdp_regs.bin de blastem_sms.py: cross-check autoral —
                      reg5 deve ser 0xFF (SAT padrao), reg6 deve bater com o
                      plano, reg2 0xFF/0xFE decifravel (bit0=0 = alerta
                      mirror SMS1, §121).

Vereditos: aprovado | aprovado_com_alertas | reprovado_* | nao_provado.
Uso: measure_vram_map.py --plan P [--snapshots DIR] [--json OUT] [--self-check]
Exit: 0 aprovado/alertas | 1 reprovado | 2 erro de uso
"""
import sys, os, json, glob, argparse, tempfile

VRAM_TOTAL = 16384
TILE_BYTES = 32
SAT_RANGE = (0x3F00, 0x4000)
REG6_POOL = {0xFB: (0x0000, 256), 0xFF: (0x2000, 192)}
NAME_ROWS = {192: 28, 224: 32, 240: 32}


def _rng_overlap(a, b):
    lo, hi = max(a[0], b[0]), min(a[1], b[1])
    return (lo, hi) if lo < hi else None


def pockets(plan):
    """Oferta de sobras legais com guardas; legal=guardas satisfeitas."""
    mode = plan.get("screen_height", 192)
    vscroll = bool(plan.get("vertical_scroll", True))
    max_sprites = plan.get("max_sprites", 32)
    out = [
        {"kind": "gap_sat", "ranges": [(0x3F40, 0x3F80)], "tiles": 2,
         "guards": [], "legal": True,
         "note": "sprite idx 250 (0xFA) / tilemap idx 506 (0x1FA) quando reg6=0xFF"},
        {"kind": "tilemap_bottom", "ranges": [(0x3E00, 0x3F00)], "tiles": 8,
         "guards": ["sem scroll vertical", "modo 192 (tilemap de 28 linhas)"],
         "legal": (mode == 192 and not vscroll),
         "note": "sprite idx 240 (0xF0) / tilemap idx 496 (0x1F0)"},
        {"kind": "sat_tail", "ranges": [(0x3F20, 0x3F40), (0x3FC0, 0x4000)],
         "tiles": 3,
         "guards": ["max 31 (ou 15) sprites com $D0 no Y da 32a entrada",
                    "terminador $D0 so vale em modo 192 (L128/§118)"],
         "legal": (mode == 192 and max_sprites <= 31),
         "note": "Y dos sprites 32-63 e X/tile idx correspondentes"},
    ]
    return out


def audit_plan(plan):
    blockers, alerts = [], []
    mode = plan.get("screen_height", 192)
    if mode not in NAME_ROWS:
        blockers.append({"code": "modo_invalido",
                         "motivo": "screen_height deve ser 192, 224 ou 240"})
    rows = NAME_ROWS.get(mode, 28)
    name_base = int(plan.get("name_base", 0x3800), 0) if isinstance(
        plan.get("name_base", 0x3800), str) else plan.get("name_base", 0x3800)
    name_blk = (name_base, name_base + rows * 64)
    reg6 = int(plan.get("reg6", 0xFF), 0) if isinstance(plan.get("reg6", 0xFF), str) \
        else plan.get("reg6", 0xFF)
    if reg6 not in REG6_POOL:
        blockers.append({"code": "reg6_invalido", "motivo": "reg6 deve ser 0xFB ou 0xFF"})
    pool_lo, pool_count = REG6_POOL.get(reg6, (0x2000, 192))
    pool = (pool_lo, pool_lo + pool_count * TILE_BYTES)

    blocks = []  # (label, range)
    for r in plan.get("regions", []):
        addr = int(r["addr"], 0) if isinstance(r["addr"], str) else r["addr"]
        end = addr + int(r["bytes"])
        blocks.append((r.get("label", "?"), (addr, end), r.get("role", "bg_tiles")))
    for x in plan.get("extra_name_tables", []):
        if not str(x.get("reason", "")).strip():
            blockers.append({"code": "tilemap_extra_sem_motivo",
                             "motivo": "name table extra exige motivo declarado "
                                       "(duplo buffer / menu / split HBlank)"})
        base = int(x["base"], 0) if isinstance(x["base"], str) else x["base"]
        blocks.append(("extra_pnt@%s" % hex(base), (base, base + rows * 64), "name_table"))

    claimed = {p["kind"] for p in plan.get("pockets", []) if "kind" in p} \
        if isinstance(plan.get("pockets"), list) else set()
    for pk in pockets(plan):
        if pk["kind"] in claimed and not pk["legal"]:
            blockers.append({"code": "sobria_sem_guarda",
                             "motivo": "%s reclamado mas guardas nao satisfeitas: %s"
                                       % (pk["kind"], "; ".join(pk["guards"]))})
        if pk["kind"] in claimed:
            for lo, hi in pk["ranges"]:
                blocks.append(("pocket:" + pk["kind"], (lo, hi), "pocket"))

    for label, blk, role in blocks:
        if blk[0] < 0 or blk[1] > VRAM_TOTAL:
            blockers.append({"code": "fora_de_vram", "label": label,
                             "motivo": "%s-%s fora de 16KB" % (hex(blk[0]), hex(blk[1]))})
        if role == "sprite_tiles" and not (pool[0] <= blk[0] and blk[1] <= pool[1]):
            blockers.append({"code": "sprite_fora_da_janela_reg6", "label": label,
                             "motivo": "reg6=%s: sprite so alcancar $%04X-$%04X "
                                       "(janela de %d tiles)"
                                       % (hex(reg6), pool[0], pool[1], pool_count)})
    all_blocks = [("pnt", name_blk, "pnt"), ("sat", SAT_RANGE, "sat")] + blocks
    for i in range(len(all_blocks)):
        for j in range(i + 1, len(all_blocks)):
            li, lj = all_blocks[i][2], all_blocks[j][2]
            # uma sobria legal mora DENTRO do bloco PNT ou SAT por definição
            # (é o miolo nao usado por esses blocos); colisao pocket-vs-dono nao e invasao
            if {li, lj} in ({"pocket", "pnt"}, {"pocket", "sat"}):
                continue
            ov = _rng_overlap(all_blocks[i][1], all_blocks[j][1])
            if ov:
                blockers.append({"code": "invasao",
                                 "motivo": "%s e %s colidem em %s-%s"
                                           % (all_blocks[i][0], all_blocks[j][0],
                                              hex(ov[0]), hex(ov[1]))})
    used = set()
    for _, blk, _ in blocks:
        used.update(range(max(0, blk[0]), min(VRAM_TOTAL, blk[1])))
    used.update(range(name_blk[0], name_blk[1]))
    used.update(range(SAT_RANGE[0], SAT_RANGE[1]))
    return blockers, alerts, {"reg6": hex(reg6),
                              "sprite_janela": [hex(pool[0]), hex(pool[1])],
                              "sprite_tiles_unicos": pool_count,
                              "pnt_bloco": [hex(name_blk[0]), hex(name_blk[1])],
                              "bytes_usados": len(used),
                              "bytes_livres": VRAM_TOTAL - len(used),
                              "pockets_oferecidos": pockets(plan)}


def check_snapshots(plan, snapshots_dir):
    """Cross-check com vdp_regs.bin reais (blastem_sms.py). Fronteira final autoritativa."""
    dumps = sorted(glob.glob(os.path.join(snapshots_dir, "*", "vdp_regs.bin"))) or \
        sorted(glob.glob(os.path.join(snapshots_dir, "vdp_regs.bin")))
    out = []
    if not dumps:
        return [{"code": "sem_dumps", "motivo": "nenhum vdp_regs.bin em %s" % snapshots_dir}]
    for p in dumps:
        blob = open(p, "rb").read()
        if len(blob) != 11:
            raise OSError("vdp_regs.bin com %d bytes (esperado 11): %s" % (len(blob), p))
        rec = {"arquivo": p, "reg2": hex(blob[2]), "reg5": hex(blob[5]), "reg6": hex(blob[6])}
        if blob[5] != 0xFF:
            rec["blocker"] = "reg5=%s: esta ferramenta assume SAT em $3F00 (reg5=0xFF)" % hex(blob[5])
        elif blob[6] != reg6_of(plan):
            rec["blocker"] = "reg6=%s diverge do plano (%s): janela de sprite real nao e a declarada" \
                             % (hex(blob[6]), hex(reg6_of(plan)))
        elif blob[2] == 0xFE:
            rec["alerta"] = "reg2 bit0=0: mirror SMS1 (§121) — invisível aqui, real no silício"
        out.append(rec)
    return out


def reg6_of(plan):
    v = plan.get("reg6", 0xFF)
    return int(v, 0) if isinstance(v, str) else v


def self_check():
    ok = True
    def check(label, cond):
        nonlocal ok
        print(("  [OK] " if cond else "  [XX] ") + label)
        ok = ok and cond
    base_plan = {"schema": "sms_vram_plan_v1", "screen_height": 192,
                 "vertical_scroll": False, "max_sprites": 31, "reg6": 0xFF,
                 "name_base": 0x3800,
                 "regions": [{"label": "bg", "addr": 0x0000, "bytes": 0x1000, "role": "bg_tiles"},
                             {"label": "spr", "addr": 0x2000, "bytes": 0x1800, "role": "sprite_tiles"}]}
    b, a, m = audit_plan(base_plan)
    check("plano basico 192/no-vscroll/31-sprites aprovado", not b and not a)
    check("janela reg6=0xFF reportada (192 unicos)", m["sprite_tiles_unicos"] == 192
          and m["sprite_janela"] == ["0x2000", "0x3800"])
    offer = {p["kind"]: p["legal"] for p in m["pockets_oferecidos"]}
    check("com 31 sprites+no-vscroll as tres sobras estao legais",
          offer["gap_sat"] and offer["tilemap_bottom"] and offer["sat_tail"])
    b, _, m = audit_plan({**base_plan, "vertical_scroll": True, "max_sprites": 32})
    offer = {p["kind"]: p["legal"] for p in m["pockets_oferecidos"]}
    check("com scroll e 32 sprites, sobram so o gap_sat",
          offer["gap_sat"] and not offer["tilemap_bottom"] and not offer["sat_tail"])
    b, _, _ = audit_plan({**base_plan, "pockets": [{"kind": "sat_tail"}],
                          "max_sprites": 32})
    check("reclamar sat_tail sem guarda reprova (sobria_sem_guarda)",
          any(x["code"] == "sobria_sem_guarda" for x in b))
    b, _, _ = audit_plan({**base_plan, "regions": base_plan["regions"] +
                          [{"label": "spill", "addr": 0x3700, "bytes": 0x200, "role": "bg_tiles"}]})
    check("tile BG invadindo a name table reprova (invasao)",
          any(x["code"] == "invasao" for x in b))
    b, _, _ = audit_plan({**base_plan, "regions": [{"label": "spr", "addr": 0x1000,
                                                    "bytes": 0x100, "role": "sprite_tiles"}]})
    check("sprite tile abaixo de $2000 com reg6=0xFF reprova (janela)",
          any(x["code"] == "sprite_fora_da_janela_reg6" for x in b))
    b, _, m = audit_plan({**base_plan, "reg6": 0xFB,
                          "regions": [{"label": "spr", "addr": 0x0000, "bytes": 0x2000,
                                       "role": "sprite_tiles"}]})
    check("reg6=0xFB abre janela de 256 tiles", not b and m["sprite_tiles_unicos"] == 256)
    b, _, _ = audit_plan({**base_plan, "regions": [],
                         "extra_name_tables": [{"base": 0x1000}]})
    check("tilemap extra sem motivo reprova", any(x["code"] == "tilemap_extra_sem_motivo" for x in b))
    b, _, _ = audit_plan({**base_plan, "regions": [], "screen_height": 240,
                          "extra_name_tables": [{"base": 0x1000, "reason": "menu"}]})
    check("modo 240 com name_base $3800 colide com a SAT (geometria §122)",
          any(x["code"] == "invasao" for x in b))
    b, _, _ = audit_plan({**base_plan, "regions": [{"label": "t", "addr": 0x1000, "bytes": 0x800,
                                                    "role": "bg_tiles"}], "screen_height": 240,
                          "name_base": 0x3700,
                          "extra_name_tables": [{"base": 0x1000, "reason": "menu"}]})
    check("tilemap extra sobre tiles existentes reprova (invasao)",
          any(x["code"] == "invasao" for x in b))
    with tempfile.TemporaryDirectory(prefix="vrammap_selfcheck_") as tmp:
        snap = os.path.join(tmp, "snapshots")
        os.makedirs(os.path.join(snap, "000"))
        open(os.path.join(snap, "000", "vdp_regs.bin"), "wb").write(
            bytes([0x04, 0x36, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x00, 0x00, 0x00, 0x00]))
        recs = check_snapshots(base_plan, snap)
        check("snapshot reg6=0xFF bate com plano", all("blocker" not in r for r in recs))
        open(os.path.join(snap, "000", "vdp_regs.bin"), "wb").write(
            bytes([0x04, 0x36, 0xFF, 0xFF, 0xFF, 0xFF, 0xFB, 0x00, 0x00, 0x00, 0x00]))
        recs = check_snapshots(base_plan, snap)
        check("snapshot reg6=0xFB diverge de plano 0xFF e reprova",
              any("blocker" in r for r in recs))
        open(os.path.join(snap, "000", "vdp_regs.bin"), "wb").write(
            bytes([0x04, 0x36, 0xFE, 0xFF, 0xFF, 0xFF, 0xFF, 0x00, 0x00, 0x00, 0x00]))
        recs = check_snapshots(base_plan, snap)
        check("snapshot reg2=0xFE gera alerta de mirror (§121), nao blocker",
              recs and "alerta" in recs[0] and "blocker" not in recs[0])
        open(os.path.join(snap, "000", "vdp_regs.bin"), "wb").write(b"\x01")
        try:
            check_snapshots(base_plan, snap)
            check("vdp_regs.bin truncado levanta OSError", False)
        except OSError:
            check("vdp_regs.bin truncado levanta OSError", True)
    print("SELFCHECK measure_vram_map.py: " + ("VERDE" if ok else "VERMELHO"))
    return 0 if ok else 1


def main():
    if "--self-check" in sys.argv:
        sys.exit(self_check())
    ap = argparse.ArgumentParser(prog=os.path.basename(sys.argv[0]))
    ap.add_argument("--plan", required=True, metavar="JSON")
    ap.add_argument("--snapshots", metavar="DIR")
    ap.add_argument("--json", metavar="OUT")
    args = ap.parse_args()
    try:
        plan = json.load(open(args.plan))
    except (OSError, ValueError) as e:
        print("erro: plano ilegivel: %s" % e, file=sys.stderr)
        sys.exit(2)
    if plan.get("schema") != "sms_vram_plan_v1":
        print("erro: expected sms_vram_plan_v1", file=sys.stderr)
        sys.exit(2)
    blockers, alerts, metrics = audit_plan(plan)
    snap_recs = []
    if args.snapshots:
        try:
            snap_recs = check_snapshots(plan, args.snapshots)
        except OSError as e:
            print("erro: %s" % e, file=sys.stderr)
            sys.exit(2)
        for r in snap_recs:
            if "blocker" in r:
                blockers.append({"code": "divergencia_snapshot",
                                 "motivo": r["blocker"], "arquivo": r["arquivo"]})
            if "code" in r:
                blockers.append(r)
    report = {"verdict": ("reprovado" if blockers else
                          ("aprovado_com_alertas" if alerts else "aprovado")),
              "blockers": blockers, "alerts": alerts, "metrics": metrics,
              "snapshots": snap_recs}
    text = json.dumps(report, indent=2, ensure_ascii=False)
    if args.json:
        open(args.json, "w").write(text + "\n")
    print(text)
    sys.exit(1 if blockers else 0)


if __name__ == "__main__":
    main()
