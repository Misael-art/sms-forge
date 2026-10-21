#!/usr/bin/env python3
"""Teste diferencial da wave-5b: pad -> anel/tier -> comando -> papel.

O eixo diferencial e entre DUAS leituras independentes dos mesmos dados
gerados:
  - Python decode o blob CMD emitido pelo conversor (`versus_scene_runtime.h`)
    pelo contrato declarado (version, n_passos, janela, passos de 3 bytes
    [want, flags, release_time]) e, SO A PARTIR DOS BYTES, sintetiza o programa
    de pad que deve casar e os programas perturbados que nao devem;
  - o C da ROM (src/input.c + src/input_tier.c + src/fight_input.c compilados
    por gcc no host) da o veredito real.

O Python nao reimplementa a maquina de matching: ele gera ESTIMULO (ticks de
pad) e EXPECTATIVA (tick do golpe, codigo, indice na tabela, sem-rota, papel).
Se a regra de estimulo estiver errada, o C reprova e o caso falha.

Fronteira declarada: este teste mede a CAMADA de input isolada (malha aberta: o
papel volta ao controlavel a cada tick). Avanco de fisica, `done` de one-shot,
poses e dano pertencem a main.c e se comprovam na ROM.
"""
import re
import subprocess
from pathlib import Path

PROJ = Path(__file__).resolve().parents[1]
GEN = PROJ / "out/generated/ryu_ken_cross"
SRC = PROJ / "src"
INC = PROJ / "inc"
BUILD = PROJ / "out/tmp_wave5b"

ROLES = ["ST_IDLE", "ST_WALK_F", "ST_WALK_B", "ST_JUMP", "ST_CROUCH", "ST_GUARD",
         "ST_PUNCH", "ST_HP", "ST_SPECIAL", "ST_KO", "ST_KICK", "ST_HK"]
CODES = {"SPECIAL_UNSUPPORTED": 1, "HP": 2, "LP": 3, "HK": 4, "LK": 5}
K_UP, K_DOWN, K_LEFT, K_RIGHT, K_LP, K_HP = 1, 2, 4, 8, 16, 32
FI_ROLE_NONE = 255


def read_uint_define(path, name):
    txt = path.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"#define\s+%s\s+(\d+)" % re.escape(name), txt)
    if not m:
        raise SystemExit(f"define {name} ausente em {path}")
    return int(m.group(1))


ALIAS_DE = {}


def parse_blob(txt, sym, seen=()):
    """[ver, n, janela, pad] + n passos de 3 bytes -> dict do contrato.

    O conversor deduplica trilhas identicas entre os dois lados emitindo
    `#define P2_CUT_CMD_HP P1_CUT_CMD_HP`; o alias e resolvido e DECLARADO no
    relatorio (alias_de), porque e justamente o tipo de reuso que um teste nao
    pode esconder atras de um simbolo proprio.
    """
    if sym in seen:
        raise SystemExit(f"alias de blob em ciclo: {sym}")
    m = re.search(r"const unsigned char %s\[(\d+)\] = \{(.*?)\};" % re.escape(sym),
                  txt, re.S)
    if not m:
        a = re.search(r"#define\s+%s\s+(P[12]_CUT_CMD_\w+)\s*$" % re.escape(sym),
                      txt, re.M)
        if not a:
            raise SystemExit(f"blob {sym} ausente no header gerado")
        blob = parse_blob(txt, a.group(1), seen + (sym,))
        blob = dict(blob)
        blob["sym"] = sym
        blob["alias_de"] = a.group(1)
        ALIAS_DE.setdefault(sym, a.group(1))
        return blob
    size = int(m.group(1))
    data = [int(x, 16) for x in re.findall(r"0x([0-9A-Fa-f]{2})", m.group(2))]
    if len(data) != size:
        raise SystemExit(f"{sym}: {len(data)} bytes lidos, declarado {size}")
    ver, n, window = data[0], data[1], data[2]
    if ver != 4:
        raise SystemExit(f"{sym}: versao {ver} fora do contrato v4")
    if size != 4 + 3 * n:
        raise SystemExit(f"{sym}: tamanho {size} nao casa com {n} passos v4")
    steps = []
    for i in range(n):
        w, f, rt = data[4 + 3 * i: 7 + 3 * i]
        steps.append({"want": w, "flags": f, "release": rt,
                      "dir": w & 0x0F, "key": w & 0xF0,
                      "tier": (f >> 2) & 3, "hold": f & 1,
                      "release_flag": f & 2, "four_way": f & 0x10})
    return {"sym": sym, "version": ver, "n": n, "window": window, "steps": steps,
            "alias_de": None}


