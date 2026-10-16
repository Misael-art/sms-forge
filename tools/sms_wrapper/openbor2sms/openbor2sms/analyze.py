# Ported from SGDK-Forge (donor), read-only source.
#   donor path : tools/openbor2sgdk_forge/openbor2sgdk_forge/analyze.py
#   donor sha256: 1b158959550a99ab81d2b78b0f7244f4a21737f9fab96976f6326fff378599dc
#   license    : MIT (SGDK-Forge LICENSE, sha256 0b685fab1e0d2e0a9f85a4356a91c7bb16126be7b06e899f6cfed155cad2cf24)
#   port date  : 2026-10-15 (SMSForge openbor2sms front-end O1)
# Body below is byte-identical to the donor file (verified by cmp at port time);
# no behavioral change.
"""Classify directives. Unknown reachable commands block the claim that uses them.

`supported_exact` copies a number or path unchanged.
`supported_adapted` is lowered with a named conversion.
`recognized_not_lowered` is a known OpenBOR command this slice does not execute.
`unknown` was not in the vocabulary. A required animation that contains one
cannot be emitted as gameplay.
"""

from __future__ import annotations

from .model_text import AnimDef, LevelFile, ModelFile

HOLD_DELAY_AT = 900

EXACT = {
    "name",
    "type",
    "health",
    "offset",
    "bbox",
    "frame",
    "loop",
    "coords",
    "flip",
    "spawn",
    "at",
    "map",
}

ADAPTED = {
    "delay",
    "attack",
    "speed",
    "jumpspeed",
    "jumpheight",
    "jumpmove",
    "grabdistance",
    "makeinv",
    "sound",
    "hitfx",
    "diesound",
    "music",
    "bossmusic",
    "background",
    "panel",
    "frontpanel",
}

# Known commands whose effect is recorded and intentionally not executed.
RECOGNIZED = {
    "mp",
    "nolife",
    "running",
    "turndelay",
    "mprate",
    "grabfinish",
    "grabback",
    "antigravity",
    "bounce",
    "noquake",
    "gfxshadow",
    "shadow",
    "flash",
    "bflash",
    "dust",
    "toflip",
    "modelflag",
    "load",
    "parrow",
    "parrow2",
    "parrow3",
    "parrow4",
    "com",
    "atchain",
    "combostyle",
    "nodieblink",
    "falldie",
    "riseinv",
    "icon",
    "icondie",
    "palette",
    "remap",
    "weapons",
    "mpset",
    "jugglecost",
    "cancel",
    "fastattack",
    "range",
    "followanim",
    "followcond",
    "jumpframe",
    "landframe",
    "flipframe",
    "damageonlanding",
    "move",
    "energycost",
    "mponly",
    "hitflash",
    "drawmethod",
    "nodrawmethod",
    "setlayer",
    "quake",
    "screen",
    "fshadow",
    "attackone",
    "counterattack",
    "blast",
    "freeze",
    "steal",
    "forcemap",
    "seal",
    "@script",
    "@end_script",
    "order",
    "settime",
    "notime",
    "stagenumber",
    "wall",
    "hole",
    "wait",
    "group",
    "direction",
    "bgspeed",
    "blocked",
    "loadingbg",
    "bglayer",
    "noslow",
    "item",
    "alias",
    "weapon",
    "credit",
    "scrollx",
    "scrollz",
    "light",
    "set",
    "next",
    "endlevel",
    "nojoin",
    "setweap",
    "spawnitem",
    "2phealth",
    "3phealth",
    "4phealth",
    "boss",
    "flavour",
    "canbepickedup",
    "nopassiveblock",
    "blockpain",
    "thold",
    "running",
    "jumpmove",
    "grabwalk",
    "grabturn",
    "throwdamage",
    "throwframewait",
    "pshotframe",
    "throwdist",
    "grabforce",
    "antigrab",
    "nodrop",
    "jumpframe",
    "landframe",
    "anim",
    "know",
    "spawn1",
    "spawn2",
    "spawn3",
    "spawn4",
    "mpset",
    "diesound",
    "facing",
    "defence",
    "offense",
    "knockdowncount",
    "falldie",
    "riseinv",
    "airjuggle",
    "jugglepoints",
    "jumpheight",
    "jumpspeed",
    "speedf",
    "speed",
    "type",
    "health",
    "name",
    "shadow",
    "gfxshadow",
    "holdblock",
    "blockodds",
    "blockpain",
    "nopain",
    "pain_sound",
    "die_sound",
    "respawn",
    "hmap",
    "iconpain",
    "iconget",
    "iconw",
    "iconmphigh",
    "iconmplow",
    "iconmpmed",
    "parrow",
    "score",
    "screentime",
    "summonframe",
    "unsummonframe",
    "weaponframe",
    "quakeframe",
    "rangez",
    "rangea",
    "rangeb",
    "rangex",
    "offset",
    "bbox",
    "delay",
    "frame",
    "loop",
    "sound",
    "hitfx",
    "music",
    "bossmusic",
    "background",
    "panel",
    "frontpanel",
    "coords",
    "flip",
    "spawn",
    "at",
    "map",
    "grabdistance",
    "makeinv",
    "attack",
}


