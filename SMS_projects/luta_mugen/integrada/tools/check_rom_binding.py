#!/usr/bin/env python3
"""Bind the ROM banks the integrated runtime actually reads.

Bank 37 must equal the generated pose-meta blob (a stale bank made the
pool upload garbage). Every tile bank cited by pose_table.h must equal
the same slice of the concatenated bank image. Banks the pose table does
not cite are not treated as proof.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ENTRY_RE = re.compile(r"\{\s*(\d+)\s*,\s*(\d+)\s*,")
META_RE = re.compile(r"#define\s+POSE_META_BANK\s+(\d+)u?")


class BindError(Exception):
    pass


def pose_uses(text: str) -> tuple[int, dict[int, list[int]]]:
    meta_m = META_RE.search(text)
    if not meta_m:
        raise BindError("POSE_META_BANK ausente no header de poses")
    entries = [(int(b), int(off)) for b, off in ENTRY_RE.findall(text)]
    if not entries:
        raise BindError("nenhuma entrada de pose no header")
    by_bank: dict[int, list[int]] = {}
    for bank, off in entries:
        by_bank.setdefault(bank, []).append(off)
    return int(meta_m.group(1)), by_bank


def check(rom: bytes, image: bytes, base_bank: int, pose_text: str,
          meta_blob: bytes, bank_bytes: int = 16384) -> tuple[list[str], list[str]]:
    failures: list[str] = []
    lines: list[str] = []
    try:
        meta_bank, by_bank = pose_uses(pose_text)
    except BindError as exc:
        return [str(exc)], []
    if len(meta_blob) != bank_bytes:
        failures.append(f"blob meta tem {len(meta_blob)} B, banco tem {bank_bytes}")
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

    meta_rom = rom_bank(meta_bank)
    if meta_rom is not None and meta_rom != meta_blob:
        failures.append(f"banco {meta_bank} da ROM diverge de pose_meta blob")
    elif meta_rom is not None:
        lines.append(f"banco {meta_bank} da ROM == blob meta ({bank_bytes} B)")
    meta_img = image_bank(meta_bank)
    if meta_img is not None and meta_blob and meta_img != meta_blob:
        failures.append(f"imagem no banco {meta_bank} diverge do blob meta")

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
    print("[PASS] check_rom_binding self-check")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--rom", type=Path)
    ap.add_argument("--image", type=Path)
    ap.add_argument("--base-bank", type=int, default=2)
    ap.add_argument("--pose-header", type=Path)
    ap.add_argument("--meta-blob", type=Path)
    ap.add_argument("--bank-bytes", type=int, default=16384)
    ap.add_argument("--self-check", action="store_true")
    args = ap.parse_args()
    if args.self_check:
        self_check()
        return 0
    if not (args.rom and args.image and args.pose_header and args.meta_blob):
        ap.error("--rom, --image, --pose-header e --meta-blob sao obrigatorios")
    failures, lines = check(
        args.rom.read_bytes(), args.image.read_bytes(), args.base_bank,
        args.pose_header.read_text(encoding="utf-8", errors="replace"),
        args.meta_blob.read_bytes(), args.bank_bytes)
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
