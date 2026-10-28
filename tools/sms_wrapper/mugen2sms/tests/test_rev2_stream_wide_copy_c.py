"""Verify the word-sized SMSlib transfer option without changing defaults."""
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


@pytest.mark.parametrize("wide", [0, 1])
def test_stream_copy_selects_declared_api_and_preserves_pair_byte_count(tmp_path, wide):
    source = SOURCE.read_text(encoding="utf-8")
    match = re.search(
        r"^#if LUTA_STREAM_WIDE_COPY\n#define STREAM_UPLOAD_PAIRS.*?^#endif",
        source, re.M | re.S,
    )
    assert match, "stream upload macro missing"
    snippet = r'''
#include <stdio.h>
static unsigned calls_wide, calls_brief;
static unsigned int last_size;
static void SMS_VRAMmemcpy(unsigned int dst, const void *src, unsigned int size) {
    (void)dst; (void)src; calls_wide++; last_size=size;
}
static void SMS_VRAMmemcpy_brief(unsigned int dst, const void *src,
                                 unsigned char size) {
    (void)dst; (void)src; calls_brief++; last_size=size;
}
''' + match.group() + r'''
#define REQUIRE(c,msg) do { if (!(c)) { puts(msg); return 1; } } while (0)
int main(void) {
    unsigned char pairs=3u;
    STREAM_UPLOAD_PAIRS(0x1000u, (const void *)0x8000u, pairs);
    REQUIRE(last_size==192u, "three pairs did not retain their byte count");
#if LUTA_STREAM_WIDE_COPY
    REQUIRE(calls_wide==1u && calls_brief==0u,
            "wide option did not select SMS_VRAMmemcpy");
#else
    REQUIRE(calls_wide==0u && calls_brief==1u,
            "default did not select SMS_VRAMmemcpy_brief");
#endif
    return 0;
}
'''
    program = tmp_path / f"stream_wide_{wide}.c"
    program.write_text(snippet, encoding="utf-8")
    exe = tmp_path / f"stream_wide_{wide}"
    compiled = subprocess.run(
        ["cc", "-std=c99", f"-DLUTA_STREAM_WIDE_COPY={wide}", str(program), "-o", str(exe)],
        capture_output=True, text=True,
    )
    assert compiled.returncode == 0, compiled.stderr
    result = subprocess.run([str(exe)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


def test_default_path_caps_brief_transfers_at_three_pairs():
    source = SOURCE.read_text(encoding="utf-8")
    assert "#if !LUTA_STREAM_WIDE_COPY\n        if (batch > 3u) batch = 3u;\n#endif" in source
    assert "STREAM_UPLOAD_PAIRS(vram, source, batch);" in source
