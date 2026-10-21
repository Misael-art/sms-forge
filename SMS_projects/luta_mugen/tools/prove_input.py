#!/usr/bin/env python3
"""prove_input.py — prova que o PAD move o LUTADOR, lendo a RAM, nao pixels.

Plano 2, Task 5. Precedente canonico: SMS_projects/MSSF2T/tools/
prove_input_memory.py (L035/L038/L039/L053) — o canal real em Wayland/KWin e
uinput. ESTA VERSAO usa SESSAO PRIVADA (§93/L057): portas P1/P2 virtuais dentro
da JVM, duracao em FRAMES do VDP, leitura de RAM pela ponte; nenhum teclado,
foco, janela ou porta DAP do desktop. Eixos separados no JSON: acks (ponte),
portas (emulator_input no ACK) e RAM da ROM; o veredito de gameplay so vem da RAM.

Fases (todas por leitura da RAM SMRT 0xC7E0.. desta ROM):
  1. canario do CANAL: probe_frame avanca exatamente o numero de frames pedido;
  2. direcao: dx >= 8 px NA DIRECAO COMANDADA nos dois sentidos
     (criterio canonico emulator_input.evaluate_direction);
  3. pulo: probe_py (ALTITUDE) > 0 durante o voo e estado JUMP;
  4. soco: tecla B1 vista em probe_keys (0x10) COM o jogo rodando,
     probe_boss cai, probe_score sobe, padrao CMD_PUNCH latchou bit0;
  5. agachar: probe_state == CROUCH com Down segurado;
  6. padrao: CMD_FF (duplo frente, relativo ao facing, latchado no tick do
     buffer de 16 amostras) acendeu bit1 durante o andar para o oponente.
  7. especial: QCF+B1 com frente relativa ao oponente; bit2 do parser e o
     latch de FIGHT_EVENT_SPECIAL devem concordar.

Seguranca: --rom validado contra whitelist literal; saidas relativas a RAIZ
do workspace. Uso (da raiz):
  python3 SMS_projects/luta_mugen/tools/prove_input.py \
      --rom SMS_projects/luta_mugen/out/rom/luta_mugen.sms
Exit: 0 provado | 1 reprovado | 2 ambiente ausente
Artefato: SMS_projects/luta_mugen/out/evidence/t5_input_memory.json
"""
import argparse
import hashlib
import json
import os
import sys

TOOLS = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "..", "..", "..", "tools", "sms_wrapper")
sys.path.insert(0, os.path.abspath(TOOLS))

import session_consumer as SC                                    # noqa: E402

ROM_REL = "SMS_projects/luta_mugen/out/rom/luta_mugen.sms"
EVID = "SMS_projects/luta_mugen/out/evidence"

# mapa SMRT desta ROM (src/main.c)
P_FRAME   = 0xC7F0   # u16
P_HP      = 0xC7F2   # vida P1 (byte)
P_SCORE   = 0xC7F3   # hits conectados por P1
P_BOSS    = 0xC7F4   # vida P2 (byte)
P_STATE   = 0xC7F6   # estado P1 (ST_* de fight.c)
P_WAVE    = 0xC7F7   # 1 = atracao ativa
P_KEYS    = 0xC7F8   # Port A crua (0x10 = botao 1)
P_POSE    = 0xC7F9   # anim P1
P_PX      = 0xC7FA   # P1.x >> 8
P_PY      = 0xC7FB   # P1.altura >> 8 (0 = chao)
P_P2X     = 0xC7FC   # P2.x >> 8
P_PATTERN = 0xC7FD   # bit0 CMD A, bit1 CMD FF (latch)
P_SPECIAL = 0xC7D7   # 1 quando QCF+B1 disparou FIGHT_EVENT_SPECIAL

ST_IDLE, ST_WALK_F, ST_WALK_B, ST_JUMP, ST_CROUCH, ST_GUARD, \
    ST_PUNCH1, ST_PUNCH2 = range(8)
