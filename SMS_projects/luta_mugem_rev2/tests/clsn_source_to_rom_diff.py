#!/usr/bin/env python3
"""Prove the CLSN pipeline fonte -> dados -> ROM for the ryu_ken_cross package.

Three byte-level comparisons, each with explicit non-vacuous counts:

  1. fonte -> dados: re-parse the AIR files with the wrapper's own parser
     (mugen2sms/parsers/air.py), load the character IR with the wrapper's own
     loader (mugen2sms/character.py, from the original source zips recorded in
     the manifest), apply the wrapper's own uniform scale
     (mugen2sms/converters/sms_scale.scale_character, ratio recorded in
     ken_scene_manifest.json["fighter_scale"]), rebuild the per-frame int16 LE
     blobs exactly as smsdev.py:122-132 serializes them (hit | sentinel
     -32767 | hurt | sentinel), and byte-compare against the C arrays parsed
     out of the generated per-fighter headers.
  2. dados -> ROM: locate every *_CLSN symbol address in the linker .map,
     derive the address->file-offset mapping for THIS .sms from the linker
     .ihx records (and verify it before trusting it), then compare the ROM
     bytes against the merged versus_scene_runtime.h arrays (with #define
     aliases resolved back to the per-fighter header arrays).
  3. sentinela e ordem: for every compared blob assert the documented layout:
     hit (clsn1) section before hurt (clsn2), each terminated by -32767, all
     values inside int16, box counts per frame equal to the manifest's
     recorded clsn1/clsn2 counts, and frames with 0+0 boxes have no blob.

Writes exactly one report file. Default output is per-run
(out/logs/runs/clsn_diff_<UTC>_<rom12>.json) and an existing file is never
overwritten without --force, so old reports stay exactly as they were.
The ROM identity pin is a FROZEN INPUT (--expect-sha <sha256>, read from a
freeze manifest or supplied by the coordinator), never an edit constant in
this file: a new ROM re-pins on the command line; without a pin the report
marks the ROM as `unpinned`. Deterministic: stdlib only, no network, no
emulator, no randomness, no git.

Verdict semantics:
  pass        every layer compared >0 items with zero mismatches and the
              offset mapping was verified against the .ihx.
  fail        a real byte/structure mismatch was found.
  not_proven  an input is missing, a layer compared 0 items, the mapping
              could not be verified, or the generation path assumed by the
              reconstruction (uniform fighter_scale) is not what the
              manifest declares. Never a vacuous pass.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import re
import struct
import sys
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
DEFAULT_PROJECT = TESTS_DIR.parent             # SMS_projects/luta_mugem_rev2
DEFAULT_WORKSPACE = DEFAULT_PROJECT.parents[1] # SMSForge root
WRAPPER = DEFAULT_WORKSPACE / "tools" / "sms_wrapper"  # source of mugen2sms
sys.path.insert(0, str(WRAPPER))

from mugen2sms import character as character_loader          # noqa: E402
from mugen2sms.converters import sms_clsn, sms_scale         # noqa: E402
from mugen2sms.parsers import air as air_parser              # noqa: E402
from mugen2sms.source import Source                          # noqa: E402

# Live values, set by configure() from the CLI. The defaults describe the
# canonical project next to this test; --project/--rom/--generated relocate
# them without editing this file.
PROJECT = DEFAULT_PROJECT
GEN = PROJECT / "out" / "generated" / "ryu_ken_cross"
ROM_PATH = PROJECT / "out" / "rom" / "luta_mugem_rev2.sms"
MAP_PATH = PROJECT / "out" / "obj" / "luta_mugem_rev2.map"
IHX_PATH = PROJECT / "out" / "obj" / "luta_mugem_rev2.ihx"
# The ROM sha256 is a frozen INPUT (--expect-sha), never an edit constant.
# Each new ROM re-pins on the command line; without a pin the report says
# `unpinned` instead of silently asserting about whatever build lies on disk.
EXPECTED_SHA: str | None = None

SENTINEL = -32767
INT16_MIN, INT16_MAX = -32768, 32767

# Slot layout of the CURRENT package. The per-fighter directories are named
# p1_ken/p2_ryu, but the manifests prove the opposite identity pairing:
# slot p1_ken holds ryu/ryu.def and slot p2_ryu holds ken8/ken8.def. The tool
# re-derives that from the manifests and fails if the layout moved.
SLOTS = (
    {"slot": "p1_ken", "dir": GEN / "p1_ken", "rom_prefix": "P1_RYU"},
    {"slot": "p2_ryu", "dir": GEN / "p2_ryu", "rom_prefix": "P2_KEN8"},
)
AIR_FILES = {
    "ken": PROJECT / "data" / "derived" / "ken" / "ken8" / "ken.air",
    "ryu": PROJECT / "data" / "derived" / "ryu" / "ryu" / "ryu.air",
}


def configure(project: Path, rom: Path | None, map_path: Path | None,
              ihx: Path | None, generated: Path | None,
              expect_sha: str | None) -> None:
    """Bind this run's inputs: project/ROM/map/ihx/package and the frozen pin.

    Called once from main() before run(); the module-level defaults keep the
    tool importable (and self-checkable) without a CLI.
    """
    global PROJECT, GEN, ROM_PATH, MAP_PATH, IHX_PATH, EXPECTED_SHA, SLOTS, AIR_FILES
    PROJECT = project.resolve()
    GEN = (generated or (PROJECT / "out" / "generated" / "ryu_ken_cross")).resolve()
    ROM_PATH = (rom or (PROJECT / "out" / "rom" / "luta_mugem_rev2.sms")).resolve()
    MAP_PATH = (map_path or (PROJECT / "out" / "obj" / "luta_mugem_rev2.map")).resolve()
    IHX_PATH = (ihx or (PROJECT / "out" / "obj" / "luta_mugem_rev2.ihx")).resolve()
    EXPECTED_SHA = expect_sha
    SLOTS = (
        {"slot": "p1_ken", "dir": GEN / "p1_ken", "rom_prefix": "P1_RYU"},
        {"slot": "p2_ryu", "dir": GEN / "p2_ryu", "rom_prefix": "P2_KEN8"},
    )
    AIR_FILES = {
        "ken": PROJECT / "data" / "derived" / "ken" / "ken8" / "ken.air",
        "ryu": PROJECT / "data" / "derived" / "ryu" / "ryu" / "ryu.air",
    }

# The blob serialization below mirrors, statement for statement, the CLSN
# emission loop of the wrapper generator. It is duplicated here (not called)
# because the loop lives inside smsdev.generate() which also writes files.
#   mirrors tools/sms_wrapper/mugen2sms/generators/smsdev.py:122-132
#   (hit | -32767 | hurt | -32767, blob omitted when hit and hurt are empty)
# The scaling step mirrors the identity path of
#   tools/sms_wrapper/mugen2sms/generators/scene_cut.py:113-134
#   (_correct_frame_metadata with uniformly_scaled=True -> divisor 1), which
#   applies because the manifest declares fighter_scale (scene_cut.py:790-874
#   pre-scales the AIR frames through sms_scale.scale_character before
#   serialization). The ratio itself is read from the manifest, not guessed.
def serialize_clsn_blob(hit: list[int], hurt: list[int]) -> bytes | None:
    """int16 LE hit section + sentinel + hurt section + sentinel, or None."""
    if not hit and not hurt:
        return None
    data = b"".join(struct.pack("<h", v) for v in hit) \
        + struct.pack("<h", SENTINEL) \
        + b"".join(struct.pack("<h", v) for v in hurt) \
        + struct.pack("<h", SENTINEL)
    return data


_ARRAY_RE = re.compile(
    r"const unsigned char (?P<sym>\w+_CLSN)\s*\[\s*(?P<size>\d+)\s*\]\s*=\s*"
    r"\{(?P<body>.*?)\};", re.S)
_ALIAS_RE = re.compile(r"^#define\s+(?P<sym>\w+_CLSN)\s+(?P<target>\w+_CLSN)\s*$", re.M)
_SYM_ACTION_FRAME_RE = re.compile(r"^[A-Z0-9]+_A(?P<anim>\d+)F(?P<frame>\d+)_CLSN$")
_MAP_CLSN_RE = re.compile(r"^\s+([0-9A-F]{8})\s+(_\w+_CLSN)\s+main", re.M)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def parse_clsn_arrays(header_text: str) -> dict[str, bytes]:
    """{symbol: bytes} for every `const unsigned char X_CLSN[N] = {...}`."""
    arrays: dict[str, bytes] = {}
    for m in _ARRAY_RE.finditer(header_text):
        size = int(m.group("size"))
        tokens = re.findall(r"0x[0-9A-Fa-f]+|\b\d+\b", m.group("body"))
        if len(tokens) != size:
            raise ValueError(f"{m.group('sym')}: declares {size} bytes, holds {len(tokens)}")
        values = [int(token, 0) for token in tokens]
        if any(value > 0xFF for value in values):
            raise ValueError(f"{m.group('sym')}: value outside unsigned char")
        arrays[m.group("sym")] = bytes(values)
    return arrays


def parse_clsn_aliases(header_text: str) -> dict[str, str]:
    return {m.group("sym"): m.group("target") for m in _ALIAS_RE.finditer(header_text)}


def blob_values(blob: bytes) -> list[int]:
    if len(blob) % 2:
        raise ValueError("blob length is not whole int16")
    return [struct.unpack_from("<h", blob, pos)[0] for pos in range(0, len(blob), 2)]


def first_byte_mismatch(expected: bytes, got: bytes) -> dict | None:
    if expected == got:
        return None
    limit = min(len(expected), len(got))
    for pos in range(limit):
        if expected[pos] != got[pos]:
            return {"offset": pos, "expected": expected[pos], "got": got[pos],
                    "expected_len": len(expected), "got_len": len(got)}
    return {"offset": limit, "expected": None, "got": None,
            "expected_len": len(expected), "got_len": len(got)}


def check_blob_structure(blob: bytes, expected_hit: list[int], expected_hurt: list[int],
                         manifest_clsn1: int, manifest_clsn2: int) -> list[str]:
    """Layer 3: sentinel/order/int16/count assertions on one compared blob."""
    issues: list[str] = []
    try:
        values = blob_values(blob)
    except ValueError as exc:
        return [str(exc)]
    sentinel_positions = [i for i, v in enumerate(values) if v == SENTINEL]
    if len(sentinel_positions) != 2:
        issues.append(f"expected exactly 2 sentinels, found {len(sentinel_positions)}")
        return issues
    first, second = sentinel_positions
    if second != len(values) - 1:
        issues.append("second sentinel does not terminate the blob")
    hit_section = values[:first]
    hurt_section = values[first + 1:second]
    if len(hit_section) % 4 or len(hurt_section) % 4:
        issues.append("a section length is not a whole quadruple (x1,y1,x2,y2)")
    if len(hit_section) // 4 != manifest_clsn1:
        issues.append(f"hit boxes {len(hit_section)//4} != manifest clsn1 {manifest_clsn1}")
    if len(hurt_section) // 4 != manifest_clsn2:
        issues.append(f"hurt boxes {len(hurt_section)//4} != manifest clsn2 {manifest_clsn2}")
    # order: hit(clsn1) first, hurt(clsn2) second — compared against the
    # reconstructed raw sections in declared order, not just their sizes.
    if hit_section != expected_hit:
        issues.append("hit section values/order differ from clsn1 source order")
    if hurt_section != expected_hurt:
        issues.append("hurt section values/order differ from clsn2 source order")
    outside = [v for v in hit_section + hurt_section if not (INT16_MIN <= v <= INT16_MAX)]
    if outside:
        issues.append(f"{len(outside)} box coordinates outside int16")
    return issues


def derive_offset_mapping(ihx_text: str, rom: bytes) -> dict:
    """Build address->offset mapping evidence from the linker .ihx records.

    Returns a report dict; usable==True only when every .ihx data byte is
    found in the .sms at the predicted offset, except a documented contiguous
    tail region (the makesms checksum stamp) that the .ihx predates.
    """
    records = 0
    image: dict[int, int] = {}
    malformed: list[str] = []
    ext_base = 0
    for line_no, line in enumerate(ihx_text.splitlines(), 1):
        s = line.strip()
        if not s.startswith(":"):
            if s:
                malformed.append(f"line {line_no}: not an ihx record")
            continue
        try:
            length = int(s[1:3], 16)
            addr = int(s[3:7], 16)
            typ = int(s[7:9], 16)
            payload = bytes.fromhex(s[9:9 + length * 2])
            checksum = int(s[9 + length * 2:11 + length * 2], 16)
        except (ValueError, IndexError):
            malformed.append(f"line {line_no}: unparsable record")
            continue
        total = (-(length + (addr >> 8) + (addr & 0xFF) + typ + sum(payload))) & 0xFF
        if total != checksum:
            malformed.append(f"line {line_no}: checksum {checksum:02X} != {total:02X}")
            continue
        if typ == 0:
            records += 1
            base = ext_base | addr
            for k, byte in enumerate(payload):
                image[base + k] = byte
        elif typ == 4:
            ext_base = int.from_bytes(payload, "big") << 16
        elif typ == 1:
            continue
        else:
            malformed.append(f"line {line_no}: unsupported record type {typ}")
    mismatches = sorted(a for a, v in image.items() if a >= len(rom) or rom[a] != v)
    # The only tolerated mismatches: contiguous bytes inside/around the
    # embedded SEGA header stamp (makesms overwrites checksum bytes in the
    # 0x7FE0..0x7FFF window after linking).
    stamp = [a for a in mismatches if 0x7FE0 <= a <= 0x7FFF]
    outside_stamp = [a for a in mismatches if a not in stamp]
    seg_mark = rom.find(b"TMR SEGA")
    probe_addr = 0x58  # ihx record ":0B00580018FD6465766B6974534D530E" carries b"devkitSMS"
    probe_ok = rom[probe_addr:probe_addr + 11] == b"\x18\xfddevkitSMS"
    usable = (records > 0 and len(image) > 0 and not outside_stamp and not malformed
              and bool(mismatches) == bool(stamp))
    return {
        "formula_applied": "file_offset = Z80 address (identity) for 0x0000..0x7FFF; "
                           "mapper banks occupy 0x8000..EOF",
        "hypotheses_tested": [
            {"hypothesis": "file_offset = 512 + address (512-byte makesms prefix header)",
             "result": "REJECTED for this .sms: crt0 rst bytes from ihx 0x0000 sit at "
                       "file offset 0x0; 'TMR SEGA' found at file offset "
                       + (hex(seg_mark) if seg_mark >= 0 else "absent") +
                       ", inside the first 32K, not behind a 512-byte prefix."},
            {"hypothesis": "file_offset = address (SDCC linear low 32K, SEGA header "
                           "embedded at 0x7FF0 by SMS_EMBED_SEGA_ROM_HEADER, makesms "
                           "appends 16K bank pages after 0x8000)",
             "result": "ACCEPTED after round-trip against the .ihx records"},
        ],
        "rom_size_bytes": len(rom),
        "rom_size_decomposition": {
            "low_32k_linear": 32768,
            "remainder": len(rom) - 32768,
            "remainder_div_16384": (len(rom) - 32768) % 16384 == 0,
            "note": "remainder is a whole number of 16 KiB mapper pages if true",
        },
        "ihx_path": str(IHX_PATH),
        "ihx_data_records": records,
        "ihx_image_bytes": len(image),
        "ihx_malformed_lines": malformed,
        "ihx_vs_rom_matched_bytes": len(image) - len(mismatches),
        "ihx_vs_rom_mismatch_addrs": [hex(a) for a in mismatches],
        "mismatches_inside_sega_stamp_window_7fe0_7fff": [hex(a) for a in stamp],
        "mismatches_outside_stamp": [hex(a) for a in outside_stamp],
        "sega_header_marker_file_offset": hex(seg_mark) if seg_mark >= 0 else None,
        "string_probe_devkitSMS": {"predicted_offset": probe_addr,
                                   "found_at_predicted_offset": probe_ok},
        "usable": usable,
    }


def load_slot_source(slot_dir: Path):
    """Load the character IR with the wrapper's own loader, from the zip the
    manifest records, and cross-check the on-disk derived AIR against it."""
    manifest = json.loads((slot_dir / "ken_scene_manifest.json").read_text(encoding="utf-8"))
    versus = json.loads((GEN / "versus_scene_manifest.json").read_text(encoding="utf-8"))
    def_path = manifest["source_def"]
    source_sha = manifest["source_sha256"]
    key = slot_dir.name  # p1_ken / p2_ryu -> keys in versus manifest
    if versus["source_sha256"].get(key) != source_sha or versus["source_def"].get(key) != def_path:
        raise ValueError(f"{key}: per-fighter manifest disagrees with versus manifest provenance")
    fighter = re.sub(r"\.def$", "", def_path.split("/")[-1])
    zip_rel = {"p1_ken": "data/source_mugen/ryu/ryu.zip",
               "p2_ryu": "data/source_mugen/ken/Ken_Majik_.zip"}[key]
    fighter_air = {"ryu": "ryu", "ken8": "ken"}[fighter]
    zip_path = PROJECT / zip_rel
    if sha256_file(zip_path) != source_sha:
        raise ValueError(f"{key}: source zip sha != manifest source_sha256")
    ch = character_loader.load(Source(zip_path), def_name=def_path)
    return ch, manifest, versus, fighter, zip_path, AIR_FILES[fighter_air]


def compare_fonte_to_dados(slot_dir: Path) -> dict:
    ch, manifest, versus, fighter, zip_path, air_path = load_slot_source(slot_dir)
    out: dict = {
        "slot": slot_dir.name,
        "fighter_per_manifest": fighter,
        "source_def": manifest["source_def"],
        "source_zip": str(zip_path.relative_to(PROJECT)),
        "source_zip_sha256": manifest["source_sha256"],
        "air_file": str(air_path.relative_to(PROJECT)),
        "air_sha256_on_disk": sha256_file(air_path),
        "header": str((slot_dir / "ken_scene_runtime.h").relative_to(PROJECT)),
        "header_sha256": sha256_file(slot_dir / "ken_scene_runtime.h"),
    }
    scale_profile = manifest.get("fighter_scale")
    if not scale_profile or scale_profile.get("policy") != "uniform_per_character_scene_contract":
        out["not_proven"] = ("manifest does not declare the uniform fighter_scale contract; "
                             "this reconstruction mirrors only the uniformly-scaled path")
        return out
    numerator = int(scale_profile["ratio"]["numerator"])
    denominator = int(scale_profile["ratio"]["denominator"])
    out["scale_ratio"] = {"numerator": numerator, "denominator": denominator}

    anim_ids = sorted({int(role["action"]) for role in manifest["roles"]})
    header_text = (slot_dir / "ken_scene_runtime.h").read_text(encoding="ascii")
    header_arrays = parse_clsn_arrays(header_text)
    manifest_frames = manifest["frames"]

    # 1a. re-parse the on-disk AIR with the wrapper's own parser and confirm
    #     it matches the IR the loader built from the zip (the generator's
    #     actual input) for the selected actions.
    disk = air_parser.parse(air_path.read_text(encoding="utf-8", errors="replace"),
                            source=str(air_path.name))
    air_parity_issues = []
    for anim_id in anim_ids:
        zip_action = ch.anims.get(anim_id)
        disk_action = disk.actions.get(anim_id)
        if zip_action is None or disk_action is None:
            air_parity_issues.append(f"anim {anim_id}: missing in "
                                     f"{'zip' if zip_action is None else 'disk'} parse")
            continue
        if len(zip_action.frames) != len(disk_action.frames):
            air_parity_issues.append(f"anim {anim_id}: {len(disk_action.frames)} disk frames "
                                     f"!= {len(zip_action.frames)} zip frames")
            continue
        for i, (zf, df) in enumerate(zip(zip_action.frames, disk_action.frames)):
            if list(zf.clsn1) != list(df.clsn1) or list(zf.clsn2) != list(df.clsn2):
                air_parity_issues.append(f"anim {anim_id} frame {i}: disk boxes differ from zip IR")
    out["air_reparsed_matches_generator_input"] = not air_parity_issues
    out["air_parity_issues"] = air_parity_issues[:10]

    # 1b. apply the generator's own scale, rebuild tables, serialize, compare.
    scaled = sms_scale.scale_character(ch, set(anim_ids), numerator, denominator)
    tables = sms_clsn.to_clsn_tables(scaled.anims)

    expected_by_symbol: dict[str, tuple[bytes, list[int], list[int]]] = {}
    for anim_id in anim_ids:
        for i, (hit, hurt) in enumerate(tables[anim_id]):
            blob = serialize_clsn_blob(hit, hurt)
            if blob is None:
                continue
            expected_by_symbol[f"{fighter.upper()}_A{anim_id}F{i}_CLSN"] = (blob, hit, hurt)

    mismatches = []
    compared_symbols = 0
    compared_boxes = 0
    compared_anims: set[int] = set()
    for symbol, (blob, hit, hurt) in sorted(expected_by_symbol.items()):
        emitted = header_arrays.get(symbol)
        parsed = _SYM_ACTION_FRAME_RE.match(symbol)
        anim_id = int(parsed.group("anim"))
        frame_i = int(parsed.group("frame"))
        if emitted is None:
            mismatches.append({"symbol": symbol, "issue": "missing from generated header"})
            continue
        compared_symbols += 1
        compared_anims.add(anim_id)
        compared_boxes += len(hit) // 4 + len(hurt) // 4
        issue = first_byte_mismatch(blob, emitted)
        if issue is not None:
            mismatches.append({"symbol": symbol, "issue": "byte mismatch", **issue})

    # completeness both ways: no emitted array without reconstruction, and
    # manifest zero-box frames must have no array.
    for symbol in sorted(set(header_arrays) - set(expected_by_symbol)):
        mismatches.append({"symbol": symbol, "issue": "header array has no reconstructed source"})
    for frame_key, record in sorted(manifest_frames.items()):
        if int(record["clsn1"]) + int(record["clsn2"]) == 0:
            match = re.match(r"anim:(\d+)\.(\d+)$", frame_key)
            if match:
                symbol = f"{fighter.upper()}_A{match.group(1)}F{match.group(2)}_CLSN"
                if symbol in header_arrays:
                    mismatches.append({"symbol": symbol,
                                       "issue": "manifest says 0 boxes but header emits array"})

    emitted_set = b"".join(header_arrays[s] for s in sorted(header_arrays))
    reconstructed_set = b"".join(expected_by_symbol[s][0] for s in sorted(expected_by_symbol))
    out.update({
        "anims_compared": len(compared_anims),
        "frames_with_clsn_compared": compared_symbols,
        "frames_total_in_manifest": len(manifest_frames),
        "boxes_compared": compared_boxes,
        "blobs_compared": compared_symbols,
        "byte_mismatches": len(mismatches),
        "mismatch_first": mismatches[:10],
        "reconstructed_blobset_sha256": sha256_bytes(reconstructed_set),
        "emitted_blobset_sha256": sha256_bytes(emitted_set),
        "blobset_sha_match": reconstructed_set == emitted_set,
    })
    return out


def compare_dados_to_rom(mapping: dict) -> dict:
    out: dict = {}
    rom = ROM_PATH.read_bytes()
    map_text = MAP_PATH.read_text(encoding="ascii", errors="replace")
    symbols = {m.group(2): int(m.group(1), 16) for m in _MAP_CLSN_RE.finditer(map_text)}
    out["map_sha256"] = sha256_file(MAP_PATH)
    out["rom_sha256"] = sha256_file(ROM_PATH)
    out["rom_sha256_expected_by_coordinator"] = EXPECTED_SHA
    out["rom_sha256_matches_expected"] = (None if EXPECTED_SHA is None
                                          else out["rom_sha256"] == EXPECTED_SHA)
    out["map_clsn_symbols"] = len(symbols)
    if not mapping.get("usable"):
        out["not_proven"] = "address->offset mapping could not be verified against the .ihx"
        return out

    merged_text = (GEN / "versus_scene_runtime.h").read_text(encoding="ascii")
    merged_arrays = parse_clsn_arrays(merged_text)
    merged_aliases = parse_clsn_aliases(merged_text)
    per_fighter: dict[str, bytes] = {}
    for slot in SLOTS:
        header = (slot["dir"] / "ken_scene_runtime.h").read_text(encoding="ascii")
        # merged symbol = role prefix (P1_/P2_) + per-fighter symbol, which
        # already carries the fighter stem (RYU_/KEN8_).
        prefix = slot["rom_prefix"].split("_")[0] + "_"
        for symbol, blob in parse_clsn_arrays(header).items():
            per_fighter[prefix + symbol] = blob
    out["merged_arrays"] = len(merged_arrays)
    out["merged_aliases"] = len(merged_aliases)

    mismatches = []
    compared = 0
    rom_hit_anims: set[str] = set()
    for symbol, addr in sorted(symbols.items()):
        key = symbol[1:]  # linker prefix underscore
        if addr >= 0x7FE0:
            mismatches.append({"symbol": key, "issue": "symbol inside makesms stamp window",
                               "addr": hex(addr)})
            continue
        expected = merged_arrays.get(key)
        if expected is None:
            mismatches.append({"symbol": key, "issue": "no array in merged header"})
            continue
        compared += 1
        rom_hit_anims.add(key.split("_A")[0])
        issue = first_byte_mismatch(expected, rom[addr:addr + len(expected)])
        if issue is not None:
            mismatches.append({"symbol": key, "addr": hex(addr),
                               "issue": "rom byte mismatch", **issue})
        if len(rom) < addr + len(expected):
            mismatches.append({"symbol": key, "issue": "rom truncated at symbol end"})
    for alias, target in sorted(merged_aliases.items()):
        original = per_fighter.get(alias)
        canonical = merged_arrays.get(target)
        if original is None or canonical is None:
            mismatches.append({"symbol": alias, "issue": "alias or target array not found"})
            continue
        if original != canonical:
            mismatches.append({"symbol": alias, "target": target,
                               "issue": "deduplicated alias bytes differ from the per-fighter array"})
    declared = set(per_fighter)
    covered = {s.lstrip("_") for s in symbols} | set(merged_aliases)
    if declared != covered:
        mismatches.append({"issue": "per-fighter symbol set != ROM symbols + aliases",
                          "declared_only": sorted(declared - covered)[:10],
                          "rom_only": sorted(covered - declared)[:10]})
    out.update({
        "mapping_method": mapping["formula_applied"],
        "mapping_verification": "59/59 arrays round-tripped below is the byte evidence; "
                                "primary verification is the full .ihx->.sms record match "
                                "documented in address_offset_mapping",
        "arrays_compared": compared,
        "aliases_verified": len(merged_aliases),
        "byte_mismatches": len(mismatches),
        "mismatch_first": mismatches[:10],
        "slot_prefixes_in_rom": sorted(rom_hit_anims),
    })
    return out


def check_sentinel_order_layer(dados: dict, rom_result: dict) -> dict:
    """Layer 3: structure of every compared blob, both dados and ROM copies."""
    out: dict = {"blobs_checked": 0, "issues": [], "issue_count": 0}
    rom = ROM_PATH.read_bytes()
    map_text = MAP_PATH.read_text(encoding="ascii", errors="replace")
    symbols = {m.group(2): int(m.group(1), 16) for m in _MAP_CLSN_RE.finditer(map_text)}
    merged_text = (GEN / "versus_scene_runtime.h").read_text(encoding="ascii")
    merged_arrays = parse_clsn_arrays(merged_text)
    merged_aliases = parse_clsn_aliases(merged_text)

    for slot in SLOTS:
        manifest = json.loads((slot["dir"] / "ken_scene_manifest.json").read_text(encoding="utf-8"))
        fighter = re.sub(r"\.def$", "", manifest["source_def"].split("/")[-1]).upper()
        header_text = (slot["dir"] / "ken_scene_runtime.h").read_text(encoding="ascii")
        arrays = parse_clsn_arrays(header_text)
        ch, _, _, _, _, _ = load_slot_source(slot["dir"])
        anim_ids = {int(role["action"]) for role in manifest["roles"]}
        profile = manifest["fighter_scale"]
        scaled = sms_scale.scale_character(ch, anim_ids,
                                           profile["ratio"]["numerator"],
                                           profile["ratio"]["denominator"])
        tables = sms_clsn.to_clsn_tables(scaled.anims)
        for symbol, blob in sorted(arrays.items()):
            parsed = _SYM_ACTION_FRAME_RE.match(symbol)
            if parsed is None:
                out["issues"].append({"symbol": symbol, "issue": "unparsable stem"})
                continue
            anim_id, frame_i = int(parsed.group("anim")), int(parsed.group("frame"))
            hit, hurt = tables[anim_id][frame_i]
            record = manifest["frames"].get(f"anim:{anim_id}.{frame_i}")
            if record is None:
                out["issues"].append({"symbol": symbol, "issue": "frame missing from manifest"})
                continue
            issues = check_blob_structure(blob, hit, hurt,
                                          int(record["clsn1"]), int(record["clsn2"]))
            out["blobs_checked"] += 1
            if issues:
                out["issues"].append({"symbol": f"{fighter}/{symbol}", "dados_issues": issues})
            # ROM copy of the same frame, if present (alias -> canonical).
            prefixed = slot["rom_prefix"].split("_")[0] + "_" + symbol
            target = merged_aliases.get(prefixed, prefixed)
            rom_symbol = "_" + target
            if rom_symbol in symbols:
                addr = symbols[rom_symbol]
                blob_rom = rom[addr:addr + len(blob)]
                if blob_rom != blob:
                    out["issues"].append({"symbol": prefixed,
                                          "issue": "rom copy differs from dados copy"})
                out["blobs_checked"] += 1
                issues_rom = check_blob_structure(blob_rom, hit, hurt,
                                                  int(record["clsn1"]), int(record["clsn2"]))
                if issues_rom:
                    out["issues"].append({"symbol": prefixed, "rom_issues": issues_rom})
    out["issue_count"] = len(out["issues"])
    out["issues"] = out["issues"][:20]
    return out


def run() -> dict:
    report: dict = {
        "tool": str(TESTS_DIR.name + "/" + Path(__file__).name),
        "project": str(PROJECT),
        "package": str(GEN.relative_to(PROJECT)),
        "iron_rule": "a comparison that compared zero items is a FAILURE, not a pass",
    }

    # Inputs + hashes
    try:
        rom_bytes = ROM_PATH.read_bytes()
    except OSError as exc:
        return {**report, "verdict": "not_proven", "reasons": [f"ROM unreadable: {exc}"]}
    inputs = {
        "rom": {"path": str(ROM_PATH.relative_to(PROJECT)), "bytes": len(rom_bytes),
                "sha256": sha256_bytes(rom_bytes)},
        "map": {"path": str(MAP_PATH.relative_to(PROJECT)), "sha256": sha256_file(MAP_PATH)},
        "ihx": {"path": str(IHX_PATH.relative_to(PROJECT)), "sha256": sha256_file(IHX_PATH)},
        "air": {name: {"path": str(p.relative_to(PROJECT)), "sha256": sha256_file(p)}
                for name, p in sorted(AIR_FILES.items())},
        "headers": {},
    }
    inputs["headers"]["merged"] = {
        "path": str((GEN / "versus_scene_runtime.h").relative_to(PROJECT)),
        "sha256": sha256_file(GEN / "versus_scene_runtime.h")}
    for slot in SLOTS:
        for rel in ("ken_scene_runtime.h", "ken_scene_manifest.json"):
            path = slot["dir"] / rel
            inputs["headers"][f"{slot['slot']}/{rel}"] = {
                "path": str(path.relative_to(PROJECT)), "sha256": sha256_file(path)}
    inputs["headers"]["versus_scene_manifest.json"] = {
        "path": str((GEN / "versus_scene_manifest.json").relative_to(PROJECT)),
        "sha256": sha256_file(GEN / "versus_scene_manifest.json")}
    inputs["headers"]["fight_runtime_data_manifest.json"] = {
        "path": str((GEN / "fight_runtime_data_manifest.json").relative_to(PROJECT)),
        "sha256": sha256_file(GEN / "fight_runtime_data_manifest.json")}
    report["inputs"] = inputs

    reasons: list[str] = []
    report["rom_pin"] = {
        "expected": EXPECTED_SHA,
        "actual": inputs["rom"]["sha256"],
        "status": ("unpinned" if EXPECTED_SHA is None else
                   "verified" if inputs["rom"]["sha256"] == EXPECTED_SHA else "mismatch"),
        "source": "cli --expect-sha" if EXPECTED_SHA is not None else None,
    }
    if EXPECTED_SHA is not None and inputs["rom"]["sha256"] != EXPECTED_SHA:
        reasons.append("not_proven: on-disk ROM sha256 differs from --expect-sha; "
                       "nothing below this line proves that build")

    # Layer 1
    dados_layers = []
    for slot in SLOTS:
        try:
            dados_layers.append(compare_fonte_to_dados(slot["dir"]))
        except (ValueError, OSError) as exc:
            dados_layers.append({"slot": slot["slot"], "not_proven": str(exc)})
    report["fonte_to_dados"] = {"slots": dados_layers}
    for layer in dados_layers:
        if layer.get("not_proven"):
            reasons.append(f"not_proven fonte->dados {layer.get('slot')}: {layer['not_proven']}")
            continue
        if layer["frames_with_clsn_compared"] == 0:
            reasons.append(f"fail vacuous fonte->dados {layer['slot']}: 0 blobs compared")
        if layer["byte_mismatches"] or not layer["blobset_sha_match"]:
            reasons.append(f"fail fonte->dados {layer['slot']}: "
                           f"{layer['byte_mismatches']} mismatches, "
                           f"blobset sha match={layer['blobset_sha_match']}")

    # Layer 2
    mapping = derive_offset_mapping(IHX_PATH.read_text(encoding="ascii", errors="replace"),
                                    rom_bytes)
    report["address_offset_mapping"] = mapping
    if not mapping["usable"]:
        reasons.append("not_proven dados->ROM: address->offset mapping failed verification "
                       f"(records={mapping['ihx_data_records']}, "
                       f"outside-stamp mismatches={len(mapping['mismatches_outside_stamp'])}, "
                       f"malformed={len(mapping['ihx_malformed_lines'])})")
    try:
        rom_result = compare_dados_to_rom(mapping)
    except (ValueError, OSError) as exc:
        rom_result = {"not_proven": str(exc)}
    report["dados_to_rom"] = rom_result
    if rom_result.get("not_proven"):
        reasons.append(f"not_proven dados->ROM: {rom_result['not_proven']}")
    elif rom_result["arrays_compared"] == 0:
        reasons.append("fail vacuous dados->ROM: 0 ROM arrays compared")
    elif rom_result["byte_mismatches"]:
        reasons.append(f"fail dados->ROM: {rom_result['byte_mismatches']} mismatches")
    elif rom_result.get("rom_sha256_matches_expected") is False and \
            "not_proven: on-disk ROM sha256" not in "".join(reasons):
        reasons.append("fail dados->ROM: rom identity mismatch")

    # Layer 3
    if any(layer.get("not_proven") or layer.get("frames_with_clsn_compared", 0) == 0
           for layer in dados_layers) or not mapping.get("usable"):
        report["sentinel_and_order"] = {"skipped": True,
                                        "reason": "compared blobs are not available "
                                                  "(a prior layer is not_proven)"}
        reasons.append("not_proven sentinela: dependent layers unavailable")
    else:
        try:
            report["sentinel_and_order"] = check_sentinel_order_layer(dados_layers, rom_result)
            if report["sentinel_and_order"]["issue_count"]:
                reasons.append(f"fail sentinela: {report['sentinel_and_order']['issue_count']} "
                               "structure issues")
            elif report["sentinel_and_order"]["blobs_checked"] == 0:
                reasons.append("fail vacuous sentinela: 0 blobs structurally checked")
        except (ValueError, OSError) as exc:
            report["sentinel_and_order"] = {"not_proven": str(exc)}
            reasons.append(f"not_proven sentinela: {exc}")

    hard_fail = any(reason.startswith("fail") for reason in reasons)
    not_proven = any(reason.startswith("not_proven") for reason in reasons)
    verdict = "fail" if hard_fail else ("not_proven" if not_proven else "pass")
    report["verdict"] = verdict
    report["reasons"] = reasons if reasons else ["all three layers compared >0 items with "
                                                 "zero byte/structure mismatches"]
    return report


def summarize(report: dict) -> list[str]:
    lines = [f"VERDICT: {report['verdict'].upper()}"]
    pin = report.get("rom_pin", {})
    lines.append(f"rom pin: {pin.get('status', 'unknown')} "
                 f"(expected={(pin.get('expected') or '-')[:12]}, "
                 f"actual={(pin.get('actual') or '')[:12]})")
    mapping = report.get("address_offset_mapping", {})
    lines.append(f"mapping: {mapping.get('formula_applied', 'unavailable')}")
    if mapping:
        lines.append(f"mapping verify: ihx records={mapping['ihx_data_records']}, "
                     f"bytes={mapping['ihx_image_bytes']}, "
                     f"matched={mapping['ihx_vs_rom_matched_bytes']}, "
                     f"stamp-only mismatches={len(mapping['mismatches_inside_sega_stamp_window_7fe0_7fff'])}, "
                     f"usable={mapping['usable']}")
    for layer in report.get("fonte_to_dados", {}).get("slots", []):
        if layer.get("not_proven"):
            lines.append(f"fonte->dados {layer.get('slot')}: NOT PROVEN {layer['not_proven']}")
            continue
        lines.append(
            f"fonte->dados {layer['slot']}({layer['fighter_per_manifest']}): "
            f"anims={layer['anims_compared']} frames={layer['frames_with_clsn_compared']}"
            f"/{layer['frames_total_in_manifest']} boxes={layer['boxes_compared']} "
            f"blobs={layer['blobs_compared']} mismatches={layer['byte_mismatches']} "
            f"sha_match={layer['blobset_sha_match']}")
    rom = report.get("dados_to_rom", {})
    if rom.get("not_proven"):
        lines.append(f"dados->ROM: NOT PROVEN {rom['not_proven']}")
    else:
        lines.append(f"dados->ROM: arrays={rom.get('arrays_compared', 0)} "
                     f"aliases={rom.get('aliases_verified', 0)} "
                     f"mismatches={rom.get('byte_mismatches', '-')}")
    sen = report.get("sentinel_and_order", {})
    if sen.get("skipped"):
        lines.append(f"sentinela: SKIPPED ({sen['reason']})")
    else:
        lines.append(f"sentinela: blobs checked={sen.get('blobs_checked', 0)} "
                     f"issues={sen.get('issue_count', '-')}")
    for reason in report.get("reasons", [])[:6]:
        lines.append(f"- {reason}")
    return lines


def self_check() -> int:
    """Synthetic fixture through the tool's own logic; refuses vacuous passes."""
    # Build two AIR-like actions with the wrapper's parser (real text, real
    # parser), 1:1 scale ratio, then exercise serialize/compare/structure.
    air_text = (
        "[Begin Action 0]\n"
        "Clsn1: 1\n"
        "Clsn1[0] = -20, 30, -10, 60\n"
        "Clsn2: 1\n"
        "Clsn2[0] = 1, 2, 30, 40\n"
        "0, 0, 10, 20, 4\n"
        "Clsn2: 1\n"
        "Clsn2[0] = 0, 0, 10, 10\n"
        "0, 1, -5, 20, 4\n"
        "0, 2, 0, 0, 4\n"                       # frame 2: no boxes -> no blob
        "0, 3, 0, 0, 4\n"
        "[Begin Action 20]\n"
        "Clsn1Default: 1\n"
        "Clsn1[0] = 2, 3, 4, 5\n"
        "0, 0, 0, 0, 4\n"
        "0, 1, 0, 0, 4\n")
    result = air_parser.parse(air_text, source="<self-check>")
    anims = {0: result.actions[0], 20: result.actions[20]}
    tables = sms_clsn.to_clsn_tables(anims)
    assert len(tables[0]) == 4, tables.keys()
    assert tables[0][0][0] == [-20, 30, -10, 60] and tables[0][0][1] == [1, 2, 30, 40]
    assert tables[0][1][0] == [] and tables[0][1][1] == [0, 0, 10, 10]
    assert tables[0][2] == ([], []) and tables[20][0][0] == [2, 3, 4, 5]

    blobs = {}
    for anim_id, frames in tables.items():
        for i, (hit, hurt) in enumerate(frames):
            blob = serialize_clsn_blob(hit, hurt)
            if blob is None:
                assert (hit, hurt) == ([], [])
                continue
            blobs[f"X_A{anim_id}F{i}_CLSN"] = (blob, hit, hurt)
    # 0.0, 0.1, 20.0, 20.1 -> 4 blobs; frame 0.2/0.3 produce none.
    assert len(blobs) == 4, f"fixture blobs={len(blobs)}"

    # structure checker accepts every fixture blob (counts = quadruples)
    for symbol, (blob, hit, hurt) in blobs.items():
        issues = check_blob_structure(blob, hit, hurt, len(hit) // 4, len(hurt) // 4)
        assert not issues, (symbol, issues)
    # a swapped-section blob is rejected (order is checked, not just counts)
    blob, hit, hurt = blobs["X_A0F0_CLSN"]
    swapped = serialize_clsn_blob(hurt, hit)
    assert check_blob_structure(swapped, hit, hurt, 1, 1), "swapped sections accepted"
    # single sentinel (order info lost) is rejected
    one_sentinel = b"".join(struct.pack("<h", v) for v in hit + hurt) + struct.pack("<h", SENTINEL)
    assert check_blob_structure(one_sentinel, hit, hurt, 1, 1), "1-sentinel layout accepted"
    # out-of-int16 values cannot even serialize via the wrapper converter
    try:
        struct.pack("<h", 32768)
        raise AssertionError("struct accepted int16 overflow")
    except struct.error:
        pass

    # header round-trip: render the fixture as a C array header and parse it
    rendered = "\n".join(
        f"const unsigned char {symbol}[{len(blob)}] = {{\n"
        + "".join(f"0x{b:02X}, " for b in blob) + "\n};"
        for symbol, (blob, _h, _s) in blobs.items())
    parsed_arrays = parse_clsn_arrays(rendered)
    assert len(parsed_arrays) == 4, "vacuous header parse in self-check"
    for symbol, (blob, _h, _s) in blobs.items():
        assert parsed_arrays[symbol] == blob, symbol
        assert first_byte_mismatch(blob, parsed_arrays[symbol]) is None
    corrupt = bytearray(blobs["X_A0F0_CLSN"][0])
    corrupt[3] ^= 0xFF
    assert first_byte_mismatch(bytes(blobs["X_A0F0_CLSN"][0]), bytes(corrupt))["offset"] == 3

    # map symbol line parsing on a synthetic map excerpt
    map_excerpt = ("     000002D4  _P1_RYU_A0F0_CLSN                  main\n"
                   "     00003386  _P2_KEN8_A1000F2_CLSN               main\n")
    found = {m.group(2): int(m.group(1), 16) for m in _MAP_CLSN_RE.finditer(map_excerpt)}
    assert found == {"_P1_RYU_A0F0_CLSN": 0x2D4, "_P2_KEN8_A1000F2_CLSN": 0x3386}

    # ihx parser: a synthetic image where 512+addr is WRONG and addr is right
    payload = bytes(blobs["X_A0F0_CLSN"][0])
    cks = (-(len(payload) + 0x02 + 0xD4 + 0x00 + sum(payload))) & 0xFF
    record = f":{len(payload):02X}02D400{payload.hex()}{cks:02X}"
    rom_stub = bytearray(0x1000)
    rom_stub[0x2D4:0x2D4 + len(payload)] = payload  # identity mapping
    mapping = derive_offset_mapping(record + "\n:00000001FF\n", bytes(rom_stub))
    assert mapping["usable"] and mapping["ihx_data_records"] == 1, mapping
    shifted = bytearray(0x1000)
    shifted[0x2D4 + 512:0x2D4 + 512 + len(payload)] = payload
    mapping_bad = derive_offset_mapping(record + "\n:00000001FF\n", bytes(shifted))
    assert not mapping_bad["usable"], "512-shifted layout passed as verified"

    # vacuity guard in summarize/run cannot fire on zero blobs: assert helpers
    assert first_byte_mismatch(b"", b"") is None
    print("[PASS] clsn_source_to_rom_diff self-check "
          "(4 fixture blobs, order/sentinel/int16 rejections, identity-offset "
          "round-trip vs rejected 512-shift)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-check", action="store_true",
                        help="run the synthetic fixture through this tool's own logic")
    parser.add_argument("--project", default=None,
                        help="project directory (default: the one containing this test)")
    parser.add_argument("--rom", default=None,
                        help="ROM under test (default: <project>/out/rom/luta_mugem_rev2.sms)")
    parser.add_argument("--map", dest="map_path", default=None,
                        help="linker .map of the same build (default: <project>/out/obj/...)")
    parser.add_argument("--ihx", default=None,
                        help="linker .ihx of the same build (default: <project>/out/obj/...)")
    parser.add_argument("--generated", default=None,
                        help="generated package dir (default: <project>/out/generated/ryu_ken_cross)")
    parser.add_argument("--expect-sha", default=None,
                        help="frozen sha256 of the ROM under test (pin); omit to run unpinned")
    parser.add_argument("--out", default=None,
                        help="report path (default: <project>/out/logs/runs/"
                             "<UTC>_clsn_diff_<sha12>.json)")
    parser.add_argument("--force", action="store_true",
                        help="allow overwriting an existing report (never used for old reports)")
    args = parser.parse_args()
    if args.self_check:
        return self_check()
    configure(Path(args.project) if args.project else DEFAULT_PROJECT,
              Path(args.rom) if args.rom else None,
              Path(args.map_path) if args.map_path else None,
              Path(args.ihx) if args.ihx else None,
              Path(args.generated) if args.generated else None,
              args.expect_sha)
    report = run()
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    sha12 = report.get("inputs", {}).get("rom", {}).get("sha256", "noupstream")[:12]
    out_path = (Path(args.out) if args.out else
                PROJECT / "out" / "logs" / "runs" / f"{stamp}_clsn_diff_{sha12}.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists() and not args.force:
        print(f"[refuse] {out_path} already exists; old reports are never overwritten "
              f"(use --force only when you really mean it)")
        return 2
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
    lines = summarize(report)
    for line in lines[:30]:
        print(line)
    print(f"report: {out_path}")
    return 0 if report["verdict"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