def program_for(blob, tier_t):
    """Programa de pad derivado so dos bytes do blob.

    Regras do contrato (inc/input.h, inc/input_tier.h):
      - passo de direcao puro: segurar a direcao exata por 2 ticks (ou
        `release_time` ticks quando o passo declara duracao de carga);
      - passo que exige soltura: um tick de pad neutro depois;
      - tier 1 (fraco): tocar 3 ticks e soltar -> pulso no 4o tick;
      - tier 2 (forte): segurar tier_t + 2 ticks -> pulso no tick tier_t - 1.
    """
    prog = []
    for st in blob["steps"]:
        if st["key"]:
            if st["tier"] == 1:
                prog += [st["key"]] * 3 + [0]
            elif st["tier"] == 2:
                prog += [st["key"]] * (tier_t + 2)
            else:
                raise SystemExit(f"{blob['sym']}: tier {st['tier']} nao tem limiar "
                                 f"na maquina (deveria falhar fechado)")
        else:
            prog += [st["dir"]] * (st["release"] or 2)
            if st["release"] or st["release_flag"]:
                prog.append(0)
        if st["hold"]:
            prog.append(prog[-1])
    return prog


def expected_tick(prog, blob, tier_t):
    """Tick (0-based) em que o C DEVE reportar o golpe."""
    last = blob["steps"][-1]
    if last["tier"] == 2:
        return (len(prog) - (tier_t + 2)) + tier_t - 1
    return len(prog) - 1


def negative_prog(prog, blob, tier_t):
    """Perturbacao do tier invertido: forte com toque curto, fraco com carga."""
    key = blob["steps"][-1]["key"]
    if not key:
        return None
    if blob["steps"][-1]["tier"] == 1:
        return [key] * (tier_t + 2) + [0]        # so gera pulso FORTE
    return [key] * 3 + [0, 0]                    # so gera pulso FRACO


