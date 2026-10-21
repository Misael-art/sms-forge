#!/usr/bin/env python3
"""Wave-5b: prova CAUSAL da camada de input na ROM (Emulicious, sessao privada).

Cadeia afirmada, leitura por leitura:

  pad injetado -> probe_keys_raw / probe_levels_p1   (mapeamento de bit)
  -> anel + maquina de tier                          (contadores por lado)
  -> cmd_hits / cmd_unrouted / cmd_last_index        (papel de golpe, rota)
  -> role_changes + probe_b_role_p1                  (papel assumido)
  -> clsn_checks                                     (a pose tem hitbox avaliada)
  -> hit/guard/damage/life/KO                        (consequencia na simulacao)

UNIDADE DE TEMPO -- foi o defeito deste harness antes de ser medido. O `step` da
ponte NAO e o frame da ROM: na sessao de 2026-10-17 o contador proprio do
programa (probe_frame) avancou ~1 a cada 2 frames injetados. Orcamentos escritos
em steps produzem presses mais curtas que o limiar de tier (T=6) e esperas mais
curtas que o arco de golpe (medido em ~46-48 ticks em S_HIT, durante o qual o
gate de comando de fight_input.c esta legitimamente fechado). Isso foi lido como
"humano nunca acha rota" -- era ausencia de oportunidade, nao de rota.
Todo orcamento daqui e declarado em frames DA ROM e conferido contra
probe_frame; o step injetado e meio, nao unidade. A calibracao sai no relatorio
como bridge_steps_per_rom_frame.

Nada aqui escreve na ROM: o bridge so faz peek (self-check do wrapper o garante).
A IA do lado 1 nao recebe pad: os niveis dela vem de fight_input_ai_levels e
percorrem o MESMO input_tick/tier/anel/tabela, o que faz da contagem de comando
dela evidencia de caminho, nao de dano direto.

QUATRO RELOGIOS (secao Z): frames de VDP ackados pela ponte (`step` = 1
fronteira de frame), contador logico da ROM (`probe_frame`), limites de
animacao (`role_changes` -- proxy DECLARADO, a sonda nao expoe fidx) e relogio
de parede. Alem deles, D2 mede os deadlines input->rota->papel->apresentacao
(clsn)->consequencia (dano) em steps VDP E frames da ROM, com a resolucao de
leitura declarada.

PIN: a identidade da ROM e entrada congelada (`--expect-sha`, vinda do freeze
ou do coordenador); sem pin o relatorio sai `unpinned`, e pin divergente
recusa a sessao antes de abrir qualquer emulador. O default de saida e por
corrida (`out/logs/runs/<UTC>_wave5b_rom_causal_<sha12>.json`) e relatorio
existente nunca e sobrescrito sem `--force`: relatorios velhos ficam intactos.

Diagnostico. Nao promove FPS, audio, qualidade visual nem entrega.
"""
import argparse, datetime, hashlib, json, shutil, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJ = HERE.parent
WS = PROJ.parents[1]
sys.path.insert(0, str(WS / "tools" / "sms_wrapper"))

from session_bridge.isolated import start, request, close_session  # noqa: E402

BASE = 0xC800
SPAN = 0x100         # corredor medido inteiro: 0xC800..0xC8FB

# offset, largura, nome logico. Derivado do .map pos-link (audit_probe_corridor
# confirma o corredor); qualquer troca de layout sem atualizar aqui quebra o
# self-check abaixo, nao o veredito.
LAYOUT = [
    (0x00, 2, "magic"), (0x02, 2, "schema"), (0x04, 2, "frame"),
    (0x06, 2, "step"), (0x18, 2, "disp_p1"), (0x1A, 2, "disp_p2"),
    (0x26, 2, "hit_events"), (0x28, 2, "guard_events"),
    (0x2A, 2, "damage_p1"), (0x2C, 2, "damage_p2"),
    (0x2E, 2, "life_p1"), (0x30, 2, "life_p2"),
    (0x32, 2, "hitstop_frames"), (0x34, 2, "ko_events"),
    (0x36, 2, "clsn_checks"), (0x38, 2, "pusher_frames"),
    (0x3A, 2, "face_flips"), (0x3C, 2, "x_p1"), (0x3E, 2, "x_p2"),
    (0x40, 2, "face_p1"), (0x42, 2, "face_p2"),
    (0x44, 1, "levels_p1"), (0x45, 1, "levels_p2"),
    (0x46, 2, "keys_raw"),
    (0x48, 2, "cmd_hits_p1"), (0x4A, 2, "cmd_hits_p2"),
    (0x4C, 2, "cmd_unrouted_p1"), (0x4E, 2, "cmd_unrouted_p2"),
    (0x50, 2, "input_frames_p1"), (0x52, 2, "input_frames_p2"),
    (0x54, 2, "role_changes_p1"), (0x56, 2, "role_changes_p2"),
    (0x58, 1, "cmd_route_count"), (0x59, 1, "cmd_unrouted_mask"),
    (0x5A, 1, "tier_t"), (0x5B, 1, "ai_beat"),
    (0x5C, 2, "cmd_last_index_p1"), (0x5E, 2, "cmd_last_index_p2"),
]

# Borda util declarada no runtime (DIAG_X_MIN/MAX em src/main.c). A sonda e o
# pixel inteiro: main.c grava fighter[s].x >> 8, nao o Q8.8.
X_MIN_PX, X_MAX_PX = 16, 240
K_UP, K_DOWN, K_LEFT, K_RIGHT, K_LP, K_HP = 1, 2, 4, 8, 0x10, 0x20

# Paapis controlaveis no chao, por autoridade dupla: o enum ST_* de
# inc/rev2_diag.h e as flags da tabela gerada (p1_states: IDLE/WALK_F/WALK_B
# = S_CONTROL, CROUCH/GUARD = S_CONTROL|S_BLOCKABLE, JUMP = S_AIR, golpes =
# S_HIT, KO = 0). O gate de comando so roda dentro desse conjunto.
CONTROLABLE = (0, 1, 2, 4, 5)
# Enum COMPLETO do contrato (inc/rev2_diag.h:57-61). A secao C agora afirma o
# papel EXATO por contexto (tabela de context_role em fight_input.c:44-56), nao
# so "mudou de papel": um offset errado nao tem como passar por acidente.
(ST_IDLE, ST_WALK_F, ST_WALK_B, ST_JUMP, ST_CROUCH, ST_GUARD, ST_PUNCH,
 ST_HP, ST_SPECIAL, ST_KO, ST_KICK, ST_HK) = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11)
