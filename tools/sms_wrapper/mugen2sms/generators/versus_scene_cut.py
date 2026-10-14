"""Generate a two-character package for the SMS versus runtime.

Individual cuts still come from scene_cut. This module assigns distinct
mapper pages and joins their runtime tables without carrying either source
archive into the repository.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import tempfile
from pathlib import Path

if __package__:
    from . import fight_runtime_data, scene_cut
else:  # direct-script invocation used by local wrapper workflows
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from mugen2sms.generators import fight_runtime_data, scene_cut

MAKESMS_MAX_MERGES = 8  # devkitSMS makesms/src/makesms.c: MAX_MERGES
PALETTE_POLICY = (
    "P1 uses entries 1-7; P2 uses entries 9-15; index 0 transparent"
)

_BYTE_ARRAY = re.compile(
    r"^(?P<decl>(?:static\s+)?const\s+unsigned\s+char\s+"
    r"(?P<symbol>[A-Za-z_]\w*)\s*\[\s*(?P<size>\d+)\s*\]\s*"
    r"=\s*\{(?P<body>.*?)\};)",
    re.M | re.S,
)
_BYTE_VALUE = re.compile(r"0x[0-9A-Fa-f]+|\b\d+\b")


def _deduplicate_metasprite_arrays(header: str) -> tuple[str, dict]:
    """Alias exact metadata and command arrays while retaining public symbols."""
    canonical_by_bytes: dict[tuple[str, bytes], str] = {}
    aliases: dict[str, str] = {}

    def replace(match: re.Match[str]) -> str:
        symbol = match.group("symbol")
        if symbol.endswith(("_META", "_METAL", "_AXIS", "_CLSN")):
            array_kind = "metadata"
        elif "_CUT_CMD_" in symbol:
            array_kind = "command"
        else:
            return match.group("decl")
        body = match.group("body")
        values = _BYTE_VALUE.findall(body)
        residue = _BYTE_VALUE.sub("", body)
        if residue.strip(" ,\t\r\n"):
            raise ValueError(f"malformed byte array while deduplicating {symbol}")
        size = int(match.group("size"))
        if len(values) != size:
            raise ValueError(f"{symbol} declares {size} bytes but contains {len(values)}")
        numbers = [int(value, 0) for value in values]
        if any(value > 0xFF for value in numbers):
            raise ValueError(f"{symbol} contains a value outside unsigned char")
        payload = bytes(numbers)
        dedup_key = (array_kind, payload)
        canonical = canonical_by_bytes.get(dedup_key)
        if canonical is None:
            canonical_by_bytes[dedup_key] = symbol
            return match.group("decl")
        aliases[symbol] = canonical
        return f"#define {symbol} {canonical}"

    output = _BYTE_ARRAY.sub(replace, header)
    size_macros = {name: int(value) for name, value in re.findall(
        r"^#define\s+(\w+_SIZE)\s+(\d+)\s*$", output, re.M)}
    bytes_saved = 0
    for symbol, canonical in aliases.items():
        size = size_macros.get(symbol + "_SIZE")
        canonical_size = size_macros.get(canonical + "_SIZE")
        if size is None or size != canonical_size:
            raise ValueError(f"alias size mismatch: {symbol} -> {canonical}")
        bytes_saved += size
    return output, {"alias_count": len(aliases), "bytes_saved": bytes_saved,
                    "aliases": aliases}


def _metadata_dedup_summary(header: str) -> dict:
    aliases = {name: target for name, target in re.findall(
        r"^#define\s+([A-Za-z_]\w*_(?:META(?:L)?|AXIS|CLSN))\s+"
        r"([A-Za-z_]\w*_(?:META(?:L)?|AXIS|CLSN))\s*$",
        header, re.M)}
    sizes = {name: int(value) for name, value in re.findall(
        r"^#define\s+(\w+_SIZE)\s+(\d+)\s*$", header, re.M)}
    command_aliases = {name: target for name, target in re.findall(
        r"^#define\s+([A-Za-z_]\w*_CUT_CMD_[A-Za-z0-9_]+)\s+"
        r"([A-Za-z_]\w*_CUT_CMD_[A-Za-z0-9_]+)\s*$", header, re.M)}
    return {"alias_count": len(aliases),
            "bytes_saved": sum(sizes[name + "_SIZE"] for name in aliases),
            "aliases": aliases,
            "scope": "exact byte-identical META/METAL/AXIS/CLSN arrays",
            "command_pattern_alias_count": len(command_aliases),
            "command_pattern_bytes_saved": sum(
                sizes[name + "_SIZE"] for name in command_aliases),
            "command_pattern_aliases": command_aliases}


def _pose_rows(text: str) -> tuple[list[str], re.Match[str]]:
    pattern = re.compile(
        r"static const PoseRef\s+poses_all\s*\[[^]]+\]\s*=\s*\{(.*?)\n\};",
        re.S,
    )
    match = pattern.search(text)
    if not match:
        raise ValueError("generated header has no poses_all table")
    rows = [line.strip().rstrip(",") for line in match.group(1).splitlines()
            if line.strip()]
    if not rows or any(not row.startswith("{") or not row.endswith("}")
                       for row in rows):
        raise ValueError("malformed PoseRef table")
    return rows, match


def _palette(text: str) -> list[int]:
    match = re.search(
        r"static const unsigned char\s+cut_sprite_palette\s*\[16\]\s*=\s*\{(.*?)\};",
        text,
        re.S,
    )
    if not match:
        raise ValueError("generated header has no 16-entry sprite palette")
    values = [int(token, 0) for token in
              re.findall(r"0x[0-9A-Fa-f]+|\b\d+\b", match.group(1))]
    if len(values) != 16 or any(value > 0x3F for value in values):
        raise ValueError("malformed sprite palette")
    return values


def _artifact_prefix(text: str) -> str:
    """Return the one source stem used by this generated scene-cut header."""
    symbols = re.findall(
        r"^\s*const\s+unsigned\s+char\s+([A-Za-z_]\w*_A\d+F\d+_AXIS)\s*\[",
        text,
        re.M,
    )
    prefixes = {re.sub(r"_A\d+F\d+_AXIS$", "", symbol) for symbol in symbols}
    if len(prefixes) != 1:
        raise ValueError(f"expected one source artifact prefix, found {sorted(prefixes)}")
    return next(iter(prefixes))


def _prefix_header(text: str, prefix: str) -> tuple[str, list[str]]:
    rows, match = _pose_rows(text)
    text = text[:match.start()] + text[match.end():]
    role = prefix.upper()
    text = re.sub(r"\bCUT_", role + "_CUT_", text)
    text = re.sub(r"\bframes_all\b", prefix + "_frames_all", text)
    text = re.sub(r"\banims\b", prefix + "_anims", text)
    text = re.sub(r"\bcut_sprite_palette\b", prefix + "_cut_sprite_palette", text)

    # A mirror match can feed the same generated character header twice. Its
    # artifact symbols (for example FFSPRYO_A0F0_META) need a role namespace
    # just like the runtime tables, including references in the extracted
    # PoseRef rows. The generated CUT_* command symbols were already
    # namespaced above and do not use the source action/frame naming scheme.
    declarations = set(re.findall(r"^#define\s+([A-Za-z_]\w*)\b", text, re.M))
    declarations.update(re.findall(
        r"^\s*const\s+unsigned\s+char\s+([A-Za-z_]\w*)\s*\[", text, re.M))
    source_symbols = sorted(
        (name for name in declarations if re.search(r"_A\d+F\d+_", name)),
        key=len,
        reverse=True,
    )
    symbol_map = {name: f"{role}_{name}" for name in source_symbols}
    if symbol_map:
        symbol_pattern = re.compile(
            r"\b(" + "|".join(re.escape(name) for name in source_symbols) + r")\b"
        )

        def namespace_symbols(value: str) -> str:
            return symbol_pattern.sub(lambda found: symbol_map[found.group(1)], value)

        text = namespace_symbols(text)
        rows = [namespace_symbols(row) for row in rows]

    guard = prefix.upper() + "_SCENE_RUNTIME_H"
    text = text.replace("ken_scene_runtime_H", guard)
    text = re.sub(r"\A#ifndef\s+" + guard + r"\s+#define\s+" + guard +
                  r"\s+", "", text, count=1)
    text = re.sub(r"\n#endif\s*/\*\s*" + guard + r"\s*\*/\s*$", "\n", text)
    if "#ifndef " + guard in text or "#endif /* " + guard + " */" in text:
        raise ValueError("could not remove the generated header guard")
    return text, rows


def merge_headers(p1_text: str, p2_text: str,
                  p1_poses: int, p2_poses: int) -> str:
    p1_palette, p2_palette = _palette(p1_text), _palette(p2_text)
    # Stable slot symbols let the C consumer remain unchanged when a .def is
    # replaced. Character/source names stay in provenance manifests only.
    p1_text, p1_rows = _prefix_header(p1_text, "p1")
    p2_text, p2_rows = _prefix_header(p2_text, "p2")
    if len(p1_rows) != p1_poses * 2 or len(p2_rows) != p2_poses * 2:
        raise ValueError("PoseRef count disagrees with scene-cut manifest")

    palette = [0] * 16
    palette[1:8] = p1_palette[1:8]
    palette[9:16] = p2_palette[9:16]
    all_poses = p1_rows[:p1_poses] + p2_rows[p2_poses:]
    lines = [
        "#ifndef VERSUS_SCENE_RUNTIME_H",
        "#define VERSUS_SCENE_RUNTIME_H",
        "",
        p1_text,
        p2_text,
        f"#define VERSUS_POSE_COUNT {p1_poses + p2_poses}",
        "#define P1_POSE_BASE 0",
        f"#define P2_POSE_BASE {p1_poses}",
        "static const PoseRef versus_poses[VERSUS_POSE_COUNT] = {",
        *["    " + row + "," for row in all_poses],
        "};",
        "static const unsigned char versus_sprite_palette[16] = {",
        "    " + ", ".join(f"0x{value:02X}" for value in palette) + ",",
        "};",
        "#endif /* VERSUS_SCENE_RUNTIME_H */",
        "",
    ]
    merged, _dedup = _deduplicate_metasprite_arrays("\n".join(lines))
    return merged


def _pack_mapper_images(banks: list[dict], out_dir: Path) -> list[dict]:
    """Concatenate contiguous 16 KiB mapper pages to stay under makesms' cap."""
    ordered = sorted(banks, key=lambda item: item["bank"])
    groups: list[list[dict]] = []
    for item in ordered:
        if not groups or item["bank"] != groups[-1][-1]["bank"] + 1:
            groups.append([item])
        else:
            groups[-1].append(item)
    if len(groups) > MAKESMS_MAX_MERGES:
        raise ValueError(f"mapper layout needs {len(groups)} contiguous file merges; "
                         f"makesms supports at most {MAKESMS_MAX_MERGES}")
    images = []
    for group in groups:
        start, end = group[0]["bank"], group[-1]["bank"]
        path = out_dir / f"versus_scene_banks_{start:02d}.bin"
        payload = bytearray()
        for item in group:
            data = Path(item["path"]).read_bytes()
            if len(data) != 16384:
                raise ValueError(f"bank {item['bank']} has {len(data)} bytes; expected 16384")
            payload.extend(data)
        path.write_bytes(payload)
        images.append({"bank_start": start, "bank_count": end - start + 1,
                       "file": path.name, "path": str(path), "bytes": len(payload),
                       "sha256": hashlib.sha256(payload).hexdigest()})
    return images