def build_all_cases(gen_txt, tier_t):
    cases = []
    syms = ["P1_CUT_CMD_PUNCH", "P1_CUT_CMD_HP", "P1_CUT_CMD_KICK", "P1_CUT_CMD_HK",
            "P1_CUT_CMD_SPECIAL", "P2_CUT_CMD_HP", "P2_CUT_CMD_HK",
            "P2_CUT_CMD_SPECIAL"]
    for sym in syms:
        blob = parse_blob(gen_txt, sym)
        prog = program_for(blob, tier_t)
        side = 0 if sym.startswith("P1") else 1
        cases.append({"name": f"ring_{sym}", "mode": "ring", "side": side,
                      "blob": sym, "prog": prog,
                      "expect_tick": expected_tick(prog, blob, tier_t)})
        neg = negative_prog(prog, blob, tier_t)
        if neg:
            cases.append({"name": f"ringneg_tier_{sym}", "mode": "ring", "side": side,
                          "blob": sym, "prog": neg, "expect_tick": None})
        if blob["n"] > 1:
            mid = len(prog) // 2
            wide = prog[:mid] + [0] * (blob["window"] + 4) + prog[mid:]
            cases.append({"name": f"ringneg_window_{sym}", "mode": "ring",
                          "side": side, "blob": sym, "prog": wide,
                          "expect_tick": None})
    # cruzar os dois planos de movimento com o blob do OUTRO lutador
    p1 = parse_blob(gen_txt, "P1_CUT_CMD_SPECIAL")
    p2 = parse_blob(gen_txt, "P2_CUT_CMD_SPECIAL")
    if p1["steps"] != p2["steps"]:
        cases.append({"name": "ringneg_cross_p1prog_p2blob", "mode": "ring", "side": 1,
                      "blob": "P2_CUT_CMD_SPECIAL", "prog": program_for(p1, tier_t),
                      "expect_tick": None})
        cases.append({"name": "ringneg_cross_p2prog_p1blob", "mode": "ring", "side": 0,
                      "blob": "P1_CUT_CMD_SPECIAL", "prog": program_for(p2, tier_t),
                      "expect_tick": None})
    else:
        raise SystemExit("os dois especiais sao identicos: caso cruzado seria vacuo")

    # mesma coisa pela CAMADA, onde a TABELA decide rota e prioridade
    table = [(0, "P1_CUT_CMD_SPECIAL", CODES["SPECIAL_UNSUPPORTED"], 0),
             (0, "P1_CUT_CMD_HP", CODES["HP"], 1),
             (0, "P1_CUT_CMD_HK", CODES["HK"], 2),
             (1, "P2_CUT_CMD_SPECIAL", CODES["SPECIAL_UNSUPPORTED"], 0),
             (1, "P2_CUT_CMD_HP", CODES["HP"], 1),
             (1, "P2_CUT_CMD_HK", CODES["HK"], 2)]
    for side, sym, code, idx in table:
        blob = parse_blob(gen_txt, sym)
        prog = program_for(blob, tier_t)
        routed = code in (CODES["HP"], CODES["HK"])
        cases.append({"name": f"layer_{sym}", "mode": "layer", "side": side,
                      "prog": prog, "expect_tick": expected_tick(prog, blob, tier_t),
                      "expect_code": code, "expect_index": idx,
                      "expect_unrouted": 0 if routed else 1,
                      "expect_role": (ROLES.index("ST_HP") if code == CODES["HP"]
                                      else ROLES.index("ST_HK") if code == CODES["HK"]
                                      else FI_ROLE_NONE)})
    # os dois golpes LEVES tem padrao e dano no pacote, mas nenhuma linha na
    # tabela: a camada NAO pode inventa-los (contabilidade vive no mask)
    for sym in ["P1_CUT_CMD_PUNCH", "P1_CUT_CMD_KICK"]:
        blob = parse_blob(gen_txt, sym)
        cases.append({"name": f"layer_absent_{sym}", "mode": "layer", "side": 0,
                      "prog": program_for(blob, tier_t), "expect_tick": None,
                      "expect_code": 0, "expect_index": 255,
                      "expect_unrouted": 0, "expect_role": FI_ROLE_NONE})

    # contexto por direcao crua, nos dois faces
    idle, wf, wb, jump, crouch, guard = [ROLES.index(r) for r in
                                        ["ST_IDLE", "ST_WALK_F", "ST_WALK_B",
                                         "ST_JUMP", "ST_CROUCH", "ST_GUARD"]]
    for lv, face, role, why in [(0, 0, FI_ROLE_NONE, "neutro_sem_transicao"),
           (K_RIGHT, 0, wf, "frente_face_dir"),
           (K_LEFT, 0, wb, "tras_face_dir"),
           (K_LEFT, 1, wf, "frente_face_esq"),
           (K_RIGHT, 1, wb, "tras_face_esq"),
           (K_DOWN, 0, crouch, "baixo"),
           (K_DOWN | K_LEFT, 0, guard, "baixo_tras"),
           (K_DOWN | K_RIGHT, 1, guard, "baixo_tras_espelho"),
           (K_UP, 0, jump, "cima_no_chao"),
           (K_DOWN | K_RIGHT, 0, crouch, "baixo_frente_nao_guarda")]:
        cases.append({"name": f"context_{why}", "mode": "context", "side": 0,
                      "levels": lv, "face": face, "expect_role": role,
                      "cmode": 0})
    # soltar o direcional DESDE uma guarda tem de emitir a volta ao idle: sem
    # este caso, o 255 do neutro acima seria satisfeito pela API nunca falar.
    cases.append({"name": "context_volta_idle_desde_guarda", "mode": "context",
                  "side": 0, "levels": 0, "face": 0, "expect_role": idle,
                  "cmode": 3})
    cases.append({"name": "context_ko_terminal", "mode": "context", "side": 0,
                  "levels": K_LP, "face": 0, "expect_role": FI_ROLE_NONE,
                  "cmode": 1})
    cases.append({"name": "context_air_no_revert", "mode": "context", "side": 0,
                  "levels": 0, "face": 0, "expect_role": FI_ROLE_NONE,
                  "cmode": 2})
    return cases


