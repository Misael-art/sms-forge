#!/usr/bin/env bash
# ensure_toolchain.sh — instalação ROOTLESS das dependências do SMSForge.
#
# Instala (sem precisar de root):
#   1. SDCC >= 4.2   -> sdk/sdcc-portable/  (pacote Arch extraível; fallback: fonte)
#   2. devkitSMS     -> sdk/devkitSMS/      (clone raso: headers, .lib, crt0)
#   3. makesms       -> sdk/devkitSMS/tools/ (compilado com cc; fallback binário do repo)
#
# Idempotente: roda quantas vezes quiser. Verificação final compila/linka/rom
# um smoke-test REAL antes de declarar OK.
#
# Windows: roadmap (paridade com ensure_*.ps1 do SGDKForge). Hoje o fluxo
# canônico Windows é manual via sdk/README.md.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SDK="$HERE/../../sdk"
UPSTREAM="$SDK/devkitSMS-upstream"
CANON="$SDK/devkitSMS"
PORTABLE="$SDK/sdcc-portable"

say()  { printf '%s\n' "$*"; }
ok()   { printf '[OK] %s\n' "$*"; }
skip() { printf '[SKIP] %s\n' "$*"; }
die()  { printf '[FAIL_AMBIENTE] %s\n' "$*" >&2; exit 2; }

SDCC_BIN=""

need_sdcc() {
  if command -v sdcc >/dev/null 2>&1; then
    v="$(sdcc --version | head -1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)"
    major="${v%%.*}"
    [ "${major:-0}" -ge 4 ] || die "sdcc do sistema é $v (<4.2); remova ou instale portátil"
    SDCC_BIN="$(command -v sdcc)"
    ok "sdcc do sistema: $v ($SDCC_BIN)"
    return
  fi
  if [ -x "$PORTABLE/bin/sdcc" ]; then
    SDCC_BIN="$PORTABLE/bin/sdcc"
    ok "sdcc portátil já presente: $("$SDCC_BIN" --version | head -1)"
    return
  fi
  # baixar e extrair pacote Arch (rootless) — funciona em qualquer x86_64 Linux atual
  say "[..] SDCC ausente; extraindo pacote Arch localmente em $PORTABLE (sem root)"
  meta="$(curl -fsSL https://archlinux.org/packages/extra/x86_64/sdcc/json/)"
  fn="$(printf '%s' "$meta" | python3 -c 'import json,sys;print(json.load(sys.stdin)["filename"])')"
  url="https://geo.mirror.pkgbuild.com/extra/os/x86_64/$fn"
  tmp="$(mktemp -d /tmp/smsforge_sdcc.XXXXXX)"
  trap 'rm -rf "$tmp"' EXIT
  curl -fSL --retry 3 -o "$tmp/$fn" "$url" || die "download falhou: $url"
  mkdir -p "$tmp/x" "$PORTABLE"
  bsdtar -xf "$tmp/$fn" -C "$tmp/x" || die "extração falhou (bsdtar/zstd ausentes?)"
  # pacote traz usr/bin, usr/share -> colapsa usr/
  cp -r "$tmp/x/usr/." "$PORTABLE/"
  [ -x "$PORTABLE/bin/sdcc" ] || die "sdcc não apareceu pós-extração"
  SDCC_BIN="$PORTABLE/bin/sdcc"
  ok "sdcc instalado: $("$SDCC_BIN" --version | head -1)"
}

need_devkitsms() {
  if [ -f "$CANON/SMSlib/SMSlib.lib" ] && [ -f "$CANON/crt0/crt0_sms.rel" ]; then
    skip "devkitSMS canônico já presente em $CANON"
  else
    say "[..] clonando devkitSMS (shallow)"
    rm -rf "$UPSTREAM"
    git clone --depth 1 https://github.com/sverx/devkitSMS "$UPSTREAM" \
      || die "git clone devkitSMS falhou (rede?)"
    mkdir -p "$CANON/SMSlib" "$CANON/PSGlib" "$CANON/crt0" "$CANON/tools"
    cp "$UPSTREAM/SMSlib/src/SMSlib.h" "$CANON/SMSlib/"
    cp "$UPSTREAM/PSGlib/src/PSGlib.h" "$CANON/PSGlib/"
    cp "$UPSTREAM/crt0/crt0_sms.rel" "$CANON/crt0/"
    [ -f "$UPSTREAM/peep-rules.txt" ] && cp "$UPSTREAM/peep-rules.txt" "$CANON/" || true
    ok "headers/crt0 copiados para $CANON"
  fi
  if [ ! -d "$UPSTREAM/SMSlib/src" ]; then
    say "[..] upstream ausente p/ rebuild de libs; clonando"
    git clone --depth 1 https://github.com/sverx/devkitSMS "$UPSTREAM" \
      || die "re-clone falhou"
  fi
  need_libs
  need_makesms
}