def _collect_unique_bank_pages(p1: dict, p1_dir: Path, p2: dict, p2_dir: Path,
                               out_dir: Path, first_bank: int) -> tuple[list[dict], dict, dict]:
    """Pack byte-identical 16 KiB source pages once and return both bank maps.

    Palette variants and mirrored characters can produce the same page at
    different mapper numbers. Reuse is safe only for an exact page match; the
    caller remaps every generated *_TILES_BANK macro through the returned map.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    for pattern in ("ken_scene_bank*.bin", "ryu_scene_bank*.bin",
                    "versus_scene_banks_*.bin"):
        for stale in out_dir.glob(pattern):
            stale.unlink()

    pages_by_bytes: dict[bytes, int] = {}
    owner_by_bank: dict[int, str] = {}
    maps: dict[str, dict[int, int]] = {"p1_ken": {}, "p2_ryu": {}}
    output: list[dict] = []
    aliases: list[dict] = []
    next_bank = first_bank

    for role, manifest, source_dir in (("p1_ken", p1, p1_dir),
                                       ("p2_ryu", p2, p2_dir)):
        file_prefix = "ken" if role == "p1_ken" else "ryu"
        for source_row in sorted(manifest["banks"], key=lambda row: int(row["bank"])):
            source_bank = int(source_row["bank"])
            payload = (source_dir / source_row["file"]).read_bytes()
            if len(payload) != 16384:
                raise ValueError(f"bank {source_bank} has {len(payload)} bytes; expected 16384")
            canonical = pages_by_bytes.get(payload)
            digest = hashlib.sha256(payload).hexdigest()
            if canonical is not None:
                maps[role][source_bank] = canonical
                aliases.append({"fighter": role, "source_bank": source_bank,
                                "bank": canonical, "sha256": digest,
                                "identical_to": owner_by_bank[canonical]})
                continue

            canonical = next_bank
            next_bank += 1
            pages_by_bytes[payload] = canonical
            owner_by_bank[canonical] = role
            maps[role][source_bank] = canonical
            filename = f"{file_prefix}_scene_bank{canonical}.bin"
            target = out_dir / filename
            target.write_bytes(payload)
            output.append({**source_row, "bank": canonical,
                           "source_bank": source_bank, "file": filename,
                           "path": str(target), "bytes": len(payload),
                           "sha256": digest, "fighter": role})

    reuse = {
        "method": "exact_16k_page_bytes",
        "source_pages": {"p1_ken": len(p1["banks"]),
                         "p2_ryu": len(p2["banks"])},
        "unique_pages": len(output),
        "exact_aliases": aliases,
    }
    return output, maps, reuse


def _remap_bank_macros(header: str, bank_map: dict[int, int], fighter: str) -> str:
    """Rewrite every generated tile bank reference and reject unlisted pages."""
    pattern = re.compile(r"^(#define\s+\w+_TILES_BANK\s+)(\d+)\s*$", re.M)
    seen: set[int] = set()

    def replace(match: re.Match[str]) -> str:
        source_bank = int(match.group(2))
        if source_bank not in bank_map:
            raise ValueError(f"{fighter} header references unlisted bank {source_bank}")
        seen.add(source_bank)
        return match.group(1) + str(bank_map[source_bank])

    remapped, count = pattern.subn(replace, header)
    if not count or seen != set(bank_map):
        raise ValueError(f"{fighter} bank macros disagree with manifest bank pages")
    return remapped


def _update_project(project_json: Path, mapper_images: list[dict]) -> None:
    project = json.loads(project_json.read_text(encoding="utf-8"))
    extra = project["toolchain"].get("makesms_extra", [])
    kept: list[str] = []
    i = 0
    while i < len(extra):
        value = extra[i]
        if value == "-mbank" and i + 1 < len(extra):
            spec = extra[i + 1]
            name = Path(spec.split(":", 1)[0]).name
            if name.startswith(("ken_scene_bank", "ryu_scene_bank",
                                "versus_scene_banks_")):
                i += 2
                continue
            kept.extend((value, spec))
            i += 2
        else:
            kept.append(value)
            i += 1
    for item in mapper_images:
        bank_file = Path(item["path"]).resolve()
        project_root = project_json.parent.parent.resolve()
        rel = bank_file.relative_to(project_root).as_posix()
        kept.extend(("-mbank", f"{rel}:0:{item['bank_count']}:{item['bank_start']}"))
    if sum(1 for value in kept if value == "-mbank") > MAKESMS_MAX_MERGES:
        raise ValueError("project manifest exceeds the eight -mbank merge limit")
    project["toolchain"]["makesms_extra"] = kept
    project_json.write_text(json.dumps(project, ensure_ascii=False, indent=2) + "\n",
                            encoding="utf-8")


def generate(p1_source: Path, p1_config: Path, p2_source: Path,
             p2_config: Path, out_dir: Path, p1_first_bank: int = 2,
             p2_first_bank: int = 5, project_json: Path | None = None) -> dict:
    p1_dir, p2_dir = out_dir / "p1_ken", out_dir / "p2_ryu"
    p1 = scene_cut.generate(p1_source, p1_config, p1_dir,
                            first_bank=p1_first_bank)
    p2 = scene_cut.generate(p2_source, p2_config, p2_dir,
                            first_bank=p2_first_bank)
    p1_header = (p1_dir / "ken_scene_runtime.h").read_text(encoding="ascii")
    p2_header = (p2_dir / "ken_scene_runtime.h").read_text(encoding="ascii")
    banks, bank_maps, bank_reuse = _collect_unique_bank_pages(
        p1, p1_dir, p2, p2_dir, out_dir, p1_first_bank)
    p1_header = _remap_bank_macros(p1_header, bank_maps["p1_ken"], "P1")
    p2_header = _remap_bank_macros(p2_header, bank_maps["p2_ryu"], "P2")
    merged = merge_headers(p1_header, p2_header,
                           int(p1["pose_count_per_fighter"]),
                           int(p2["pose_count_per_fighter"]))
    out_dir.mkdir(parents=True, exist_ok=True)
    header_path = out_dir / "versus_scene_runtime.h"
    header_path.write_text(merged, encoding="ascii")
    runtime_data_path = out_dir / "fight_runtime_data.h"
    runtime_data_report_path = out_dir / "fight_runtime_data_manifest.json"
    runtime_data_report = fight_runtime_data.generate(
        (p1_dir / "ken_scene_manifest.json", p2_dir / "ken_scene_manifest.json"),
        header_path, runtime_data_path, runtime_data_report_path)
    input_profile_path = out_dir / "fight_input_profile.h"

    bank_ids = [item["bank"] for item in banks]
    if len(set(bank_ids)) != len(bank_ids):
        raise ValueError("P1 and P2 mapper banks overlap")
    mapper_images = _pack_mapper_images(banks, out_dir)

    manifest = {
        "schema": "sms_versus_scene_cut_v1",
        "source_sha256": {"p1_ken": p1["source_sha256"],
                          "p2_ryu": p2["source_sha256"]},
        "source_def": {"p1_ken": p1["source_def"],
                       "p2_ryu": p2["source_def"]},
        "runtime_symbol_prefix": {
            "p1": "P1_" + _artifact_prefix(p1_header),
            "p2": "P2_" + _artifact_prefix(p2_header),
        },
        "pose_count": {"p1_ken": p1["pose_count_per_fighter"],
                       "p2_ryu": p2["pose_count_per_fighter"]},
        "pose_base": {"p1_ken": 0,
                      "p2_ryu": p1["pose_count_per_fighter"]},
        "runtime_constants": {"p1_ken": p1["runtime_constants"],
                              "p2_ryu": p2["runtime_constants"]},
        "fighter_scale": {"p1_ken": p1.get("fighter_scale"),
                          "p2_ryu": p2.get("fighter_scale")},
        "duration_policy": {"p1_ken": p1.get("duration_policy"),
                            "p2_ryu": p2.get("duration_policy")},
        "banks": banks,
        "bank_reuse": bank_reuse,
        "mapper_images": mapper_images,
        "header": str(header_path),
        "header_sha256": hashlib.sha256(header_path.read_bytes()).hexdigest(),
        "fight_runtime_data": str(runtime_data_path),
        "fight_runtime_data_sha256": hashlib.sha256(runtime_data_path.read_bytes()).hexdigest(),
        "fight_runtime_data_manifest": str(runtime_data_report_path),
        "fight_runtime_data_manifest_sha256": hashlib.sha256(
            runtime_data_report_path.read_bytes()).hexdigest(),
        "fight_runtime_data_schema": runtime_data_report["schema"],
        "fight_input_profile": str(input_profile_path),
        "fight_input_profile_sha256": hashlib.sha256(
            input_profile_path.read_bytes()).hexdigest(),
        "damage_models": {"p1": p1.get("damage_models", []),
                          "p2": p2.get("damage_models", [])},
        "unsupported_capabilities": {
            "p1": p1.get("unsupported_capabilities", []),
            "p2": p2.get("unsupported_capabilities", []),
        },
        "source_limitations": {
            "p1": p1.get("source_limitations", []),
            "p2": p2.get("source_limitations", []),
        },
        "header_metadata_deduplication": _metadata_dedup_summary(merged),
        "palette_policy": PALETTE_POLICY,
    }
    manifest_path = out_dir / "versus_scene_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                             encoding="utf-8")
    if project_json is not None:
        _update_project(project_json, mapper_images)
    return manifest


def _self_check() -> None:
    assert "Ken" not in PALETTE_POLICY and "Ryu" not in PALETTE_POLICY
    assert "P1 uses entries 1-7" in PALETTE_POLICY
    assert "P2 uses entries 9-15" in PALETTE_POLICY
    assert "index 0 transparent" in PALETTE_POLICY

    p1 = """#ifndef ken_scene_runtime_H