C_DRIVER = r"""
/* Gerado por tests/input_wave5b_diff.py — nao editar a mào. */
#include <stdio.h>
#include <string.h>
#include "rev2_diag.h"
#include "fight_input.h"
#include "input_tier.h"
#include "versus_scene_runtime.h"
#include "fight_runtime_data.h"

static FightView view;
static FightResult res;

static unsigned short run_ring(const unsigned char *blob, unsigned char side,
                               const unsigned char *prog, unsigned char n) {
    unsigned short t;
    input_init();
    for (t = 0u; t < n; t++) {
        input_tick(side, prog[t], 0u);
        if (input_pattern_hit(side, blob)) return (unsigned short)(t + 1u);
    }
    return 0u;                       /* 0 = nenhum golpe no programa */
}

static void run_layer(unsigned char side, const unsigned char *prog,
                      unsigned char n, const char *name) {
    unsigned short t;
    input_init();
    view.role = (unsigned char)ST_IDLE;
    view.done = 0u;
    view.on_ground = 1u;
    view.alive = 1u;
    view.face = 0u;
    for (t = 0u; t < n; t++) {
        view.role = (unsigned char)ST_IDLE;      /* malha aberta */
        fight_input_step(side, &characters[side], &view, prog[t], &res);
        if (res.cmd_index != FI_CMD_NONE) {
            printf("LAYER %s tick %u code %u idx %u unrou %u role %u\n",
                   name, (unsigned)(t + 1u), (unsigned)res.cmd_code,
                   (unsigned)res.cmd_index, (unsigned)res.unrouted,
                   (unsigned)res.role);
            return;
        }
    }
    printf("LAYER %s tick 0 code 0 idx 255 unrou 0 role %u\n", name,
           (unsigned)res.role);
}

static void run_context(unsigned char side, unsigned char levels,
                        unsigned char face, unsigned char mode,
                        const char *name) {
    /* mode 0 = contexto, 1 = KO terminal, 2 = one-shot expirado no ar,
     * 3 = solta o direcional a partir de uma guarda (transicao de volta) */
    input_init();
    view.done = (mode == 2u) ? 1u : 0u;
    view.on_ground = (mode == 2u) ? 0u : 1u;
    view.alive = (mode == 1u) ? 0u : 1u;
    view.role = (mode == 2u) ? (unsigned char)ST_JUMP
                             : (mode == 1u) ? (unsigned char)ST_KO
                             : (mode == 3u) ? (unsigned char)ST_GUARD
                                            : (unsigned char)ST_IDLE;
    view.face = face;
    fight_input_step(side, &characters[side], &view, levels, &res);
    printf("CONTEXT %s role %u code %u\n", name, (unsigned)res.role,
           (unsigned)res.cmd_code);
}

int main(void) {
    printf("TIER_T %u\n", (unsigned)INPUT_TIER_T);
    printf("UNROUTED_MASK_P1 %u\n", (unsigned)fight_unrouted_mask(&characters[0]));
    printf("UNROUTED_MASK_P2 %u\n", (unsigned)fight_unrouted_mask(&characters[1]));
    printf("CMD_COUNT_P1 %u\n", (unsigned)characters[0].command_count);
    printf("CMD_COUNT_P2 %u\n", (unsigned)characters[1].command_count);

%RING_CASES%

%LAYER_CASES%

%CONTEXT_CASES%

    /* IA em malha aberta: niveis do plano passam pelo MESMO anel/tier/tabela */
    {
        unsigned char side;
        for (side = 0u; side < 2u; side++) {
            unsigned short f;
            unsigned char hits = 0u, unr = 0u, roles = 0u;
            input_init();
            for (f = 0u; f < 600u; f++) {
                unsigned char beat = 0u;
                unsigned char lv = fight_input_ai_levels(f, side, &beat);
                view.role = (unsigned char)ST_IDLE;
                view.done = 0u;
                view.on_ground = 1u;
                view.alive = 1u;
                view.face = side;
                fight_input_step(side, &characters[side], &view, lv, &res);
                if (res.cmd_index != FI_CMD_NONE) {
                    hits++;
                    if (res.unrouted) unr++;
                    printf("AIEV %u tick %u beat %u code %u idx %u unrou %u\n",
                           side, (unsigned)(f + 1u), (unsigned)beat,
                           (unsigned)res.cmd_code, (unsigned)res.cmd_index,
                           (unsigned)res.unrouted);
                }
                if (res.role != FI_ROLE_NONE) roles++;
            }
            printf("AI_SUMMARY side %u cmds %u unrou %u roles %u\n",
                   (unsigned)side, (unsigned)hits, (unsigned)unr, (unsigned)roles);
        }
    }

    {
        unsigned short f;
        unsigned char diff = 0u;
        for (f = 0u; f < 600u; f++) {
            unsigned char b1 = 0u, b2 = 0u;
            unsigned char l1 = fight_input_ai_levels(f, 0u, &b1);
            unsigned char l2 = fight_input_ai_levels(f, 0u, &b2);
            if (l1 != l2 || b1 != b2) diff = 1u;
        }
        printf("AI_PURE %u\n", (unsigned)diff);
    }
    return 0;
}
"""


