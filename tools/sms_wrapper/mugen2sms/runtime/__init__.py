"""Modelos de runtime do mugen2sms (Lote B): espelhos da politica da ROM.

O runtime autoritativo e' a ROM de `SMS_projects/<projeto>/src/main.c`; estes
modulos pre-validam decisoes de VRAM e de fila de commit em fixtures/eventos,
cada um com --self-check proprio (regra §19: sem self-check nao e fonte).
Extensao registrada de verdade: descoberta em `mugen2sms/__main__.py`
(`runtime-vram-plan`, `runtime-commit-budget`) e no gate de doutrina de
`validate_measurement_tools.DOCTRINE_ALWAYS` — nao e codigo orfao.
"""