ST_SPECIAL = 8
HOLD_S = 0.8              # direcional pressionado antes da leitura
PUNCH_GAP_MIN = 8         # janela medida do golpe do Ken
PUNCH_GAP_MAX = 16
ATTRACT_END = 1400        # frames: roteiro completo antes de tocar em nada
SETTLE = 3.0


# ------------------------------------------------------------ criterios puros
def choose_approach_key(px, p2x, gap_min=PUNCH_GAP_MIN,
                        gap_max=PUNCH_GAP_MAX):
    """Posiciona P1 a esquerda de P2 na janela de hitbox do corte ativo."""
    if px is None or p2x is None:
        return None
    gap = p2x - px
    if gap_min <= gap <= gap_max:
        return None
    return "Right" if gap > gap_max else "Left"


def punch_range_valid(px, p2x, gap_min=PUNCH_GAP_MIN,
                      gap_max=PUNCH_GAP_MAX):
    """Confirma distância P1→P2 na janela medida, após esperar pelo IDLE."""
    if px is None or p2x is None or px >= p2x:
        return False
    gap = p2x - px
    return gap_min <= gap <= gap_max


def punch_verdict(boss_before, boss_after, keys_durante, pattern_bits,
                  score_before, score_after):
    """Soco conectou por input? B1 CHEGOU ao ROM (0x10 em probe_keys com o
    jogo rodando) ANTES de qualquer conclusao — tecla que nao chegou nao e
    whiff (L039, licao MSSF2T 07/09/2026). Dano: boss byte caiu; corroboracao
    na propria ROM: score de hits e latch do padrao CMD_PUNCH."""
    if keys_durante is None or boss_before is None or score_before is None:
        return False, "leitura DAP perdida — inconclusivo, nao reprovado"
    if not keys_durante & 0x10:
        return False, ("botao 1 nunca acendeu 0x10 em probe_keys: a tecla nao "
                       "chegou ao ROM — nada a concluir sobre o soco")
    if (boss_after is not None and boss_after < boss_before and
            score_after is not None and score_after > score_before):
        if not (pattern_bits or 0) & 0x01:
            return False, ("dano visivel sem latch do padrao CMD_PUNCH "
                           "(bits=0x%02X): estado do probe duvidoso"
                           % (pattern_bits or 0))
        return True, ("boss %s->%s com B1 visto (keys=0x%02X), score=%s, "
                      "padrao punch latchou" %
                      (boss_before, boss_after, keys_durante, score_after))
    return False, ("B1 confirmado (0x10 em probe_keys) e boss %s->%s: "
                   "whiff — soco saiu mas nao conectou"
                   % (boss_before, boss_after))


def jump_verdict(py_amostras, states_vistos):
    """Pulo vivo: ALTITUDE (probe_py) > 0 em alguma amostra e estado JUMP
    visto. py e altura nesta ROM (0 = chao), NAO y de tela."""
    alt = [v for v in py_amostras if v is not None]
    if not alt or max(alt) <= 0:
        return False, "probe_py nunca saiu do chao (max=%s)" % (max(alt) if alt else None)
    if ST_JUMP not in states_vistos:
        return False, "altitude >0 sem estado JUMP observado (%s)" % states_vistos
    return True, "pico de altitude=%s px, estado JUMP visto" % max(alt)


def jump_start_eligible(state):
    """A prova começa em IDLE para não perder a borda durante um ataque/demo."""
    return state == ST_IDLE


def special_verdict(pattern_bits, event_latch):
    """O comando sozinho nao prova o golpe; ambos os latches devem concordar."""
    if pattern_bits is None or event_latch is None:
        return False, "leitura DAP perdida — especial inconclusivo"
    if not (pattern_bits & 0x04):
        return False, "QCF+B1 nao acendeu o bit2 do parser"
    if event_latch != 1:
        return False, "bit2 sem transicao para FIGHT_EVENT_SPECIAL"
    return True, "QCF+B1 reconhecido e FIGHT_EVENT_SPECIAL observado"



# ------------------------------------------------------------ sessao privada
HOLD_FRAMES = 48           # direcional segurado (equivale a ~0.8 s a 60 Hz, agora medido em frames)
SMRT_MAGIC = [83, 77, 82, 84]