need_libs() {
  # LIÇÃO 2026-08-25: as .lib pré-compiladas do repo foram geradas com SDCC antigo
  # e conflitam de convenção de chamada (sdcccall) com SDCC >= 4.2+.
  # Reconstruir SEMPRE do fonte com o sdcc local — ABI garantido igual.
  say "[..] reconstruindo SMSlib/PSGlib do fonte (ABI igual ao sdcc local)"
  export PATH="$(dirname "$SDCC_BIN"):$PATH"
  ( cd "$UPSTREAM/SMSlib/src" && make >/dev/null ) || die "make SMSlib falhou"
  ( cd "$UPSTREAM/PSGlib/src" && make >/dev/null ) || die "make PSGlib falhou"
  cp -f "$UPSTREAM/SMSlib/src/SMSlib.lib" "$CANON/SMSlib/SMSlib.lib"
  cp -f "$UPSTREAM/PSGlib/src/PSGlib.lib" "$CANON/PSGlib/PSGlib.lib"
  ok "libs reconstruídas e publicadas em $CANON"
}

need_makesms() {
  if [ -x "$CANON/tools/makesms" ] && "$CANON/tools/makesms" 2>&1 | head -1 >/dev/null; then
    skip "makesms já instalado"
    return
  fi
  src="$UPSTREAM/makesms/src/makesms.c"
  [ -f "$src" ] || { rm -rf "$UPSTREAM"; git clone --depth 1 \
      https://github.com/sverx/devkitSMS "$UPSTREAM" \
      || die "re-clone falhou"; }
  if command -v cc >/dev/null 2>&1 && [ -f "$src" ]; then
    cc -O2 -o "$CANON/tools/makesms" "$src" \
      || die "compilação do makesms falhou"
    ok "makesms compilado de $src"
  else
    cp "$UPSTREAM/makesms/Linux/makesms" "$CANON/tools/makesms"
    chmod +x "$CANON/tools/makesms"
    ok "makesms binário pré-compilado (repo)"
  fi
}

verify_smoke() {
  say "[..] verificação: compilando smoke-test REAL (crt0 + SMSlib + PSGlib + makesms)"
  t="$(mktemp -d /tmp/smsforge_smoke.XXXXXX)"
  cat > "$t/main.c" <<'EOF'
#include "SMSlib.h"
void main (void) {
    SMS_init();
    SMS_displayOn();
    for (;;) { SMS_waitForVBlank(); }
}
EOF
  ( cd "$t" && \
    "$SDCC_BIN" -c -mz80 main.c -I"$CANON/SMSlib" -I"$CANON/PSGlib" \
      && "$SDCC_BIN" -o smoke.ihx -mz80 --no-std-crt0 --data-loc 0xC000 \
         "$CANON/crt0/crt0_sms.rel" main.rel "$CANON/SMSlib/SMSlib.lib" \
         "$CANON/PSGlib/PSGlib.lib" \
      && "$CANON/tools/makesms" smoke.ihx smoke.sms ) \
      || die "smoke-test falhou — toolchain incompleto"
  sz=$(stat -c%s "$t/smoke.sms")
  [ "$sz" -gt 0 ] && [ $((sz % 16384)) -eq 0 ] || die "ROM smoke com tamanho inválido: $sz"
  hdr=$(dd if="$t/smoke.sms" bs=1 skip=32752 count=8 2>/dev/null || true)
  rm -rf "$t"
  ok "smoke ROM gerada (${sz}B); header 0x7FF0 = '$hdr'"
  case "$hdr" in
    TMR\ SEGA*) ok "header SEGA confirmado" ;;
    *) printf '[WARN] header 0x7FF0 sem assinatura TMR SEGA (%s)\n' "$hdr" ;;
  esac
}

write_env() {
  cat > "$SDK/env.sh" <<EOF
# source este arquivo ou deixe o wrapper autodetectar
export PATH="$PORTABLE/bin:\$PATH"
export SMS_DEVKITSMS="$CANON"
EOF
  ok "ambiente escrito em $SDK/env.sh"
}

say "== SMSForge :: instalação de toolchain (rootless) =="
need_sdcc
need_devkitsms
verify_smoke
write_env
say "== RESULTADO: toolchain completo e PROVADO por smoke-test =="
