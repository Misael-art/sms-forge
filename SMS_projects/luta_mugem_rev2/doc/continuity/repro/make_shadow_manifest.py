#!/usr/bin/env python3
"""Manifesto SAT shadow generico (SMSlib; Y=0xC137, XN=0xC177, next=0xC1F7)."""
import json, sys
from pathlib import Path

SNAP, IDX, OUT, LABEL, ROM = sys.argv[1:6]
RAM = (Path(SNAP) / f"snapshots/{IDX}/ram.bin").read_bytes()
Y = RAM[0xC137 - 0xC000:0xC137 - 0xC000 + 64]
XN = RAM[0xC177 - 0xC000:0xC177 - 0xC000 + 128]
NEXT = RAM[0xC1F7 - 0xC000]
n = min(int(NEXT), 64)
sprites = [{"x": XN[2 * i], "y": int(Y[i]) + 1, "tile": XN[2 * i + 1],
            "sat_index": i, "stored_y": int(Y[i])} for i in range(n)]
doc = {
    "schema": "sprite_scene_manifest_v1",
    "sprite_size": "8x16", "zoomed": False, "screen_h": 192,
    "sat_terminated": False,
    "scene": f"{LABEL}_shadow_sat_frame_{IDX}",
    "source": {
        "emulator": "BlastEm 1.0.0",
        "snapshot": str(Path(SNAP) / "snapshots" / IDX),
        "method": "SMSlib shadow SAT (SpriteTableY 0xC137 / SpriteTableXN 0xC177); y=stored+1; valid entries = SpriteNextFree",
        "rom_sha256": ROM,
        "sprite_next_free": int(NEXT),
    },
    "sprites": sprites,
}
Path(OUT).write_text(json.dumps(doc, indent=1) + "\n")
print(f"{OUT}: {len(sprites)} sprites, next_free={int(NEXT)}")
