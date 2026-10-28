"""Build a banked, two-palette runtime cut from real MUGEN character data.

The source archive stays outside the repository.  This generator writes only
derived artifacts to the caller-selected output directory and emits a compact
C table consumed by the SMS fight runtime.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import struct
import sys
import tempfile
from collections import Counter
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from mugen2sms import character as character_loader
from mugen2sms.analysis.fidelity import classify_character
from mugen2sms.analysis.sms_budget import SmsLimits
from mugen2sms.converters import sms_cmd, sms_scale as scale
from mugen2sms.converters.sms_controls import ControlMap, DEFAULT_MAP
from mugen2sms.generators import smsdev
from mugen2sms.generators.runtime_format import decode_indices
from mugen2sms.source import Source
from mugen2sms.converters.sms_tiles import _pal

BANK_PAGE = 16384
STREAM_CHUNK_BYTES = 64
PALETTE_COLORS_PER_SIDE = 7
CLOSE_ROLE_COMMAND_ALIASES = {
    "punch_close": "lp",
    "hp_close": "hp",
    "kick_close": "lk",
    "hk_close": "hk",
}
FAR_ROLE_COMMAND_ALIASES = {
    "punch_far": "lp",
    "hp_far": "hp",
    "kick_far": "lk",
    "hk_far": "hk",
}


def _nearest_word(rgb: tuple[int, int, int]) -> int:
    r, g, b = _pal.nearest_code(rgb)
    return r | (g << 2) | (b << 4)


def _word_rgb(word: int) -> tuple[int, int, int]:
    return _pal.code_rgb((word & 3, (word >> 2) & 3, (word >> 4) & 3))


def _distance(a: int, b: int) -> int:
    ar, ag, ab = _word_rgb(a)
    br, bg, bb = _word_rgb(b)
    return (ar - br) ** 2 + (ag - bg) ** 2 + (ab - bb) ** 2


def _luma_word(word: int) -> float:
    red, green, blue = _word_rgb(word)
    return 0.30 * red + 0.59 * green + 0.11 * blue


# One Master System channel step is 85 in contract RGB. 7225 is that step squared.
_CHANNEL_STEP = 85
# Skin, gi and highlights on Ken/Ryu sit above this. A darker outline may not
# spend one of those steps: the pixels would fall into a neighbor and the
# picture would lose a shade.
_BODY_COLOR_LUMA = 100.0
# Mean contract-RGB brightness of every opaque pixel. The reserved book dropped
# Ken by 4.6 and Ryu by 4.8 against the frequency book.
_MEAN_LUMA_DROP_LIMIT = 1.0


def _assign_index(word: int, codebook: list[int]) -> int:
    """Nearest color. An exact distance tie keeps the closer brightness."""
    return min(range(len(codebook)), key=lambda n: (
        _distance(word, codebook[n]),
        abs(_luma_word(word) - _luma_word(codebook[n])),
        n,
    ))


def _weighted_error(counts: Counter[int], codebook: list[int]) -> int:
    return sum(_distance(word, codebook[_assign_index(word, codebook)]) * count
               for word, count in counts.items())


def _mean_luma(counts: Counter[int], codebook: list[int]) -> float:
    total = sum(counts.values())
    if not total:
        return 0.0
    return sum(_luma_word(codebook[_assign_index(word, codebook)]) * count
               for word, count in counts.items()) / total


def _choose_codebook(counts: Counter[int]) -> list[int]:
    """Frequency first. An outside anchor replaces a slot only when the swap
    keeps the squared error and the mean brightness, and the slot is not a
    body shade or the most used color.
    """
    ranked = [word for word, _count in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))]
    chosen = ranked[:PALETTE_COLORS_PER_SIDE]
    if len(chosen) < 2:
        return chosen
    darkest = min(ranked, key=lambda word: (_luma_word(word), -counts[word], word))
    lightest = max(ranked, key=lambda word: (_luma_word(word), counts[word], -word))
    protected: set[int] = set()
    for anchor in (darkest, lightest):
        if anchor in chosen:
            protected.add(anchor)
            continue
        if anchor == lightest and any(
            _distance(anchor, word) <= _CHANNEL_STEP ** 2
            and _luma_word(word) >= _luma_word(anchor) - 20
            for word in chosen
        ):
            continue
        base_error = _weighted_error(counts, chosen)
        base_mean = _mean_luma(counts, chosen)
        best = None
        for victim in chosen:
            if victim in protected or victim == ranked[0]:
                continue
            if _luma_word(victim) >= _BODY_COLOR_LUMA:
                continue
            if anchor == lightest and _luma_word(victim) + 40 < _luma_word(anchor):
                continue
            trial = [anchor if word == victim else word for word in chosen]
            error = _weighted_error(counts, trial)
            mean = _mean_luma(counts, trial)
            if error > base_error or mean + _MEAN_LUMA_DROP_LIMIT < base_mean:
                continue
            candidate = (error - base_error, -mean, counts[victim], victim)
            if best is None or candidate < best:
                best = candidate
        if best is None:
            continue
        victim = best[3]
        chosen = [anchor if word == victim else word for word in chosen]
        protected.add(anchor)
    return chosen


def _palette_codebook(entries: list[smsdev.Artifact], by_symbol: dict[str, smsdev.Artifact]) -> list[int]:
    """Seven shared colors. Transparency is palette index 0, not CRAM word 0.

    Word 0 is opaque black and remains eligible. Frequency fills the slots.
    A missing outline may replace one darker, less used slot when that swap
    does not raise the squared RGB error and does not drop the mean brightness
    of all opaque pixels by more than one contract-RGB unit. A body shade at
    luma 100 or above stays. A highlight one channel from white stays too.
    """
    counts: Counter[int] = Counter()
    for entry in entries:
        if not entry.symbol.endswith("_TILES"):
            continue
        palette = by_symbol[entry.symbol.removesuffix("_TILES") + "_PAL"].data
        blob = entry.data
        for offset in range(0, len(blob), 32):
            for index in decode_indices(blob[offset:offset + 32]):
                if index:
                    counts[palette[index]] += 1
    return _choose_codebook(counts)


def _remap_blob(blob: bytes, palette: bytes, codebook: list[int], offset: int) -> bytes:
    """Map each local pose palette to the shared seven-color character line."""
    if len(palette) != 16 or not codebook:
        raise ValueError("pose palette/codebook is empty or malformed")
    index_map = [0] * 16
    for index in range(1, 16):
        word = palette[index]
        # Index 0 in CRAM is transparent; opaque black is kept in an available
        # codebook slot when present, never mapped to transparency.
        slot = _assign_index(word, codebook)
        index_map[index] = slot + 1 + offset
    out = bytearray()
    for pos in range(0, len(blob), 32):
        pixels = decode_indices(blob[pos:pos + 32])
        mapped = [0 if value == 0 else index_map[value] for value in pixels]
        encoded = bytearray()
        for row in range(8):
            planes = [0, 0, 0, 0]
            for x in range(8):
                color = mapped[row * 8 + x]
                for plane in range(4):
                    planes[plane] |= ((color >> plane) & 1) << (7 - x)
            encoded.extend(planes)
        out.extend(encoded)
    return bytes(out)


def _scale_signed(value: int, divisor: int) -> int:
    # C-style truncation toward zero; AIR coordinates can be negative.
    return int(value / divisor)


def _correct_frame_metadata(artifacts: list[smsdev.Artifact], ch, actions: dict,
                            by_key: dict, uniformly_scaled: bool = False) -> None:
    by_symbol = {a.symbol: a for a in artifacts}
    slug = smsdev.slug(Path(ch.def_path).stem)
    for action_id, action in actions.items():
        for frame_index, frame in enumerate(action.frames):
            sprite = by_key[(frame.group, frame.image)]
            divisor = (1 if uniformly_scaled else
                       (scale.SCALE if scale.needs_scale(sprite.width, sprite.height) else 1))
            stem = f"{slug}_A{action_id}F{frame_index}"
            axis = by_symbol.get(stem + "_AXIS")
            if axis:
                ax = _scale_signed(frame.x - sprite.axis_x, divisor)
                ay = _scale_signed(frame.y - sprite.axis_y, divisor)
                axis.data = struct.pack("<2h", ax, ay)
            clsn = by_symbol.get(stem + "_CLSN")
            if clsn:
                values = [struct.unpack_from("<h", clsn.data, pos)[0]
                          for pos in range(0, len(clsn.data), 2)]
                scaled = [value if value == -32767 else _scale_signed(value, divisor)
                          for value in values]
                clsn.data = b"".join(struct.pack("<h", value) for value in scaled)


def _selected_variant(ch, actions: dict[int, object], palette: list[tuple[int, int, int]] | None):
    variant = replace(ch, anims=actions, commands=ch.commands)
    if palette is not None:
        variant.sprites = [replace(sprite, palette=palette) for sprite in ch.sprites]
    return variant


def _artifacts(manifest) -> list[smsdev.Artifact]:
    return [smsdev.Artifact(entry["symbol"], entry["blob"], entry["source"])
            for entry in manifest.entries]


def _palette_metas(stem: str, p1_by_symbol: dict[str, smsdev.Artifact],
                   p2_by_symbol: dict[str, smsdev.Artifact]) -> list[smsdev.Artifact]:
    """Keep each color variant's metasprite IDs paired with its tile pool."""
    output = []
    for suffix in ("_META", "_METAL"):
        symbol = stem + suffix
        p1_meta, p2_meta = p1_by_symbol.get(symbol), p2_by_symbol.get(symbol)
        if p1_meta is None or p2_meta is None:
            raise ValueError(f"palette-specific metasprite is missing: {symbol}")
        output.append(copy.copy(p1_meta))
        output.append(smsdev.Artifact(stem + "_P2" + suffix,
                                      p2_meta.data, p2_meta.source))
    return output