#define ken_scene_runtime_H
static const PoseRef poses_all[2] = {
    { A_BANK, A_OFF, A_SIZE },
    { A_P2_BANK, A_P2_OFF, A_P2_SIZE },
};
#define CUT_POSE_COUNT 1
static const Frame frames_all[1] = { { 1, 0, A_META, A_METAL, 0, A_AXIS, 8, 16 }, };
static const Anim anims[1] = { { 0, 1, 255, frames_all }, };
static const unsigned char cut_sprite_palette[16] = { 0,1,2,3,4,5,6,7,0,9,10,11,12,13,14,15 };
#endif /* ken_scene_runtime_H */
"""
    p2 = (p1.replace("A_P2_LEFT_", "B_P2_LEFT_")
          .replace("A_LEFT_", "B_LEFT_").replace("A_P2_", "B_P2_")
          .replace("A_BANK", "B_BANK").replace("A_OFF", "B_OFF")
          .replace("A_SIZE", "B_SIZE").replace("A_META", "B_META")
          .replace("A_METAL", "B_METAL").replace("A_AXIS", "B_AXIS"))
    merged = merge_headers(p1, p2, 1, 1)
    assert "#define P1_CUT_POSE_COUNT 1" in merged
    assert "#define P2_CUT_POSE_COUNT 1" in merged
    assert "{ A_BANK, A_OFF, A_SIZE }" in merged
    assert "{ B_P2_BANK, B_P2_OFF, B_P2_SIZE }" in merged
    assert "#define P2_POSE_BASE 1" in merged

    # Same source header on both sides must get distinct artifact symbols.
    mirror = """#ifndef ken_scene_runtime_H