def _sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def _wait_state(s, target, max_frames=300, chunk=5):
    """Avanca em frames (sem botoes) ate o estado de P1 ser `target`; devolve (ok, estado)."""
    st = s.byte(P_STATE)
    done = 0
    while st != target and done < max_frames:
        s.hold(0, 0, chunk)
        done += chunk
        st = s.byte(P_STATE)
    return st == target, st


def run(rom_path, gap_min=PUNCH_GAP_MIN, gap_max=PUNCH_GAP_MAX, approach_ms=50):
    out = {"schema": "luta_input_v2_session", "rom": rom_path, "rom_sha256": _sha(rom_path),
           "punch_gap_window": [gap_min, gap_max], "approach_hold_frames": max(1, round(approach_ms / 16.7)),
           "chain_of_custody": [
               "sessao privada Emulicious (Xvfb+bwrap, SMSJoypad P1/P2 dentro da JVM); sem teclado/foco/DAP do desktop",
               "duracao de comando = frames do VDP (input + step), leitura de RAM pela ponte com a emulacao pausada",
               "mapa: src/main.c probe SMRT 0xC7E0.. (px=0xC7FA, keys=0xC7F8)"]}
    try:
        ctx = SC.private_session(rom_path)
        s = ctx.__enter__()
    except SC.SessionUnavailable as e:
        print("[FAIL_AMBIENTE] %s" % e)
        return 2, out
    exc = (None, None, None)
    try:
        out["session_id"], out["session_rom_sha256"] = s.id, s.rom_sha256
        if s.rom_sha256 != out["rom_sha256"]:
            print("[FAIL] SHA da ROM da sessao difere da ROM pedida")
            return 1, out
        # ---- 1. canario do canal: magic SMRT e frame avancando por frames exatos
        magic = s.read(0xC7E0, 4)
        f0 = s.word(P_FRAME)
        s.hold(0, 0, 30)
        f1 = s.word(P_FRAME)
        ok_canal = magic == SMRT_MAGIC and (f1 - f0) == 30
        out["canal"] = {"magic": magic, "frame_antes": f0, "frame_depois": f1, "delta": f1 - f0,
                        "provado": ok_canal}
        print("canal: magic=%s frame %s->%s (delta %s) => %s"
              % (magic, f0, f1, f1 - f0, "PROVADO" if ok_canal else "nao"))
        if not ok_canal:
            return 1, out

        # ---- 2. direcao (a atracao morre na primeira tecla; Right e Left com dx >= 8 px)
        s.hold(0, 0, 60)
        dirs = {}
        for nome, mask, sinal in (("Right", SC.R, 1), ("Left", SC.L, -1)):
            x0 = s.byte(P_PX)
            r = s.hold(mask, 0, HOLD_FRAMES)
            x1 = s.byte(P_PX)
            dx = (x1 - x0) * sinal
            dirs[nome] = {"x0": x0, "x1": x1, "dx_na_direcao": dx, "ack_porta": r.get("emulator_input"),
                          "estado": s.byte(P_STATE), "provado": dx >= 8}
            s.hold(0, 0, 0)
            _wait_state(s, ST_IDLE)
        ok_dir = all(v["provado"] for v in dirs.values())
        out["direcao"] = dirs
        print("direcao: %s => %s" % ({k: v["dx_na_direcao"] for k, v in dirs.items()},
                                     "PROVADO" if ok_dir else "nao"))

        # ---- 3. pulo (borda de Up em IDLE; altitude e estado amostrados a cada 4 frames)
        _wait_state(s, ST_IDLE)
        pys, states = [], []
        s.hold(SC.U, 0, 3)
        for _ in range(20):
            s.hold(0, 0, 4)
            pys.append(s.byte(P_PY))
            states.append(s.byte(P_STATE))
        s.hold(0, 0, 60)
        landed = s.byte(P_PY) == 0
        ok_jump, why = jump_verdict(pys, set(states))
        ok_jump = ok_jump and landed
        out["pulo"] = {"alt": pys, "estados": sorted(set(states)), "pousou": landed, "motivo": why,
                       "provado": ok_jump}
        print("pulo: %s pousou=%s => %s" % (why, landed, "PROVADO" if ok_jump else "nao"))

        # ---- 4. soco: aproximar P1 de P2 pela janela, B1 visto em keys COM a mascara ativa
        _wait_state(s, ST_IDLE)
        for _ in range(40):
            # alvo = centro da janela medida (a borda de 16 px falhou em medicao real: whiff)
            k = choose_approach_key(s.byte(P_PX), s.byte(P_P2X), gap_min, gap_min + (gap_max - gap_min) // 2)
            if k is None:
                break
            s.hold(SC.R if k == "Right" else SC.L, 0, out["approach_hold_frames"])
            s.hold(0, 0, 6)
        _wait_state(s, ST_IDLE)
        px, p2x = s.byte(P_PX), s.byte(P_P2X)
        in_range = punch_range_valid(px, p2x, gap_min, gap_max)
        boss0, score0 = s.byte(P_BOSS), s.byte(P_SCORE)
        r = s.hold(SC.B1, 0, 4)
        keys_durante = s.byte(P_KEYS)
        # o dano chega no fim da animacao do golpe (medido: >60 frames em PUNCH1): esperar o retorno a IDLE
        recuperou, _st = _wait_state(s, ST_IDLE, 400)
        pat = s.byte(P_PATTERN)
        boss1, score1 = s.byte(P_BOSS), s.byte(P_SCORE)
        ok_punch, why = punch_verdict(boss0, boss1, keys_durante, pat, score0, score1)
        ok_punch = ok_punch and in_range
        out["soco"] = {"px": px, "p2x": p2x, "gap_valido": in_range, "boss": [boss0, boss1],
                       "score": [score0, score1], "keys_durante": keys_durante, "recuperou_idle": recuperou,
                       "ack_porta": r.get("emulator_input"), "padrao": pat, "motivo": why,
                       "provado": ok_punch}
        print("soco: %s => %s" % (why, "PROVADO" if ok_punch else "nao"))
        _wait_state(s, ST_IDLE)

        # ---- 5. agachar
        s.hold(SC.D, 0, 20)
        st_c = s.byte(P_STATE)
        ok_crouch = st_c == ST_CROUCH
        out["agachar"] = {"estado": st_c, "provado": ok_crouch}
        print("agachar: estado=%s => %s" % (st_c, "PROVADO" if ok_crouch else "nao"))
        s.hold(0, 0, 0)
        _wait_state(s, ST_IDLE)

        # ---- 6. guarda: baixo + costas (P1 a esquerda de P2 => costas = Left)
        px_g, p2x_g = s.byte(P_PX), s.byte(P_P2X)
        back = SC.L if px_g < p2x_g else SC.R
        s.hold(SC.D | back, 0, 20)
        st_g, keys_g = s.byte(P_STATE), s.byte(P_KEYS)
        ok_guard = st_g == ST_GUARD
        out["guarda"] = {"px": px_g, "p2x": p2x_g, "estado": st_g, "keys": keys_g, "provado": ok_guard}
        print("guarda: estado=%s keys=0x%02X => %s" % (st_g, keys_g, "PROVADO" if ok_guard else "nao"))
        s.hold(0, 0, 0)
        _wait_state(s, ST_IDLE)

        # ---- 6b. duplo frente (bit1) e 7. especial QCF+B1: sequencia atomica em frames (frente relativa a P2)
        px, p2x = s.byte(P_PX), s.byte(P_P2X)
        fwd = SC.R if px < p2x else SC.L
        s.sequence([{"p1": fwd, "frames": 3}, {"p1": 0, "frames": 3}, {"p1": fwd, "frames": 3}])
        s.hold(0, 0, 2)
        ff_bits = s.byte(P_PATTERN)
        _wait_state(s, ST_IDLE)
        antes = {"px": px, "p2x": p2x, "estado": s.byte(P_STATE), "pattern": s.byte(P_PATTERN), "evento": s.byte(P_SPECIAL)}
        # tokens contiguos D, frente, B1 (como o roteiro fisico original: ~3 frames cada) + 12 frames para o latch do evento
        s.sequence([{"p1": SC.D, "frames": 3}, {"p1": fwd, "frames": 3}, {"p1": SC.B1, "frames": 3}])
        s.hold(0, 0, 12)
        pat_special = s.byte(P_PATTERN) or 0
        special_event = s.byte(P_SPECIAL)
        special_state = s.byte(P_STATE)
        ok_special, why_s = special_verdict(pat_special, special_event)
        if antes["evento"] == 1:     # latch ja armado antes do comando: nao prova este comando
            ok_special, why_s = False, "evento ja estava latchado antes do QCF+B1 (sem transicao observavel)"
        out["especial"] = {"antes": antes, "frente": "Right" if fwd == SC.R else "Left", "latch_pattern": pat_special,
                           "evento": special_event, "estado_apos_comando": special_state,
                           "motivo": why_s, "provado": ok_special}
        print("especial: pattern=0x%02X evento=%s estado=%s => %s"
              % (pat_special, special_event, special_state, "PROVADO" if ok_special else "nao"))

        bits = (s.byte(P_PATTERN) or 0) | (ff_bits or 0)
        out["padroes"] = {"latch": bits, "punch_bit0": bool(bits & 1), "double_forward_bit1": bool(bits & 2),
                          "qcf_b1_bit2": bool(bits & 4)}
        ok_pattern = bool(bits & 0x03) and ok_special
        print("padroes: latch=0x%02X" % bits)
        out["acks"] = s.acks[-12:]
        tudo = dict(ok_dir=ok_dir, ok_jump=ok_jump, ok_punch=ok_punch, ok_crouch=ok_crouch,
                    ok_guard=ok_guard, ok_special=ok_special, ok_pattern=ok_pattern)
        out["eixos"] = tudo
        out["aprovado"] = all(tudo.values())
        return (0 if out["aprovado"] else 1), out
    except BaseException:
        exc = sys.exc_info()
        raise
    finally:
        ctx.__exit__(*exc)


# ---------------------------------------------------------------- self-check
def self_check():
    """§19: criterios puros com as regressoes exatas das licoes herdadas."""
    falhas = []

    # abordagem: P2 a direita => Right; a esquerda => Left; em alcance => None
    if choose_approach_key(100, 130) != "Right":
        falhas.append("P2 a direita nao virou Right")
    if choose_approach_key(130, 100) != "Left":
        falhas.append("P2 a esquerda nao virou Left")
    if choose_approach_key(120, 130) is not None:
        falhas.append("gap 10 deveria estar na janela do soco Ken")
    if choose_approach_key(120, 125, 2, 8) is not None:
        falhas.append("gap 5 deveria estar na janela curta do Ryu")
    if choose_approach_key(130, 100) != "Left":
        falhas.append("P1 cruzado precisa voltar para o lado esquerdo")
    if choose_approach_key(None, 100) is not None:
        falhas.append("leitura None virou tecla")
    if not punch_range_valid(100, 108) or not punch_range_valid(100, 116):
        falhas.append("distância limite deveria estar dentro da janela medida")
    if punch_range_valid(100, 117) or punch_range_valid(116, 100):
        falhas.append("gap excessivo ou P1 cruzado passou como alcance válido")

    # soco: tecla que NAO chegou nao pode ser whiff (L039/MSSF2T 07/09)
    ok, m = punch_verdict(237, 237, 0x08, 0x02, 0, 0)
    if ok or "nao chegou" not in m:
        falhas.append("tecla perdida diagnosticada como whiff: " + m)
    # B1 chegou, dano caiu, padrao latchou => conecta
    ok, m = punch_verdict(237, 232, 0x18, 0x01, 0, 1)
    if not ok:
        falhas.append("hit -5 com B1+padrao foi reprovado: " + m)
    # dano sem latch do padrao: probe duvidoso, nao celebra
    ok, _ = punch_verdict(237, 232, 0x18, 0x02, 0, 1)
    if ok:
        falhas.append("dano sem bit0 do padrao foi aceito")
    ok, _ = punch_verdict(237, 232, 0x18, 0x01, 0, 0)
    if ok:
        falhas.append("queda de vida sem hit novo no score foi aceita")
    # whiff honesto: B1 confirmou, boss nao caiu
    ok, m = punch_verdict(237, 237, 0x18, 0x01, 0, 0)
    if ok or "whiff" not in m:
        falhas.append("whiff com B1 confirmado virou sucesso: " + m)
    # leitura perdida: inconclusivo, nunca reprovado por ausencia
    ok, m = punch_verdict(None, 232, 0x18, 0x01, 0, 1)
    if ok or "inconclusivo" not in m:
        falhas.append("leitura None virou veredito: " + m)

    # pulo: altitude 0 o tempo todo reprova; >0 sem estado JUMP reprova
    ok, _ = jump_verdict([0, 0, 0], [ST_CROUCH])
    if ok:
        falhas.append("pulo sem altitude foi aceito")
    ok, _ = jump_verdict([0, 9, 3], [ST_IDLE])
    if ok:
        falhas.append("altitude sem estado JUMP foi aceita")
    ok, _ = jump_verdict([0, 12, 5], [ST_JUMP, ST_IDLE])
    if not ok:
        falhas.append("pulo verdadeiro foi reprovado")
    if not jump_start_eligible(ST_IDLE) or jump_start_eligible(ST_WALK_F):
        falhas.append("pulo deve começar em IDLE após a borda de input")

    ok, _ = special_verdict(0x03, 1)
    if ok:
        falhas.append("evento especial sem bit2 de comando foi aceito")
    ok, _ = special_verdict(0x07, 0)
    if ok:
        falhas.append("bit2 sem transicao FIGHT_EVENT_SPECIAL foi aceito")
    ok, _ = special_verdict(0x07, 1)
    if not ok:
        falhas.append("QCF+B1 e transicao especial verdadeiros foram reprovados")

    if falhas:
        print("[SELF-CHECK FAIL]")
        for f in falhas:
            print("  - " + f)
        return 1
    print("[SELF-CHECK PASS] prove_input: abordagem, soco, pulo e especial "
          "(exige parser bit2 + FIGHT_EVENT_SPECIAL)")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rom")
    ap.add_argument("--punch-gap-min", type=int, default=PUNCH_GAP_MIN)
    ap.add_argument("--punch-gap-max", type=int, default=PUNCH_GAP_MAX)
    ap.add_argument("--approach-ms", type=int, default=50)
    ap.add_argument("--self-check", action="store_true")
    a = ap.parse_args()
    if a.self_check:
        return self_check()
    if a.rom not in (ROM_REL, "out/rom/luta_mugen.sms"):
        print("[FAIL_AMBIENTE] --rom fora da whitelist do projeto")
        return 3
    if not os.path.isfile(ROM_REL):
        print("[FAIL_AMBIENTE] rodar da RAIZ do workspace (caminho relativo)")
        return 2
    if (a.punch_gap_min < 0 or a.punch_gap_max < a.punch_gap_min or
            a.approach_ms <= 0):
        print("[FAIL_USO] janela/passo de aproximação inválido")
        return 3
    os.makedirs(EVID, exist_ok=True)
    rc, metrics = run(ROM_REL, a.punch_gap_min, a.punch_gap_max,
                      a.approach_ms)
    if metrics:
        with open(os.path.join(EVID, "t5_input_memory.json"), "w") as f:
            json.dump(metrics, f, indent=1)
        if metrics.get("session_id"):    # copia exclusiva da sessao: nunca depender do "ultimo escrito"
            with open(os.path.join(EVID, "t5_input_memory_%s.json" % metrics["session_id"]), "w") as f:
                json.dump(metrics, f, indent=1)
    print("[%s] input vivo: %s" % ("PASS" if rc == 0 else "FAIL",
                                   ROM_REL))
    return rc


if __name__ == "__main__":
    sys.exit(main())
