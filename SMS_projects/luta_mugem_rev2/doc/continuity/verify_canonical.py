#!/usr/bin/env python3
"""Compare a rebuilt luta_mugem_rev2 ROM with the canonical production ROM.

The only accepted differences are the SDSC timestamp fields written by
makesms at build time and the SEGA checksum that depends on them.  If the
payload is byte-identical, the script restores the canonical timestamp and
recomputes the checksum over [0x0000, 0x7FF0), then checks the canonical
SHA-256.  This proves reproducibility of the code/data payload without
pretending that a wall-clock timestamp is reproducible.

Usage:
  python3 verify_canonical.py \
      --built out/rom/luta_mugem_rev2.sms \
      --canonical doc/continuity/assets/luta_mugem_rev2_canonical_087df676.sms

Exit codes: 0 = identical or canonicalizable; 1 = divergent.
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

DATE_START = 0x7FE4
DATE_END = 0x7FE8
CHECKSUM_START = 0x7FFA
CHECKSUM_END = 0x7FFC
CHECKSUM_SUM_END = 0x7FF0
EXPECTED_CANONICAL = "087df67677626bfcd61188cb5ff0a5c054eb4feb24c420434fcfbeebf5fa7a65"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--built", required=True, type=Path)
    parser.add_argument("--canonical", required=True, type=Path)
    parser.add_argument(
        "--expect-sha",
        default=EXPECTED_CANONICAL,
        help="expected canonical SHA-256 (pass empty string to skip)",
    )
    args = parser.parse_args()

    built = args.built.read_bytes()
    canon = args.canonical.read_bytes()
    built_sha = sha256(built)
    canon_sha = sha256(canon)

    print(f"built     : {args.built}")
    print(f"built_sha : {built_sha}")
    print(f"canonical : {args.canonical}")
    print(f"canon_sha : {canon_sha}")

    if args.expect_sha and canon_sha != args.expect_sha:
        print(f"FAIL canonical asset SHA is not {args.expect_sha}", file=sys.stderr)
        return 1
    if len(built) != len(canon):
        print(f"FAIL size {len(built)} != canonical {len(canon)}", file=sys.stderr)
        return 1
    if built_sha == canon_sha:
        print("PASS identical: rebuilt ROM is byte-for-byte canonical")
        return 0

    diffs = [i for i, (a, b) in enumerate(zip(built, canon)) if a != b]
    allowed = [
        i
        for i in diffs
        if DATE_START <= i < DATE_END or CHECKSUM_START <= i < CHECKSUM_END
    ]
    outside = [i for i in diffs if i not in allowed]
    print(f"diffs     : {len(diffs)}")
    print("diff_offsets: " + " ".join(f"0x{i:05X}" for i in diffs[:32]))
    if outside:
        print(
            "FAIL payload diverges outside SDSC timestamp/checksum: "
            + " ".join(f"0x{i:05X}" for i in outside[:32]),
            file=sys.stderr,
        )
        return 1

    canonical_checksum = int.from_bytes(canon[CHECKSUM_START:CHECKSUM_END], "little")
    recomputed = sum(canon[:CHECKSUM_SUM_END]) & 0xFFFF
    if canonical_checksum != recomputed:
        print(
            f"WARN canonical stored checksum 0x{canonical_checksum:04X} "
            f"!= recomputed 0x{recomputed:04X}; refusing to call this canonical",
            file=sys.stderr,
        )
        return 1

    normalized = bytearray(built)
    normalized[DATE_START:DATE_END] = canon[DATE_START:DATE_END]
    normalized_checksum = sum(normalized[:CHECKSUM_SUM_END]) & 0xFFFF
    normalized[CHECKSUM_START:CHECKSUM_END] = normalized_checksum.to_bytes(2, "little")
    normalized_sha = sha256(bytes(normalized))
    print(f"canonicalized_sha: {normalized_sha}")
    if normalized_sha != canon_sha:
        print(
            "FAIL payload differs from canonical even after timestamp/checksum "
            "normalization",
            file=sys.stderr,
        )
        return 1

    print(
        "PASS canonicalizable: payload identical; only SDSC timestamp/SEGA "
        "checksum differed and were restored"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