def command_kind(command: str) -> str:
    """Classify a command token. Attack slots collapse to 'attack'."""
    base = "attack" if command.startswith("attack") and (command == "attack" or command[6:].isdigit()) else command
    if base in EXACT:
        return "supported_exact"
    if base in ADAPTED:
        return "supported_adapted"
    if base in RECOGNIZED or base.startswith("spawn") and base[5:].isdigit():
        return "recognized_not_lowered"
    return "unknown"


def delay_to_frames(delay: int, fps: int) -> int | None:
    """Convert a centisecond-shaped delay. 900 and above is the hold idiom, not a duration.

    The distributed executable was not run. The centisecond reading matches the
    current ChronoCrash animation page and the legacy manual; it is a hypothesis
    until a version-pinned engine trace exists. NTSC uses fps 60, PAL uses 50.
    """
    if delay >= HOLD_DELAY_AT:
        return None
    return max(1, (delay * fps) // 100)


def anim_unknowns(anim: AnimDef) -> list[dict]:
    found = []
    for directive in anim.directives:
        if command_kind(directive.command) == "unknown":
            found.append(
                {
                    "line": directive.line,
                    "command": directive.command,
                    "args": directive.args,
                    "raw": directive.raw.strip(),
                }
            )
    return found


def script_sites(anim: AnimDef) -> list[dict]:
    return [
        {"start_line": block.start_line, "end_line": block.end_line, "lines": len(block.body)}
        for block in anim.scripts
    ]


def summarize_model(model: ModelFile, required_anims: list[str]) -> dict:
    required = {name.lower() for name in required_anims}
    rows = []
    blocked = list(model.issues)
    seen: set[str] = set()
    for anim in model.anims:
        seen.add(anim.name.lower())
        unknown = anim_unknowns(anim)
        needed = anim.name.lower() in required
        if needed and unknown:
            blocked.append(f"{model.path}:{anim.line}: anim '{anim.name}' has unknown commands")
        if needed and any(frame.delay is None for frame in anim.frames):
            blocked.append(f"{model.path}:{anim.line}: anim '{anim.name}' has a frame without delay")
        if needed and any(frame.offset is None for frame in anim.frames):
            blocked.append(f"{model.path}:{anim.line}: anim '{anim.name}' has a frame without offset")
        rows.append(
            {
                "anim": anim.name,
                "line": anim.line,
                "frames": len(anim.frames),
                "loop": anim.loop,
                "required": needed,
                "unknown": unknown,
                "scripts": script_sites(anim),
                "recognized_not_lowered": sorted(
                    {
                        directive.command
                        for directive in anim.directives
                        if command_kind(directive.command) == "recognized_not_lowered"
                    }
                ),
            }
        )
    for name in required_anims:
        if name.lower() not in seen:
            blocked.append(f"missing required anim '{name}'")
            rows.append({"anim": name, "status": "missing", "unknown": [], "scripts": [], "required": True})
    return {"path": model.path, "anims": rows, "blocked": blocked, "header_issues": model.issues}


def summarize_level(level: LevelFile, world_w: int, wave_at: int) -> dict:
    in_slice = []
    outside = []
    for spawn in level.spawns:
        screen_x = spawn.coords[0] if spawn.coords else None
        world_x = (spawn.at + screen_x) if spawn.at is not None and screen_x is not None else None
        row = {
            "line": spawn.line,
            "name": spawn.name,
            "at": spawn.at,
            "health": spawn.health,
            "coords": spawn.coords,
            "world_x": world_x,
            "flip": spawn.flip,
        }
        if spawn.at == wave_at and world_x is not None and 0 <= world_x < world_w:
            in_slice.append(row)
        else:
            outside.append(row)
    music = level.header_value("music")
    music_claim = "unsupported_reachable" if music and music[0].lower().endswith(".bor") else "unknown"
    return {
        "path": level.path,
        "issues": level.issues,
        "music": music,
        "music_claim": music_claim if music else "absent",
        "panel": level.header_value("panel"),
        "background": level.header_value("background"),
        "frontpanel": level.header_value("frontpanel"),
        "spawns_in_slice": in_slice,
        "spawns_outside_slice": len(outside),
    }
