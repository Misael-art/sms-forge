"""Harness no host (gcc) do playerpush e do auto-facing (doc/23, secao 6.B).

`integrada/src/body.c` nao inclui SMSlib nem luta.h: recebe posicoes Q8.8 e
meias-larguras e devolve posicoes separadas. Assim a REGRA do corpo-a-corpo e
provada no host, e o fight.c vira so o chamador.

Cobre o achado L098 (`doc/curation/2026-10-01_l098_atraso_de_pose_visivel.json`:
"No cenario andar_frente, P1 atravessa P2 … Nao ha colisao de corpo"): com
separacao, atravessar e impossivel e o auto-facing nao inverte no meio do
caminho. Tambem cobre o negativo obrigatorio do handoff "bordas de arena com
push".
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]
SRC = ROOT / "SMS_projects/luta_mugen/integrada"

pytestmark = pytest.mark.skipif(shutil.which("gcc") is None, reason="gcc ausente")

X_MIN = 16 * 256               # borda util da arena, mesma de fight.c (Q8.8)
X_MAX = 240 * 256
W = 12                         # meia-largura de corpo, px


def _build(tmp_path: Path) -> Path:
    (tmp_path / "h.c").write_text(HARNESS, encoding="utf-8")
    exe = tmp_path / "body"
    res = subprocess.run(
        ["gcc", "-Wall", "-Werror", "-std=c99", "-I", str(SRC / "inc"),
         str(tmp_path / "h.c"), str(SRC / "src/body.c"), "-o", str(exe)],
        capture_output=True, text=True)
    if res.returncode:
        raise AssertionError("compilacao do body.c falhou:\n" + res.stderr)
    return exe


HARNESS = r'''
#include <stdio.h>
#include "body.h"

int main(void) {
    char op;
    while (scanf(" %c", &op) == 1) {
        if (op == 's') {
            Body a, b;
            unsigned ax, ay, aw, bx, by, bw, min_x, max_x;
            int moved;
            if (scanf("%u %u %u %u %u %u %u %u", &ax, &ay, &aw, &bx, &by,
                      &bw, &min_x, &max_x) != 8) return 2;
            a.x = ax; a.y = ay; a.half_w = (unsigned char)aw;
            b.x = bx; b.y = by; b.half_w = (unsigned char)bw;
            moved = body_separate(&a, &b, min_x, max_x);
            printf("%d %u %u\n", moved, a.x, b.x);
        } else if (op == 'f') {
            unsigned self_x, other_x;
            int current;
            if (scanf("%u %u %d", &self_x, &other_x, &current) != 3) return 3;
            printf("%u\n", (unsigned)body_facing(self_x, other_x,
                                                 (unsigned char)current));
        } else {
            return 4;
        }
    }
    return 0;
}
'''


def _drive(exe: Path, script: list[str]) -> list[list[int]]:
    res = subprocess.run([str(exe)], input="\n".join(script) + "\n",
                         capture_output=True, text=True, check=True)
    return [[int(v) for v in line.split()] for line in res.stdout.split("\n")
            if line.strip()]


def _sep(exe, ax, bx, ay=0, by=0, wa=W, wb=W, x_min=X_MIN, x_max=X_MAX):
    row = _drive(exe, [f"s {ax} {ay} {wa} {bx} {by} {wb} {x_min} {x_max}"])[0]
    return {"moved": row[0], "ax": row[1], "bx": row[2]}


def test_sobreposicao_no_chao_separa_pela_soma_das_meias_larguras(tmp_path):
    exe = _build(tmp_path)
    gap = 2 * W * 256                        # contato exato: nada a fazer aqui
    r = _sep(exe, 120 * 256, 120 * 256 + gap - 256)      # 1 px de sobreposicao
    assert r["moved"] == 1
    assert r["bx"] - r["ax"] == gap


def test_sem_sobreposicao_nada_se_move(tmp_path):
    exe = _build(tmp_path)
    r = _sep(exe, 100 * 256, 140 * 256)
    assert r == {"moved": 0, "ax": 100 * 256, "bx": 140 * 256}


def test_ator_no_ar_nao_empurra_nem_e_empurrado(tmp_path):
    """Linha de piso: o push so vale entre dois corpos no chao (pular por cima
    continua possivel; foi assim que o achado L098 separou andar de pulo)."""
    exe = _build(tmp_path)
    r = _sep(exe, 120 * 256, 122 * 256, ay=32 * 256)
    assert r == {"moved": 0, "ax": 120 * 256, "bx": 122 * 256}
    r2 = _sep(exe, 120 * 256, 122 * 256, by=32 * 256)
    assert r2 == {"moved": 0, "ax": 120 * 256, "bx": 122 * 256}


def test_fora_da_borda_o_empurrao_cai_todo_no_outro(tmp_path):
    """P1 encostado na borda esquerda: ele nao pode ser empurrado para fora,
    entao P2 absorve a separacao inteira (negativo 'bordas com push')."""
    exe = _build(tmp_path)
    r = _sep(exe, X_MIN, X_MIN + 2 * 256)    # 2 px de sobreposicao
    assert r["ax"] == X_MIN
    assert r["bx"] - r["ax"] == 2 * W * 256


def test_os_dois_encostados_na_mesma_borda_nao_atravessam(tmp_path):
    """Arena mais estreita que a separacao: o clamp vence, mas a ordem dos dois
    e preservada — ninguem passa para o outro lado e ninguem sai da arena."""
    exe = _build(tmp_path)
    r = _sep(exe, 0, 4 * 256, x_min=0, x_max=10 * 256)
    assert 0 <= r["ax"] <= r["bx"] <= 10 * 256
    assert r["bx"] - r["ax"] < 2 * W * 256        # nao deu para separar 24 px
    repeat = _sep(exe, r["ax"], r["bx"], x_min=0, x_max=10 * 256)
    assert (repeat["ax"], repeat["bx"]) == (r["ax"], r["bx"])   # nao anda mais


def test_empate_de_posicao_tem_desempate_deterministico(tmp_path):
    """Dois frames seguidos com a mesma entrada nao podem dar saidas diferentes:
    sem isso o auto-facing do L098 oscila entre dois lados."""
    exe = _build(tmp_path)
    a = _sep(exe, 120 * 256, 120 * 256)
    b = _sep(exe, 120 * 256, 120 * 256)
    assert a == b and a["moved"] == 1
    assert a["ax"] < a["bx"]


def test_andar_para_frente_nao_atravessa_o_adversario(tmp_path):
    """Reproduz o achado L098: P1 caminhando sobre P2 parava do outro lado e o
    auto-facing invertia o controle. Com push, a travessia e impossivel."""
    exe = _build(tmp_path)
    ax, bx = 96 * 256, 140 * 256
    inversions = []
    for _ in range(80):                       # 80 ticks de 1 px = 80 px andados
        ax += 256                             # fight.c aplica a velocidade primeiro
        r = _sep(exe, ax, bx)
        ax, bx = r["ax"], r["bx"]
        inversions.append(_drive(exe, [f"f {ax} {bx} 0"])[0][0])
    assert max(inversions) == 0               # nunca virou para tras
    assert ax < bx                            # nunca atravessou
    assert ax == bx - 2 * W * 256             # parou no contato


def test_auto_facing_decide_por_posicao_e_mantem_no_empate(tmp_path):
    exe = _build(tmp_path)
    rows = _drive(exe, ["f 100 200 1",        # adversario a direita -> 0
                        "f 200 100 0",        # adversario a esquerda -> 1
                        "f 100 100 0",        # empate mantem 0
                        "f 100 100 1"])       # empate mantem 1
    assert [r[0] for r in rows] == [0, 1, 0, 1]


def test_push_e_idempotente_aplicar_duas_vezes_nao_anda_mais(tmp_path):
    exe = _build(tmp_path)
    primeiro = _sep(exe, 120 * 256, 126 * 256)
    segundo = _sep(exe, primeiro["ax"], primeiro["bx"])
    assert segundo["moved"] == 0
    assert (segundo["ax"], segundo["bx"]) == (primeiro["ax"], primeiro["bx"])
