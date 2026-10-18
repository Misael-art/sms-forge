#!/usr/bin/env bash
# clean.sh — delega ao wrapper (padrao: apaga out/, preserva changelog/)
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
rm -rf "$DIR/out"
mkdir -p "$DIR/out"
echo "[CLEAN OK] $DIR/out"