#define ken_scene_runtime_H
#define SAME_A0F0_TILES_SIZE 8
#define SAME_A0F0_TILES_BANK 2
#define SAME_A0F0_TILES_OFF 0
#define SAME_A0F0_LEFT_TILES_SIZE 8
#define SAME_A0F0_LEFT_TILES_BANK 2
#define SAME_A0F0_LEFT_TILES_OFF 8
#define SAME_A0F0_P2_TILES_SIZE 8
#define SAME_A0F0_P2_TILES_BANK 2
#define SAME_A0F0_P2_TILES_OFF 16
#define SAME_A0F0_P2_LEFT_TILES_SIZE 8
#define SAME_A0F0_P2_LEFT_TILES_BANK 2
#define SAME_A0F0_P2_LEFT_TILES_OFF 24
#define SAME_A0F0_META_SIZE 4
const unsigned char SAME_A0F0_META[4] = { 0, 1, 2, 128 };
#define SAME_A0F0_METAL_SIZE 4
const unsigned char SAME_A0F0_METAL[4] = { 3, 2, 1, 128 };
#define SAME_A0F0_AXIS_SIZE 4
const unsigned char SAME_A0F0_AXIS[4] = { 0, 0, 0, 0 };
#define SAME_A0F0_CLSN_SIZE 4
const unsigned char SAME_A0F0_CLSN[4] = { 1, 0, 2, 0 };
#define CUT_POSE_COUNT 1
static const PoseRef poses_all[2] = {
    { SAME_A0F0_TILES_BANK, SAME_A0F0_TILES_OFF, SAME_A0F0_TILES_SIZE },
    { SAME_A0F0_P2_TILES_BANK, SAME_A0F0_P2_TILES_OFF, SAME_A0F0_P2_TILES_SIZE },
};
static const Frame frames_all[1] = {
    { 1, 0, SAME_A0F0_META, SAME_A0F0_METAL, 0, SAME_A0F0_AXIS, 8, 16 },
};
static const Anim anims[1] = { { 0, 1, 255, frames_all }, };
static const unsigned char cut_sprite_palette[16] = {
    0,1,2,3,4,5,6,7,0,9,10,11,12,13,14,15
};
#endif /* ken_scene_runtime_H */
"""
    assert _artifact_prefix(mirror) == "SAME"
    mirror_merged = merge_headers(mirror, mirror, 1, 1)
    assert "{ P1_SAME_A0F0_TILES_BANK, P1_SAME_A0F0_TILES_OFF, " \
           "P1_SAME_A0F0_TILES_SIZE }" in mirror_merged
    assert "{ P2_SAME_A0F0_P2_TILES_BANK, P2_SAME_A0F0_P2_TILES_OFF, " \
           "P2_SAME_A0F0_P2_TILES_SIZE }" in mirror_merged
    assert "#define P2_SAME_A0F0_META P1_SAME_A0F0_META" in mirror_merged
    assert "#define P2_SAME_A0F0_AXIS P1_SAME_A0F0_AXIS" in mirror_merged
    assert "#define P2_SAME_A0F0_CLSN P1_SAME_A0F0_CLSN" in mirror_merged
    assert "#define P2_P2_SAME_A0F0_META" not in mirror_merged
    assert "#define P1_P1_SAME_A0F0_META" not in mirror_merged
    dedup_summary = _metadata_dedup_summary(mirror_merged)
    assert dedup_summary["bytes_saved"] == 16
    assert dedup_summary["scope"] == \
        "exact byte-identical META/METAL/AXIS/CLSN arrays"

    command_fixture = (
        "#define P1_CUT_CMD_LP_SIZE 3\n"
        "const unsigned char P1_CUT_CMD_LP[3] = { 1, 2, 3 };\n"
        "#define P2_CUT_CMD_LP_SIZE 3\n"
        "const unsigned char P2_CUT_CMD_LP[3] = { 1, 2, 3 };\n"
        "#define P2_CUT_CMD_HP_SIZE 3\n"
        "const unsigned char P2_CUT_CMD_HP[3] = { 1, 2, 3 };\n")
    command_dedup, _ = _deduplicate_metasprite_arrays(command_fixture)
    assert "#define P2_CUT_CMD_LP P1_CUT_CMD_LP" in command_dedup
    assert "#define P2_CUT_CMD_HP P1_CUT_CMD_LP" in command_dedup
    command_summary = _metadata_dedup_summary(command_dedup)
    assert command_summary["command_pattern_alias_count"] == 2
    assert command_summary["command_pattern_bytes_saved"] == 6

    route_fixture = (
        "#define P1_CUT_CMD_ROUTE_RISING_TACKLE_X_0_SIZE 13\n"
        "const unsigned char P1_CUT_CMD_ROUTE_RISING_TACKLE_X_0[13] = "
        "{ 4, 3, 10, 1, 2, 18, 15, 1, 0, 0, 16, 4, 0 };\n"
        "#define P2_CUT_CMD_ROUTE_RISING_TACKLE_X_0_SIZE 13\n"
        "const unsigned char P2_CUT_CMD_ROUTE_RISING_TACKLE_X_0[13] = "
        "{ 4, 3, 10, 1, 2, 18, 15, 1, 0, 0, 16, 4, 0 };\n")
    route_dedup, _ = _deduplicate_metasprite_arrays(route_fixture)
    assert "#define P2_CUT_CMD_ROUTE_RISING_TACKLE_X_0 " \
           "P1_CUT_CMD_ROUTE_RISING_TACKLE_X_0" in route_dedup

    bad_size = ("#define A_AXIS_SIZE 4\n"
                "const unsigned char A_AXIS[4] = { 0, 1, 2, 3 };\n"
                "#define B_AXIS_SIZE 3\n"
                "const unsigned char B_AXIS[4] = { 0, 1, 2, 3 };\n")
    try:
        _deduplicate_metasprite_arrays(bad_size)
        raise AssertionError("deduplicated AXIS with mismatched size metadata")
    except ValueError as exc:
        assert "alias size mismatch" in str(exc)

    meta = "#define A_META_SIZE 4\nconst unsigned char A_META[4] = {\n  0, 1, 2, 128,\n};"
    p1 = p1.replace("static const PoseRef", meta + "\nstatic const PoseRef", 1)
    p2 = p2.replace("static const PoseRef", meta.replace("A_META", "B_META") +
                    "\nstatic const PoseRef", 1)
    different = ("#define B_METAL_SIZE 4\n"
                 "const unsigned char B_METAL[4] = {\n  4, 5, 6, 128,\n};")
    p2 = p2.replace("static const PoseRef", different +
                    "\nstatic const PoseRef", 1)
    merged = merge_headers(p1, p2, 1, 1)
    assert "#define B_META A_META" in merged
    assert "const unsigned char B_META[4]" not in merged
    assert "const unsigned char B_METAL[4]" in merged

    with tempfile.TemporaryDirectory(prefix="versus_bank_pack_") as tmp:
        root = Path(tmp)
        banks = []
        for number in (2, 3, 5):
            path = root / f"bank{number}.bin"
            path.write_bytes(bytes((number,)) * 16384)
            banks.append({"bank": number, "path": str(path)})
        images = _pack_mapper_images(banks, root)
        assert [(item["bank_start"], item["bank_count"]) for item in images] == [
            (2, 2), (5, 1)]
        assert (root / images[0]["file"]).read_bytes() == (
            bytes((2,)) * 16384 + bytes((3,)) * 16384)
        assert len(images) <= MAKESMS_MAX_MERGES

        p1_dir, p2_dir = root / "p1", root / "p2"
        p1_dir.mkdir()
        p2_dir.mkdir()
        page_a = bytes((0x31,)) * 16384
        page_b = bytes((0x72,)) * 16384
        page_c = bytes((0x72,)) * 16383 + bytes((0x73,))
        for directory, rows in (
                (p1_dir, ((2, "p1_2.bin", page_a), (3, "p1_3.bin", page_b))),
                (p2_dir, ((5, "p2_5.bin", page_a), (6, "p2_6.bin", page_c),
                          (7, "p2_7.bin", page_c)))):
            for _bank, filename, payload in rows:
                (directory / filename).write_bytes(payload)
        p1_manifest = {"banks": [{"bank": 2, "file": "p1_2.bin"},
                                  {"bank": 3, "file": "p1_3.bin"}]}
        p2_manifest = {"banks": [{"bank": 5, "file": "p2_5.bin"},
                                  {"bank": 6, "file": "p2_6.bin"},
                                  {"bank": 7, "file": "p2_7.bin"}]}
        unique, maps, reuse = _collect_unique_bank_pages(
            p1_manifest, p1_dir, p2_manifest, p2_dir, root / "dedup", 2)
        assert [row["bank"] for row in unique] == [2, 3, 4]
        assert maps == {"p1_ken": {2: 2, 3: 3},
                        "p2_ryu": {5: 2, 6: 4, 7: 4}}
        assert reuse["unique_pages"] == 3 and len(reuse["exact_aliases"]) == 2
        assert (root / "dedup" / "ryu_scene_bank4.bin").read_bytes() == page_c
        remapped = _remap_bank_macros(
            "#define P2_A0F0_TILES_BANK 5\n"
            "#define P2_A0F1_TILES_BANK 6\n"
            "#define P2_A0F2_TILES_BANK 7\n",
            maps["p2_ryu"], "P2")
        assert "#define P2_A0F0_TILES_BANK 2" in remapped
        assert "#define P2_A0F1_TILES_BANK 4" in remapped
        assert "#define P2_A0F2_TILES_BANK 4" in remapped
        try:
            _remap_bank_macros("#define BAD_TILES_BANK 99\n",
                               maps["p2_ryu"], "P2")
            raise AssertionError("unlisted tile bank macro accepted")
        except ValueError as exc:
            assert "unlisted bank" in str(exc)

        too_many = [{"bank": index * 2, "path": "unused"} for index in range(9)]
        try:
            _pack_mapper_images(too_many, root)
            raise AssertionError("more than eight non-contiguous map images accepted")
        except ValueError as exc:
            assert "makesms supports at most 8" in str(exc)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--p1-source", type=Path)
    parser.add_argument("--p1-config", type=Path)
    parser.add_argument("--p2-source", type=Path)
    parser.add_argument("--p2-config", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--p1-first-bank", type=int, default=2)
    parser.add_argument("--p2-first-bank", type=int, default=5)
    parser.add_argument("--project-json", type=Path)
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args(argv)
    if args.self_check:
        _self_check()
        print("[PASS] versus scene cut self-check")
        return 0
    required = (args.p1_source, args.p1_config, args.p2_source,
                args.p2_config, args.out)
    if any(item is None for item in required):
        parser.error("--p1-source/config, --p2-source/config e --out são obrigatórios")
    result = generate(args.p1_source, args.p1_config, args.p2_source,
                      args.p2_config, args.out, args.p1_first_bank,
                      args.p2_first_bank, args.project_json)
    print(f"[OK] versus cut: {result['pose_count']} poses, "
          f"banks {[bank['bank'] for bank in result['banks']]}; "
          f"header={result['header']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
