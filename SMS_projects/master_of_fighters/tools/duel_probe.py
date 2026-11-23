#!/usr/bin/env python3
"""Decode the Scene 02 GD05 probe from a paused frame or a binary fixture."""

import argparse
import json
import re
import struct
import sys
from pathlib import Path


HEADER = struct.Struct("<4sBBH")
ACTOR = struct.Struct("<10B10hHB")
RECORD_BYTES = HEADER.size + 2 * ACTOR.size
BOX_FIELDS = ("left", "top", "right", "bottom")


def decode_actor(fields):
    fighter, keys, state, tick, requested, resident, presented, contact, life, flags = fields[:10]
    x, y = fields[10:12]
    if keys & ~0x3F or flags & ~0x3F or flags & 0x30 == 0x20:
        raise ValueError("Invalid GD05 keys or flags")
    boxes = {}
    for name, mask, coords in (("attack", 4, fields[12:16]), ("hurt", 8, fields[16:20])):
        if flags & mask:
            left, top, right, bottom = coords
            if not (left < right and top < bottom):
                raise ValueError(f"Inverted or empty {name} box")
            boxes[name] = dict(zip(BOX_FIELDS, coords, strict=True))
        else:
            boxes[name] = None
    observed = {
        "fighter": fighter, "keys_consumed": keys, "state": state, "action_tick": tick,
        "pose_requested": requested, "pose_resident": resident, "pose_presented": presented,
        "pose_used_for_contact": fields[21],
        "contact": contact, "life": life, "facing_right": bool(flags & 1),
        "pivot": [x, y], "boxes": boxes, "can_act": bool(flags & 2), "free_since": fields[20],
    }
    if flags & 0x10:
        observed["presented_facing_right"] = bool(flags & 0x20)
    return observed


def decode(raw):
    if len(raw) != RECORD_BYTES:
        raise ValueError("Incorrect GD05 record size")
    magic, stamp, length, logic_tick = HEADER.unpack_from(raw)
    if magic != b"MFD1" or length != RECORD_BYTES or stamp & 1:
        raise ValueError("Missing, unknown or partially published GD05 record")
    return {
        "protocol": "MFD1", "stamp": stamp, "logic_tick": logic_tick,
        "p1": decode_actor(ACTOR.unpack_from(raw, HEADER.size)),
        "p2": decode_actor(ACTOR.unpack_from(raw, HEADER.size + ACTOR.size)),
    }


def read_paused_session(session, rom_sha256, address):
    root = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(root / "tools/sms_wrapper"))
    from session_bridge import isolated

    workspace, metadata = isolated.load(session)
    if metadata["rom_sha256"] != rom_sha256:
        raise ValueError("Session ROM SHA differs from the requested digest")
    first = isolated.request(workspace, "read", address, RECORD_BYTES)
    second = isolated.request(workspace, "read", address, RECORD_BYTES)
    if first["frame"] != second["frame"] or first["ram"] != second["ram"]:
        raise ValueError("RAM changed during sampling. Pause the session before reading.")
    return {
        "session_id": metadata["session_id"], "rom_sha256": rom_sha256,
        "vdp_frame": first["frame"], "address": address, "raw_hex": bytes(first["ram"]).hex(),
        **decode(bytes(first["ram"])),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--binary", type=Path)
    source.add_argument("--session")
    parser.add_argument("--rom-sha256")
    parser.add_argument("--address", type=lambda value: int(value, 0))
    args = parser.parse_args()
    if args.binary:
        result = {"source": "unbound_binary", **decode(args.binary.read_bytes())}
    else:
        if not re.fullmatch(r"[a-f0-9]{64}", args.rom_sha256 or ""):
            parser.error("Provide the exact ROM SHA-256 for a session read")
        if args.address is None or not 0xC000 <= args.address <= 0xE000 - RECORD_BYTES:
            parser.error("Provide the map-verified probe address in the SMS RAM window")
        result = read_paused_session(args.session, args.rom_sha256, args.address)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
