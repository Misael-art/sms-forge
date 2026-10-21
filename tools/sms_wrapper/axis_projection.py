#!/usr/bin/env python3
"""axis_projection.py — CLI durável da projeção de eixos OpenBOR→SMS.

O código vive no pacote `openbor2sms` (importável e testável); este wrapper é o
ponto de entrada estável em `tools/sms_wrapper/` para o build/release e para os
gates que exigem `--self-check`.

A projeção NÃO é medição nova. Ela copia bundle consumidor + MRP3 + QA para
`out/evidence/evidence.json`/`fps.json` somente depois de provar que todas as
fontes citam o mesmo `rom_sha256` da ROM atual (`--current-rom`). Fonte de outro
binário ou sem SHA é recusada antes de escrever. Ver `SMS_GLOBAL §130` (L138).
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "openbor2sms"))

from openbor2sms.axis_projection import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