def _compact_facing_pose(tiles: bytes, metadata: bytes,
                         symbol: str) -> tuple[bytes, bytes]:
    """Keep only exact 8x16 pairs referenced by one facing's metadata.

    The SMS tall-sprite mode addresses adjacent pattern pairs. Each facing has
    its own compact payload, so the runtime can stage a new pose without
    reserving the unreferenced half of the source frame or confusing mirrored
    indices with the right-facing pool.
    """
    if len(tiles) % 32:
        raise ValueError(f"{symbol}: tile payload is not a whole 8x8 pattern")
    if not metadata or metadata[-1] != 0x80 or (len(metadata) - 1) % 3:
        raise ValueError(f"{symbol}: malformed metasprite metadata")
    pair_ids: dict[bytes, int] = {}
    compact = bytearray()
    rewritten = bytearray(metadata)
    for pos in range(0, len(metadata) - 1, 3):
        tile_id = metadata[pos + 2]
        if tile_id & 1:
            raise ValueError(f"{symbol}: odd 8x16 pattern id {tile_id}")
        start = tile_id * 32
        pattern_pair = tiles[start:start + 64]
        if len(pattern_pair) != 64:
            raise ValueError(f"{symbol}: pattern pair {tile_id // 2} exceeds tile payload")
        compact_id = pair_ids.get(pattern_pair)
        if compact_id is None:
            compact_id = len(pair_ids)
            if compact_id > 127:
                raise ValueError(f"{symbol}: compact facing exceeds 128 tall-sprite pairs")
            pair_ids[pattern_pair] = compact_id
            compact.extend(pattern_pair)
        rewritten[pos + 2] = compact_id * 2
    return bytes(compact), bytes(rewritten)


def _runtime_table(roles: list[dict], role_frames: dict[str, list[dict]],
                   pose_count: int, artifacts: list[smsdev.Artifact],
                   bank_map: dict[str, tuple[int, int]], palette: list[int],
                   runtime: dict[str, int],
                   facing_sizes: dict[str, int] | None = None) -> str:
    symbols = {artifact.symbol for artifact in artifacts}
    lines = ["", "/* Runtime tables: generated from AIR/SFF/ACT/CNS/CMD. */",
             f"#define CUT_POSE_COUNT {pose_count}", "",
             f"#define CUT_MAX_LIFE {runtime['life']}",
             f"#define CUT_WALK_FWD_Q8 {runtime['walk_fwd']}",
             f"#define CUT_WALK_BACK_Q8 {runtime['walk_back']}",
             f"#define CUT_JUMP_VY_Q8 {runtime['jump_vy']}",
             f"#define CUT_GRAVITY_Q8 {runtime['gravity']}",
             f"#define CUT_DAMAGE_PUNCH {runtime['damage_punch']}",
             f"#define CUT_DAMAGE_HP {runtime['damage_hp']}",
             f"#define CUT_DAMAGE_KICK {runtime['damage_kick']}",
             f"#define CUT_DAMAGE_HK {runtime['damage_hk']}",
             f"#define CUT_DAMAGE_SPECIAL {runtime['damage_special']}",
             f"#define CUT_SPECIAL_VEL_Q8 {runtime['special_vel']}",
             f"#define CUT_INPUT_THRESHOLD_KEY1 {runtime['input_threshold_key1']}",
             f"#define CUT_INPUT_THRESHOLD_KEY2 {runtime['input_threshold_key2']}",
             f"#define CUT_HITSTOP {runtime['hitstop']}",
             f"#define CUT_HIT_PUSH_PX {runtime['hit_push']}",
             f"#define CUT_GUARD_PUSH_PX {runtime['guard_push']}",
             f"#define CUT_STREAM_CHUNK_BYTES {STREAM_CHUNK_BYTES}", ""]
    for index, role in enumerate(roles):
        lines.append(f"#define CUT_ANIM_{role['role'].upper()} {index}")
    lines += ["",
             "/* FACE_SIZE is one facing's length in the adjacent R/L payload. */"]
    facing_sizes = facing_sizes or {}
    for role in roles:
        for frame in role_frames[role["role"]]:
            stem = frame["stem"]
            p1_face_size = int(facing_sizes.get(stem, 0))
            p2_face_size = int(facing_sizes.get(stem + "_P2", 0))
            if (p1_face_size <= 0 or p2_face_size <= 0 or
                    p1_face_size % 64 or p2_face_size % 64):
                raise ValueError(f"invalid compact facing size for {stem}: "
                                 f"P1={p1_face_size}, P2={p2_face_size}")
            lines.append(f"#define {stem}_FACE_SIZE {p1_face_size}")
            lines.append(f"#define {stem}_P2_FACE_SIZE {p2_face_size}")
    lines += ["", "static const PoseRef poses_all[CUT_POSE_COUNT * 2] = {"]
    for suffix in ("", "_P2"):
        for role in roles:
            for frame in role_frames[role["role"]]:
                stem = frame["stem"]
                tile_symbol = stem + suffix + "_TILES"
                face_size_symbol = stem + suffix + "_FACE_SIZE"
                if tile_symbol not in bank_map:
                    raise ValueError(f"missing bank entry for {tile_symbol}")
                # side 1 draws with Frame.metal_p2, whose compact pair ids
                # address the LEFT facing. The combined payload is
                # right.ljust(face_size) + left.ljust(face_size), so the P2
                # PoseRef must start at OFF + FACE_SIZE. Pointing it at the
                # right face makes every P2 cell read a valid but wrong pair
                # (the body splits at the tile seams).
                face_offset = (" + " + face_size_symbol) if suffix else ""
                lines.append(f"    {{ {tile_symbol}_BANK, {tile_symbol}_OFF{face_offset}, {face_size_symbol} }},")
    lines += ["};", "", "static const Frame frames_all[CUT_POSE_COUNT] = {"]
    pose_index = 0
    for role in roles:
        for frame in role_frames[role["role"]]:
            stem = frame["stem"]
            clsn = stem + "_CLSN" if stem + "_CLSN" in symbols else "0"
            lines.append(
                f"    {{ {frame['duration']}, {pose_index}, {stem}_META, {stem}_METAL, "
                f"{clsn}, {stem}_AXIS, {frame['width']}, {frame['height']}, "
                f"{stem}_P2_META, {stem}_P2_METAL }},")
            pose_index += 1
    lines += ["};", "", f"static const Anim anims[{len(roles)}] = {{"]
    start = 0
    for role in roles:
        count = len(role_frames[role["role"]])
        loop = role.get("loop_start")
        loop_value = 255 if loop is None else int(loop)
        lines.append(f"    {{ {role['action']}, {count}, {loop_value}, frames_all + {start} }},")
        start += count
    lines += ["};", "", "static const unsigned char cut_sprite_palette[16] = {"]
    lines.append("    " + ", ".join(f"0x{value:02X}" for value in palette) + ",")
    lines += ["};", ""]
    return "\n".join(lines)


def _q8(value: str | int | float) -> int:
    return int(Decimal(str(value)) * 256)


def _hitdef_const(ch, state_id: int, name: str):
    """First compiled HitDef constant, or None when the parameter is absent."""
    state = ch.states.get(state_id)
    if state is None:
        return None
    for controller in state.controllers:
        if controller.source_type != "hitdef":
            continue
        for param in controller.params:
            if param.name == name:
                return param.const
    return None


def _hitdef_value(ch, state_id: int, name: str, default: int) -> int:
    raw = _hitdef_const(ch, state_id, name)
    if raw is None:
        return default
    return int(raw)


