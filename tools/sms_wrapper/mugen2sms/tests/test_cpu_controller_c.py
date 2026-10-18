"""Host harness for the asset-independent CPU policy and pad adapter.

The same K_* levels emitted by input_pad_levels() are fed through the real
input ring, so a controller light tap must produce the converted MUGEN `a`
command event. This does not validate the controller in an SMS ROM.
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
from mugen2sms.converters import sms_cmd  # noqa: E402
from mugen2sms.converters.sms_controls import ControlMap, DEFAULT_MAP  # noqa: E402
from mugen2sms.parsers import cmd as cmdmod  # noqa: E402

pytestmark = pytest.mark.skipif(shutil.which("gcc") is None, reason="gcc ausente")


def _light_blob() -> bytes:
    steps, errors = cmdmod.parse_command_string("a")
    command = cmdmod.Command("LP", steps, 15, 1, 1, "a", errors)
    patterns, skipped = sms_cmd.to_patterns([command], DEFAULT_MAP)
    assert skipped == {}, skipped
    assert len(patterns) == 1
    return sms_cmd.serialize_pattern(patterns[0])


HARNESS = r'''
#include <stdio.h>
#include "cpu_controller.h"
#include "input.h"

static const unsigned char light[] = { CPU_INPUT_KEY_1, 0u };
static const unsigned char special[] = { CPU_INPUT_KEY_2, 0u };
static const unsigned char escape[] = { CPU_INPUT_UP | CPU_INPUT_FORWARD };
static const unsigned char air_attack[] = { CPU_INPUT_KEY_2 };

static const CpuMove basic[] = {
    { light, 2u, 0u, 8u, 40u, 0u, 180u, 2u }
};

static void base_observation(CpuObservation *o) {
    o->self_x = 100u; o->opponent_x = 124u; o->self_facing = 0u;
    o->self_alive = 1u; o->self_can_act = 1u; o->self_airborne = 0u;
    o->self_at_left_edge = 0u; o->self_at_right_edge = 0u;
    o->self_energy = 0u; o->self_life_band = 2u;
    o->opponent_life_band = 2u; o->opponent_alive = 1u;
    o->opponent_airborne = 0u; o->opponent_guarding = 0u;
    o->opponent_recovery_ticks = 0u; o->opponent_attack_visible = 0u;
    o->opponent_attack_height = CPU_THREAT_NONE;
    o->self_last_interaction = CPU_INTERACTION_NONE;
}

#define CHECK(condition, code) do { \
    if (!(condition)) { printf("FAIL %u\n", (unsigned)(code)); return (code); } \
} while (0)

int main(void) {
    CpuObservation o;
    CpuController a, b;
    unsigned char i, out_a, out_b, presses, fired;
    CpuProfile const *easy, *normal, *hard;

    easy = cpu_controller_profile(CPU_DIFFICULTY_EASY);
    normal = cpu_controller_profile(CPU_DIFFICULTY_NORMAL);
    hard = cpu_controller_profile(CPU_DIFFICULTY_HARD);
    CHECK(easy->reaction_ticks > normal->reaction_ticks &&
          normal->reaction_ticks > hard->reaction_ticks, 1);
    CHECK(easy->aggression < normal->aggression &&
          normal->aggression < hard->aggression, 2);
    CHECK(hard->guard_chance < 255u, 3); /* Hard não lê perfeitamente */

    /* O mesmo seed, snapshot e lista geram a mesma trilha; o bot não fica
     * preso em idle nem segura a tecla como um evento repetido infinito. */
    base_observation(&o);
    cpu_controller_init(&a, CPU_DIFFICULTY_HARD, 1u);
    cpu_controller_init(&b, CPU_DIFFICULTY_HARD, 1u);
    presses = 0u;
    for (i = 0; i < 100u; i++) {
        out_a = cpu_controller_step(&a, &o, basic, 1u);
        out_b = cpu_controller_step(&b, &o, basic, 1u);
        CHECK(out_a == out_b, 4);
        if (out_a & K_LP) presses++;
    }
    CHECK(presses >= 3u, 5);

    /* Distância fora do alcance aproxima; facing espelhado inverte somente
     * a direção física e conserva os bits de ação. */
    base_observation(&o); o.opponent_x = 200u;
    cpu_controller_init(&a, CPU_DIFFICULTY_NORMAL, 1u);
    CHECK(cpu_controller_step(&a, &o, basic, 1u) == K_RIGHT, 6);
    o.self_x = 200u; o.opponent_x = 100u; o.self_facing = 1u;
    cpu_controller_init(&a, CPU_DIFFICULTY_NORMAL, 1u);
    CHECK(cpu_controller_step(&a, &o, basic, 1u) == K_LEFT, 7);

    /* A receding opponent remains a chase target; an advancing opponent that
     * enters the range band becomes attackable without a character-specific C
     * branch. */
    base_observation(&o); o.opponent_x = 200u;
    cpu_controller_init(&a, CPU_DIFFICULTY_HARD, 1u);
    CHECK(cpu_controller_step(&a, &o, basic, 1u) == K_RIGHT, 19);
    o.opponent_x = 150u;
    CHECK(cpu_controller_step(&a, &o, basic, 1u) == K_RIGHT, 20);
    o.opponent_x = 124u;
    CHECK(cpu_controller_step(&a, &o, basic, 1u) & K_LP, 21);
    o.opponent_x = 200u;
    cpu_controller_init(&a, CPU_DIFFICULTY_HARD, 1u);
    CHECK(cpu_controller_step(&a, &o, basic, 1u) == K_RIGHT, 22);

    /* Só começa a defender depois que a animação de ataque ficou visível e
     * passou o atraso de reação. HIGH = recuo; LOW = recuo + baixo. */
    base_observation(&o); o.opponent_attack_visible = 1u;
    o.opponent_attack_height = CPU_THREAT_HIGH;
    cpu_controller_init(&a, CPU_DIFFICULTY_HARD, 1u);
    for (i = 0; i < hard->reaction_ticks; i++)
        CHECK(cpu_controller_step(&a, &o, basic, 1u) == 0u, 8);
    CHECK(cpu_controller_step(&a, &o, basic, 1u) == K_LEFT, 9);
    o.opponent_attack_height = CPU_THREAT_LOW;
    cpu_controller_init(&a, CPU_DIFFICULTY_HARD, 1u);
    for (i = 0; i < hard->reaction_ticks; i++)
        (void)cpu_controller_step(&a, &o, basic, 1u);
    CHECK(cpu_controller_step(&a, &o, basic, 1u) == (K_LEFT | K_DOWN), 10);
    o.opponent_attack_visible = 0u;
    cpu_controller_init(&a, CPU_DIFFICULTY_HARD, 1u);
    CHECK(cpu_controller_step(&a, &o, basic, 1u) == K_LP, 11);

    /* Energia é pública: sem energia, o especial sai do conjunto; com a
     * energia mínima, seu script usa a mesma tecla 2 do pad humano. */
    {
        static const CpuMove energy_moves[] = {
            { light, 2u, 0u, 0u, 16u, 0u, 180u, 2u },
            { special, 2u, CPU_MOVE_SPECIAL, 20u, 40u, 3u, 240u, 2u }
        };
        base_observation(&o); o.opponent_x = 130u; o.self_energy = 2u;
        cpu_controller_init(&a, CPU_DIFFICULTY_HARD, 1u);
        out_a = cpu_controller_step(&a, &o, energy_moves, 2u);
        CHECK(!(out_a & K_HP), 12);
        o.self_energy = 3u;
        cpu_controller_init(&a, CPU_DIFFICULTY_HARD, 1u);
        CHECK(cpu_controller_step(&a, &o, energy_moves, 2u) == K_HP, 13);
    }

    /* A leitura do estado aéreo restringe a escolha a comandos anti-aéreos. */
    {
        static const CpuMove air_moves[] = {
            { light, 2u, 0u, 8u, 40u, 0u, 255u, 2u },
            { air_attack, 1u, CPU_MOVE_ANTIAIR, 8u, 40u, 0u, 1u, 2u }
        };
        base_observation(&o); o.opponent_airborne = 1u;
        cpu_controller_init(&a, CPU_DIFFICULTY_HARD, 1u);
        CHECK(cpu_controller_step(&a, &o, air_moves, 2u) == K_HP, 14);
    }

    /* Em canto, um comando de escape tem prioridade e mantém o facing físico. */
    {
        static const CpuMove escape_move[] = {
            { escape, 1u, CPU_MOVE_ESCAPE, 8u, 40u, 0u, 32u, 2u }
        };
        base_observation(&o); o.self_x = 240u; o.opponent_x = 216u;
        o.self_facing = 1u; o.self_at_right_edge = 1u;
        cpu_controller_init(&a, CPU_DIFFICULTY_HARD, 1u);
        CHECK(cpu_controller_step(&a, &o, escape_move, 1u) == (K_UP | K_LEFT), 15);
    }

    /* Uma janela de recuperação visível permite escolher o comando de
     * resposta; guarda pública recebe um spec marcado para VS_GUARD. */
    {
        static const CpuMove guard_moves[] = {
            { special, 2u, CPU_MOVE_VS_GUARD, 8u, 40u, 0u, 20u, 2u }
        };
        base_observation(&o); o.opponent_guarding = 1u;
        o.opponent_recovery_ticks = 4u;
        cpu_controller_init(&a, CPU_DIFFICULTY_EASY, 1u);
        CHECK(cpu_controller_step(&a, &o, guard_moves, 1u) == K_HP, 16);
    }

    /* A whiff event temporarily deprioritizes the exact command that missed,
     * then releases it after a finite delay. It cannot become a permanent lock. */
    base_observation(&o);
    cpu_controller_init(&a, CPU_DIFFICULTY_HARD, 1u);
    (void)cpu_controller_step(&a, &o, basic, 1u); /* press */
    (void)cpu_controller_step(&a, &o, basic, 1u); /* release */
    for (i = 0; i < (unsigned char)(hard->decision_ticks * 2u - 1u); i++) {
        o.self_last_interaction = i ? CPU_INTERACTION_NONE : CPU_INTERACTION_WHIFF;
        out_a = cpu_controller_step(&a, &o, basic, 1u);
        CHECK(!(out_a & (K_LP | K_HP)), 23);
    }
    o.self_last_interaction = CPU_INTERACTION_NONE;
    fired = 0u;
    for (i = 0; i < 32u; i++) {
        out_a = cpu_controller_step(&a, &o, basic, 1u);
        if (out_a & K_LP) { fired = 1u; break; }
    }
    CHECK(fired, 24);

    /* CPU P2 envia os mesmos níveis a input.c; um toque curto deve casar o
     * blob real de `a` no primeiro tick de soltura. */
    base_observation(&o);
    cpu_controller_init(&a, CPU_DIFFICULTY_HARD, 1u);
    input_init(); fired = 0u;
    for (i = 0; i < 8u; i++) {
        out_a = cpu_controller_step(&a, &o, basic, 1u);
        input_tick(1u, out_a, o.self_facing);
        if (input_pattern_hit(1u, P_LP)) fired++;
    }
    CHECK(fired >= 1u, 25);

    /* KO elimina toda a saída, inclusive movimento ou script já armado. */
    o.self_alive = 0u;
    cpu_controller_init(&a, CPU_DIFFICULTY_HARD, 1u);
    CHECK(cpu_controller_step(&a, &o, basic, 1u) == 0u, 26);

    puts("PASS cpu controller scenarios");
    return 0;
}
'''


def _patterns_header(tmp_path: Path) -> None:
    data = _light_blob()
    text = "\n".join([
        "#ifndef CPU_TEST_PATTERNS_H", "#define CPU_TEST_PATTERNS_H",
        f"#define P_LP_LEN {len(data)}",
        f"static const unsigned char P_LP[{len(data)}] = {{" +
        ", ".join(f"0x{b:02X}u" for b in data) + "};",
        "#endif", "",
    ])
    (tmp_path / "patterns_gen.h").write_text(text, encoding="utf-8")


def test_cpu_controller_and_pad_contract(tmp_path: Path):
    (tmp_path / "h.c").write_text(
        '#include "patterns_gen.h"\n' + HARNESS, encoding="utf-8")
    _patterns_header(tmp_path)
    exe = tmp_path / "cpu_harness"
    res = subprocess.run(
        ["gcc", "-Wall", "-Werror", "-std=c99",
         "-DINPUT_TIER_T=6", "-I", str(SRC / "inc"),
         "-I", str(SRC / "src"), "-I", str(tmp_path),
         str(tmp_path / "h.c"), str(SRC / "src/cpu_controller.c"),
         str(SRC / "src/input.c"), str(SRC / "src/input_tier.c"),
         "-o", str(exe)], capture_output=True, text=True)
    if res.returncode:
        raise AssertionError("compilacao de cpu_controller.c falhou:\n" + res.stderr)
    run = subprocess.run([str(exe)], capture_output=True, text=True)
    assert run.returncode == 0, run.stdout + run.stderr
    assert "PASS cpu controller scenarios" in run.stdout


RYO_HARNESS = r'''
#include <stdio.h>
#include "cpu_controller.h"
#include "input.h"
#include "patterns_gen.h"

static const unsigned char weak_1[] = { CPU_INPUT_KEY_1, 0u };
static const unsigned char strong_1[] = {
    CPU_INPUT_KEY_1, CPU_INPUT_KEY_1, CPU_INPUT_KEY_1,
    CPU_INPUT_KEY_1, CPU_INPUT_KEY_1, CPU_INPUT_KEY_1
};
static const unsigned char weak_2[] = { CPU_INPUT_KEY_2, 0u };
static const unsigned char strong_2[] = {
    CPU_INPUT_KEY_2, CPU_INPUT_KEY_2, CPU_INPUT_KEY_2,
    CPU_INPUT_KEY_2, CPU_INPUT_KEY_2, CPU_INPUT_KEY_2
};

static unsigned char run_command(const unsigned char *pattern,
                                 const unsigned char *samples,
                                 unsigned char sample_count) {
    CpuObservation o = {
        100u, 124u, 0u, 1u, 1u, 0u, 0u, 0u, 0u, 2u, 2u,
        1u, 0u, 0u, 0u, CPU_THREAT_NONE, CPU_INTERACTION_NONE
    };
    CpuController cpu;
    CpuMove move = { samples, sample_count, 0u, 0u, 255u, 0u, 255u, 2u };
    unsigned char i, hits = 0u, out;
    cpu_controller_init(&cpu, CPU_DIFFICULTY_HARD, 1u);
    cpu.script_active = 1u;
    cpu.script_move = 0u;
    input_init();
    for (i = 0u; i < sample_count; i++) {
        out = cpu_controller_step(&cpu, &o, &move, 1u);
        input_tick(1u, out, o.self_facing);
        if (input_pattern_hit(1u, pattern)) hits++;
    }
    return hits;
}

#define CHECK(condition, code) do { \
    if (!(condition)) { printf("FAIL %u\\n", (unsigned)(code)); return (code); } \
} while (0)

int main(void) {
    CHECK(run_command(P_X, weak_1, 2u) == 1u, 1); /* Ryo LP: x, KEY_1 tap */
    CHECK(run_command(P_Z, strong_1, 6u) == 1u, 2); /* Ryo HP: z, KEY_1 hold */
    CHECK(run_command(P_A, weak_2, 2u) == 1u, 3); /* Ryo LK: a, KEY_2 tap */
    CHECK(run_command(P_C, strong_2, 6u) == 1u, 4); /* Ryo HK: c, KEY_2 hold */
    puts("PASS Ryo CPU button families");
    return 0;
}
'''


def _ryo_patterns_header(tmp_path: Path) -> None:
    controls = ControlMap({"1": ["x", "z"], "2": ["a", "c"]},
                          {"1": [6], "2": [6]}, dropped=("b", "y"))
    entries = []
    for button in ("x", "z", "a", "c"):
        data = _command_blob(button, controls)
        entries.append(
            f"static const unsigned char P_{button.upper()}[{len(data)}] = {{" +
            ", ".join(f"0x{byte:02X}u" for byte in data) + "};")
    text = "\n".join(["#ifndef CPU_RYO_PATTERNS_H", "#define CPU_RYO_PATTERNS_H",
                       *entries, "#endif", ""])
    (tmp_path / "patterns_gen.h").write_text(text, encoding="utf-8")


def _command_blob(button: str, controls: ControlMap) -> bytes:
    steps, errors = cmdmod.parse_command_string(button)
    command = cmdmod.Command(button, steps, 15, 1, 1, button, errors)
    patterns, skipped = sms_cmd.to_patterns([command], controls)
    assert not skipped, skipped
    assert len(patterns) == 1
    return sms_cmd.serialize_pattern(patterns[0])


def test_cpu_button_scripts_match_ryo_command_families(tmp_path: Path):
    """CPU logical samples reach the per-character Ryo x/z and a/c patterns."""
    _ryo_patterns_header(tmp_path)
    (tmp_path / "h.c").write_text(RYO_HARNESS, encoding="utf-8")
    exe = tmp_path / "cpu_ryo_harness"
    res = subprocess.run(
        ["gcc", "-Wall", "-Werror", "-std=c99", "-DINPUT_TIER_T=6",
         "-I", str(SRC / "inc"), "-I", str(SRC / "src"), "-I", str(tmp_path),
         str(tmp_path / "h.c"), str(SRC / "src/cpu_controller.c"),
         str(SRC / "src/input.c"), str(SRC / "src/input_tier.c"),
         "-o", str(exe)], capture_output=True, text=True)
    if res.returncode:
        raise AssertionError("compilacao do contrato CPU/Ryo falhou:\n" + res.stderr)
    run = subprocess.run([str(exe)], capture_output=True, text=True)
    assert run.returncode == 0, run.stdout + run.stderr
    assert "PASS Ryo CPU button families" in run.stdout