def c_array(vals):
    return "{" + ",".join(str(v) for v in vals) + "}"


def emit_cases(cases):
    ring, layer, ctx = [], [], []
    for i, c in enumerate(cases):
        if c["mode"] == "ring":
            ring.append(f'    {{ static const unsigned char p{i}[] = '
                        f'{c_array(c["prog"])};\n'
                        f'      printf("RING {c["name"]} hit %u\\n", '
                        f'(unsigned)run_ring({c["blob"]}, {c["side"]}, p{i}, '
                        f'{len(c["prog"])}u)); }}')
        elif c["mode"] == "layer":
            layer.append(f'    {{ static const unsigned char q{i}[] = '
                         f'{c_array(c["prog"])};\n'
                         f'      run_layer({c["side"]}, q{i}, {len(c["prog"])}u, '
                         f'"{c["name"]}"); }}')
        else:
            ctx.append(f'    run_context({c["side"]}, {c["levels"]}u, {c["face"]}u, '
                       f'{c["cmode"]}u, "{c["name"]}");')
    return "\n".join(ring), "\n".join(layer), "\n".join(ctx)


def parse(lines):
    scalars, ring, layer, ctx, aiev, summ = {}, {}, {}, {}, {}, {}
    for ln in lines:
        p = ln.split()
        if not p:
            continue
        if p[0] in ("TIER_T", "UNROUTED_MASK_P1", "UNROUTED_MASK_P2",
                    "CMD_COUNT_P1", "CMD_COUNT_P2", "AI_PURE"):
            scalars[p[0]] = int(p[1])
        elif p[0] == "RING":
            ring[p[1]] = int(p[3]) or None
        elif p[0] == "LAYER":
            kv = dict(zip(p[2::2], p[3::2]))
            d = {k: int(v) for k, v in kv.items()}
            d["tick"] = d["tick"] or None      # 0 = nenhum golpe no programa
            layer[p[1]] = d
        elif p[0] == "CONTEXT":
            kv = dict(zip(p[2::2], p[3::2]))
            ctx[p[1]] = int(kv["role"])
        elif p[0] == "AIEV":
            kv = dict(zip(p[2::2], p[3::2]))
            aiev.setdefault(p[1], []).append((int(kv["tick"]), int(kv["beat"]),
                                              int(kv["code"]), int(kv["unrou"])))
        elif p[0] == "AI_SUMMARY":
            kv = dict(zip(p[3::2], p[4::2]))
            summ[p[2]] = {k: int(v) for k, v in kv.items()}
    return scalars, ring, layer, ctx, aiev, summ


