"""Emite o header de arte do personagem SINTETICO dos testes (mini) — fixture
committavel para as cenas do runtime sem tocar em arte real (politica do GDD:
Ken nunca entra no git). Deterministico: mesma saida byte a byte em qualquer maquina.

Uso (de tools/sms_wrapper):
  python3 -m mugen2sms.generators.emit_synth > ../../SMS_projects/luta_mugen/inc/gen/mini_art.h
  python3 -m mugen2sms.generators.emit_synth --banked --bin ../../SMS_projects/luta_mugen/data/mini_bank2.bin \
      > ../../SMS_projects/luta_mugen/inc/gen/mini_art.h

--banked: os blobs _TILES viram defines _BANK/_OFF/_SIZE (pagina de 16 KB do slot
2 do Sega mapper) e o banco e escrito em --bin; o resto (META/METAL/PAL/AXIS/
CLSN/CMD, ~3% dos bytes) permanece inline. Sem --banked o header e o formato
antigo com arrays inline (usado pelos testes que comparam bytes).
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--banked", action="store_true", help="TILES em {slug}_bank2.bin, header com _BANK/_OFF")
    ap.add_argument("--bin", type=Path, default=None, help="destino do banco de tiles (exigido com --banked)")
    args = ap.parse_args(argv)
    if args.banked != (args.bin is not None):
        ap.error("--banked exige --bin (e --bin so faz sentido com --banked)")
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from mugen2sms import character as CH
    from mugen2sms.source import Source
    from mugen2sms.analysis.fidelity import classify_character
    from mugen2sms.analysis.sms_budget import SmsLimits
    from mugen2sms.generators import smsdev
    from mugen2sms.tests.make_fixtures import build

    with tempfile.TemporaryDirectory() as td:
        ch = CH.load(Source(build(Path(td) / "minichar")))
    fid = classify_character(ch, SmsLimits())
    with tempfile.TemporaryDirectory() as out:
        man = smsdev.generate(ch, fid, Path(out), banked=args.banked)
        hdr = Path(out, "mini_art.h").read_text(encoding="ascii")
        if args.banked:
            args.bin.parent.mkdir(parents=True, exist_ok=True)
            args.bin.write_bytes(Path(out, "mini_bank2.bin").read_bytes())
    sys.stdout.write(hdr)
    print(f"/* fixture sintetico: {man.stats} — gerado por emit_synth, nao editar */",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
