#!/usr/bin/env python3
"""Bind every ROM bank the integrated runtime actually reads.

Pose metadata can occupy one shared page or one page per fighter. Every
metadata page and every tile bank cited by pose_table.h must equal the
corresponding slice of the concatenated bank image.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ENTRY_RE = re.compile(r"\{\s*(\d+)\s*,\s*(\d+)\s*,(?:\s*(\d+)\s*,)?")
META_RE = re.compile(r"#define\s+(?:POSE_META_BANK|\w+_POSE_META_BANK)\s+(\d+)u?")
FRAME_BANK_RE = re.compile(r"#define\s+\w+_FRAME_DATA_BANK\s+(\d+)u?")
INDEX_BANK_RE = re.compile(r"#define\s+(KEN|RYU)_POSE_INDEX_BANK\s+(\d+)u?")
INDEX_COUNT_RE = re.compile(r"#define\s+(KEN|RYU)_POSE_COUNT\s+(\d+)u?")
INDEX_OFF_RE = re.compile(r"#define\s+(KEN|RYU)_POSE_INDEX_OFF\s+(\d+)u?")
ACTOR_META_RE = re.compile(r"#define\s+(KEN|RYU)_POSE_META_BANK\s+(\d+)u?")
INDEX_RECORD_RE = re.compile(r"#define\s+POSE_INDEX_RECORD_BYTES\s+(\d+)u?")


class BindError(Exception):
    pass


def pose_uses(text: str) -> tuple[set[int], dict[int, list[int]]]:
    declared_meta = {int(bank) for bank in META_RE.findall(text)}
    entries = [(int(b), int(off), int(mb) if mb else None)
               for b, off, mb in ENTRY_RE.findall(text)]
    if not entries:
        raise BindError("nenhuma entrada de pose no header")
    by_bank: dict[int, list[int]] = {}
    entry_meta: set[int] = set()
    for bank, off, meta_bank in entries:
        by_bank.setdefault(bank, []).append(off)
        if meta_bank is not None:
            entry_meta.add(meta_bank)
    if entry_meta:
        if declared_meta and declared_meta != entry_meta:
            raise BindError(
                f"macros de metadata {sorted(declared_meta)} divergem das poses "
                f"{sorted(entry_meta)}"
            )
        return entry_meta, by_bank
    if not declared_meta:
        raise BindError("banco de metadata ausente no header de poses")
    return declared_meta, by_bank


def banked_pose_uses(text: str, index_blob: bytes, bank_bytes: int
                     ) -> tuple[set[int], dict[int, list[int]], set[int]]:
    record_match = INDEX_RECORD_RE.search(text)
    if not record_match:
        raise BindError("POSE_INDEX_RECORD_BYTES ausente")
    record_bytes = int(record_match.group(1))
    if record_bytes != 11:
        raise BindError(f"registro de índice de pose tem tamanho inesperado: {record_bytes}")
    banks = {actor: int(value) for actor, value in INDEX_BANK_RE.findall(text)}
    counts = {actor: int(value) for actor, value in INDEX_COUNT_RE.findall(text)}
    offsets = {actor: int(value) for actor, value in INDEX_OFF_RE.findall(text)}
    meta = {actor: int(value) for actor, value in ACTOR_META_RE.findall(text)}
    for actor in ("KEN", "RYU"):
        if actor not in banks or actor not in counts or actor not in offsets or actor not in meta:
            raise BindError(f"pose index incompleto para {actor}")
    meta_banks = set(meta.values())
    index_banks = set(banks.values())
    by_bank: dict[int, list[int]] = {}
    for actor in ("KEN", "RYU"):
        start = offsets[actor]
        end = start + counts[actor] * record_bytes
        if start < 0 or end > len(index_blob):
            raise BindError(f"tabela {actor} excede o blob de índice")
        if end > bank_bytes:
            raise BindError(f"tabela {actor} cruza a janela de um banco ROM")
        for position in range(start, end, record_bytes):
            record = index_blob[position:position + record_bytes]
            tile_bank = record[0]
            tile_off = record[1] | (record[2] << 8)
            offsets_in_meta = [record[i] | (record[i + 1] << 8)
                               for i in (3, 5, 7, 9)]
            if tile_off >= bank_bytes:
                raise BindError(f"offset de tiles {tile_off} fora do banco {tile_bank}")
            if any(value >= bank_bytes for value in offsets_in_meta):
                raise BindError(f"offset de metadata fora do banco do ator {actor}")
            by_bank.setdefault(tile_bank, []).append(tile_off)
    return meta_banks, by_bank, index_banks


def check(rom: bytes, image: bytes, base_bank: int, pose_text: str,
          meta_blob: bytes, bank_bytes: int = 16384,
          frame_data_blob: bytes | None = None,
          frame_data_header: str | None = None,
          pose_index_blob: bytes | None = None,
          pose_index_header: str | None = None) -> tuple[list[str], list[str]]:
    failures: list[str] = []
    lines: list[str] = []
    try:
        if pose_index_blob is not None and pose_index_header is not None:
            meta_banks, by_bank, index_banks = banked_pose_uses(
                pose_index_header, pose_index_blob, bank_bytes)
        elif pose_index_blob is not None or pose_index_header is not None:
            raise BindError("pose-index blob e header devem ser fornecidos juntos")
        else:
            meta_banks, by_bank = pose_uses(pose_text)
            index_banks = set()
    except BindError as exc:
        return [str(exc)], []
    if not meta_blob or len(meta_blob) % bank_bytes:
        failures.append(
            f"blob meta tem {len(meta_blob)} B, nao e multiplo de {bank_bytes} B"
        )
    meta_pages = len(meta_blob) // bank_bytes
    ordered_meta_banks = sorted(meta_banks)
    if len(ordered_meta_banks) != meta_pages:
        failures.append(
            f"header usa {len(ordered_meta_banks)} bancos meta, blob tem {meta_pages} paginas"
        )
    if ordered_meta_banks and ordered_meta_banks != list(
            range(ordered_meta_banks[0], ordered_meta_banks[0] + len(ordered_meta_banks))):
        failures.append(f"bancos meta nao contiguos: {ordered_meta_banks}")
    for meta_bank in meta_banks:
        if meta_bank in by_bank:
            failures.append(f"banco meta {meta_bank} tambem citado como blob de tiles")

    def rom_bank(bank: int) -> bytes | None:
        start = bank * bank_bytes
        end = start + bank_bytes
        if end > len(rom):
            failures.append(f"ROM nao alcanca o banco {bank} (arquivo {len(rom)} B)")
            return None
        return rom[start:end]

    def image_bank(bank: int) -> bytes | None:
        idx = bank - base_bank
        start = idx * bank_bytes
        end = start + bank_bytes
        if idx < 0 or end > len(image):
            failures.append(
                f"banco {bank} fora da imagem (base {base_bank}, imagem {len(image)} B)")
            return None
        return image[start:end]

    if ordered_meta_banks and meta_pages == len(ordered_meta_banks):
        first_meta_bank = ordered_meta_banks[0]
        for page, meta_bank in enumerate(ordered_meta_banks):
            expected_meta = meta_blob[page * bank_bytes:(page + 1) * bank_bytes]
            meta_rom = rom_bank(meta_bank)
            if meta_rom is not None and meta_rom != expected_meta:
                failures.append(f"banco {meta_bank} da ROM diverge do blob meta")
            elif meta_rom is not None:
                lines.append(f"banco {meta_bank} da ROM == blob meta ({bank_bytes} B)")
            meta_img = image_bank(meta_bank)
            if meta_img is not None and meta_img != expected_meta:
                failures.append(f"imagem no banco {meta_bank} diverge do blob meta")
            if meta_bank < first_meta_bank:
                failures.append(f"banco meta {meta_bank} anterior ao inicio do blob")

    if frame_data_blob is not None or frame_data_header is not None:
        if frame_data_blob is None or frame_data_header is None:
            failures.append("frame-data blob e header devem ser fornecidos juntos")
        else:
            frame_banks = sorted({int(bank) for bank in FRAME_BANK_RE.findall(frame_data_header)})
            if not frame_banks:
                failures.append("nenhum FRAME_DATA_BANK no header de descritores")
            if not frame_data_blob or len(frame_data_blob) % bank_bytes:
                failures.append(
                    f"blob frame-data tem {len(frame_data_blob)} B, nao e multiplo de {bank_bytes} B"
                )
            frame_pages = len(frame_data_blob) // bank_bytes
            if len(frame_banks) != frame_pages:
                failures.append(
                    f"header usa {len(frame_banks)} bancos frame-data, blob tem {frame_pages} paginas"
                )
            if frame_banks and frame_banks != list(
                    range(frame_banks[0], frame_banks[0] + len(frame_banks))):
                failures.append(f"bancos frame-data nao contiguos: {frame_banks}")
            if set(frame_banks) & (meta_banks | set(by_bank) | index_banks):
                failures.append("banco frame-data colide com tiles ou metadata")
            if frame_banks and frame_pages == len(frame_banks):
                for page, frame_bank in enumerate(frame_banks):
                    expected_frame_data = frame_data_blob[
                        page * bank_bytes:(page + 1) * bank_bytes
                    ]
                    got = rom_bank(frame_bank)
                    if got is not None and got != expected_frame_data:
                        failures.append(f"banco {frame_bank} da ROM diverge do blob frame-data")
                    elif got is not None:
                        lines.append(f"banco {frame_bank} da ROM == blob frame-data ({bank_bytes} B)")
                    expected = image_bank(frame_bank)
                    if expected is not None and expected != expected_frame_data:
                        failures.append(f"imagem no banco {frame_bank} diverge do blob frame-data")

    if pose_index_blob is not None:
        if not pose_index_blob or len(pose_index_blob) % bank_bytes:
            failures.append(
                f"blob pose-index tem {len(pose_index_blob)} B, nao e multiplo de {bank_bytes} B"
            )
        index_pages = len(pose_index_blob) // bank_bytes
        ordered_index = sorted(index_banks)
        if len(ordered_index) != index_pages:
            failures.append(
                f"header usa {len(ordered_index)} bancos pose-index, blob tem {index_pages} paginas"
            )
        if ordered_index and ordered_index != list(
                range(ordered_index[0], ordered_index[0] + len(ordered_index))):
            failures.append(f"bancos pose-index nao contiguos: {ordered_index}")
        if set(ordered_index) & (meta_banks | set(by_bank)):
            failures.append("banco pose-index colide com tiles ou metadata")
        if frame_data_header is not None:
            frame_banks = {int(bank) for bank in FRAME_BANK_RE.findall(frame_data_header)}
            if set(ordered_index) & frame_banks:
                failures.append("banco pose-index colide com frame-data")
        if len(ordered_index) == index_pages:
            for page, index_bank in enumerate(ordered_index):
                expected_index = pose_index_blob[page * bank_bytes:(page + 1) * bank_bytes]
                got = rom_bank(index_bank)
                if got is not None and got != expected_index:
                    failures.append(f"banco {index_bank} da ROM diverge do blob pose-index")
                elif got is not None:
                    lines.append(f"banco {index_bank} da ROM == blob pose-index ({bank_bytes} B)")
                expected = image_bank(index_bank)
                if expected is not None and expected != expected_index:
                    failures.append(f"imagem no banco {index_bank} diverge do blob pose-index")

    for bank, offs in sorted(by_bank.items()):
        for off in offs:
            if off < 0 or off >= bank_bytes:
                failures.append(f"offset {off} fora do banco {bank}")
        got = rom_bank(bank)
        expect = image_bank(bank)
        if got is None or expect is None:
            continue
        if got != expect:
            failures.append(f"banco {bank} da ROM diverge da imagem (tiles usados)")
        else:
            lines.append(f"banco {bank} da ROM == imagem ({len(offs)} poses)")
    if not by_bank:
        failures.append("nenhum banco de tiles citado")
    return failures, lines


def self_check() -> None:
    bank = 16
    image = bytes([1]) * bank + bytes([2]) * bank + bytes([3]) * bank
    rom = bytes(bank) + image  # banks 0 unused, 1..3 = image at base 1
    meta = bytes([3]) * bank
    pose = ("#define POSE_META_BANK 3u\n"
            "static const PoseTiles ken[2] = {\n"
            "    { 1, 0, (const unsigned char *)0x8000u },\n"
            "    { 2, 4, (const unsigned char *)0x8010u },\n"
            "};\n")
    fail, lines = check(rom, image, 1, pose, meta, bank)
    assert not fail, fail
    assert any("banco 3" in ln for ln in lines)
    assert any("banco 1" in ln for ln in lines)

    image_multi = (bytes([1]) * bank + bytes([2]) * bank +
                   bytes([3]) * bank + bytes([4]) * bank + bytes([5]) * bank)
    rom_multi = bytes(bank) + image_multi
    meta_multi = bytes([3]) * bank + bytes([4]) * bank
    pose_multi = ("#define KEN_POSE_META_BANK 3u\n"
                  "#define RYU_POSE_META_BANK 4u\n"
                  "static const PoseTiles ken[1] = {\n"
                  "    { 1, 0, 3, (const unsigned char *)0x8000u },\n"
                  "};\n"
                  "static const PoseTiles ryu[1] = {\n"
                  "    { 2, 4, 4, (const unsigned char *)0x8000u },\n"
                  "};\n")
    frame_header = ("#define KEN_FRAME_DATA_BANK 5u\n"
                    "#define RYU_FRAME_DATA_BANK 5u\n")
    fail, lines = check(rom_multi, image_multi, 1, pose_multi, meta_multi, bank,
                        bytes([5]) * bank, frame_header)
    assert not fail, fail
    assert any("banco 3" in ln for ln in lines)
    assert any("banco 4" in ln for ln in lines)
    assert any("banco 5" in ln for ln in lines)

    # Banked tables contain compact offsets and are bound as a physical page.
    index_image = bytearray(bank)
    index_image[:11] = bytes((1, 0, 0, 0, 0, 1, 0, 2, 0, 3, 0))
    pose_index_header = (
        "#define KEN_POSE_META_BANK 3u\n#define RYU_POSE_META_BANK 3u\n"
        "#define KEN_POSE_INDEX_BANK 5u\n#define RYU_POSE_INDEX_BANK 5u\n"
        "#define KEN_POSE_COUNT 1u\n#define RYU_POSE_COUNT 0u\n"
        "#define KEN_POSE_INDEX_OFF 0u\n#define RYU_POSE_INDEX_OFF 11u\n"
        "#define POSE_INDEX_RECORD_BYTES 11u\n")
    index_frame_header = (
        "#define KEN_FRAME_DATA_BANK 4u\n#define RYU_FRAME_DATA_BANK 4u\n")
    image_index = (bytes([1]) * bank + bytes([2]) * bank + bytes([3]) * bank +
                   bytes([4]) * bank + bytes(index_image))
    rom_index_ok = bytes(bank) + image_index
    fail, lines = check(rom_index_ok, image_index, 1, "", meta_multi[:bank], bank,
                        bytes([4]) * bank, index_frame_header, bytes(index_image),
                        pose_index_header)
    assert not fail, fail
    assert any("banco 5" in ln and "pose-index" in ln for ln in lines)

    rom_bad = bytearray(rom)
    rom_bad[bank + 3] ^= 0xFF  # tile bank 1
    fail, _ = check(bytes(rom_bad), image, 1, pose, meta, bank)
    assert any("banco 1" in f for f in fail), fail

    rom_meta = bytearray(rom)
    rom_meta[3 * bank] ^= 0xFF
    fail, _ = check(bytes(rom_meta), image, 1, pose, meta, bank)
    assert any("banco 3" in f for f in fail), fail

    # An uncited bank (none here between used ones) is not a pass by itself:
    # flipping image bank bytes that no pose cites must still fail the meta
    # or a cited bank, and must NOT fail when only an uncited gap changes.
    image_gap = bytearray(bytes([1]) * bank + bytes([9]) * bank + bytes([2]) * bank + meta)
    rom_gap = bytes(bank) + bytes(image_gap)  # base 1 → banks 1,2,3,4
    pose_gap = ("#define POSE_META_BANK 4u\n"
                "    { 1, 0, (const unsigned char *)0x8000u },\n"
                "    { 3, 1, (const unsigned char *)0x8000u },\n")
    fail, _ = check(rom_gap, bytes(image_gap), 1, pose_gap, meta, bank)
    assert not fail, fail
    image_gap[bank] ^= 0xFF  # bank index 1 in the image = ROM bank 2, uncited
    fail, _ = check(rom_gap, bytes(image_gap), 1, pose_gap, meta, bank)
    assert not fail, fail

    fail, _ = check(rom, image, 1, "/* vazio */\n", meta, bank)
    assert any("POSE_META_BANK" in f or "nenhuma entrada" in f for f in fail), fail

    pose_out = pose.replace("{ 2, 4,", "{ 9, 4,")
    fail, _ = check(rom, image, 1, pose_out, meta, bank)
    assert any("fora da imagem" in f or "nao alcanca" in f for f in fail), fail

    pose_off = pose.replace("{ 2, 4,", "{ 2, 40,")
    fail, _ = check(rom, image, 1, pose_off, meta, bank)
    assert any("offset" in f for f in fail), fail
    rom_index = bytearray(rom_index_ok)
    rom_index[5 * bank] ^= 0xFF
    fail, _ = check(bytes(rom_index), image_index, 1, "", meta_multi[:bank], bank,
                    bytes([4]) * bank, index_frame_header, bytes(index_image), pose_index_header)
    assert any("pose-index" in f for f in fail), fail
    print("[PASS] check_rom_binding self-check (tiles, metadata, frame-data and pose index)")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--rom", type=Path)
    ap.add_argument("--image", type=Path)
    ap.add_argument("--base-bank", type=int, default=2)
    ap.add_argument("--pose-header", type=Path)
    ap.add_argument("--meta-blob", type=Path)
    ap.add_argument("--frame-data-blob", type=Path)
    ap.add_argument("--frame-data-header", type=Path)
    ap.add_argument("--pose-index-blob", type=Path)
    ap.add_argument("--pose-index-header", type=Path)
    ap.add_argument("--bank-bytes", type=int, default=16384)
    ap.add_argument("--self-check", action="store_true")
    args = ap.parse_args()
    if args.self_check:
        self_check()
        return 0
    if not (args.rom and args.image and args.pose_header and args.meta_blob):
        ap.error("--rom, --image, --pose-header e --meta-blob sao obrigatorios")
    if bool(args.frame_data_blob) != bool(args.frame_data_header):
        ap.error("--frame-data-blob e --frame-data-header devem ser fornecidos juntos")
    if bool(args.pose_index_blob) != bool(args.pose_index_header):
        ap.error("--pose-index-blob e --pose-index-header devem ser fornecidos juntos")
    failures, lines = check(
        args.rom.read_bytes(), args.image.read_bytes(), args.base_bank,
        args.pose_header.read_text(encoding="utf-8", errors="replace"),
        args.meta_blob.read_bytes(), args.bank_bytes,
        args.frame_data_blob.read_bytes() if args.frame_data_blob else None,
        args.frame_data_header.read_text(encoding="utf-8", errors="replace")
        if args.frame_data_header else None,
        args.pose_index_blob.read_bytes() if args.pose_index_blob else None,
        args.pose_index_header.read_text(encoding="utf-8", errors="replace")
        if args.pose_index_header else None)
    for ln in lines:
        print(f"[ROM] {ln}")
    if failures:
        for f in failures:
            print(f"[FAIL] {f}")
        return 1
    print("[PASS] banco meta e bancos de tiles citados coincidem com a ROM")
    return 0


if __name__ == "__main__":
    sys.exit(main())
