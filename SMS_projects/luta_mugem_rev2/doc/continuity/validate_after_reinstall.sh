#!/usr/bin/env bash
# Validate a fresh clone/reinstall of luta_mugem_rev2 without touching the
# tracked project or its canonical ROM.
#
# What it proves:
#   1. the canonical production source + generated banks rebuild to the
#      canonical payload (only the SDSC date byte and SEGA checksum differ);
#   2. the v043 candidate source rebuilds to the v043 payload;
#   3. the build gates that do not need an emulator pass.
#
# What it does NOT prove: boot, gameplay, 60/50 fps, audio, render fidelity or
# delivery.  The final iron rule still applies: if it was not seen running in
# the emulator, it does not exist.
#
# Usage:
#   bash SMS_projects/luta_mugem_rev2/doc/continuity/validate_after_reinstall.sh
#   bash .../validate_after_reinstall.sh --prod-only
#
# Prerequisites:
#   - sdk/sdcc-portable/bin/sdcc (extract sdk_20261021.tar.zst at repo root or
#     run tools/sms_wrapper/ensure_toolchain.sh);
#   - Python 3;
#   - the generated tarball tracked in doc/continuity/assets/ (no emulator).
set -euo pipefail

PROD_ONLY=0
if [ "${1:-}" = "--prod-only" ]; then
    PROD_ONLY=1
elif [ $# -gt 0 ]; then
    echo "usage: $0 [--prod-only]" >&2
    exit 2
fi

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [ -z "$ROOT" ]; then
    echo "FAIL: run this inside the sms-forge git clone" >&2
    exit 2
fi
PROJ="$ROOT/SMS_projects/luta_mugem_rev2"
ASSETS="$PROJ/doc/continuity/assets"
VERIFY="$PROJ/doc/continuity/verify_canonical.py"
SDK="$ROOT/sdk/sdcc-portable/bin/sdcc"

EXPECTED_SRC="042ba22e4a0763daaa4e402b90a0a5d0d40a7b5923c17575ed012b6a89773bfe"
EXPECTED_V043_SRC="eb5576ad73e5e79b3ec94a217e13b57faf38a264631ba65aaec3f7642a54cb59"
EXPECTED_GENERATED="aa6ea4ef769fee0d9f36088848a198c7c217da6f0057f58c0344e2249f5d8915"
EXPECTED_CANONICAL="087df67677626bfcd61188cb5ff0a5c054eb4feb24c420434fcfbeebf5fa7a65"
EXPECTED_V043="13b78bd2435673df089ed69302522d332c9418ea74331aeff95065c85e3920c7"

fail() { echo "FAIL: $*" >&2; exit 1; }

[ -d "$PROJ" ] || fail "project directory not found: $PROJ"
[ -f "$VERIFY" ] || fail "verify_canonical.py not found"
[ -f "$ASSETS/ryu_ken_cross_generated_20261021.tar.gz" ] || fail "generated tarball not found"
[ -x "$SDK" ] || fail "SDK not found at $SDK; extract sdk_20261021.tar.zst at the repo root or run tools/sms_wrapper/ensure_toolchain.sh"

SRC_SHA="$(sha256sum "$PROJ/src/main.c" | cut -d' ' -f1)"
[ "$SRC_SHA" = "$EXPECTED_SRC" ] || fail "src/main.c is $SRC_SHA, expected canonical $EXPECTED_SRC"
GEN_SHA="$(sha256sum "$ASSETS/ryu_ken_cross_generated_20261021.tar.gz" | cut -d' ' -f1)"
[ "$GEN_SHA" = "$EXPECTED_GENERATED" ] || fail "generated tarball is $GEN_SHA, expected $EXPECTED_GENERATED"

if [ ! -x "$PROJ/doc/continuity/repro/main.c.rowquota_v043" ] && [ ! -f "$PROJ/doc/continuity/repro/main.c.rowquota_v043" ]; then
    fail "v043 source not found"
fi
V043_SHA="$(sha256sum "$PROJ/doc/continuity/repro/main.c.rowquota_v043" | cut -d' ' -f1)"
[ "$V043_SHA" = "$EXPECTED_V043_SRC" ] || fail "v043 source is $V043_SHA, expected $EXPECTED_V043_SRC"

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
TMP="$(mktemp -d "$ROOT/SMS_projects/_continuity_validate.XXXXXX")"
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT

echo "== luta_mugem_rev2 continuity validation =="
echo "repo      : $ROOT"
echo "commit    : $(git -C "$ROOT" rev-parse --short HEAD 2>/dev/null || echo unknown)"
echo "branch    : $(git -C "$ROOT" rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)"
echo "source    : $SRC_SHA"
echo "sdk       : $SDK"
echo "temp      : $TMP"
echo

cp -a "$PROJ/src" "$PROJ/inc" "$PROJ/.mddev" "$PROJ/build.sh" "$PROJ/run.sh" "$PROJ/README.md" "$TMP"/
mkdir -p "$TMP/out" "$TMP/res"
tar -xzf "$ASSETS/ryu_ken_cross_generated_20261021.tar.gz" -C "$TMP"

PROD_LOG="$PROJ/doc/continuity/post_reinstall_${STAMP}_prod.log"
V043_LOG="$PROJ/doc/continuity/post_reinstall_${STAMP}_v043.log"

echo "== production rebuild =="
( cd "$TMP" && bash build.sh ) 2>&1 | tee "$PROD_LOG"
PROD_ROM="$TMP/out/rom/luta_mugem_rev2.sms"
[ -f "$PROD_ROM" ] || fail "production ROM not produced"
echo "production built sha: $(sha256sum "$PROD_ROM" | cut -d' ' -f1)"
python3 "$VERIFY" --built "$PROD_ROM" --canonical "$ASSETS/luta_mugem_rev2_canonical_087df676.sms" --expect-sha "$EXPECTED_CANONICAL"
echo

if [ "$PROD_ONLY" -eq 1 ]; then
    echo "PASS build-only (production); emulator/gameplay/fps/audio NOT tested"
    exit 0
fi

echo "== v043 candidate rebuild =="
cp "$PROJ/doc/continuity/repro/main.c.rowquota_v043" "$TMP/src/main.c"
( cd "$TMP" && bash build.sh ) 2>&1 | tee "$V043_LOG"
V043_ROM="$TMP/out/rom/luta_mugem_rev2.sms"
[ -f "$V043_ROM" ] || fail "v043 ROM not produced"
echo "v043 built sha: $(sha256sum "$V043_ROM" | cut -d' ' -f1)"
python3 "$VERIFY" --built "$V043_ROM" --canonical "$ASSETS/candidate_v043_13b78bd2435673df.sms" --expect-sha "$EXPECTED_V043"
echo

echo "PASS build-only (production + v043); emulator/gameplay/fps/audio NOT tested"
echo "Logs: $PROD_LOG"
echo "      $V043_LOG"
echo
echo "Next, with the release emulator assets extracted and a private display:"
echo "  tools/sms_wrapper/emulator_session.py ...   # read the runbook before starting"
echo "  SMS_projects/luta_mugem_rev2/run.sh"
echo "Do not declare delivery: boot/gameplay/fps/audio/render axes are still unproven here."