def hit_recovery(ch, state_id: int) -> dict:
    """Hit pause and control-lock times from the first HitDef of one state.

    guard.hittime omitted in the HitDef copies ground.hittime (the default
    recorded on the Ken source and in the HitDef schema). air.hittime omitted
    in the source is compiled as the schema default 20. Later HitDefs in the
    same state are not read. This does not supply a common1 hit animation or
    a knockdown.
    """
    if _hitdef_count(ch, state_id) < 1:
        raise ValueError(f"state {state_id} has no HitDef")

    def uint8(name: str, default: int) -> int:
        raw = _hitdef_const(ch, state_id, name)
        value = default if raw is None else raw
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"state {state_id} {name} is not numeric")
        if float(value) != int(value):
            raise ValueError(f"state {state_id} {name} is not an integer")
        value = int(value)
        if not 0 <= value <= 255:
            raise ValueError(f"state {state_id} {name} outside uint8")
        return value

    stop_a = uint8("pausetime[0]", 0)
    stop_d = uint8("pausetime[1]", stop_a)
    hittime = uint8("ground.hittime[0]", 0)
    guard_raw = _hitdef_const(ch, state_id, "guard.hittime[0]")
    if guard_raw is None:
        guardtime = hittime
        guard_source = "ground.hittime"
    else:
        guardtime = uint8("guard.hittime[0]", 0)
        guard_source = "hitdef"
    return {
        "stop_a": stop_a,
        "stop_d": stop_d,
        "hittime": hittime,
        "guardtime": guardtime,
        "airtime": uint8("air.hittime[0]", 20),
        "guardtime_source": guard_source,
        "fidelity": "approximate",
    }


def _hitdef_count(ch, state_id: int) -> int:
    state = ch.states.get(state_id)
    if state is None:
        return 0
    return sum(1 for controller in state.controllers
               if controller.source_type.lower() == "hitdef")


def _controller_value(ch, state_id: int, source_type: str,
                      name: str) -> int | float | None:
    state = ch.states.get(state_id)
    if state is None:
        return None
    for controller in state.controllers:
        if controller.source_type != source_type:
            continue
        for param in controller.params:
            if param.name == name and param.const is not None:
                return param.const
    return None


def _close_attack_rules(ch, roles: list[dict], commands: dict) -> list[dict]:
    """Import the narrow standing close-attack rule from the source CMD.

    This recognizes only a direct ``P2BodyDist X < integer`` trigger on the
    declared close State -1 ChangeState, with the corresponding button command
    and standing/control gate. Other predicates remain outside this runtime.
    """
    role_rows = {row["role"]: row for row in roles}
    close_roles = [name for name in CLOSE_ROLE_COMMAND_ALIASES if name in role_rows]
    if not close_roles:
        return []
    state_minus_one = ch.raw_states.get(-1)
    if state_minus_one is None:
        raise ValueError("close attack roles require source CMD State -1")

    rules = []
    for role_name in close_roles:
        row = role_rows[role_name]
        state_id = int(row.get("state", row["action"]))
        alias = CLOSE_ROLE_COMMAND_ALIASES[role_name]
        source_command = commands.get(alias)
        if not isinstance(source_command, str) or not source_command.strip():
            raise ValueError(f"{role_name}: missing commands.{alias} source mapping")
        matches = [controller for controller in state_minus_one.controllers
                   if controller.type.lower() == "changestate" and
                   controller.params.get("value", "").strip() == str(state_id)]
        if len(matches) != 1:
            raise ValueError(f"{role_name}: expected one State -1 ChangeState to {state_id}")
        controller = matches[0]
        all_conditions = list(controller.triggerall)
        if set(controller.triggers) != {1}:
            raise ValueError(
                f"{role_name}: only trigger1 is supported for close attacks")
        trigger1_conditions = list(controller.triggers[1])
        command_re = re.compile(r'^\s*command\s*=\s*["\']([^"\']+)["\']\s*$', re.I)
        command_names = [match.group(1).strip().lower()
                         for condition in all_conditions
                         if (match := command_re.fullmatch(condition))]
        if (len(command_names) != 1 or
                source_command.strip().lower() not in command_names):
            raise ValueError(
                f"{role_name}: State -1 source command does not match commands.{alias}")
        hold_down_conditions = [condition for condition in all_conditions
                                if re.fullmatch(
                                    r'\s*command\s*!=\s*["\']holddown["\']\s*',
                                    condition, re.I)]
        if len(hold_down_conditions) != 1:
            raise ValueError(
                f"{role_name}: Command != \"holddown\" is required exactly once")
        distance_conditions = [condition for condition in all_conditions
                               if re.fullmatch(
                                   r"\s*p2bodydist\s+x\s*<\s*(\d+)\s*",
                                   condition, re.I)]
        if len(distance_conditions) != 1:
            raise ValueError(
                f"{role_name}: only one direct P2BodyDist X < integer trigger is supported")
        if len(all_conditions) != 3:
            raise ValueError(
                f"{role_name}: unmodeled State -1 triggerall predicate")
        distance_match = re.fullmatch(
            r"\s*p2bodydist\s+x\s*<\s*(\d+)\s*",
            distance_conditions[0], re.I)
        assert distance_match is not None
        standing_ctrl_re = re.compile(
            r"^\s*(?:\(\s*statetype\s*=\s*s\s*\)\s*&&\s*ctrl|"
            r"statetype\s*=\s*s\s*&&\s*ctrl)\s*$", re.I)
        if (len(trigger1_conditions) != 1 or
                not standing_ctrl_re.fullmatch(trigger1_conditions[0])):
            raise ValueError(
                f"{role_name}: trigger1 must be exactly standing Statetype=S && ctrl")
        rules.append({
            "role": role_name,
            "command_alias": alias,
            "source_command": source_command,
            "source_state": state_id,
            "comparison": "lt",
            "threshold_source_units": int(distance_match.group(1)),
            "source_condition": distance_conditions[0].strip(),
            "source_line": int(controller.line),
            "source_predicates": {
                "triggerall_command": source_command,
                "exclude_hold_down": True,
                "distance_condition": distance_conditions[0].strip(),
                "trigger1_condition": trigger1_conditions[0].strip(),
            },
            "runtime_gate": {
                "command_alias": alias,
                "hold_down": False,
                "statetype": "S",
                "ctrl": True,
                "distance": {"axis": "x", "comparison": "lt",
                             "threshold_source_units": int(distance_match.group(1))},
            },
            "scope": "only the listed command, no-hold-down, standing/control, and distance predicates are compiled",
        })
    return rules


def _far_attack_rules(ch, roles: list[dict], commands: dict) -> list[dict]:
    """Import an ordered far fallback when its near partner has a distance gate.

    The source uses the earlier near ChangeState as priority and a later
    standing/control ChangeState as the far fallback. Only the direct standing
    entry is compiled; source cancel branches remain outside this runtime.
    """
    role_rows = {row["role"]: row for row in roles}
    far_roles = [name for name in FAR_ROLE_COMMAND_ALIASES if name in role_rows]
    if not far_roles:
        return []
    state_minus_one = ch.raw_states.get(-1)
    if state_minus_one is None:
        raise ValueError("far attack roles require source CMD State -1")
    controllers = state_minus_one.controllers
    command_re = re.compile(r'^\s*command\s*=\s*["\']([^"\']+)["\']\s*$', re.I)
    hold_down_re = re.compile(r'^\s*command\s*!=\s*["\']holddown["\']\s*$', re.I)
    distance_re = re.compile(r"^\s*p2bodydist\s+x\s*<\s*(\d+)\s*$", re.I)
    rules = []
    for role_name in far_roles:
        base_role = role_name.removesuffix("_far")
        if base_role not in role_rows:
            raise ValueError(f"{role_name}: near/base role {base_role} is missing")
        far_row = role_rows[role_name]
        near_row = role_rows[base_role]
        far_state = int(far_row.get("state", far_row["action"]))
        near_state = int(near_row.get("state", near_row["action"]))
        alias = FAR_ROLE_COMMAND_ALIASES[role_name]
        source_command = commands.get(alias)
        if not isinstance(source_command, str) or not source_command.strip():
            raise ValueError(f"{role_name}: missing commands.{alias} source mapping")

        matches = [i for i, controller in enumerate(controllers)
                   if controller.type.lower() == "changestate" and
                   controller.params.get("value", "").strip() == str(far_state)]
        if len(matches) != 1:
            raise ValueError(f"{role_name}: expected one State -1 ChangeState to {far_state}")
        far_index = matches[0]
        far_controller = controllers[far_index]
        far_all = list(far_controller.triggerall)
        command_names = [m.group(1).strip().lower() for condition in far_all
                         if (m := command_re.fullmatch(condition))]
        hold_down = [condition for condition in far_all
                     if hold_down_re.fullmatch(condition)]
        if (command_names != [source_command.strip().lower()] or len(hold_down) != 1 or
                len(far_all) != 2):
            raise ValueError(
                f"{role_name}: far fallback requires only its mapped command and no-hold-down gates")
        far_triggers = list(far_controller.triggers.get(1, []))
        if (len(far_triggers) != 2 or
                not any(re.fullmatch(r"\s*statetype\s*=\s*s\s*", t, re.I)
                        for t in far_triggers) or
                not any(re.fullmatch(r"\s*ctrl\s*(?:=\s*1)?\s*", t, re.I)
                        for t in far_triggers)):
            raise ValueError(
                f"{role_name}: direct far entry must be exactly trigger1 Statetype=S and ctrl")

        near_matches = []
        for i, controller in enumerate(controllers[:far_index]):
            if (controller.type.lower() != "changestate" or
                    controller.params.get("value", "").strip() != str(near_state)):
                continue
            near_all = list(controller.triggerall)
            near_commands = [m.group(1).strip().lower() for condition in near_all
                             if (m := command_re.fullmatch(condition))]
            near_holds = [condition for condition in near_all
                          if hold_down_re.fullmatch(condition)]
            near_distances = [m.group(1) for condition in near_all
                              if (m := distance_re.fullmatch(condition))]
            near_trigger1 = list(controller.triggers.get(1, []))
            if (near_commands == [source_command.strip().lower()] and
                    len(near_holds) == 1 and len(near_distances) == 1 and
                    len(near_all) == 3 and len(near_trigger1) == 2 and
                    any(re.fullmatch(r"\s*statetype\s*=\s*s\s*", t, re.I)
                        for t in near_trigger1) and
                    any(re.fullmatch(r"\s*ctrl\s*(?:=\s*1)?\s*", t, re.I)
                        for t in near_trigger1)):
                near_matches.append((i, controller, int(near_distances[0])))
        if len(near_matches) != 1:
            raise ValueError(
                f"{role_name}: expected one earlier same-command near rule for State {near_state}")
        near_index, near_controller, threshold = near_matches[0]
        if near_index >= far_index or threshold <= 0:
            raise ValueError(f"{role_name}: far fallback does not follow a positive near threshold")
        rules.append({
            "role": role_name,
            "near_role": base_role,
            "command_alias": alias,
            "source_command": source_command,
            "source_state": far_state,
            "near_source_state": near_state,
            "comparison": "ge",
            "threshold_source_units": threshold,
            "source_condition": f"P2BodyDist X >= {threshold} (ordered fallback after < {threshold})",
            "source_near_condition": next(
                condition.strip() for condition in near_controller.triggerall
                if distance_re.fullmatch(condition)),
            "source_line": int(far_controller.line),
            "source_near_line": int(near_controller.line),
            "source_near_uncompiled_trigger_groups": {
                str(group): list(conditions)
                for group, conditions in near_controller.triggers.items() if group != 1
            },
            "source_uncompiled_trigger_groups": {
                str(group): list(conditions)
                for group, conditions in far_controller.triggers.items() if group != 1
            },
            "runtime_gate": {
                "command_alias": alias,
                "hold_down": False,
                "statetype": "S",
                "ctrl": True,
                "distance": {"axis": "x", "comparison": "ge",
                             "threshold_source_units": threshold},
            },
            "scope": "direct standing/control far fallback only; chain/cancel trigger groups are not executed",
        })
    return rules


