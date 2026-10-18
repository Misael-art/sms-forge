#!/usr/bin/env python3
"""gen_banks.py — gera assets/banks/banks_2_7.bin (deterministico).

- Banco 2 (destino do merge): bloco alvo da copia — byte 0 = 'M', resto
  padrao p(i) = (7*i + 3) & 0xFF por 1856 B.
- Banco 3: byte 0 = 'P' (prova de troca de banco via SMS_mapROMBank).
- Bancos 4..7: 0x00 (reserva que faz a ROM chegar a 128 KB num unico -mbank,
  limite de 8 merges do makesms — L084).
"""
import hashlib
import json
import sys
from pathlib import Path

BANK = 16384
BANKS = 6
COPY_BYTES = 1856
HERE = Path(__file__).resolve().parent
OUT = HERE / "assets" / "banks" / "banks_2_7.bin"


def main():
    data = bytearray(BANKS * BANK)
    b2 = memoryview(data)[0:BANK]
    for i in range(COPY_BYTES):
        b2[i] = (7 * i + 3) & 0xFF
    b2[0] = ord("M")
    b3 = memoryview(data)[BANK:2 * BANK]
    b3[0] = ord("P")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes(bytes(data))
    print(json.dumps({"path": str(OUT), "bytes": len(data),
                      "sha256": hashlib.sha256(data).hexdigest()}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
