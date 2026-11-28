"""Exercise the source upload scheduler's aggregate quota and side rotation."""
from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[4]
SOURCE = ROOT / "SMS_projects/luta_mugem_rev2/src/main.c"
pytestmark = [pytest.mark.rev2,
              pytest.mark.skipif(shutil.which("cc") is None, reason="C compiler unavailable")]


def test_aggregate_upload_budget_redistributes_and_rotates(tmp_path):
    source = SOURCE.read_text(encoding="utf-8")
    match = re.search(
        r"^static unsigned char stream_pending_budget\([^\n]*\n?.*?^}",
        source,
        re.M | re.S,
    )
    assert match, "runtime upload scheduler missing"
    function = match.group()
    code = r'''
#include <stdio.h>
static unsigned char pending[2], calls[2];
static unsigned char stream_pending(unsigned char side, unsigned char budget) {
    unsigned char moved = pending[side] < budget ? pending[side] : budget;
    calls[side]++;
    pending[side] = (unsigned char)(pending[side] - moved);
    return moved;
}
''' + function + r'''
#define REQUIRE(c, msg) do { if (!(c)) { puts(msg); return 1; } } while (0)
static void reset(unsigned char p1, unsigned char p2) {
    pending[0] = p1; pending[1] = p2; calls[0] = calls[1] = 0u;
}
int main(void) {
    unsigned char p1, p2, total;

    reset(3u, 8u);
    total = stream_pending_budget(0u, 8u, &p1, &p2);
    REQUIRE(total == 8u && p1 == 3u && p2 == 5u,
            "unused first-side quota was not redistributed");
    REQUIRE(p1 + p2 <= 8u, "aggregate quota exceeded");

    reset(8u, 3u);
    total = stream_pending_budget(1u, 8u, &p1, &p2);
    REQUIRE(total == 8u && p1 == 5u && p2 == 3u,
            "reverse priority produced wrong trace sides");

    reset(8u, 8u);
    total = stream_pending_budget(0u, 8u, &p1, &p2);
    REQUIRE(total == 8u && p1 == 8u && p2 == 0u && calls[1] == 0u,
            "first side did not retain full quota when busy");
    total = stream_pending_budget(1u, 8u, &p1, &p2);
    REQUIRE(total == 8u && p1 == 0u && p2 == 8u,
            "rotating priority starved the second side");

    reset(8u, 8u);
    p1 = p2 = 99u;
    REQUIRE(stream_pending_budget(2u, 8u, &p1, &p2) == 0u &&
            p1 == 0u && p2 == 0u && calls[0] == 0u && calls[1] == 0u,
            "invalid first side was not rejected safely");
    REQUIRE(stream_pending_budget(0u, 0u, &p1, &p2) == 0u &&
            calls[0] == 0u && calls[1] == 0u, "zero budget touched a side");
    return 0;
}
'''
    program = tmp_path / "upload_scheduler.c"
    program.write_text(code, encoding="utf-8")
    exe = tmp_path / "upload_scheduler"
    compiled = subprocess.run(["cc", "-std=c99", str(program), "-o", str(exe)],
                              capture_output=True, text=True)
    assert compiled.returncode == 0, compiled.stderr
    result = subprocess.run([str(exe)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
