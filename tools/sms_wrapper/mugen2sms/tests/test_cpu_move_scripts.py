import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from mugen2sms.converters.sms_controls import DEFAULT_MAP
from mugen2sms.generators.cpu_move_scripts import (
    DEFAULT_TIER_TICKS,
    INPUT_KEY_1,
    INPUT_KEY_2,
    compile_command,
    serialize_command_pattern,
)
from mugen2sms.parsers import cmd as cmdmod

ROOT = Path(__file__).resolve().parents[4]
INTEGRATED = ROOT / "SMS_projects/luta_mugen/integrada"
pytestmark = pytest.mark.skipif(shutil.which("gcc") is None, reason="gcc ausente")


def _command(name: str, raw: str, time: int = 15) -> cmdmod.Command:
    steps, errors = cmdmod.parse_command_string(raw)
    return cmdmod.Command(name, steps, time, 1, 1, raw, errors)


def test_cpu_samples_reach_weak_strong_and_motion_command_levels():
    weak, weak_reason = compile_command(_command("lp", "a"))
    strong, strong_reason = compile_command(_command("hp", "c", time=1))
    wave, wave_reason = compile_command(_command("wave", "~D, DF, F, x"))

    assert weak_reason is None and weak == [INPUT_KEY_1, 0]
    assert strong_reason is None and strong == [INPUT_KEY_1] * DEFAULT_TIER_TICKS
    assert wave_reason is None
    assert wave == [0x04, 0, 0x05, 0x01, INPUT_KEY_2, 0]


def test_cpu_samples_support_four_way_and_fail_closed_for_other_unsupported_terms():
    four_way, why_four_way = compile_command(_command("charge", "/$D, DF, x"))
    timed, why_timed = compile_command(_command("rising", "~15$D, U, x", time=10))
    strict, why_strict = compile_command(_command("strict", ">D, DF, F, x"))
    medium, why_medium = compile_command(_command("mp", "b"))

    assert four_way == [0x04, 0x05, INPUT_KEY_2, 0]
    assert why_four_way is None
    assert timed == [0x04] * 15 + [0, 0x08, INPUT_KEY_2, 0]
    assert why_timed is None
    assert strict is None and why_strict == "strict-step-nao-suportado-no-runtime"
    assert medium is None and why_medium == "botao-sem-tier-no-mapa"


def test_script_fits_fixed_cpu_buffer_and_command_time_window():
    too_long, reason = compile_command(_command("long", "D, DF, F, D, DF, F, x", time=5))
    assert too_long is None
    assert reason in {"script-maior-que-anel-16", "script-excede-janela-time-do-cmd"}


def test_generated_scripts_trigger_real_input_ring_for_both_facings():
    cases = []
    for name, raw, command_time in (("lp", "a", 15), ("hp", "c", 15),
                                    ("powerwave", "~D, DF, F, x", 15),
                                    ("rising", "~15$D, U, x", 10)):
        command = _command(name, raw, command_time)
        samples, reason = compile_command(command)
        blob, pattern_reason = serialize_command_pattern(command, DEFAULT_MAP)
        assert reason is None and pattern_reason is None and blob is not None
        cases.append((samples, list(blob)))

    arrays = []
    checks = []
    for index, (samples, blob) in enumerate(cases):
        arrays.append(
            f"static const unsigned char samples_{index}[] = "
            f"{{ {', '.join(f'0x{x:02X}' for x in samples)} }};\n"
            f"static const unsigned char pattern_{index}[] = "
            f"{{ {', '.join(f'0x{x:02X}' for x in blob)} }};\n"
        )
        checks.extend([
            f"if (!run(samples_{index}, sizeof(samples_{index}), pattern_{index}, 0u)) return {index * 2 + 1};",
            f"if (!run(samples_{index}, sizeof(samples_{index}), pattern_{index}, 1u)) return {index * 2 + 2};",
        ])
    harness = r'''#include "cpu_controller.h"
#include "input.h"
''' + "".join(arrays) + r'''
static unsigned char run(const unsigned char *samples, unsigned char count,
                         const unsigned char *pattern, unsigned char facing) {
    unsigned char i;
    input_flush(0u);
    for (i = 0; i < count; i++) {
        unsigned char levels = cpu_controller_pad_levels(samples[i], facing);
        input_tick(0u, levels, facing);
        if (input_pattern_hit(0u, pattern)) return 1u;
    }
    return 0u;
}
int main(void) {
''' + "\n".join(checks) + r'''
    return 0;
}
'''
    with tempfile.TemporaryDirectory() as tmp:
        c_path = Path(tmp) / "cpu_move_scripts.c"
        exe_path = Path(tmp) / "cpu_move_scripts"
        c_path.write_text(harness, encoding="ascii")
        build = subprocess.run([
            "gcc", "-std=c99", "-I", str(INTEGRATED / "inc"), str(c_path),
            str(INTEGRATED / "src/cpu_controller.c"),
            str(INTEGRATED / "src/input.c"),
            str(INTEGRATED / "src/input_tier.c"), "-o", str(exe_path),
        ], capture_output=True, text=True)
        assert build.returncode == 0, build.stderr
        run = subprocess.run([str(exe_path)], capture_output=True, text=True)
        assert run.returncode == 0, run.stdout + run.stderr