def main():
    if not GEN.is_dir():
        raise SystemExit(f"pacote gerado ausente: {GEN}")
    tier_t = read_uint_define(INC / "input_tier.h", "INPUT_TIER_T")
    gen_txt = (GEN / "versus_scene_runtime.h").read_text(encoding="utf-8",
                                                          errors="replace")
    cases = build_all_cases(gen_txt, tier_t)
    r, l, x = emit_cases(cases)
    driver = C_DRIVER.replace("%RING_CASES%", r).replace("%LAYER_CASES%", l)\
                     .replace("%CONTEXT_CASES%", x)

    BUILD.mkdir(parents=True, exist_ok=True)
    (BUILD / "driver.c").write_text(driver, encoding="utf-8")
    exe = BUILD / "wave5b_diff"
    cc = subprocess.run(["gcc", "-Wall", "-std=c99", "-I", str(INC), "-I", str(GEN),
                         "-o", str(exe), str(BUILD / "driver.c"),
                         str(SRC / "input.c"), str(SRC / "input_tier.c"),
                         str(SRC / "fight_input.c")],
                        capture_output=True, text=True)
    if cc.returncode != 0:
        print(cc.stdout + cc.stderr)
        raise SystemExit("compilacao do driver falhou")
    if cc.stderr.strip():
        print("[aviso gcc no host]", cc.stderr.strip())

    run = subprocess.run([str(exe)], capture_output=True, text=True)
    if run.returncode != 0:
        raise SystemExit(f"driver saiu com {run.returncode}\n{run.stdout}\n{run.stderr}")
    lines = [ln for ln in run.stdout.splitlines() if ln.strip()]
    (BUILD / "last_stdout.txt").write_text(run.stdout, encoding="utf-8")
    scalars, ring, layer, ctx, aiev, summ = parse(lines)

    fails = []
    if scalars.get("TIER_T") != tier_t:
        fails.append(f"TIER_T {scalars.get('TIER_T')} != header {tier_t}")
    for side in ("P1", "P2"):
        if scalars.get(f"UNROUTED_MASK_{side}") != 0x05:
            fails.append(f"unrouted_mask {side} = {scalars.get(f'UNROUTED_MASK_{side}')} "
                         f"!= 0x05 (LP|LK sem rota)")
        if scalars.get(f"CMD_COUNT_{side}") != 3:
            fails.append(f"command_count {side} != 3")
    if scalars.get("AI_PURE") != 0:
        fails.append("fight_input_ai_levels nao e pura em (frame, face)")

    for c in cases:
        if c["mode"] == "ring":
            got = ring.get(c["name"])
            exp = None if c["expect_tick"] is None else c["expect_tick"] + 1
            if got != exp:
                fails.append(f"{c['name']}: hit {got} != esperado {exp}")
        elif c["mode"] == "layer":
            got = layer.get(c["name"])
            if not got:
                fails.append(f"{c['name']}: sem saida")
                continue
            exp_tick = None if c["expect_tick"] is None else c["expect_tick"] + 1
            if got["tick"] != exp_tick:
                fails.append(f"{c['name']}: tick {got['tick']} != {exp_tick}")
            if exp_tick is not None:
                for k, want in (("code", c["expect_code"]), ("idx", c["expect_index"]),
                                ("unrou", c["expect_unrouted"]), ("role", c["expect_role"])):
                    if got[k] != want:
                        fails.append(f"{c['name']}: {k} {got[k]} != {want}")
        else:
            got = ctx.get(c["name"])
            if got is None:
                fails.append(f"{c['name']}: sem saida")
            elif got != c["expect_role"]:
                fails.append(f"{c['name']}: role {got} != {c['expect_role']}")

    # IA: dois ciclos de 300 frames por lado -> 2 HP + 2 HK roteados e 2
    # especiais sem rota; e o movimento que casa o especial tem de ser o do
    # PROPRIO lado (beat 10 para P1, beat 11 para P2).
    for side in ("0", "1"):
        s = summ.get(side)
        if not s:
            fails.append(f"IA lado {side}: sem sumario")
            continue
        if s["cmds"] != 6 or s["unrou"] != 2:
            fails.append(f"IA lado {side}: cmds {s['cmds']} unrou {s['unrou']} != 6/2")
        if s["roles"] == 0:
            fails.append(f"IA lado {side}: nenhum papel decidido pelo plano")
        ev = aiev.get(side, [])
        # batidas de movimento: dentro de QUALQUER ciclo de 300 frames, o par
        # de ticks >= 250 e o MOTION_A (beat 10) / MOTION_B (beat 11)
        motion = [e for e in ev if (e[0] - 1) % 300 >= 250]
        esperado_beat = 10 if side == "0" else 11
        got_beats = sorted({e[1] for e in motion})
        if got_beats != [esperado_beat]:
            fails.append(f"IA lado {side}: beats de movimento com golpe {got_beats} "
                         f"!= [{esperado_beat}]")
        routed = {e[2] for e in ev if e[3] == 0}
        if routed != {CODES["HP"], CODES["HK"]}:
            fails.append(f"IA lado {side}: codigos roteados {sorted(routed)} != [2,4]")

    n_ring = sum(1 for c in cases if c["mode"] == "ring")
    n_layer = sum(1 for c in cases if c["mode"] == "layer")
    n_ctx = sum(1 for c in cases if c["mode"] == "context")
    print(f"casos: anel={n_ring} camada={n_layer} contexto={n_ctx} "
          f"(+2x600 frames de IA, tier_t={tier_t})")
    if ALIAS_DE:
        print("alias declarados pelo conversor (simbolo proprio, bytes emprestados):")
        for k, v in sorted(ALIAS_DE.items()):
            print(f"  - {k} -> {v}")
    if fails:
        print("FALHAS:")
        for f in fails:
            print("  -", f)
        print(f"(stdout completo em {BUILD / 'last_stdout.txt'})")
        raise SystemExit(f"{len(fails)} falha(s) diferenciais")
    print(f"[PASS] {len(cases)} casos + IA pura e roteada; mask P1/P2 = 0x05; "
          f"especial reconhecido e CONTADO como sem-rota, nao sacrificado")


if __name__ == "__main__":
    main()