def _compile_source_routes(ch, roles: list[dict], source_routes,
                           controls: ControlMap | None = None) -> list[dict]:
    """Resolve declared CNS routes to canonical AIR action roles.

    Several source states can select the same AIR action. Keep those routes as
    metadata aliases instead of creating duplicate pose roles, which would
    make the generated runtime pose identity ambiguous.
    """
    if source_routes is None:
        return []
    if not isinstance(source_routes, list):
        raise ValueError("source_routes must be a list")

    role_by_name = {}
    for role in roles:
        name = role.get("role")
        action = role.get("action")
        if not isinstance(name, str) or type(action) is not int:
            raise ValueError("source route roles require string names and integer actions")
        if name in role_by_name:
            raise ValueError(f"source route action role is duplicated: {name}")
        role_by_name[name] = role

    command_state = ch.raw_states.get(-1)
    if source_routes and command_state is None:
        raise ValueError("source_routes require parsed Cmd.cmd State -1")
    controllers_by_line = {}
    if command_state is not None:
        for controller in command_state.controllers:
            controllers_by_line.setdefault(controller.line, []).append(controller)

    compiled = []
    route_by_id = {}
    canonical_by_role = {}
    route_symbol_prefixes = set()
    for route in source_routes:
        if not isinstance(route, dict):
            raise ValueError("each source route must be an object")
        route_id = route.get("route_id")
        action_role = route.get("action_role")
        state_id = route.get("source_state")
        source_line = route.get("source_controller_line")
        command_terms = route.get("source_command_terms")
        alias_of = route.get("alias_of")
        state_resolution = route.get("source_state_resolution")
        if not isinstance(route_id, str) or not route_id.strip() or route_id in route_by_id:
            raise ValueError("source route ids must be unique non-empty strings")
        symbol_prefix = sms_cmd.route_command_prefix(route_id)
        if symbol_prefix in route_symbol_prefixes:
            raise ValueError(
                f"{route_id}: source route id collides after C symbol normalization")
        route_symbol_prefixes.add(symbol_prefix)
        if not isinstance(action_role, str) or action_role not in role_by_name:
            raise ValueError(f"{route_id}: action_role must name an imported action role")
        if type(state_id) is not int or not 0 <= state_id <= 0xFFFF:
            raise ValueError(f"{route_id}: source_state must be uint16")
        if type(source_line) is not int or source_line <= 0:
            raise ValueError(f"{route_id}: source_controller_line must be positive")
        if (not isinstance(command_terms, list) or not command_terms or
                any(not isinstance(term, str) or not term.strip()
                    for term in command_terms)):
            raise ValueError(f"{route_id}: source_command_terms must be non-empty strings")
        candidates = controllers_by_line.get(source_line, [])
        if len(candidates) != 1:
            raise ValueError(f"{route_id}: expected one State -1 controller at line {source_line}")
        controller = candidates[0]
        if controller.type.lower() != "changestate":
            raise ValueError(f"{route_id}: source controller is not ChangeState")
        target_expression = controller.params.get("value", "").strip()
        assignment = None
        if re.fullmatch(r"\d+", target_expression):
            target_state = int(target_expression)
            if state_resolution is not None:
                raise ValueError(
                    f"{route_id}: fixed ChangeState cannot declare a variable resolution")
        else:
            if (not isinstance(state_resolution, dict) or
                    state_resolution.get("kind") != "varset_constant"):
                raise ValueError(
                    f"{route_id}: dynamic ChangeState requires varset_constant resolution")
            variable = state_resolution.get("source_variable")
            setter_line = state_resolution.get("setter_controller_line")
            if (type(variable) is not int or not 0 <= variable <= 255 or
                    type(setter_line) is not int or setter_line <= 0):
                raise ValueError(f"{route_id}: variable resolution coordinates are invalid")
            expression_match = re.fullmatch(
                r"\s*var\s*\(\s*(\d+)\s*\)\s*", target_expression, re.I)
            if expression_match is None or int(expression_match.group(1)) != variable:
                raise ValueError(
                    f"{route_id}: ChangeState expression is not the declared Var(n)")
            setters = [item for item in command_state.controllers
                       if item.line == setter_line]
            if len(setters) != 1:
                raise ValueError(
                    f"{route_id}: expected one VarSet at line {setter_line}")
            setter = setters[0]
            if setter.type.lower() != "varset":
                raise ValueError(f"{route_id}: declared resolution controller is not VarSet")
            try:
                setter_variable = int(setter.params.get("v", "").strip())
                target_state = int(setter.params.get("value", "").strip())
            except (TypeError, ValueError) as exc:
                raise ValueError(f"{route_id}: VarSet target must be integer constant") from exc
            if setter_variable != variable or target_state != state_id:
                raise ValueError(
                    f"{route_id}: VarSet destination disagrees with declared source state")
            controller_positions = {
                id(item): index for index, item in enumerate(command_state.controllers)
            }
            if controller_positions[id(setter)] >= controller_positions[id(controller)]:
                raise ValueError(
                    f"{route_id}: VarSet must precede its dynamic ChangeState")
            assignment = {
                "source_controller_type": "varset",
                "source_controller_line": setter_line,
                "source_variable": setter_variable,
                "source_value": target_state,
                "source_triggerall": list(setter.triggerall),
                "source_triggers": {
                    str(index): list(conditions)
                    for index, conditions in setter.triggers.items()
                },
            }
        if target_state != state_id:
            raise ValueError(f"{route_id}: declared source state disagrees with State -1 target")

        raw_state = ch.raw_states.get(state_id)
        raw_anim = raw_state.params.get("anim") if raw_state is not None else None
        if raw_anim is None or not re.fullmatch(r"\s*\d+\s*", raw_anim):
            raise ValueError(f"{route_id}: source State {state_id} has no fixed integer anim")
        source_action = int(raw_anim)
        action_id = role_by_name[action_role]["action"]
        if source_action != action_id:
            raise ValueError(
                f"{route_id}: State {state_id} selects AIR Action {source_action}, "
                f"but role {action_role} imports {action_id}")

        source_conditions = (assignment["source_triggerall"] + [
            condition for group in assignment["source_triggers"].values()
            for condition in group] if assignment is not None else
            list(controller.triggerall) + [
                condition for group in controller.triggers.values()
                for condition in group])
        actual_terms = {
            term.strip().casefold()
            for condition in source_conditions
            for term in re.findall(
                r"\bcommand\s*=\s*[\"']([^\"']+)[\"']",
                condition, re.IGNORECASE)
        }
        missing_terms = [term for term in command_terms
                         if term.strip().casefold() not in actual_terms]
        if missing_terms:
            raise ValueError(f"{route_id}: State -1 command terms not found: {missing_terms}")

        command_definitions = []
        matched_lines = set()
        for term in command_terms:
            matches = [command for command in ch.commands
                       if command.name.strip().casefold() == term.strip().casefold()]
            if not matches:
                raise ValueError(
                    f"{route_id}: no [Command] definition matches {term!r}")
            for command in matches:
                if command.line in matched_lines:
                    continue
                matched_lines.add(command.line)
                patterns, skipped = sms_cmd.to_patterns([command], controls)
                pattern = patterns[0] if patterns else None
                command_definitions.append({
                    "source_command_term": term.strip(),
                    "source_command": command.name,
                    "source_command_line": command.line,
                    "source_command_raw": command.raw,
                    "source_command_time": command.time,
                    "source_command_buffer_time": command.buffer_time,
                    "source_command_errors": list(command.errors),
                    "source_command_steps": [
                        {"strict": step.strict,
                         "keys": [{"key": key.key,
                                   "release": key.release,
                                   "release_time": key.release_time,
                                   "hold": key.hold,
                                   "four_way": key.four_way}
                                  for key in step.keys]}
                        for step in command.steps],
                    "conversion_status": "represented" if pattern else "unsupported",
                    "conversion_reason": None if pattern else skipped.get(command.name),
                    "pattern_blob_hex": (sms_cmd.serialize_pattern(pattern).hex()
                                         if pattern else None),
                })
        for definition_index, definition in enumerate(command_definitions):
            definition["runtime_command_symbol"] = (
                sms_cmd.route_command_symbol(route_id, definition_index)
                if definition["conversion_status"] == "represented" else None)
        unrepresented_patterns = [
            {"source_command_term": definition["source_command_term"],
             "source_command_line": definition["source_command_line"],
             "reason": definition["conversion_reason"]}
            for definition in command_definitions
            if definition["conversion_status"] != "represented"
        ]

        canonical_id = canonical_by_role.get(action_role)
        if canonical_id is None:
            if alias_of is not None:
                raise ValueError(f"{route_id}: first route for {action_role} cannot be an alias")
            canonical_by_role[action_role] = route_id
        else:
            if alias_of != canonical_id:
                raise ValueError(
                    f"{route_id}: shared action role {action_role} must alias {canonical_id}")
            target = route_by_id.get(alias_of)
            if (target is None or target["action_role"] != action_role or
                    target["source_action"] != source_action):
                raise ValueError(f"{route_id}: alias must resolve to the same AIR action role")

        compiled_route = {
            "route_id": route_id,
            "source_command_terms": [term.strip() for term in command_terms],
            "source_controller_type": controller.type.lower(),
            "source_controller_line": source_line,
            "source_triggerall": list(controller.triggerall),
            "source_triggers": {
                str(index): list(conditions)
                for index, conditions in controller.triggers.items()
            },
            "source_state": state_id,
            "source_action": source_action,
            "action_role": action_role,
            "alias_of": alias_of,
            "source_command_definitions": command_definitions,
            "command_pattern_coverage": (
                "complete" if not unrepresented_patterns else "incomplete"),
            "unrepresented_command_patterns": unrepresented_patterns,
        }
        if assignment is not None:
            compiled_route["source_state_resolution"] = {
                "kind": "varset_constant",
                "change_state_expression": target_expression,
                "source_variable": assignment["source_variable"],
                "setter_controller_line": assignment["source_controller_line"],
                "setter_value": assignment["source_value"],
            }
            compiled_route["source_command_assignment"] = assignment
        compiled.append(compiled_route)
        route_by_id[route_id] = compiled_route
    return compiled