# Dano por papel, lido da mesma tabela gerada (StateDef.dmg): prova de que o
# drive de KO tem orcamento de ticks suficiente, nao aposta.
HP_DMG, HK_DMG, MAX_LIFE = 112, 119, 1000

# Medida na ROM (trace frame a frame, sessao 2026-10-17): o FORTE casa no 6o
# tick consecutivo segurado e o papel fica em S_HIT por ~46-48 ticks antes de
# expirar para o controlavel. Pressar dentro desse arco nao e rota ausente --
# e o gate fechado por design.
TIER_TICKS = 6
PUNCH_ANIM_TICKS = 48


def decode(block):
    out = {}
    for off, size, name in LAYOUT:
        if size == 1:
            out[name] = block[off]
        else:
            out[name] = block[off] | (block[off + 1] << 8)
    out["role_p1"] = block[0xFB]            # espelho byte do papel (0xC8FB)
    return out


def self_check():
    """O decodificador e a afirmação mais barata deste teste: sem ele um offset
    errado produziria verde sobre lixo."""
    blk = [0] * SPAN
    blk[0x00], blk[0x01] = 0x32, 0x52               # magic 0x5232
    blk[0x04], blk[0x05] = 0x34, 0x12               # frame 0x1234
    blk[0x44] = 0x0A                                 # levels_p1
    blk[0x48], blk[0x49] = 0x07, 0x01               # cmd_hits_p1 = 0x0107
    blk[0x58] = 3; blk[0x59] = 0x05; blk[0x5A] = 6; blk[0x5B] = 11
    d = decode(blk)
    assert d["magic"] == 0x5232, d["magic"]
    assert d["frame"] == 0x1234, d["frame"]
    assert d["levels_p1"] == 0x0A
    assert d["cmd_hits_p1"] == 0x0107
    assert (d["cmd_route_count"], d["cmd_unrouted_mask"], d["tier_t"], d["ai_beat"]) == (3, 5, 6, 11)
    # larguras nao sobrepostas: cada sonda ocupa exatamente o seu par de bytes
    for (o1, s1, n1), (o2, s2, n2) in zip(LAYOUT, LAYOUT[1:]):
        assert o1 + s1 <= o2, f"{n1} invade {n2}"
    # injecao do pad e o mask que a ROM deve ecoar (bit a bit)
    assert [K_UP, K_DOWN, K_LEFT, K_RIGHT, K_LP, K_HP] == [1, 2, 4, 8, 16, 32]
    # os papis que o settle aceita: chao + controlavel. JUMP(3, S_Air) e golpe
    # (S_HIT) e KO(9) ficam fora; se o enum mudar de ordem, o teste para aqui.
    assert len(set(CONTROLABLE)) == 5 and 3 not in CONTROLABLE and ST_KO not in CONTROLABLE
    assert ST_HP != ST_HK
    # papéis de contexto EXATOS (afirmados na secao C): a ordem deste assert e
    # a ordem do enum; um shift de enum quebra aqui, nao no veredito.
    assert (ST_IDLE, ST_WALK_F, ST_WALK_B, ST_JUMP, ST_CROUCH, ST_GUARD,
            ST_PUNCH, ST_HP, ST_SPECIAL, ST_KO, ST_KICK, ST_HK) == \
           (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11)
    # deadlines: funcao pura exercitada com amostras sinteticas (um offset de
    # 1 tick na rota tem que aparecer no delta, nao sumir em arredondamento).
    b_syn = {"bridge_steps": 100, "frame": 50, "cmd_hits_p1": 3,
             "clsn_checks": 10, "damage_p2": 200, "role_p1": ST_IDLE}
    samples_syn = [
        {"bridge_steps": 102, "rom_frame": 51, "cmd": 3, "role": ST_IDLE, "clsn": 10, "dmg2": 200},
        {"bridge_steps": 104, "rom_frame": 52, "cmd": 4, "role": ST_IDLE, "clsn": 10, "dmg2": 200},
        {"bridge_steps": 106, "rom_frame": 53, "cmd": 4, "role": ST_HP,   "clsn": 10, "dmg2": 200},
        {"bridge_steps": 108, "rom_frame": 54, "cmd": 4, "role": ST_HP,   "clsn": 11, "dmg2": 200},
        {"bridge_steps": 110, "rom_frame": 55, "cmd": 4, "role": ST_HP,   "clsn": 11, "dmg2": 312},
    ]
    dl = compute_deadlines(b_syn, samples_syn, {"bridge_steps": 100, "frame": 50})
    assert dl["input_to_route"] == {"vdp_steps": 4, "rom_frames": 2}, dl
    assert dl["input_to_action"] == {"vdp_steps": 6, "rom_frames": 3}, dl
    assert dl["input_to_presentation"] == {"vdp_steps": 8, "rom_frames": 4}, dl
    assert dl["input_to_consequence"] == {"vdp_steps": 10, "rom_frames": 5}, dl
    assert dl["action_to_presentation"] == {"vdp_steps": 2, "rom_frames": 1}, dl
    # orcamento do drive de KO: com 112 de dano por HP forte, 1000 de vida pede
    # no minimo 9 acertos -- menos de 9 iteracoes no drive seria expectativa falsa.
    assert -(-MAX_LIFE // HP_DMG) == 9 and -(-MAX_LIFE // HK_DMG) == 9
    # unidade de tempo: limiar de tier e arco de golpe sao grandezas DA ROM. Se
    # o arco nao couber no settle, as pressoes cairiam no gate fechado e o
    # harness voltaria a mentir.
    assert d["tier_t"] == TIER_TICKS == 6, d["tier_t"]
    assert PUNCH_ANIM_TICKS > TIER_TICKS
    assert PUNCH_ANIM_TICKS + 12 <= 90, "settle nao cobre a expiracao do golpe"
    print("[SELF-CHECK OK] decodificador + bits do pad + papis + unidade de tempo")
    return 0


def compute_deadlines(b, samples, anchor):
    """Deadlines da pressa D2 a partir da serie de amostras (funcao pura).

    `b` e a leitura-baseline; `samples` sao leituras apos cada chunk; `anchor`
    e o carimbo (bridge_steps, frame) do baseline. Devolve deltas em steps VDP
    e frames DA ROM; None quando a cadeia nao completou dentro do teto. A
    resolucao e a do chunk de amostragem (declarada no relatorio).
    """
    def first(pred):
        return next((s for s in samples if pred(s)), None)

    route = first(lambda s: s["cmd"] > b["cmd_hits_p1"])
    role = first(lambda s: s["role"] == ST_HP)
    pres = first(lambda s: s["clsn"] > b["clsn_checks"])
    dmg = first(lambda s: s["dmg2"] > b["damage_p2"])

    def since(s):
        if s is None:
            return None
        return {"vdp_steps": s["bridge_steps"] - anchor["bridge_steps"],
                "rom_frames": (s["rom_frame"] - anchor["frame"]) & 0xFFFF}

    def between(x, y):
        if x is None or y is None:
            return None
        return {"vdp_steps": y["bridge_steps"] - x["bridge_steps"],
                "rom_frames": (y["rom_frame"] - x["rom_frame"]) & 0xFFFF}

    return {
        "input_to_route": since(route),
        "input_to_action": since(role),
        "input_to_presentation": since(pres),
        "input_to_consequence": since(dmg),
        "action_to_presentation": between(role, pres),
        "presentation_to_consequence": between(pres, dmg),
    }


def copy_custody(session_root, dest):
    """Custodia da sessao privada: estado/journal copiados para fora do
    diretorio efemero (/tmp), com hash de cada arquivo copiado."""
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    copied = {}
    for name in ("session.json", "commands.jsonl", "supervisor.log",
                 "emulator.log", "ready.json"):
        src = Path(session_root) / name
        if src.is_file():
            shutil.copy2(src, dest / name)
            copied[name] = hashlib.sha256((dest / name).read_bytes()).hexdigest()
    return copied


class Rig:
    """O relogio do teste e o probe_frame da ROM, nunca o step da ponte.

    `hold` garante o orcamento: se a ponte avancar mais devagar que a razao
    calibrada, ela completa em chunks ate a ROM contar os ticks pedidos. O
    contrato do orcamento fica assim independente da velocidade de emulacao.
    """

    def __init__(self, session):
        self.s = session
        self.bridge_steps = 0     # meio injetado
        self.rom_ticks = 0        # unidade observada
        self.ratio = None
        self.chunk = 2

    def step(self, n):
        request(self.s, "step", n)
        self.bridge_steps += n

    def pad(self, p1):
        request(self.s, "input", p1, 0, 0)

    def read(self):
        p = decode(request(self.s, "read", BASE, SPAN)["ram"])
        p["bridge_steps"] = self.bridge_steps   # relogio VDP no momento da leitura
        return p

    def calibrate(self):
        """Quantos steps da ponte valem um frame da ROM. Diagnostico, nao fix."""
        f0 = self.read()["frame"]
        self.step(100)
        adv = (self.read()["frame"] - f0) & 0xFFFF
        self.ratio = round(100 / adv, 3) if adv else None
        self.chunk = max(1, min(8, int(round(self.ratio)) if self.ratio else 2))
        return adv

    def hold(self, p1, ticks):
        """Mantem `p1` por PELO MENOS `ticks` frames contados pela ROM."""
        self.pad(p1)
        est = max(1, int(round(ticks * (self.ratio if self.ratio else 2))))
        f0 = self.read()["frame"]
        self.step(est)
        spent = est
        limit = 8 * (ticks + 4)
        while True:
            p = self.read()
            adv = (p["frame"] - f0) & 0xFFFF
            if adv >= ticks or spent > limit:
                self.rom_ticks += adv
                return p
            self.step(self.chunk)
            spent += self.chunk

    def settle(self, max_ticks=90):
        """Espera o humano voltar a um papel controlavel no chao.

        Nao e conforto de script: o gate em fight_input.c so considera comando
        com (flags & S_CONTROL) && on_ground, e um pulo NAO reverte no ar (a
        fonte nao traz estado aereo alcancavel). Devolve a ultima leitura.
        """
        p = self.read()
        spent = 0
        while p["role_p1"] not in CONTROLABLE and spent < max_ticks:
            p = self.hold(0, 6)
            spent += 6
        return p

    @staticmethod
    def dirs(p):
        return (K_RIGHT, K_LEFT) if p["face_p1"] == 0 else (K_LEFT, K_RIGHT)

    def approach(self, gap_px, max_ticks=90):
        """Fecha a distancia andando na direcao que reduz |gap|."""
        p = self.read()
        spent = 0
        while spent < max_ticks:
            gap = p["x_p2"] - p["x_p1"]
            if abs(gap) <= gap_px:
                return p
            p = self.hold(K_RIGHT if gap > 0 else K_LEFT, 6)
            spent += 6
        return p

    def strong_press(self, key, ticks=TIER_TICKS + 2):
        """Pressao FORTE: segura alem do limiar T com a tecla ainda no anel.

        Devolve (leitura apos soltar, rotas, sem_rota, ultimo_indice, papel_sob_
        pressao, baseline). O papel e lido com o pad ainda segurado porque a
        expiracao para o controlavel vem ~48 ticks depois.
        """
        p = self.settle()
        b = p
        p = self.hold(key, ticks)
        fired = p["cmd_hits_p1"] - b["cmd_hits_p1"]
        unr = p["cmd_unrouted_p1"] - b["cmd_unrouted_p1"]
        idx = p["cmd_last_index_p1"]
        role = p["role_p1"]
        p = self.hold(0, 2)
        return p, fired, unr, idx, role, b

    def trace_press(self, key, max_rom_ticks=180, chunk=2):
        """Pressa instrumentada para os deadlines (D2): amostra a ROM a cada
        `chunk` steps ate a cadeia completa (papel de golpe + clsn avaliada +
        dano) ou o teto. A resolucao e a do chunk -- declarada no relatorio,
        nunca prometida abaixo dela."""
        b = self.read()
        self.pad(key)
        samples, guard = [], 0
        while True:
            self.step(chunk)
            p = self.read()
            adv = (p["frame"] - b["frame"]) & 0xFFFF
            samples.append({"bridge_steps": p["bridge_steps"], "rom_frame": p["frame"],
                            "adv": adv, "cmd": p["cmd_hits_p1"], "role": p["role_p1"],
                            "clsn": p["clsn_checks"], "dmg2": p["damage_p2"]})
            if (p["role_p1"] == ST_HP and p["clsn_checks"] > b["clsn_checks"]
                    and p["damage_p2"] > b["damage_p2"]):
                break
            if adv >= max_rom_ticks or guard > 400:
                break
            guard += 1
        self.pad(0)
        return b, samples


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", default=None,
                    help="diretorio do projeto (default: o que contem este teste)")
    ap.add_argument("--rom", default=None,
                    help="ROM sob teste (default: <project>/out/rom/luta_mugem_rev2.sms)")
    ap.add_argument("--expect-sha", default=None,
                    help="pin congelado da ROM; sem ele o relatorio sai 'unpinned'")
    ap.add_argument("--out", default=None,
                    help="caminho do relatorio (default por corrida em out/logs/runs/)")
    ap.add_argument("--force", action="store_true",
                    help="sobrescrever relatorio existente (nunca usado em relatorio velho)")
    ap.add_argument("--self-check", action="store_true")
    ap.add_argument("--xvfb", default=None)
    ap.add_argument("--ecj", default=None)
    a = ap.parse_args()
    if a.self_check:
        return self_check()

    project = Path(a.project).resolve() if a.project else PROJ
    rom = Path(a.rom).resolve() if a.rom else (project / "out/rom/luta_mugem_rev2.sms")
    rom_sha = hashlib.sha256(rom.read_bytes()).hexdigest()
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = (Path(a.out) if a.out else
                project / "out/logs/runs" / f"{stamp}_wave5b_rom_causal_{rom_sha[:12]}.json")

    def write_report(rep):
        out_path.parent.mkdir(parents=True, exist_ok=True)
        if out_path.exists() and not a.force:
            print(f"[refuse] {out_path} exists; old reports are never overwritten (--force)")
            return False
        out_path.write_text(json.dumps(rep, indent=1, ensure_ascii=False))
        return True

    if a.expect_sha and rom_sha != a.expect_sha:
        rep = {"schema": 3, "onda": "wave5b-input-causal-rom",
               "status": "refused_rom_identity", "rom": str(rom), "rom_sha256": rom_sha,
               "expected_sha256": a.expect_sha, "aprovado": False, "cases": [],
               "motivo": "pin congelado nao bate: nenhuma sessao foi aberta (frozen input)"}
        write_report(rep)
        print(f"[REFUSE] ROM {rom_sha[:12]} != pin {a.expect_sha[:12]}; sessao nao iniciada")
        return 2

    cases, session, meta, rig = [], None, {}, None
    p_start = None
    deadlines, clocks, custody = None, None, {}
    t0 = time.time()

    def chk(name, ok, **ev):
        cases.append({"case": name, "ok": bool(ok), **ev})
        print(("  PASS " if ok else "  FAIL ") + name + "  " +
              " ".join(f"{k}={v}" for k, v in ev.items()))
        return ok

    try:
        session = start(rom, a.xvfb, a.ecj, ttl=2400, enable_audio=False)
        rig = Rig(session)
        meta = json.loads((Path(session) / "session.json").read_text())
        adv100 = rig.calibrate()
        print(f"[clock] 100 steps da ponte -> {adv100} frames da ROM "
              f"(ratio {rig.ratio}, chunk {rig.chunk})")
        p_start = rig.read()   # relogio 0 dos quatro contadores do run

        # ---- A. boot: contrato de input + unidade de tempo -----------------
        p = rig.hold(0, 120)
        chk("A_boot_contrato", p["magic"] == 0x5232 and p["schema"] == 1
            and p["cmd_route_count"] == 3 and p["cmd_unrouted_mask"] == 0x05
            and p["tier_t"] == TIER_TICKS,
            magic=hex(p["magic"]), rotas=p["cmd_route_count"],
            mask=hex(p["cmd_unrouted_mask"]), tier_t=p["tier_t"])
        chk("A_anel_dos_dois_lados_cada_frame",
            p["input_frames_p1"] == p["input_frames_p2"] > 0,
            p1=p["input_frames_p1"], p2=p["input_frames_p2"])
        # A firma real do orcamento: hold(20) entregou >= 20 frames DA ROM, seja
        # qual for a velocidade de emulacao. O ratio fica no relatorio.
        q = rig.hold(0, 20)
        chk("A_orcamento_e_em_frames_da_rom",
            1.0 <= (rig.ratio or 0) <= 3.0
            and ((q["frame"] - p["frame"]) & 0xFFFF) >= 20,
            bridge_steps_per_rom_frame=rig.ratio,
            frames_rom_entregues=(q["frame"] - p["frame"]) & 0xFFFF)
        p = q

        # ---- B. controle: humano parado nao produz nada --------------------
        b0 = p
        p = rig.hold(0, 300)
        d_role = p["role_changes_p1"] - b0["role_changes_p1"]
        d_hits1 = p["cmd_hits_p1"] - b0["cmd_hits_p1"]
        d_unr1 = p["cmd_unrouted_p1"] - b0["cmd_unrouted_p1"]
        chk("B_zero_input_zero_rota_humana",
            d_role == 0 and d_hits1 == 0 and d_unr1 == 0
            and p["levels_p1"] == 0 and p["keys_raw"] == 0,
            levels=p["levels_p1"], keys=hex(p["keys_raw"]))
        d_hits2 = p["cmd_hits_p2"] - b0["cmd_hits_p2"]
        d_unr2 = p["cmd_unrouted_p2"] - b0["cmd_unrouted_p2"]
        d_dmg1 = p["damage_p1"] - b0["damage_p1"]
        chk("B_IA_rota_pelo_mesmo_caminho", d_hits2 + d_unr2 > 0,
            cmds_p2=d_hits2 + d_unr2, hits=d_hits2, unrout=d_unr2,
            beat=p["ai_beat"])
        chk("B_IA_dano_alcancado", d_dmg1 > 0, dmg_p1_delta=d_dmg1,
            life_p1=p["life_p1"])
        chk("B_IA_nao_escreve_por_fora_do_input",
            d_dmg1 == 0 or (d_hits2 + d_unr2) > 0,
            dmg_delta=d_dmg1, cmds_p2=d_hits2 + d_unr2,
            nota="dano da IA so existe acompanhado de casamento de rota")

        # ---- C. contexto: papel EXATO por direcao crua (tabela de context_role)
        fwd, back = rig.dirs(p)
        for why, mask, expect in (("frente", fwd, ST_WALK_F),
                                  ("tras", back, ST_WALK_B),
                                  ("baixo", K_DOWN, ST_CROUCH),
                                  ("baixo_tras_guarda", K_DOWN | back, ST_GUARD),
                                  ("baixo_frente", K_DOWN | fwd, ST_CROUCH),
                                  ("cima_pulo", K_UP, ST_JUMP)):
            b = p
            p = rig.hold(mask, 3)
            d = p["role_changes_p1"] - b["role_changes_p1"]
            chk(f"C_contexto_{why}", p["levels_p1"] == mask and p["role_p1"] == expect
                and d >= 1,
                mask=hex(mask), eco=p["levels_p1"], papel=p["role_p1"], esperado=expect,
                delta_role=d, face=p["face_p1"])
            p = rig.hold(0, 10)
        p = rig.settle()

        # ---- D. golpe forte humano: rota -> papel -> hitbox -> dano --------
        # Blob P1_CUT_CMD_HP = {v4, n=1, janela 1, _, 0x10, 0x08, 0}: passo
        # unico S_K1 com tier 2 (FORTE), i.e. segurar a tecla 1 ate o limiar T(6)
        # com a tecla ainda no anel. K_LP e a tecla 1.
        p = rig.approach(48)
        p, fired, unr, idx, role_press, b = rig.strong_press(K_LP)
        chk("D_forte_humano_acha_rota", fired >= 1 and idx == 1 and unr == 0,
            cmds=fired, last_index=idx, sem_rota=unr,
            tier_ticks=TIER_TICKS, orcamento_pressao=TIER_TICKS + 2)
        chk("D_rota_vira_papel_de_golpe", role_press == ST_HP,
            papel_sob_pressao=role_press, st_hp=ST_HP)
        p_after = rig.hold(0, PUNCH_ANIM_TICKS + 12)
        chk("D_pose_com_hitbox_avaliada",
            p_after["clsn_checks"] - b["clsn_checks"] >= 1,
            clsn_checks_delta=p_after["clsn_checks"] - b["clsn_checks"],
            hit_delta=p_after["hit_events"] - b["hit_events"],
            guard_delta=p_after["guard_events"] - b["guard_events"])
        chk("D_dano_na_cadeia_do_humano",
            p_after["damage_p2"] - b["damage_p2"] > 0,
            dmg_p2_delta=p_after["damage_p2"] - b["damage_p2"],
            life_p2=p_after["life_p2"], hp_dmg_tabela=HP_DMG)
        chk("D_one_shot_expira_para_controlavel",
            p_after["role_p1"] in CONTROLABLE
            and p_after["role_changes_p1"] - b["role_changes_p1"] >= 2,
            papel_final=p_after["role_p1"],
            delta_role=p_after["role_changes_p1"] - b["role_changes_p1"],
            arco_medido_ticks=PUNCH_ANIM_TICKS)
        p = p_after

        # ---- D2. deadlines input->acao->apresentacao->consequencia ---------
        # Pressa instrumentada com amostragem fina; a unidade de saida e VDP
        # steps E frames da ROM, com a resolucao da amostragem declarada no
        # relatorio. Nada aqui promove frame rate.
        p = rig.settle()
        p = rig.approach(48)
        b_trace, samples = rig.trace_press(K_LP, max_rom_ticks=180, chunk=2)
        deadlines = {
            "baseline": {"bridge_steps": b_trace["bridge_steps"],
                         "rom_frame": b_trace["frame"]},
            "resolucao_do_traco": {"chunk_steps": 2,
                                   "aprox_frames_da_rom": round(2 / (rig.ratio or 2.2), 2)},
            "samples": samples,
            **compute_deadlines(b_trace, samples,
                                {"bridge_steps": b_trace["bridge_steps"],
                                 "frame": b_trace["frame"]}),
        }
        chk("D2_cadeia_completa_no_traco",
            deadlines["input_to_route"] is not None
            and deadlines["input_to_action"] is not None
            and deadlines["input_to_presentation"] is not None
            and deadlines["input_to_consequence"] is not None,
            input_to_route=deadlines["input_to_route"],
            input_to_action=deadlines["input_to_action"],
            input_to_presentation=deadlines["input_to_presentation"],
            input_to_consequence=deadlines["input_to_consequence"],
            action_to_presentation=deadlines["action_to_presentation"],
            presentation_to_consequence=deadlines["presentation_to_consequence"],
            amostras=len(samples))
        p = rig.settle()

        # ---- E. especial humano: reconhecido e CONTADO como sem rota -------
        # Blob P1_CUT_CMD_SPECIAL = F(libera) -> D -> DF -> toque K2 tier 1
        # (FRACO: soltar antes do limiar emite o pulso no tick da soltura).
        # Janela 15; o plano abaixo cabe no anel de 16 -- em frames DA ROM.
        p = rig.settle()
        fwd, back = rig.dirs(p)
        b = p
        for mask, fr in ((fwd, 2), (0, 1), (K_DOWN, 2), (K_DOWN | fwd, 2),
                         (K_HP, 2), (0, 2)):
            p = rig.hold(mask, fr)
        unr = p["cmd_unrouted_p1"] - b["cmd_unrouted_p1"]
        chk("E_especial_humano_contado_sem_rota",
            unr >= 1 and p["cmd_last_index_p1"] == 0,
            unrouted_delta=unr, last_index=p["cmd_last_index_p1"],
            hits_delta=p["cmd_hits_p1"] - b["cmd_hits_p1"],
            nota="sem rota nao significa sacrificado: o padrao casa e e contabilizado")
        p = rig.settle()

        # ---- F. borda: clamp EXATO quando afirmado; caso contrario o limite
        # tem que ser explicado pelo pusher sustentado, nunca por ruido. -----
        p = rig.hold(back, 150)
        x_left = p["x_p1"]
        chk("F_borda_esquerda_clamp_exato", x_left == X_MIN_PX,
            x_p1=x_left, x_min_px=X_MIN_PX, ticks=150)
        p_stay = rig.hold(back, 30)
        chk("F_esquerda_permanece_clampada",
            p_stay["x_p1"] == X_MIN_PX and p_stay["role_p1"] == ST_WALK_B,
            x_p1=p_stay["x_p1"], papel=p_stay["role_p1"], ticks=30)
        p = rig.hold(0, 20)
        b_r = p
        p = rig.hold(fwd, 260)
        d_pusher = p["pusher_frames"] - b_r["pusher_frames"]
        if p["x_p1"] == X_MAX_PX:
            chk("F_borda_direita_clamp_exato", True,
                x_p1=p["x_p1"], x_max_px=X_MAX_PX, ticks=260)
        else:
            chk("F_borda_direita_limitada_por_pusher",
                X_MIN_PX < p["x_p1"] < X_MAX_PX and d_pusher >= 10,
                x_p1=p["x_p1"], x_min_px=X_MIN_PX, x_max_px=X_MAX_PX,
                pusher_delta=d_pusher, ticks=260, x_p2=p["x_p2"],
                nota="sem clamp exato: o avanco parou em contato sustentado "
                     "(pusher), nao em ruido")

        # ---- G. humano como defensor: guarda sustentada NEGA dano ----------
        # O ramo de guarda em combat_step nunca inscreve dano (so guard_push):
        # o que se afirma agora e (a) existiu evento de bloqueio na janela
        # [b0..p] e (b) na janela INTEIRA em guarda [b1..p] nao houve nem hit
        # nao-bloqueado nem dano. clsn_checks separa "pose nunca avaliada"
        # (distancia) de "avaliou e bloqueou" (mecanica). Aproximar ANTES
        # continua sendo parte do teste, nao conveniencia.
        p = rig.settle()
        fwd, back = rig.dirs(p)
        p = rig.approach(24)
        b0 = p
        p = rig.hold(K_DOWN | back, 40)      # engaja e sustenta a guarda
        b1 = p
        p = rig.hold(K_DOWN | back, 200)     # janela medida (240 ticks no total)
        d_guard_total = p["guard_events"] - b0["guard_events"]
        d_guard_win = p["guard_events"] - b1["guard_events"]
        d_hit_win = p["hit_events"] - b1["hit_events"]
        dmg_win = p["damage_p1"] - b1["damage_p1"]
        d_clsn_g = p["clsn_checks"] - b0["clsn_checks"]
        guard_ev = dict(guard_total=d_guard_total, guard_janela=d_guard_win,
                        hit_janela=d_hit_win, dano_janela=dmg_win,
                        clsn_delta=d_clsn_g, papel=p["role_p1"],
                        x_p1=p["x_p1"], x_p2=p["x_p2"], ticks=240)
        chk("G_guarda_humana_gera_evento_de_bloqueio", d_guard_total >= 1, **guard_ev)
        chk("G_zero_dano_sob_guarda",
            dmg_win == 0 and d_hit_win == 0 and p["role_p1"] == ST_GUARD,
            **guard_ev,
            nota="invariante do ramo de guarda: S_BLOCKABLE nunca inscreve dano; "
                 "hit_janela separa bloqueio de acerto nao visto")
        p = rig.hold(0, 10)

        # ---- H. drive de KO: defensor movel, simultaneidade, terminal ------
        # Vida 1000 contra HP=112: 9 acertos derrubam o oponente. O drive
        # recompoe a distancia a cada iteracao e settle-a o papel entre pressoes,
        # porque pressar em pose de golpe ou no ar nao e rota ausente.
        moved_defenders, ko = set(), None
        human_hits = 0
        dmg_p1_0, dmg_p2_0 = p["damage_p1"], p["damage_p2"]
        wins = []
        for it in range(14):
            p = rig.settle()
            if p["life_p1"] == 0 or p["life_p2"] == 0:
                ko = p
                break
            # Baseline da ITERACAO inteiro, tomado no topo do laco: o dano da IA
            # pode cair durante o approach/pressao, antes do b interno do
            # strong_press. Comparar contra b interno perderia a simultaneidade
            # real -- a janela errada, nao a cadeia.
            b_iter = p
            rig.approach(48)
            p, fired, unr, idx, role_press, b = rig.strong_press(K_LP)
            human_hits += fired
            p = rig.hold(0, PUNCH_ANIM_TICKS + 6)
            moved_defenders.add(p["x_p2"])
            wins.append({
                "d_dmg_p1": p["damage_p1"] - b_iter["damage_p1"],
                "d_dmg_p2": p["damage_p2"] - b_iter["damage_p2"],
                "d_cmd_p1": (p["cmd_hits_p1"] - b_iter["cmd_hits_p1"])
                + (p["cmd_unrouted_p1"] - b_iter["cmd_unrouted_p1"]),
                "d_cmd_p2": (p["cmd_hits_p2"] - b_iter["cmd_hits_p2"])
                + (p["cmd_unrouted_p2"] - b_iter["cmd_unrouted_p2"]),
            })
            print(f"    [drive {it}] rota_p1+{fired} hits_p1={p['cmd_hits_p1']} "
                  f"clsn={p['clsn_checks']} papel={p['role_p1']} "
                  f"life_p1={p['life_p1']} life_p2={p['life_p2']} "
                  f"x_p1={p['x_p1']} x_p2={p['x_p2']} "
                  f"hit={p['hit_events']} guard={p['guard_events']} "
                  f"janela={wins[-1]}")
            if p["life_p1"] == 0 or p["life_p2"] == 0:
                ko = p
                break

        # Simultaneidade: os dois lados percorrem anel/tier/tabela na MESMA
        # janela e os dois lados apanham. Dano cruzado dentro de uma mesma
        # iteracao de ~60 ticks e coincidencia de agenda da IA (beat longo),
        # nao propriedade da cadeia -- entao o cotejo e declarado com janela
        # de 3 iteracoes e o numero de cada janela sai no evidencial.
        both_routes = any(w["d_cmd_p1"] > 0 and w["d_cmd_p2"] > 0 for w in wins)
        overlap3 = any(sum(w["d_dmg_p1"] for w in wins[i:i + 3]) > 0
                       and sum(w["d_dmg_p2"] for w in wins[i:i + 3]) > 0
                       for i in range(len(wins)))

        chk("H_defensor_movel_atingido", len(moved_defenders) > 3,
            pos_p2_distintas=len(moved_defenders))
        chk("H_dano_humano_acumulado",
            p["damage_p2"] > dmg_p2_0 and human_hits >= 1,
            dmg_p2_delta=p["damage_p2"] - dmg_p2_0, rotas_humano=human_hits)
        chk("H_simultaneidade_dos_dois_lados",
            both_routes and overlap3
            and p["damage_p1"] > dmg_p1_0 and p["damage_p2"] > dmg_p2_0,
            janelas=len(wins),
            rotas_dos_dois_lados_na_mesma_janela=both_routes,
            dano_cruzado_em_3_janelas=overlap3,
            dmg_p1_total=p["damage_p1"] - dmg_p1_0,
            dmg_p2_total=p["damage_p2"] - dmg_p2_0,
            janela_de_cotejo=3)
        chk("H_pelder_face_flips_operaram",
            p["pusher_frames"] > 0 and p["face_flips"] > 0,
            pusher=p["pusher_frames"], flips=p["face_flips"])

        if ko is not None:
            side = "p2" if ko["life_p2"] == 0 else "p1"
            b = ko
            p = rig.hold(0, 180)
            # Depois do KO o defensor morto e PULADO em combat_step (life==0
            # antes de clsn/hit/dano), entao todos os contadores de combate
            # ficam congelados: nao basta "vida 0", o congelamento e afirmado.
            frozen = (p["hit_events"] == b["hit_events"]
                      and p["guard_events"] == b["guard_events"]
                      and p["clsn_checks"] == b["clsn_checks"])
            chk("H_ko_terminal_sem_dano_pos_ko",
                p["ko_events"] >= 1 and p["life_p1"] == b["life_p1"]
                and p["life_p2"] == b["life_p2"]
                and p["damage_p1"] == b["damage_p1"] and p["damage_p2"] == b["damage_p2"]
                and frozen,
                lado=side, ko=p["ko_events"],
                dano_pos_ko=((p["damage_p1"] - b["damage_p1"])
                             + (p["damage_p2"] - b["damage_p2"])),
                hit_events_pos=p["hit_events"] - b["hit_events"],
                clsn_pos=p["clsn_checks"] - b["clsn_checks"],
                vidas=(p["life_p1"], p["life_p2"]))
            if side == "p2":
                # Tentativa ATIVA sobre o lado morto: o humano (vivo) PODE
                # casar rota, mas nada pode ser inscrito no defensor morto --
                # o mutismo dos contadores e a prova, nao a ausencia de pressao.
                p, fired2, unr2, idx2, role2, b2 = rig.strong_press(K_LP)
                chk("H_p2_morto_nao_recebe_ataque_ativo",
                    p["damage_p2"] == b2["damage_p2"]
                    and p["hit_events"] == b2["hit_events"]
                    and p["clsn_checks"] == b2["clsn_checks"]
                    and p["ko_events"] == b2["ko_events"]
                    and p["life_p2"] == 0,
                    rotas_pos_ko=fired2, sem_rota_pos_ko=unr2,
                    ultimo_indice=idx2, papel_p1=role2,
                    dmg_p2=p["damage_p2"] - b2["damage_p2"],
                    hit_events=p["hit_events"] - b2["hit_events"],
                    clsn=p["clsn_checks"] - b2["clsn_checks"],
                    nota="rota do lado vivo permitida; inscricao no morto proibida")
            else:
                chk("H_papel_terminal_do_humano", p["role_p1"] == ST_KO,
                    role_p1=p["role_p1"], st_ko=ST_KO)
                # reset do objeto em KO: combat_step faz input_flush(d) e o
                # matcher retorna em !v->alive. Pressionar depois do KO proprio
                # nao pode gerar rota nem evento -- e o silencio dos contadores
                # de combate e afirmado, nao presumido.
                p, fired_ko, unr_ko, idx_ko, _, b_ko = rig.strong_press(K_LP)
                chk("H_humano_ko_nao_gera_rota",
                    fired_ko == 0 and unr_ko == 0 and p["role_p1"] == ST_KO
                    and p["damage_p1"] == b_ko["damage_p1"]
                    and p["hit_events"] == b_ko["hit_events"]
                    and p["clsn_checks"] == b_ko["clsn_checks"]
                    and p["ko_events"] == b_ko["ko_events"],
                    rotas_pos_ko=fired_ko, sem_rota_pos_ko=unr_ko,
                    ultimo_indice=idx_ko, papel=p["role_p1"], st_ko=ST_KO,
                    dano_extra=p["damage_p1"] - b_ko["damage_p1"],
                    clsn_extra=p["clsn_checks"] - b_ko["clsn_checks"])
        else:
            chk("H_ko_terminal_sem_dano_pos_ko", False,
                motivo="drive de 14 iteracoes nao levou a um KO",
                life_p2=p["life_p2"], life_p1=p["life_p1"],
                dmg_p2_do_drive=p["damage_p2"] - dmg_p2_0,
                rotas_humano=human_hits)

        # ---- Z. os QUATRO relogios avancaram dentro do mesmo run -----------
        clocks = {
            "vdp_frames_acked": rig.bridge_steps,
            "rom_frames_logical": (p["frame"] - p_start["frame"]) & 0xFFFF,
            "rom_frames_observed_by_holds": rig.rom_ticks,
            "animation_boundaries_role_changes": {
                "p1": (p["role_changes_p1"] - p_start["role_changes_p1"]) & 0xFFFF,
                "p2": (p["role_changes_p2"] - p_start["role_changes_p2"]) & 0xFFFF,
            },
            "wall_seconds": round(time.time() - t0, 1),
            "vdp_steps_per_rom_frame_measured": rig.ratio,
            "nota": "limites de animacao = role_changes (proxy declarado de FSM; "
                    "a sonda nao expoe fidx)",
        }
        chk("Z_quadro_dos_quatro_relogios",
            clocks["vdp_frames_acked"] > 0
            and clocks["rom_frames_logical"] > 0
            and clocks["rom_frames_observed_by_holds"] > 0
            and (clocks["animation_boundaries_role_changes"]["p1"]
                 + clocks["animation_boundaries_role_changes"]["p2"]) > 0
            and clocks["wall_seconds"] > 0,
            vdp=clocks["vdp_frames_acked"], rom_logico=clocks["rom_frames_logical"],
            rom_por_holds=clocks["rom_frames_observed_by_holds"],
            limites_p1=clocks["animation_boundaries_role_changes"]["p1"],
            limites_p2=clocks["animation_boundaries_role_changes"]["p2"],
            parede_s=clocks["wall_seconds"])
    finally:
        if session:
            try:
                close_session(session)
                print("[cleanup] sessao privada fechada")
            except Exception as e:                       # noqa: BLE001
                print("[cleanup] FALHOU:", e)
            try:
                custody_dir = out_path.parent / (out_path.stem + "_custody")
                custody = copy_custody(Path(session), custody_dir)
                print(f"[custody] {len(custody)} arquivos de sessao copiados para {custody_dir}")
            except Exception as e:                       # noqa: BLE001
                print("[custody] FALHOU:", e)

    limitacoes = [
        "o papel terminal do lado 1 (IA) nao tem sonda: so probe_b_role_p1 e "
        "espelhado. KO de p2 e afirmado por life/ko_events, nunca por role.",
        "probe_frame/frames stepped provam sequencia, nao velocidade de fps.",
        "sem round reset nesta ROM: KO e terminal dentro da sessao medida.",
        "simultaneidade de dano e cotejada em janela de 3 iteracoes do drive: o "
        "beat da IA e mais longo que uma iteracao, entao sobrepor na janela "
        "unica e questao de agenda, nao da cadeia causal.",
        "limites de animacao sao contados por role_changes (proxy declarado): a "
        "sonda nao expoe fidx; o numero mede transicoes de FSM, nao quadros.",
        "deadlines do D2 tem resolucao de ~1 frame da ROM (leitura a cada 2 "
        "steps VDP); nenhum valor e reivindicado abaixo disso.",
        "o pin da ROM e entrada congelada (--expect-sha); corrida 'unpinned' "
        "nao prova identidade de build, so consistencia interna.",
    ]
    report = {
        "schema": 3, "onda": "wave5b-input-causal-rom",
        "rom": str(rom), "rom_sha256": rom_sha,
        "project": str(project),
        "rom_pin": {"expected": a.expect_sha, "actual": rom_sha,
                    "status": ("unpinned" if not a.expect_sha else "verified")},
        "session_id": (meta or {}).get("session_id"),
        "display": (meta or {}).get("display"),
        "emulator_pid": (meta or {}).get("emulator_process", {}).get("pid"),
        "session_preconditions": {
            "emulator_sha256": (meta or {}).get("emulator_sha256"),
            "bridge_sha256": (meta or {}).get("bridge_sha256"),
            "rom_bytes": len(rom.read_bytes()),
            "host_load_at_boot": (meta or {}).get("host_load"),
            "ttl_seconds": (meta or {}).get("ttl_seconds"),
        },
        "unidade_de_tempo": "frames da ROM (probe_frame) para asserts; steps VDP "
                            "para deadlines e relogio de VDP",
        "bridge_steps_per_rom_frame": rig.ratio if rig else None,
        "frames_stepped": rig.bridge_steps if rig else 0,
        "rom_ticks_observed": rig.rom_ticks if rig else 0,
        "clocks": clocks,
        "deadlines_vdp_e_rom": deadlines,
        "custody": custody,
        "delta_vs_wave5b_v1": [
            "pin --expect-sha como entrada congelada (antes: constante de arquivo)",
            "saida por corrida em out/logs/runs/ sem sobrescrita",
            "C afirma papel EXATO por contexto (antes: apenas 'mudou')",
            "F afirma clamp exato e, quando nao alcancado, exige pusher sustentado",
            "G afirma zero dano E zero hit nao-bloqueado na janela em guarda",
            "KO terminal nos DOIS lados: contadores congelados + tentativa ativa",
            "D2 mede deadlines input->rota->papel->apresentacao->dano",
            "quatro relogios registrados (VDP/logico/limites de animacao/parede)",
            "custodia da sessao (journal de comandos) copiada para o relatorio",
        ],
        "tier_ticks": TIER_TICKS,
        "punch_anim_ticks_medidos": PUNCH_ANIM_TICKS,
        "elapsed_s": round(time.time() - t0, 1),
        "status": "diagnostic_only",
        "cases": cases,
        "limitacoes": limitacoes,
        "aprovado": all(c["ok"] for c in cases) if cases else False,
    }
    wt_ok = write_report(report)
    n_ok = sum(1 for c in cases if c["ok"])
    print(f"\n[{'PASS' if report['aprovado'] else 'FALHA'}] {n_ok}/{len(cases)} casos "
          f"| ROM {rom_sha[:12]} | {report['rom_ticks_observed']} frames da ROM "
          f"({report['frames_stepped']} steps, ratio {report['bridge_steps_per_rom_frame']}) "
          f"| {report['elapsed_s']}s")
    if wt_ok:
        print(f"relatorio: {out_path}")
    return 0 if report["aprovado"] else 1


if __name__ == "__main__":
    sys.exit(main())
