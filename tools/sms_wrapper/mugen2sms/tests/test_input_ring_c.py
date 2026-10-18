"""Harness no host (gcc) para o anel temporal por ator + tier (doc/23, secao 6.B).

Compila `integrada/src/input.c` + `integrada/src/input_tier.c` SEM SDCC e SEM
SMSlib: o anel nao depende de hardware — quem le a porta e `main.c`. Os blobs de
padrao sao os bytes REAIS que `converters/sms_cmd.py` serializa, escritos num
header gerado pelo teste. Isso prova as duas pontas de uma vez: o que o Python
escreve e o que o C le.

Negativos obrigatorios do handoff cobertos aqui:
  * dois toques que nao geram acorde inviavel;
  * liberacao antes e depois de T;
  * input concorrente nos dois pads.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]
SRC = ROOT / "SMS_projects/luta_mugen/integrada"
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from mugen2sms.converters import sms_cmd                                # noqa: E402
from mugen2sms.converters.sms_controls import ControlMap, DEFAULT_MAP    # noqa: E402
from mugen2sms.parsers import cmd as cmdmod                             # noqa: E402

pytestmark = pytest.mark.skipif(shutil.which("gcc") is None, reason="gcc ausente")

T = 6                       # INPUT_TIER_T compilado no harness
K_LP, K_HP = 0x10, 0x20     # niveis fisicos: KEY_1, KEY_2 (fight.h)
K_UP, K_DOWN, K_LEFT, K_RIGHT = 0x01, 0x02, 0x04, 0x08

# nomes dos padroes que o harness expoe; CROSS e a+x (acorde entre familias)
PATTERNS = ["LP", "HP", "LK", "HK", "FF", "CROSS", "HEAVY_CROSS",
            "V1", "T3", "FLEX_D", "FLEX_F", "HOLD_FLEX_F",
            "BAD_FLAGS", "BAD_WANT", "RISING", "RISING_TERRY_Y",
            "RISING_TERRY_X255", "LEGACY_V3", "RISING_EXACT"]
_COMMANDS = {"LP": "a", "HP": "c", "LK": "x", "HK": "z",
             "FF": "F, F", "CROSS": "a+x", "HEAVY_CROSS": "c+z",
             "FLEX_D": "$D", "FLEX_F": "$F", "HOLD_FLEX_F": "/$F",
             "RISING": "~15$D, U, x", "RISING_EXACT": "~15D, U, x"}


def _command(name: str, text: str) -> cmdmod.Command:
    steps, errors = cmdmod.parse_command_string(text)
    return cmdmod.Command(name, steps, 15, 1, 1, text, errors)


def _blobs() -> dict[str, bytes]:
    names = {v: k for k, v in _COMMANDS.items()}
    patterns, skipped = sms_cmd.to_patterns(
        [_command(n, c) for c, n in names.items()], DEFAULT_MAP)
    assert skipped == {}, skipped
    blobs = {p.name.upper(): sms_cmd.serialize_pattern(p) for p in patterns}
    terry_controls = ControlMap({"1": ["x", "y"], "2": ["a", "b"]},
                                {"1": [T], "2": [T]})
    steps, errors = cmdmod.parse_command_string("~15$D, U, y")
    terry_command = cmdmod.Command("RISING_TERRY_Y", steps, 10, 1, 1,
                                   "~15$D, U, y", errors)
    terry_y, skipped = sms_cmd.to_patterns(
        [terry_command], terry_controls)
    assert skipped == {}, skipped
    blobs["RISING_TERRY_Y"] = sms_cmd.serialize_pattern(terry_y[0])
    steps, errors = cmdmod.parse_command_string("~255$D, U, x")
    terry_x255 = cmdmod.Command("RISING_TERRY_X255", steps, 10, 1, 1,
                                "~255$D, U, x", errors)
    max_charge, skipped = sms_cmd.to_patterns([terry_x255], terry_controls)
    assert skipped == {}, skipped
    blobs["RISING_TERRY_X255"] = sms_cmd.serialize_pattern(max_charge[0])
    # V1: o blob ANTERIOR a versao (3 bytes de cabecalho) — deve reprovar.
    blobs["V1"] = bytes([1, 1, 15, 1, 0x10, 0x00])
    blobs["LEGACY_V3"] = bytes([3, 1, 15, 1, 0x10, 0x00])
    # T3: campo de tier 3 — a maquina de runtime tem UM limiar, nao distingue.
    blobs["T3"] = bytes([sms_cmd.BLOB_FMT_VERSION, 1, 15, 1,
                          0x10, 3 << 2, 0])
    blobs["BAD_FLAGS"] = bytes([sms_cmd.BLOB_FMT_VERSION, 1, 15, 1,
                                 0x10, 0x20, 0])
    blobs["BAD_WANT"] = bytes([sms_cmd.BLOB_FMT_VERSION, 1, 15, 1,
                                0x40, 0x00, 0])
    return blobs


def _patterns_h(tmp_path: Path) -> Path:
    blobs = _blobs()
    lines = ["/* gerado por test_input_ring_c.py - bytes reais do conversor */",
             "#ifndef PATTERNS_GEN_H", "#define PATTERNS_GEN_H", ""]
    for name in PATTERNS:
        data = blobs[name]
        lines.append(f"#define P_{name}_LEN {len(data)}")
        lines.append(f"static const unsigned char P_{name}[{len(data)}] = {{")
        lines.append("    " + ", ".join(f"0x{b:02X}" for b in data) + "};")
    lines += ["", "static const unsigned char *harness_patterns[] = {" +
              ", ".join(f"P_{n}" for n in PATTERNS) + "};",
              "#define HARNESS_PATTERN_COUNT " + str(len(PATTERNS)), "",
              "#endif"]
    path = tmp_path / "patterns_gen.h"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


HARNESS = r'''
#include <stdio.h>
#include "input.h"
#include "input.c"            /* branco: o anel e static e a unica forma de
                               * conferir a contagem contra o proprio anel */
#include "patterns_gen.h"

int main(void) {
    char op;
    unsigned who, a, b;
    input_init();
    while (scanf(" %c", &op) == 1) {
        if (op == 't') {                       /* tick: who, niveis, facing */
            if (scanf("%u %u %u", &who, &a, &b) != 3) return 2;
            input_tick((unsigned char)who, (unsigned char)a, (unsigned char)b);
        } else if (op == 'q') {                /* consulta: who, indice */
            if (scanf("%u %u", &who, &a) != 2) return 2;
            printf("%d\n", input_pattern_hit((unsigned char)who,
                                             harness_patterns[a]));
        } else if (op == 'b') {                /* ocupado: ator */
            if (scanf("%u", &who) != 1) return 2;
            printf("%d\n", input_busy((unsigned char)who));
        } else if (op == 'i') {                /* invariantes: recontagem x contador */
            unsigned char i, nz = 0, np = 0;
            if (scanf("%u", &who) != 1) return 2;
            for (i = 0; i < INPUT_BUF; i++) {
                if (buf[who][i]) nz++;
                if (buf[who][i] & S_PULSE) np++;
            }
            printf("%u %u %u %u\n", nz, nonzero[who], np, pulsos[who]);
        } else if (op == 'f') {                /* descarta o anel de um ator */
            if (scanf("%u", &who) != 1) return 2;
            input_flush((unsigned char)who);
        } else if (op == 'r') {
            input_init();
        } else {
            return 3;
        }
    }
    return 0;
}
'''


def _build(tmp_path: Path, threshold: int):
    (tmp_path / "h.c").write_text(HARNESS, encoding="utf-8")
    _patterns_h(tmp_path)
    exe = tmp_path / f"ring{threshold}"
    res = subprocess.run(
        ["gcc", "-Wall", "-Werror", "-std=c99", f"-DINPUT_TIER_T={threshold}",
         "-I", str(SRC / "inc"), "-I", str(SRC / "src"), "-I", str(tmp_path),
         str(tmp_path / "h.c"), str(SRC / "src/input_tier.c"), "-o", str(exe)],
        capture_output=True, text=True)
    if res.returncode:
        raise AssertionError("compilacao do anel falhou:\n" + res.stderr)
    return exe


def _drive(exe, script: list[str]) -> list[int]:
    """script: linhas 't who levels facing' e 'q who idx'. Retorno: so os 'q'."""
    res = subprocess.run([str(exe)], input="\n".join(script) + "\n",
                         capture_output=True, text=True, check=True)
    return [int(line) for line in res.stdout.split()]


def _idx(name: str) -> int:
    return PATTERNS.index(name)


def _tap(who: int, held_ticks: int, level: int, facing: int = 0,
         queries: tuple[str, ...] = ()) -> tuple[list[str], list[int]]:
    """Uma pressao de `held_ticks` ticks seguida de soltura, com consultas por tick.

    Retorna (script, ordem das consultas) — as consultas viram 0/1 na saida.
    """
    script, asked = [], []
    for tick in range(held_ticks + 1):
        level_now = level if tick < held_ticks else 0
        script.append(f"t {who} {level_now} {facing}")
        for name in queries:
            script.append(f"q {who} {_idx(name)}")
            asked.append(name)
    return script, asked


def test_toque_curto_casa_fraco_na_soltura_e_nada_antes(tmp_path):
    exe = _build(tmp_path, T)
    script, asked = _tap(0, 2, K_LP, queries=("LP", "HP"))
    hits = _drive(exe, script)
    by_tick = {i: (hits[2 * i], hits[2 * i + 1]) for i in range(len(hits) // 2)}
    assert by_tick[0] == (0, 0) and by_tick[1] == (0, 0)     # durante a pressao
    assert by_tick[2] == (1, 0)                              # fraco no 1o tick solto
    assert asked == ["LP", "HP"] * 3


def test_segurar_alem_de_T_casa_forte_em_T_1_e_nunca_fraco(tmp_path):
    exe = _build(tmp_path, T)
    script, _ = _tap(0, 10, K_LP, queries=("LP", "HP"))
    hits = _drive(exe, script)
    lp = [hits[2 * i] for i in range(len(hits) // 2)]
    hp = [hits[2 * i + 1] for i in range(len(hits) // 2)]
    assert hp.count(1) == 1 and hp.index(1) == T - 1         # forte no tick T-1
    assert lp == [0] * len(lp)                               # segurado nao e fraco


def test_liberacao_em_T_1_ticks_ainda_fraco_e_em_T_ticks_ja_forte(tmp_path):
    """O limiar do handoff: um tick de pressao decide entre os dois tiers."""
    exe = _build(tmp_path, T)
    script_a, _ = _tap(0, T - 1, K_LP, queries=("LP", "HP"))
    hits_a = _drive(exe, script_a)
    assert (hits_a[2 * (T - 1)], hits_a[2 * (T - 1) + 1]) == (1, 0)

    exe2 = _build(tmp_path, T)
    script_b, _ = _tap(0, T, K_LP, queries=("LP", "HP"))
    hits_b = _drive(exe2, script_b)
    assert (hits_b[2 * (T - 1)], hits_b[2 * (T - 1) + 1]) == (0, 1)
    assert hits_b.count(1) == 1                              # e so um evento


def test_um_golpe_por_pressao_o_pulso_e_consumido(tmp_path):
    """Sem consumo, o padrao continuaria casando enquanto o pulso estivesse no anel."""
    exe = _build(tmp_path, T)
    script = ["t 0 0 0", "q 0 " + str(_idx("LP"))]           # ainda sem toque
    script += ["t 0 16 0", "t 0 0 0",                         # toque de 1 tick
               "q 0 " + str(_idx("LP")), "q 0 " + str(_idx("LP")),
               "q 0 " + str(_idx("LP"))]                      # mesmo tick, depois
    hits = _drive(exe, script)
    assert hits == [0, 1, 0, 0]


def test_dois_toques_seguidos_geram_dois_fragos(tmp_path):
    exe = _build(tmp_path, T)
    script, _ = _tap(0, 2, K_LP, queries=("LP",))
    script += ["r"]
    script2, _ = _tap(0, 3, K_LP, queries=("LP",))
    hits = _drive(exe, script + script2)
    assert hits.count(1) == 2


def test_acorde_de_ticks_diferentes_nao_forma_acorde_inviavel(tmp_path):
    """Negativo do handoff: KEY_1 num tick e KEY_2 no seguinte NAO e `a+x` —
    o acorde exige os dois pulsos na mesma amostra."""
    exe = _build(tmp_path, T)
    script = ["t 0 16 0", "t 0 0 0",        # tecla 1: toque de 1 tick (fraco)
              "t 0 32 0", "t 0 0 0",        # tecla 2: toque de 1 tick (fraco)
              "q 0 " + str(_idx("CROSS"))]
    hits = _drive(exe, script)
    assert hits == [0]


def test_acorde_no_mesmo_tick_casa_uma_vez(tmp_path):
    exe = _build(tmp_path, T)
    script = ["t 0 48 0", "t 0 0 0",        # KEY_1 + KEY_2 juntos, 1 tick
              "q 0 " + str(_idx("CROSS")),
              "q 0 " + str(_idx("CROSS"))]
    hits = _drive(exe, script)
    assert hits == [1, 0]


def test_chord_not_mapped_as_single_button_attack(tmp_path):
    """A y+b-like chord cannot fall through to its HP/HK members."""
    exe = _build(tmp_path, T)
    script = []
    for _ in range(T):
        script.append(f"t 0 {K_LP | K_HP} 0")
        script.extend(f"q 0 {_idx(name)}" for name in
                      ("HP", "HK", "HEAVY_CROSS"))
    hits = _drive(exe, script)
    assert hits[-3:] == [0, 0, 1]


def test_dois_pads_concorrentes_nao_se_misturam(tmp_path):
    """P1 tecla KEY_1 (toque) enquanto P2 segura KEY_2 alem de T."""
    exe = _build(tmp_path, T)
    script = []
    for tick in range(T + 1):
        p1 = K_LP if tick < 2 else 0
        p2 = K_HP                                     # P2 segura o tempo todo
        script += [f"t 0 {p1} 0", f"t 1 {p2} 1"]
        if tick in (2, T - 1):
            for who in (0, 1):
                for name in ("LP", "HP", "LK", "HK"):
                    script.append(f"q {who} {_idx(name)}")
    hits = _drive(exe, script)
    assert len(hits) == 16
    # consulta na ordem: tick2 (P1 LP HP LK HK) P2(...), tick T-1 (P1..) P2(..)
    tick2_p1, tick2_p2, tickT_p1, tickT_p2 = hits[:4], hits[4:8], hits[8:12], hits[12:]
    assert tick2_p1 == [1, 0, 0, 0]        # P1: fraco de soco, nada de chute
    assert tick2_p2 == [0, 0, 0, 0]        # P2 ainda nao liberou nada
    assert tickT_p1 == [0, 0, 0, 0]        # P1 ja consumiu seu pulso
    assert tickT_p2 == [0, 0, 0, 1]        # P2: forte de chute no proprio anel


def test_direcoes_decodificadas_pelo_lado_de_cada_ator(tmp_path):
    """F = para o oponente: P1 olhando a direita usa RIGHT, P2 olhando a esquerda usa LEFT."""
    exe = _build(tmp_path, T)
    script = []
    for tick in range(4):
        script += ["t 0 8 0", "q 0 " + str(_idx("FF")),     # P1 virado p/ direita
                   "t 1 4 1", "q 1 " + str(_idx("FF"))]     # P2 virado p/ esquerda
    hits = _drive(exe, script)
    assert hits == [0, 0, 1, 1, 1, 1, 1, 1]   # 1o tick: ainda falta o segundo passo

    exe2 = _build(tmp_path, T)
    script2 = []
    for tick in range(4):
        script2 += ["t 0 4 0", "q 0 " + str(_idx("FF"))]    # RIGHT errado p/ quem
    hits2 = _drive(exe2, script2)                           # olha a direita
    assert hits2 == [0, 0, 0, 0]


def test_blob_sem_a_versao_do_formato_reprova(tmp_path):
    exe = _build(tmp_path, T)
    script = ["t 0 16 0", "t 0 0 0",
              "q 0 " + str(_idx("V1")), "q 0 " + str(_idx("LP"))]
    hits = _drive(exe, script)
    assert hits == [0, 1]        # o legado nao casa; o atual casa (controlo valido)


def test_tier_fora_da_capacidade_da_maquina_reprova(tmp_path):
    """A maquina de runtime tem UM limiar: campo 3 nao e distinguivel, falha fechado."""
    exe = _build(tmp_path, T)
    script = ["t 0 16 0", "t 0 0 0", "q 0 " + str(_idx("T3"))]
    assert _drive(exe, script) == [0]


def test_bits_reservados_no_blob_cmd_v3_falham_fechado(tmp_path):
    exe = _build(tmp_path, T)
    script = ["t 0 16 0", "t 0 0 0",
              f"q 0 {_idx('BAD_FLAGS')}", f"q 0 {_idx('BAD_WANT')}"]
    assert _drive(exe, script) == [0, 0]


def test_busy_marca_o_frame_da_soltura_onde_o_fraco_nasce(tmp_path):
    """`fight_step` tem um atalho de idle que nao roda o passo cheio; sem este
    sinal o fraco (que nasce no tick em que a tecla JA solta) seria perdido."""
    exe = _build(tmp_path, T)
    script = ["t 0 16 0", "b 0",          # tecla 1 pressionada: ocupado
              "t 0 0 0", "b 0",           # soltura: o pulso nasce neste frame
              "t 0 0 0", "b 0"]           # nem nivel, nem pulso: livre de novo
    assert _drive(exe, script) == [1, 1, 0]


def test_busy_e_por_ator_um_pad_nao_acorda_o_outro(tmp_path):
    exe = _build(tmp_path, T)
    script = ["t 0 0 0", "t 1 8 0", "b 0", "b 1"]
    assert _drive(exe, script) == [0, 1]


def test_direcional_segurado_ocupa_e_solto_libera_o_atalho(tmp_path):
    """Andar mantem o passo cheio; ao soltar, o idle volta ao atalho — o mesmo
    orcamento de linha de scanline do idle puro continua valendo."""
    exe = _build(tmp_path, T)
    held = []
    for _ in range(4):
        held += ["t 0 2 0", "b 0"]                     # Down segurado
    assert _drive(exe, held) == [1, 1, 1, 1]
    assert _drive(_build(tmp_path, T), ["t 0 2 0", "b 0",
                                        "t 0 0 0", "b 0"]) == [1, 0]


def test_janela_de_multipasso_exige_os_dois_direcionais(tmp_path):
    """FF = F,F: um so tick de direcional nao monta o passo duplo dentro da janela."""
    exe = _build(tmp_path, T)
    script = ["t 0 8 0", "q 0 " + str(_idx("FF")), "t 0 0 0",
              "q 0 " + str(_idx("FF"))]
    hits = _drive(exe, script)
    assert hits == [0, 0]
    exe2 = _build(tmp_path, T)
    script2 = ["t 0 8 0", "t 0 8 0", "q 0 " + str(_idx("FF"))]
    assert _drive(exe2, script2) == [1]


def test_modificador_four_way_casa_cardinal_e_diagonais_vizinhas(tmp_path):
    exe = _build(tmp_path, T)
    down_script = []
    for levels in (K_DOWN, K_DOWN | K_LEFT, K_DOWN | K_RIGHT):
        down_script += [f"t 0 {levels} 0", f"q 0 {_idx('FLEX_D')}"]
    forward_script = [f"t 0 {K_LEFT} 0", f"q 0 {_idx('FLEX_F')}"]
    for levels in (K_RIGHT, K_UP | K_RIGHT, K_DOWN | K_RIGHT):
        forward_script += [f"t 0 {levels} 0", f"q 0 {_idx('FLEX_F')}"]
    hold_script = []
    for levels in (K_RIGHT, K_UP | K_RIGHT, K_DOWN | K_RIGHT):
        hold_script += [f"t 0 {levels} 0", f"q 0 {_idx('HOLD_FLEX_F')}"]
    assert _drive(exe, down_script) == [1, 1, 1]
    assert _drive(exe, forward_script) == [0, 1, 1, 1]
    assert _drive(exe, hold_script) == [1, 1, 1]


def test_rising_tackle_carga_temporizada_casa_fora_do_anel_de_16_amostras(tmp_path):
    exe = _build(tmp_path, T)
    script = []
    for _ in range(14):
        script.append(f"t 0 {K_DOWN} 0")
    for sample in (0, K_UP, K_HP, 0):
        script.append(f"t 0 {sample} 0")
    script.append(f"q 0 {_idx('RISING')}")
    script.append("r")
    for _ in range(15):
        script.append(f"t 0 {K_DOWN} 0")
    for sample in (0, K_UP, K_HP, 0):
        script.append(f"t 0 {sample} 0")
    script.extend([f"q 0 {_idx('RISING')}", f"q 0 {_idx('RISING')}"])
    assert _drive(exe, script) == [0, 1, 0]


def test_rising_tackle_four_way_charge_releases_down_from_a_diagonal(tmp_path):
    exe = _build(tmp_path, T)
    script = [f"t 0 {K_DOWN | K_LEFT} 0" for _ in range(15)]
    for sample in (K_LEFT, K_UP, K_HP, 0):
        script.append(f"t 0 {sample} 0")
    script.append(f"q 0 {_idx('RISING')}")
    assert _drive(exe, script) == [1]


def test_terry_rising_tackle_y_requires_strong_tier_after_timed_charge(tmp_path):
    exe = _build(tmp_path, T)
    script = [f"t 0 {K_DOWN} 0" for _ in range(15)]
    script.extend([f"t 0 0 0", f"t 0 {K_UP} 0"])
    for _ in range(T):
        script.extend([f"t 0 {K_LP} 0", f"q 0 {_idx('RISING_TERRY_Y')}"])
    hits = _drive(exe, script)
    assert hits == [0] * (T - 1) + [1]


def test_timed_release_saturates_at_the_full_uint8_charge_boundary(tmp_path):
    exe = _build(tmp_path, T)

    def probe(charge_ticks: int) -> list[int]:
        script = [f"t 0 {K_DOWN} 0" for _ in range(charge_ticks)]
        script.extend([f"t 0 0 0", f"t 0 {K_UP} 0", f"t 0 {K_LP} 0",
                       f"t 0 0 0", f"q 0 {_idx('RISING_TERRY_X255')}"])
        return _drive(exe, script)

    assert probe(254) == [0]
    assert probe(255) == [1]


def test_release_temporizado_sem_four_way_rejeita_a_carga_diagonal(tmp_path):
    exe = _build(tmp_path, T)
    script = [f"t 0 {K_DOWN | K_LEFT} 0" for _ in range(15)]
    for sample in (K_LEFT, K_UP, K_HP, 0):
        script.append(f"t 0 {sample} 0")
    script.append(f"q 0 {_idx('RISING_EXACT')}")
    assert _drive(exe, script) == [0]


def test_v3_blob_permanece_aceito_durante_migracao(tmp_path):
    exe = _build(tmp_path, T)
    assert _drive(exe, ["t 0 16 0", "t 0 0 0",
                        f"q 0 {_idx('LEGACY_V3')}"]) == [1]


def test_flush_esquece_pulso_pendente_sem_tocar_no_outro_ator(tmp_path):
    """Um pulso de tier mora no anel por INPUT_BUF ticks. Entre um round e o
    proximo a ROM nao da tick de input; sem descarte, o primeiro frame de luta
    dispararia o golpe do round anterior. O flush e por ator: o P2 nao perde o
    toque dele porque o P1 entrou no round com a mao no botao."""
    exe = _build(tmp_path, T)
    script = ["t 0 %d 0" % K_LP, "t 0 %d 0" % K_LP, "t 0 0 0",
              "t 1 %d 0" % K_LP, "t 1 %d 0" % K_LP, "t 1 0 0",
              "f 0", "q 0 %d" % _idx("LP"), "q 1 %d" % _idx("LP")]
    assert _drive(exe, script) == [0, 1]


def test_flush_de_um_ator_nao_libera_o_atalho_do_outro(tmp_path):
    exe = _build(tmp_path, T)
    script = ["t 0 %d 0" % K_LP, "t 1 2 0", "b 1", "f 0", "b 1"]
    assert _drive(exe, script) == [1, 1]


def _idle(who: int, ticks: int) -> list[str]:
    return ["t %d 0 0" % who for _ in range(ticks)]


def test_mar_de_ticks_ociosos_nao_muda_o_toque_que_chega_depois(tmp_path):
    """O corpo de `input_tick` custa ~13 linhas de scanline por ator (medido por
    `diag_step_attr.py` contra a ROM) e o idle nao pode paga-las. O atalho tem
    de ser OBSERVACIONALMENTE identico ao corpo: mesma mar, mesmo toque, mesmas
    consultas — e o toque tem de casar, senão a igualdade vazia não prova nada."""
    exe = _build(tmp_path, T)
    tap, _ = _tap(0, 2, K_LP, queries=("LP", "HP"))
    com_mar = _drive(exe, _idle(0, 40) + tap)
    sem_mar = _drive(_build(tmp_path, T), tap)
    assert com_mar == sem_mar
    assert 1 in com_mar


def test_pulso_solto_antes_da_mar_casa_no_primeiro_tick_ocioso(tmp_path):
    """O FRACO nasce no tick em que a tecla JA foi solta (doc/22). Se o atalho
    tambem zerasse a maquina de tier, o golpe se perderia neste tick; se a
    maquina corresse duas vezes, o golpe se repetiria nos 20 ticks seguintes."""
    exe = _build(tmp_path, T)
    script = ["t 0 %d 0" % K_LP, "t 0 %d 0" % K_LP,
              "q 0 %d" % _idx("LP")]                    # ainda segurado: nada
    script += ["t 0 0 0", "b 0", "q 0 %d" % _idx("LP")]  # 1o ocioso: o fraco
    for _ in range(20):
        script += ["t 0 0 0", "q 0 %d" % _idx("LP")]
    hits = _drive(exe, script)
    assert hits[0] == 0 and hits[1] == 1 and hits[2] == 1
    assert hits[3:] == [0] * (len(hits) - 3)


def test_duas_pastas_separadas_pela_mar_nao_formam_passo_duplo(tmp_path):
    """FF exige os dois passos dentro da janela do blob (15 ticks). O atalho tem
    de ADVANCAR o relogio do anel: congelar `buf_i` durante a mar deixaria o
    primeiro F a um tick do segundo e o especial dispararia depois de 40 frames
    de repouso."""
    exe = _build(tmp_path, T)
    script = ["t 0 %d 0" % K_RIGHT] + _idle(0, 40)
    script += ["t 0 %d 0" % K_RIGHT, "q 0 %d" % _idx("FF")]
    assert _drive(exe, script) == [0]
    exe2 = _build(tmp_path, T)
    assert _drive(exe2, ["t 0 %d 0" % K_RIGHT, "t 0 %d 0" % K_RIGHT,
                         "q 0 %d" % _idx("FF")]) == [1]


def test_mar_direcional_nunca_casa_golpe_e_o_toque_que_chega_depois_sai(tmp_path):
    """Andar e o estado sustentado mais comum da luta: 20 ticks com o anel cheio
    de direcional e nenhum pulso. Hoje cada um desses ticks varre as 16 amostras
    nos QUATRO padroes de ataque para concluir 0. Este teste e a fronteira que o
    atalho por pulso tem de manter: veredicto 0 em todos, e o toque logo apos a
    mar casa -- sem ele a igualdade dos zeros seria vazia."""
    exe = _build(tmp_path, T)
    script, asked = [], []
    for _ in range(20):
        script.append("t 0 %d 0" % K_RIGHT)
        for name in ("LP", "HP", "LK", "HK"):
            script.append("q 0 %d" % _idx(name))
            asked.append(name)
    script += ["t 0 %d 0" % (K_RIGHT | K_LP), "t 0 0 0",
               "q 0 %d" % _idx("LP")]
    hits = _drive(exe, script)
    assert set(hits[:-1]) == {0}, hits
    assert hits[-1] == 1


def _mar(seed: int) -> tuple[list[str], list[int]]:
    """Mar deterministica: dois atores, duas facing, toques de 1 a 9 ticks
    (cruzando T=6 pelos dois lados), diagonais, guarda, solturas e descartes.

    Retorna (script, aridades): `q` devolve 1 numero, `i` devolve 3. As
    aridades ficam do lado de quem montou o script para a leitura nao depender
    de adivinhar onde cada linha caiu."""
    import random
    rnd = random.Random(seed)
    niveles = [0, K_LP, K_HP, K_LP | K_HP, K_RIGHT, K_LEFT, K_DOWN,
               K_DOWN | K_LEFT, K_RIGHT | K_DOWN, K_UP,
               K_LEFT | K_HP, K_RIGHT | K_LP]
    ataque = [n for n in PATTERNS if n not in ("V1", "T3")]
    so_movimento = ["FF", "CROSS"]        # nenhum casa com um pulso solo de K1
    script: list[str] = []
    aridades: list[int] = []
    for tick in range(120):
        if tick and tick % 37 == 0:
            script.append("f %d" % rnd.randint(0, 1))
            continue
        for who in (0, 1):
            script.append("t %d %d %d" % (who, rnd.choice(niveles), who))
            script.append("i %d" % who)           # antes: o pulso ainda vivo
            aridades.append(4)
            for name in (so_movimento if tick % 3 == 0 else ataque):
                script.append("q %d %d" % (who, _idx(name)))
                aridades.append(1)
            script.append("i %d" % who)           # depois: consumo visivel
            aridades.append(4)
    return script, aridades


def test_contadores_do_anel_igualam_a_propria_recontagem_em_cada_tick(tmp_path):
    """Oraculo branco do contador.

    `nonzero` e a premissa de que `input_pattern_hit` depende para varrer (ou
    nao) as 16 amostras, e o atalho de ociosidade de `input_tick` depende dele
    para pular o corpo. Nenhum teste conferia esse contador contra o proprio
    anel: por baixo ele silencia golpe, por cima só custa tempo -- e o proximo
    contador da mesma familia (o de pulso) tem de satisfazer a mesma igualdade.
    Cada ator da dois checkpoints por tick -- antes e depois das consultas --
    porque o consumo (`q` casa e limpa o pulso) e o descarte (`f`) sao os dois
    caminhos que podem descompassar uma contagem, e porque um pulso que nenhum
    padrao consultado consome tem de continuar no anel."""
    exe = _build(tmp_path, T)
    script, aridades = _mar(20261003)
    vals = _drive(exe, script)
    linhas, pos = [], 0
    for n in aridades:
        linhas.append(vals[pos:pos + n])
        pos += n
    assert pos == len(vals), "saida do harness nao bate com o script"

    consultas = [r[0] for r in linhas if len(r) == 1]
    inv = [r for r in linhas if len(r) == 4]
    assert len(inv) == len([s for s in script if s.startswith("i ")])
    assert 1 in consultas, "mar sem golpe nao testa consumo"
    for anel, nz, viv, puls in inv:
        assert nz == anel, (anel, nz, viv, puls)
        assert puls == viv, (anel, nz, viv, puls)
        assert viv <= anel, (anel, nz, viv, puls)
    antes, depois = inv[0::2], inv[1::2]
    assert any(r[2] > 0 for r in antes), "mar sem pulso vivo no anel"
    assert any(r[2] > 0 for r in depois), ("pulso que nenhum padrao consultado "
                                           "consome sumiu do anel")
    assert any(r[2] == 0 for r in depois), "mar sem tick de anel limpo"