def controls_from_config(config: dict) -> ControlMap:
    """Mapa de controle do corte. Sem declaracao vale o mapa do GDD (doc/22:
    2 tiers por tecla, T=6) — o blob `_CMD_` precisa do mesmo mapa que o
    `analysis/move_checklist.py` usa para dizer o que e digitavel."""
    declared = config.get("controls")
    return DEFAULT_MAP if not declared else ControlMap.from_dict(declared)


def _prepare_pose_budget(ch, roles: list[dict], config: dict, source_sizes, selected_ids):
    """Framebuffer fit, then an extra scale that keeps the neutral pose at 4 SAT columns."""
    from mugen2sms.converters import display_fit as display

    fit = display.resolve_display_fit("pose_budget", config.get("source"), config.get("target"))
    if fit.status != "applied":
        raise ValueError(fit.reason)
    original_durations = {aid: [frame.time for frame in ch.anims[aid].frames] for aid in selected_ids}
    original_counts = {aid: [len(frame.clsn1) + len(frame.clsn2) for frame in ch.anims[aid].frames]
                       for aid in selected_ids}
    fx_groups = config.get("fx_groups") or []
    idle_action = next((int(role["action"]) for role in roles if role.get("role") == "idle"), 0)
    scaled_ch, _changed, pose_report = display.scale_character(
        ch, fit, fx_groups, idle_action)
    selected = {aid: scaled_ch.anims[aid] for aid in selected_ids}
    durations_preserved = all(
        [frame.time for frame in scaled_ch.anims[aid].frames] == original_durations[aid]
        for aid in selected_ids)
    boxes_preserved = all(
        [len(frame.clsn1) + len(frame.clsn2) for frame in scaled_ch.anims[aid].frames]
        == original_counts[aid] for aid in selected_ids)
    if not durations_preserved or not boxes_preserved:
        raise ValueError("pose budget changed animation timing or CLSN box counts")
    pose_report["source"] = config.get("source")
    pose_report["target"] = config.get("target") or "sms"
    pose_report["framebuffer_scale"] = {
        "x": [fit.scale_num_x, fit.scale_den_x],
        "y": [fit.scale_num_y, fit.scale_den_y],
    }
    pose_report["sampling"] = "nearest_neighbor_indexed_pixels"
    pose_report["source_sizes_by_group_image"] = {
        f"{group}:{image}": size for (group, image), size in source_sizes.items()}
    # The scene manifest stores this under the historical key "ratio".
    # numerator/denominator are the extra pose scale only. They are not the
    # legacy 40/49 scale. The framebuffer fractions are siblings, not optional.
    extra = list(pose_report.get("extra_scale") or [1, 1])
    pose_report["ratio"] = {
        "policy": pose_report.get("policy", "pose_budget_pair"),
        "meaning": "numerator/denominator are the extra pose scale only, not legacy 40/49",
        "framebuffer_x": [fit.scale_num_x, fit.scale_den_x],
        "framebuffer_y": [fit.scale_num_y, fit.scale_den_y],
        "pose_extra": extra,
        "numerator": extra[0],
        "denominator": extra[1],
    }
    if pose_report.get("neutral_columns_after", 0) > display.NEUTRAL_COLUMNS:
        raise ValueError(
            "neutral pose still occupies "
            f"{pose_report['neutral_columns_after']} SAT columns after the body fraction")
    excluded = {(item["group"], item["image"]) for item in pose_report.get("fx_excluded") or []}
    for sprite in scaled_ch.sprites:
        if sprite.group in display.EXEMPT_GROUPS:
            excluded.add((sprite.group, sprite.image))
    role_of = {int(role["action"]): role.get("role", role["action"]) for role in roles}
    anims = dict(scaled_ch.anims)
    for aid in list(selected):
        action = selected[aid]
        kept = [frame for frame in action.frames
                if (frame.group, frame.image) not in excluded]
        if not kept:
            raise ValueError(f"{role_of.get(aid, aid)}: every frame is outside the fight cut")
        if len(kept) != len(action.frames):
            action = replace(action, frames=kept)
            selected[aid] = action
            anims[aid] = action
    scaled_ch = replace(scaled_ch, anims=anims)
    return scaled_ch, selected, pose_report


