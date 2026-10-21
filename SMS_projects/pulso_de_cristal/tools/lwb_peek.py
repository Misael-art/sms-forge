#!/usr/bin/env python3
"""lwb_peek.py — leitura ad-hoc do bloco de perfil por fase da ROM pulso.

Molde idêntico ao measure_worst_frame.py (L082): Emulicious privado com
-remotedebug, NENHUMA conexão DAP durante a janela de 3000 frames, conexão
única depois do selo done=1. Não reinterpreta: devolve os bytes crus dos
endereços que main.c declara, para atribuição da causa do derrame.

Uso: python3 tools/lwb_peek.py [--wait 100]
"""
import os
import subprocess
import sys
import time
import shutil

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "sms_wrapper"))

import capture_evidence as CE                       # noqa: E402
import measure_runtime_probe as MRP                 # noqa: E402
import measure_worst_frame as MWF                   # noqa: E402
from emulicious_dap import PORT, EmuliciousDap      # noqa: E402

PROJ = os.path.join(ROOT, "SMS_projects", "pulso_de_cristal")
ROM = os.path.join(PROJ, "out", "rom", "pulso_de_cristal.sms")
SRC = os.path.join(PROJ, "src")

# O corredor lido é o corredor DECLARADO (dono: measure_worst_frame
# .declared_probes), nunca uma tabela copiada — L089.
ADDRS = MWF.declared_probes(SRC)


def main():
    if not ADDRS:
        print("[FAIL_CONTRATO] nenhum __at() lido em %s" % SRC); return 3
    wait_s = 100.0
    if "--wait" in sys.argv:
        wait_s = float(sys.argv[sys.argv.index("--wait") + 1])
    if not shutil.which("java"):
        print("[FAIL_AMBIENTE] java ausente"); return 2
    jar = CE.resolve_jar()
    if not jar:
        print("[FAIL_AMBIENTE] Emulicious.jar ausente"); return 2
    if not MRP._zombie_guard() or not MRP._port_free():
        print("[FAIL_AMBIENTE] porta DAP ocupada ou zumbi"); return 2
    log = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "lwb_peek_emu.log"), "w")
    proc = subprocess.Popen(
        ["java", "-jar", jar, "-remotedebug", str(PORT), ROM],
        stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    try:
        print("[peek] %.0f s sem DAP ate o selo" % wait_s)
        time.sleep(wait_s)
        dap = MRP._connect_live()
        if dap is None:
            print("[FAIL] DAP nao ficou vivo"); return 1
        try:
            by_name = {n: (a, w) for n, a, w in ADDRS}
            frame = dap.read_word(by_name["probe_frame"][0])
            done = dap.read_byte(by_name["probe_worst_done"][0])
            vovf = dap.read_word(by_name["probe_vovf"][0])
            lo = min(a for _, a, _ in ADDRS)
            hi = max(a + w - 1 for _, a, w in ADDRS)
            print("[peek] corredor %04X..%04X (%d bytes) frame=%d done=%d "
                  "vovf=%d" % (lo, hi, len(ADDRS), frame, done, vovf))
            for nome, addr, width in ADDRS:
                if nome in ("probe_frame", "probe_vovf"):
                    continue                    # já impressos no resumo
                val = (dap.read_word(addr) if width == 2
                       else dap.read_byte(addr))
                print("  %-20s @%04X = %d" % (nome, addr, val))
        finally:
            dap.close()
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
        log.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
