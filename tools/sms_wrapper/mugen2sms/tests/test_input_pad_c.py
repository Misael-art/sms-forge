"""Mapa final dos dois pads (doc/23, secao 6.B) — seis direcionais + duas teclas.

Compila `integrada/src/input_pad.c` no host (gcc), sem SMSlib. A autoridade
dos bits e o header do devkitSMS (`sdk/devkitSMS/SMSlib/SMSlib.h:296-302`),
entao este teste le o header e confere, bit a bit, contra o que o C produz:
se o SMSlib mudar um valor, o teste quebra em vez de a ROM ler o pad errado.

Cobre o furo que a ROM tinha: KEY_2 virava K_GUARD e os direcionais
continuavam mascarados (`main.c:read_pad` antigo).
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]
SRC = ROOT / "SMS_projects/luta_mugen/integrada"
SMSLIB_H = ROOT / "sdk/devkitSMS/SMSlib/SMSlib.h"
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

pytestmark = pytest.mark.skipif(shutil.which("gcc") is None, reason="gcc ausente")

# bits K_* de inc/input.h, repetidos aqui so para o teste poder conferir
K_UP, K_DOWN, K_LEFT, K_RIGHT, K_LP, K_HP, K_GUARD, K_SPECIAL = (
    0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80)

HARNESS = r'''
#include <stdio.h>
#include "input_pad.h"

int main(void) {
    unsigned int held;
    unsigned port;
    while (scanf("%u %u", &held, &port) == 2)
        printf("%u\n", (unsigned)input_pad_levels(held, (unsigned char)port));
    return 0;
}
'''


def _build(tmp_path: Path) -> Path:
    (tmp_path / "p.c").write_text(HARNESS, encoding="utf-8")
    exe = tmp_path / "pad"
    res = subprocess.run(
        ["gcc", "-Wall", "-Werror", "-std=c99", "-I", str(SRC / "inc"),
         str(tmp_path / "p.c"), str(SRC / "src/input_pad.c"), "-o", str(exe)],
        capture_output=True, text=True)
    if res.returncode:
        raise AssertionError("compilacao do mapa de pad falhou:\n" + res.stderr)
    return exe


def _drive(exe: Path, rows: list[tuple[int, int]]) -> list[int]:
    res = subprocess.run([str(exe)],
                         input="\n".join(f"{h} {p}" for h, p in rows) + "\n",
                         capture_output=True, text=True, check=True)
    out = [int(v) for v in res.stdout.split()]
    assert len(out) == len(rows), f"{len(out)} respostas para {len(rows)} linhas"
    return out


def _levels(exe: Path, held: int, port: int) -> int:
    return _drive(exe, [(held, port)])[0]


def _port_bits(name: str) -> dict[str, int]:
    """Le PORT_A_*/PORT_B_* do header do devkitSMS — a autoridade, nao a memoria.

    O header tambem define aliases por simbolo (`PORT_A_KEY_START PORT_A_KEY_1`),
    entao o valor e resolvido uma vez antes de virar numero.
    """
    text = SMSLIB_H.read_text(encoding="utf-8")
    raw = {m.group(1): m.group(2) for m in re.finditer(
        rf"#define\s+PORT_{name}_(KEY_\w+)\s+(\S+)", text)}

    def value(key: str) -> int:
        v = raw[key]
        if re.fullmatch(r"(0x[0-9A-Fa-f]+|\d+)", v):
            return int(v, 0)
        assert v.startswith(f"PORT_{name}_"), f"PORT_{name}_{key} -> {v}"
        return value(v.split("_", 2)[2])

    return {k: value(k) for k in raw}


def test_os_seis_bits_do_port_a_casam_com_o_smslib_header(tmp_path):
    exe = _build(tmp_path)
    bits = _port_bits("A")
    by_input = {"KEY_UP": K_UP, "KEY_DOWN": K_DOWN, "KEY_LEFT": K_LEFT,
                "KEY_RIGHT": K_RIGHT, "KEY_1": K_LP, "KEY_2": K_HP}
    assert set(bits) >= set(by_input), sorted(bits)
    rows = [(bits[n], 0) for n in by_input]
    for name, got in zip(by_input, _drive(exe, rows)):
        assert bits[name] == by_input[name], f"SMSlib mudou PORT_A_{name}"
        assert got == by_input[name], f"PORT_A_{name} decodificado como {got:02X}"


def test_os_seis_bits_do_port_b_casam_com_o_smslib_header(tmp_path):
    exe = _build(tmp_path)
    bits = _port_bits("B")
    by_input = {"KEY_UP": K_UP, "KEY_DOWN": K_DOWN, "KEY_LEFT": K_LEFT,
                "KEY_RIGHT": K_RIGHT, "KEY_1": K_LP, "KEY_2": K_HP}
    rows = [(bits[n], 1) for n in by_input]
    for name, got in zip(by_input, _drive(exe, rows)):
        assert bits[name] == by_input[name] << 6, f"SMSlib mudou PORT_B_{name}"
        assert got == by_input[name], f"PORT_B_{name} decodificado como {got:02X}"


def test_start_e_alias_da_tecla_1_e_nao_ganha_semantico_proprio(tmp_path):
    """inc/input_pad.h declara que START cai no mesmo bit de KEY_1; se o header
    do devkitSMS mudar isso, a ROM comeca round com o botao errado."""
    bits_a, bits_b = _port_bits("A"), _port_bits("B")
    assert bits_a["KEY_START"] == bits_a["KEY_1"]
    assert bits_b["KEY_START"] == bits_b["KEY_1"]
    exe = _build(tmp_path)
    assert _drive(exe, [(bits_a["KEY_START"], 0), (bits_b["KEY_START"], 1)]) == \
        [K_LP, K_LP]


def test_tecla_fisica_nunca_sintetiza_guarda_nem_especial(tmp_path):
    """Guarda e Down+Tras e especial vem de comando de movimento: nenhum bit
    fisico produz K_GUARD/K_SPECIAL — o antigo read_pad inventava K_GUARD.

    Varre os 4096 valores das duas palavras baixas: em porta A isso tambem
    prova que os bits do segundo pad (0x40..) nao vazam para o P1.
    """
    exe = _build(tmp_path)
    rows = [(held, port) for port in (0, 1) for held in range(0x1000)]
    bad = [(held, port, got) for (held, port), got in zip(rows, _drive(exe, rows))
           if got & (K_GUARD | K_SPECIAL)]
    assert bad == []


def test_em_porta_a_os_bits_do_segundo_pad_nao_vazem(tmp_path):
    exe = _build(tmp_path)
    assert _drive(exe, [(0x0040, 0), (0xFF00, 0), (0x4000, 0), (0x8000, 1)]) == \
        [0, 0, 0, 0]


def test_nada_pressionado_e_nada_decodificado(tmp_path):
    exe = _build(tmp_path)
    assert _drive(exe, [(0, 0), (0, 1)]) == [0, 0]


def test_direcional_com_tecla_preserva_os_dois_bits(tmp_path):
    """A guarda exige Down+Tras juntos no MESMO frame: os bits coexistem."""
    exe = _build(tmp_path)
    assert _drive(exe, [(0x0002 | 0x0004 | 0x0010, 0),
                        (0x0080 | 0x0100 | 0x0400, 1)]) == [
        K_DOWN | K_LEFT | K_LP, K_DOWN | K_LEFT | K_LP]


# Escopo donor: le SMS_projects/luta_mugen (doc/ EIO na midia). Deselecionado por --project rev2.
pytestmark = pytest.mark.donor