def _prepare_scene(ch, roles: list[dict], scale_profile: dict | None, pose_config: dict | None = None):
    """Select actions and apply the declared uniform scale before fidelity checks.

    Source-size SAT overflow is expected for MUGEN art that is intentionally
    authored for a larger canvas.  A scene with `fighter_scale` must be judged
    on the uniformly transformed poses it will generate, while retaining the
    original dimensions and timings in its report.
    """
    source_sizes = {(sprite.group, sprite.image): [sprite.width, sprite.height]
                    for sprite in ch.sprites}
    selected: dict[int, object] = {}
    for role in roles:
        action_id = int(role["action"])
        action = ch.anims.get(action_id)
        if action is None:
            raise ValueError(f"{role['role']}: AIR action {action_id} is missing")
        loop_start = role.get("loop_start")
        if loop_start is not None and not 0 <= int(loop_start) < len(action.frames):
            raise ValueError(f"{role['role']}: loop_start {loop_start} is outside the AIR action")
        selected[action_id] = action

    if pose_config and pose_config.get("size_policy") == "pose_budget":
        scaled_ch, selected, pose_report = _prepare_pose_budget(
            ch, roles, pose_config, source_sizes, set(selected))
        return scaled_ch, selected, source_sizes, pose_report, True

    if scale_profile is None:
        return ch, selected, source_sizes, None, False

    idle_roles = [role for role in roles if role.get("role") == "idle"]
    if len(idle_roles) != 1:
        raise ValueError("uniform fighter scale requires exactly one idle role")
    target_px = int(scale_profile.get("target_idle_opaque_height_px", 80))
    accepted = scale_profile.get("accepted_height_px", [72, 88])
    if (not isinstance(accepted, list) or len(accepted) != 2 or
            not all(isinstance(v, int) and not isinstance(v, bool) for v in accepted)):
        raise ValueError("fighter_scale.accepted_height_px must be [min,max]")

    idle_action_id = int(idle_roles[0]["action"])
    before_bounds, before_frames = scale.measure_idle_opaque_bounds(
        ch, ch.anims[idle_action_id])
    input_height = before_bounds[3] - before_bounds[2] + 1
    numerator, denominator = scale.target_ratio(
        input_height, target_px, (accepted[0], accepted[1]))
    selected_ids = set(selected)
    original_durations = {aid: [frame.time for frame in ch.anims[aid].frames]
                          for aid in selected_ids}
    original_counts = {aid: [len(frame.clsn1) + len(frame.clsn2)
                             for frame in ch.anims[aid].frames]
                       for aid in selected_ids}

    scaled_ch = scale.scale_character(ch, selected_ids, numerator, denominator)
    selected = {aid: scaled_ch.anims[aid] for aid in selected_ids}
    after_bounds, after_frames = scale.measure_idle_opaque_bounds(
        scaled_ch, scaled_ch.anims[idle_action_id])
    output_height = after_bounds[3] - after_bounds[2] + 1
    if not accepted[0] <= output_height <= accepted[1]:
        raise ValueError(f"uniform scale produced idle height {output_height}px outside "
                         f"{accepted[0]}..{accepted[1]}px")
    durations_preserved = all(
        [frame.time for frame in scaled_ch.anims[aid].frames] == original_durations[aid]
        for aid in selected_ids)
    boxes_preserved = all(
        [len(frame.clsn1) + len(frame.clsn2) for frame in scaled_ch.anims[aid].frames]
        == original_counts[aid] for aid in selected_ids)
    scale_report = {
        "policy": "uniform_per_character_scene_contract",
        "ratio": {"numerator": numerator, "denominator": denominator},
        "target_idle_opaque_height_px": target_px,
        "accepted_height_px": accepted,
        "source_idle_opaque_bounds_xyxy": before_bounds,
        "source_idle_opaque_height_px": input_height,
        "runtime_idle_opaque_bounds_xyxy": after_bounds,
        "runtime_idle_opaque_height_px": output_height,
        "idle_frame_bounds_source": before_frames,
        "idle_frame_bounds_runtime": after_frames,
        "selected_action_frame_counts_preserved": all(
            len(scaled_ch.anims[aid].frames) == len(original_durations[aid])
            for aid in selected_ids),
        "selected_action_air_durations_preserved": durations_preserved,
        "selected_action_clsn_box_counts_preserved": boxes_preserved,
        "sampling": "nearest_neighbor_indexed_pixels",
        "source_sizes_by_group_image": {
            f"{group}:{image}": size for (group, image), size in source_sizes.items()},
        "runtime_note": "AIR values are preserved in generated tables; runtime timing still "
                        "depends on pose streaming and requires emulator measurement."
    }
    if not durations_preserved or not boxes_preserved:
        raise ValueError("uniform scaling changed animation timing or CLSN box counts")
    return scaled_ch, selected, source_sizes, scale_report, True


