# Teste diferencial: input_tier.c (host, gcc) contra a referencia Python classify_trace.
# Desde 2026-10-03 o modulo esta ligado ao build da ROM (integrada/src) e o estado vive
# numa struct: dois pads = duas maquinas independentes (doc/23, 6.B).
import random
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]
SRC = ROOT / "SMS_projects/luta_mugen/integrada"
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from mugen2sms.converters.sms_controls import classify_trace   # noqa: E402

pytestmark = pytest.mark.skipif(shutil.which("gcc") is None or not (SRC / "src/input_tier.c").exists(),
                                reason="gcc ou input_tier.c ausente")

HARNESS = r'''
#include <stdio.h>
#include "input_tier.h"
int main(void) {
    InputTier t;
    unsigned v; int tick = 0;
    input_tier_init(&t);
    while (scanf("%u", &v) == 1) {
        unsigned char ev = input_tier_step(&t, (unsigned char)v);
        if (ev) printf("%d %u\n", tick, ev);
        tick++;
    }
    printf("%d %u\n", tick, (unsigned)input_tier_step(&t, 0));  /* tick sentinela */
    return 0;
}
'''


def _build(tmp_path, T):
    (tmp_path / "h.c").write_text(HARNESS)
    exe = tmp_path / f"h{T}"
    subprocess.run(["gcc", "-Wall", "-Werror", f"-DINPUT_TIER_T={T}", "-I", str(SRC / "inc"),
                    str(tmp_path / "h.c"), str(SRC / "src/input_tier.c"), "-o", str(exe)], check=True)
    return exe


def _run(exe, trace):
    out = subprocess.run([str(exe)], input=" ".join(map(str, trace)), capture_output=True, text=True,
                         check=True).stdout.split("\n")
    events = []
    for line in out:
        if not line:
            continue
        t, ev = map(int, line.split())
        for bit, (key, tier) in ((1, (0, 0)), (2, (0, 1)), (4, (1, 0)), (8, (1, 1))):
            if ev & bit:
                events.append((t, key, tier))
    return sorted(events)


@pytest.mark.parametrize("T", [6, 2, 10])
def test_c_matches_reference_on_random_traces(tmp_path, T):
    exe = _build(tmp_path, T)
    rng = random.Random(1234 + T)
    for _ in range(300):
        n = rng.randint(1, 40)
        trace, cur = [], rng.randint(0, 3)
        for _ in range(n):
            if rng.random() < 0.25:
                cur = rng.randint(0, 3)
            trace.append(cur)
        # o harness acrescenta 1 tick sentinela de soltura; a referencia faz o mesmo
        assert _run(exe, trace) == classify_trace(trace, T), trace


def test_worst_case_latency_is_T_minus_1(tmp_path):
    exe = _build(tmp_path, 6)
    assert _run(exe, [1] * 9) == [(5, 0, 1)]                 # forte no tick T-1
    assert _run(exe, [1] * 5 + [0]) == [(5, 0, 0)]           # fraco mais lento possivel: tambem T-1
    assert _run(exe, [2, 2, 0]) == [(2, 1, 0)]               # toque tipico de 2 ticks