def generate(source_path: Path, config_path: Path, out_dir: Path,
             first_bank: int = 2,
             project_json: Path | None = None) -> dict:
    ch = character_loader.load(Source(source_path))
    config = json.loads(config_path.read_text(encoding="utf-8"))
    source_limitations = config.get("source_limitations", [])
    if (not isinstance(source_limitations, list) or
            any(not isinstance(item, str) or not item.strip()
                for item in source_limitations)):
        raise ValueError("source_limitations must be a list of non-empty strings")
    roles = config["actions"]
    source_routes = _compile_source_routes(
        ch, roles, config.get("source_routes"), controls_from_config(config))
    ch, selected, source_sizes, scale_report, uniformly_scaled = _prepare_scene(
        ch, roles, config.get("fighter_scale"), config)
    scale_label = None
    if (uniformly_scaled and scale_report
            and scale_report.get("policy") == "pose_budget_pair"):
        fb = scale_report["framebuffer_scale"]
        extra = scale_report.get("extra_scale") or [1, 1]
        scale_label = (f"framebuffer x={fb['x'][0]}/{fb['x'][1]} "
                       f"y={fb['y'][0]}/{fb['y'][1]} extra={extra[0]}/{extra[1]}")
    fidelity = classify_character(ch, SmsLimits(), scale_label=scale_label)
    for role in roles:
        action_id = int(role["action"])
        action = selected[action_id]
        for frame_index, frame in enumerate(action.frames):
            element = fidelity.by_id.get(f"anim:{action_id}.{frame_index}")
            if element is None or element.classe not in ("direct", "approximate"):
                kind = element.classe if element else "unclassified"
                raise ValueError(f"{role['role']}: anim:{action_id}.{frame_index} is {kind}")
            if frame.blend:
                raise ValueError(f"{role['role']}: anim:{action_id}.{frame_index} uses unsupported blend")
    by_key = {(sprite.group, sprite.image): sprite for sprite in ch.sprites}

    palette_by_name = {name.lower(): colors for name, colors in ch.palettes}
    p1_name = config["palette_p1"].lower()
    p2_name = config["palette_p2"].lower()
    if p1_name not in palette_by_name or p2_name not in palette_by_name:
        raise ValueError(f"ACT palette missing: requested {p1_name}/{p2_name}; available={list(palette_by_name)}")
    p1_ch = _selected_variant(ch, selected, palette_by_name[p1_name])
    p2_ch = _selected_variant(ch, selected, palette_by_name[p2_name])
    by_key = {(sprite.group, sprite.image): sprite for sprite in ch.sprites}

    out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="scene_cut_", dir=out_dir) as tmp:
        p1_manifest = smsdev.generate(p1_ch, fidelity, Path(tmp) / "p1",
                                      pre_scaled=uniformly_scaled,
                                      omit_blank_sprites=uniformly_scaled,
                                      controls=controls_from_config(config))
        p2_manifest = smsdev.generate(p2_ch, fidelity, Path(tmp) / "p2",
                                      pre_scaled=uniformly_scaled,
                                      omit_blank_sprites=uniformly_scaled,
                                      controls=controls_from_config(config))
        p1_artifacts = _artifacts(p1_manifest)
        p2_artifacts = _artifacts(p2_manifest)
        _correct_frame_metadata(p1_artifacts, p1_ch, selected, by_key,
                                uniformly_scaled=uniformly_scaled)
        _correct_frame_metadata(p2_artifacts, p2_ch, selected, by_key,
                                uniformly_scaled=uniformly_scaled)
        p1_by_symbol = {a.symbol: a for a in p1_artifacts}
        p2_by_symbol = {a.symbol: a for a in p2_artifacts}
        slug = smsdev.slug(Path(ch.def_path).stem)
        required = [f"{slug}_A{role['action']}F{i}_TILES"
                    for role in roles for i in range(len(selected[int(role['action'])].frames))]
        if len(set(required)) != len(required):
            raise ValueError("action roles reuse a source action; runtime pose identity would be ambiguous")
        for symbol in required:
            if symbol not in p1_by_symbol or symbol not in p2_by_symbol:
                raise ValueError(f"asset generation omitted required tiles: {symbol}")

        # Histogram colors only where generated pixels use them.  Each side has
        # seven stable indices; the P2 tiles are shifted into CRAM entries 9-15.
        p1_codebook = _palette_codebook([p1_by_symbol[s] for s in required], p1_by_symbol)
        p2_codebook = _palette_codebook([p2_by_symbol[s] for s in required], p2_by_symbol)
        if not p1_codebook or not p2_codebook:
            raise ValueError("selected art rendered fully transparent")

        palette_words = [0] * 16
        for index, word in enumerate(p1_codebook, 1):
            palette_words[index] = word
        for index, word in enumerate(p2_codebook, 9):
            palette_words[index] = word

        final: list[smsdev.Artifact] = []
        compact_sizes: dict[str, int] = {}
        compact_face_sizes: dict[str, int] = {}
        for symbol in required:
            stem = symbol[:-6]
            p1_tiles = p1_by_symbol[symbol]
            p2_tiles = p2_by_symbol[symbol]
            p1_pal = p1_by_symbol[stem + "_PAL"].data
            p2_pal = p2_by_symbol[stem + "_PAL"].data
            p1_blob = _remap_blob(p1_tiles.data, p1_pal, p1_codebook, 0)
            p2_blob = _remap_blob(p2_tiles.data, p2_pal, p2_codebook, 8)
            p1_right, p1_meta = _compact_facing_pose(
                p1_blob, p1_by_symbol[stem + "_META"].data, stem + " P1 right")
            p1_left, p1_metal = _compact_facing_pose(
                p1_blob, p1_by_symbol[stem + "_METAL"].data, stem + " P1 left")
            p2_right, p2_meta = _compact_facing_pose(
                p2_blob, p2_by_symbol[stem + "_META"].data, stem + " P2 right")
            p2_left, p2_metal = _compact_facing_pose(
                p2_blob, p2_by_symbol[stem + "_METAL"].data, stem + " P2 left")
            p1_face_size = max(len(p1_right), len(p1_left))
            p2_face_size = max(len(p2_right), len(p2_left))
            p1_combined = (p1_right.ljust(p1_face_size, b"\0") +
                           p1_left.ljust(p1_face_size, b"\0"))
            p2_combined = (p2_right.ljust(p2_face_size, b"\0") +
                           p2_left.ljust(p2_face_size, b"\0"))
            final.extend((
                smsdev.Artifact(symbol, p1_combined, "sff+act"),
                smsdev.Artifact(stem + "_P2_TILES", p2_combined, "sff+act"),
                smsdev.Artifact(stem + "_META", p1_meta, "air"),
                smsdev.Artifact(stem + "_METAL", p1_metal, "air"),
                smsdev.Artifact(stem + "_P2_META", p2_meta, "air"),
                smsdev.Artifact(stem + "_P2_METAL", p2_metal, "air"),
            ))
            compact_sizes[stem] = max(p1_face_size, p2_face_size)
            compact_face_sizes[stem] = p1_face_size
            compact_face_sizes[stem + "_P2"] = p2_face_size
            for suffix in ("_AXIS", "_CLSN"):
                artifact = p1_by_symbol.get(stem + suffix)
                palette2_artifact = p2_by_symbol.get(stem + suffix)
                if suffix in ("_AXIS", "_CLSN"):
                    if artifact and palette2_artifact and artifact.data != palette2_artifact.data:
                        raise ValueError(f"palette variants changed geometry/collision metadata: {stem + suffix}")
                    if artifact:
                        final.append(copy.copy(artifact))
        # Export the small runtime input contract under stable names. The C
        # core never depends on a character's DEF/command symbol prefix; the
        # selected character cut maps these aliases to that DEF's command
        # names. This lets a different character's cut link unchanged C.
        commands = config.get("commands", {})
        command_symbols = {a.symbol: a for a in p1_artifacts
                           if a.source == "cmd"}
        slug_upper = slug.upper() + "_CMD_"
        for alias, requested_name in commands.items():
            wanted = slug_upper + re.sub(r"[^0-9a-zA-Z]+", "_",
                                         requested_name).upper()
            matches = [a for symbol, a in command_symbols.items()
                       if symbol == wanted]
            if len(matches) != 1:
                raise ValueError(f"command alias {alias}: expected one {wanted}, "
                                 f"found {len(matches)}")
            final.append(smsdev.Artifact("CUT_CMD_" + alias.upper(),
                                         matches[0].data,
                                         "cmd"))

        # Keep each source route's full input pattern as an independently
        # addressable C array. Generic LP/HP aliases are not substitutes for
        # motions such as Terry's timed Rising Tackle charge.
        for route in source_routes:
            for definition in route["source_command_definitions"]:
                symbol = definition["runtime_command_symbol"]
                if symbol is None:
                    continue
                final.append(smsdev.Artifact(
                    symbol, bytes.fromhex(definition["pattern_blob_hex"]), "cmd"))

        # Pack each complete pose within one mapper page.  No pose crosses a
        # bank boundary because stream.c maps one 16 KB page per upload.
        pages: list[bytearray] = []
        bank_map: dict[str, tuple[int, int]] = {}
        for artifact in final:
            if not artifact.symbol.endswith("_TILES"):
                continue
            if len(artifact.data) > BANK_PAGE:
                raise ValueError(f"single pose exceeds a mapper page: {artifact.symbol}")
            if not pages or len(pages[-1]) + len(artifact.data) > BANK_PAGE:
                pages.append(bytearray())
            page_index = len(pages) - 1
            bank_map[artifact.symbol] = (first_bank + page_index, len(pages[-1]))
            pages[-1].extend(artifact.data)

    for index, page in enumerate(pages):
        path = out_dir / f"ken_scene_bank{first_bank + index}.bin"
        path.write_bytes(bytes(page).ljust(BANK_PAGE, b"\0"))

        header = smsdev.render_header(final, "ken_scene_runtime", bank_map)
        guard_end = "#endif /* ken_scene_runtime_H */\n"
        if not header.endswith(guard_end):
            raise ValueError("unexpected generated header guard")
        header = header[:-len(guard_end)]
        pose_frames: dict[str, list[dict]] = {}
        source_frames = {}
        for role in roles:
            aid = int(role["action"])
            action = selected[aid]
            pose_frames[role["role"]] = []
            for i, frame in enumerate(action.frames):
                sprite = by_key[(frame.group, frame.image)]
                divisor = (1 if uniformly_scaled else
                           (scale.SCALE if scale.needs_scale(sprite.width, sprite.height) else 1))
                width = max(1, sprite.width // divisor)
                height = max(1, sprite.height // divisor)
                symbol_stem = f"{slug}_A{aid}F{i}"
                tile_symbol = symbol_stem + "_TILES"
                p2_symbol = symbol_stem + "_P2_TILES"
                stream_ticks = ((compact_sizes[symbol_stem] +
                                 STREAM_CHUNK_BYTES - 1) // STREAM_CHUNK_BYTES)
                duration = (255 if frame.time < 0 else
                            max(1, min(254, frame.time)))
                pose_frames[role["role"]].append({"stem": symbol_stem, "duration": duration,
                                                    "raw_duration": frame.time,
                                                    "stream_ticks": stream_ticks,
                                                    "width": width, "height": height})
                source_frames[f"anim:{aid}.{i}"] = {
                    "class": fidelity.by_id[f"anim:{aid}.{i}"].classe,
                    "size_source": source_sizes[(frame.group, frame.image)],
                    "size_after_pre_scale": [sprite.width, sprite.height],
                    "size_runtime": [width, height],
                    "scale": (scale_report["ratio"] if scale_report else divisor),
                    "uniform_scale_ratio": (scale_report["ratio"]
                                             if scale_report else None),
                    "duration_air": frame.time,
                    "duration_runtime": duration,
                    "stream_ticks": stream_ticks,
                    "clsn1": len(frame.clsn1), "clsn2": len(frame.clsn2),
                }
        velocity = ch.constants.get("velocity", {})
        movement = ch.constants.get("movement", {})
        data = ch.constants.get("data", {})
        jump_parts = [part.strip() for part in velocity.get("jump.neu", "0,-8").split(",")]
        if len(jump_parts) < 2:
            raise ValueError("velocity.jump.neu must contain x,y")
        punch_role = next(role for role in roles if role["role"] == "punch")
        hp_role = next(role for role in roles if role["role"] == "hp")
        kick_role = next(role for role in roles if role["role"] == "kick")
        hk_role = next(role for role in roles if role["role"] == "hk")
        special_role = next(role for role in roles if role["role"] == "special")
        punch_state = int(punch_role.get("state", punch_role["action"]))
        hp_state = int(hp_role.get("state", hp_role["action"]))
        kick_state = int(kick_role.get("state", kick_role["action"]))
        hk_state = int(hk_role.get("state", hk_role["action"]))
        special_state = int(special_role.get("state", special_role["action"]))
        special_speed = special_role.get("velocity_fwd")
        if special_speed is None:
            special_speed = _controller_value(ch, special_state, "velset", "x[0]")
        if special_speed is None or Decimal(str(special_speed)) == 0:
            special_vel_q8 = abs(_q8(velocity.get("walk.fwd", "2")))
        else:
            special_vel_q8 = abs(_q8(special_speed))
        control_profile = controls_from_config(config)
        thresholds = control_profile.thresholds
        if (len(thresholds.get("1", [])) != 1 or
                len(thresholds.get("2", [])) != 1):
            raise ValueError("runtime supports exactly two button tiers per physical key")
        input_threshold_key1 = int(thresholds["1"][0])
        input_threshold_key2 = int(thresholds["2"][0])
        if not (2 <= input_threshold_key1 <= 255 and
                2 <= input_threshold_key2 <= 255):
            raise ValueError("button tier thresholds must be in 2..255 ticks")
        runtime = {
            "life": int(data.get("life", "1000")),
            "walk_fwd": _q8(velocity.get("walk.fwd", "2")),
            "walk_back": _q8(velocity.get("walk.back", "-1.5")),
            "jump_vy": -_q8(jump_parts[1]),
            "gravity": _q8(movement.get("yaccel", "0.5")),
            "damage_punch": _hitdef_value(ch, punch_state, "damage[0]", 5),
            "damage_hp": _hitdef_value(ch, hp_state, "damage[0]",
                                        _hitdef_value(ch, punch_state, "damage[0]", 5)),
            "damage_kick": _hitdef_value(ch, kick_state, "damage[0]", 8),
            "damage_hk": _hitdef_value(ch, hk_state, "damage[0]",
                                        _hitdef_value(ch, kick_state, "damage[0]", 8)),
            "damage_special": _hitdef_value(ch, special_state, "damage[0]",
                                               _hitdef_value(ch, kick_state,
                                                             "damage[0]", 8) * 3),
            "special_vel": special_vel_q8,
            "input_threshold_key1": input_threshold_key1,
            "input_threshold_key2": input_threshold_key2,
            "hitstop": _hitdef_value(ch, punch_state, "pausetime[0]", 8),
            "hit_push": abs(_hitdef_value(ch, punch_state, "ground.velocity[0]", -3)),
            "guard_push": abs(_hitdef_value(ch, punch_state, "guard.velocity[0]", -5)),
            "ground_front_source": int(Decimal(
                ch.constants.get("size", {}).get("ground.front", "0"))),
        }
        close_damage_fallbacks = {
            "punch_close": "damage_punch",
            "hp_close": "damage_hp",
            "kick_close": "damage_kick",
            "hk_close": "damage_hk",
        }
        for close_role, base_damage_key in close_damage_fallbacks.items():
            role = next((item for item in roles if item["role"] == close_role), None)
            if role is None:
                continue
            close_state = int(role.get("state", role["action"]))
            runtime["damage_" + close_role] = _hitdef_value(
                ch, close_state, "damage[0]", runtime[base_damage_key])
        far_damage_fallbacks = {
            "punch_far": "damage_punch",
            "hp_far": "damage_hp",
            "kick_far": "damage_kick",
            "hk_far": "damage_hk",
        }
        for far_role, base_damage_key in far_damage_fallbacks.items():
            role = next((item for item in roles if item["role"] == far_role), None)
            if role is None:
                continue
            far_state = int(role.get("state", role["action"]))
            runtime["damage_" + far_role] = _hitdef_value(
                ch, far_state, "damage[0]", runtime[base_damage_key])
        close_attack_rules = _close_attack_rules(ch, roles, commands)
        far_attack_rules = _far_attack_rules(ch, roles, commands)
        header += _runtime_table(roles, pose_frames, len(required), final, bank_map,
                                 palette_words, runtime, compact_face_sizes)
        header += guard_end
        (out_dir / "ken_scene_runtime.h").write_text(header, encoding="ascii")

    generated = {"source_sha256": ch.source_sha256,
                 "source_def": ch.def_path,
                 "palette_p1_act": p1_name, "palette_p2_act": p2_name,
                 "palette_p1_words": p1_codebook, "palette_p2_words": p2_codebook,
                 "palette_index_shift_p2": 8,
                 "runtime_constants": runtime,
                 "close_attack_rules": close_attack_rules,
                 "far_attack_rules": far_attack_rules,
                 "source_routes": source_routes,
                 "damage_models": [
                     {"role": role_name,
                      "source_state": int(role.get("state", role["action"])),
                      "source_hitdef_count": _hitdef_count(
                          ch, int(role.get("state", role["action"]))),
                      "runtime_hit_policy": "first_visible_overlap_once",
                      "fidelity": "approximate",
                      "reason": "runtime does not preserve separate HitDef timing, hit count, or per-hit damage"}
                     for role_name, role in (("punch", punch_role), ("hp", hp_role),
                                             ("kick", kick_role), ("hk", hk_role))] + [
                     {"role": role["role"],
                      "source_state": int(role.get("state", role["action"])),
                      "source_hitdef_count": _hitdef_count(
                          ch, int(role.get("state", role["action"]))),
                      "runtime_hit_policy": "first_visible_overlap_once",
                      "fidelity": "approximate",
                      "reason": "runtime does not preserve separate HitDef timing, hit count, or per-hit damage"}
                     for role in roles
                     if role["role"] in CLOSE_ROLE_COMMAND_ALIASES] + [
                     {"role": role["role"],
                      "source_state": int(role.get("state", role["action"])),
                      "source_hitdef_count": _hitdef_count(
                          ch, int(role.get("state", role["action"]))),
                      "runtime_hit_policy": "first_visible_overlap_once",
                      "fidelity": "approximate",
                      "reason": "runtime does not preserve separate HitDef timing, hit count, or per-hit damage"}
                     for role in roles
                     if role["role"] in FAR_ROLE_COMMAND_ALIASES],
                 "unsupported_capabilities": [
                     {"role": "special", "source_action": int(special_role["action"]),
                      "source_state": special_state, "fidelity": "unsupported",
                      "reason": "projectile entities are not implemented in the fight runtime"}],
                 "source_limitations": source_limitations,
                 "roles": [{"role": role["role"], "action": int(role["action"]),
                            "state": (int(role["state"]) if role.get("state") is not None else None),
                            "loop_start": role.get("loop_start"),
                            "frame_count": len(pose_frames[role["role"]])}
                           for role in roles],
                 "commands": commands,
                 "frames": source_frames,
                 "pose_count_per_fighter": len(required),
                 "stream_chunk_bytes": STREAM_CHUNK_BYTES,
                 "duration_policy": ("air_exact_candidate_stream_timing_unproven"
                                     if uniformly_scaled else "air_duration_extended_to_stream_ticks"),
                 "fighter_scale": scale_report,
                 "bank_page_bytes": BANK_PAGE,
                 "banks": [],
                 "asset_sha256": {}}
    for bank in range(first_bank, first_bank + len(pages)):
        path = out_dir / f"ken_scene_bank{bank}.bin"
        generated["banks"].append({"bank": bank, "file": path.name,
                                    "used_bytes": len(pages[bank - first_bank]),
                                    "file_bytes": path.stat().st_size,
                                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    header_path = out_dir / "ken_scene_runtime.h"
    generated["asset_sha256"][header_path.name] = hashlib.sha256(header_path.read_bytes()).hexdigest()
    generated["hit_timing"] = {
        item["role"]: hit_recovery(ch, int(item["source_state"]))
        for item in generated["damage_models"]
        if item.get("source_state") is not None
    }
    manifest_path = out_dir / "ken_scene_manifest.json"
    manifest_path.write_text(json.dumps(generated, ensure_ascii=False, indent=2), encoding="utf-8")
    active_bank_files = {entry["file"] for entry in generated["banks"]}
    for stale in out_dir.glob("ken_scene_bank*.bin"):
        if stale.name not in active_bank_files:
            stale.unlink()
    if project_json is not None:
        project = json.loads(project_json.read_text(encoding="utf-8"))
        extra = project["toolchain"].get("makesms_extra", [])
        kept = []
        i = 0
        while i < len(extra):
            value = extra[i]
            if value == "-mbank" and i + 1 < len(extra):
                bank_spec = extra[i + 1]
                if Path(bank_spec.split(":", 1)[0]).name.startswith("ken_scene_bank"):
                    i += 2
                    continue
                kept.extend((value, bank_spec))
                i += 2
            else:
                kept.append(value)
                i += 1
        for entry in generated["banks"]:
            kept.extend(("-mbank", f"out/local_study/generated/scene_cut/{entry['file']}:0:1:{entry['bank']}"))
        project["toolchain"]["makesms_extra"] = kept
        project_json.write_text(json.dumps(project, ensure_ascii=False, indent=2) + "\n",
                                encoding="utf-8")
    print(f"[OK] {len(required)} poses/fighter, {len(pages)} banks, "
          f"palette slots P1=1-7 P2=9-15; source={ch.source_sha256}")
    return generated


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="local-only MUGEN archive or directory")
    parser.add_argument("--config", type=Path, required=True, help="action and palette cut JSON")
    parser.add_argument("--out", type=Path, required=True, help="ignored local output directory")
    parser.add_argument("--first-bank", type=int, default=2)
    parser.add_argument("--project-json", type=Path,
                        help="atualiza makesms_extra para mapear exatamente os bancos gerados")
    args = parser.parse_args(argv)
    generate(args.source, args.config, args.out, args.first_bank,
             args.project_json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
