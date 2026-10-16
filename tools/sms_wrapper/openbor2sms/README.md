# openbor2sms — engine OpenBOR → Sega Master System

Motor reutilizável (host + runtime) que converte módulos OpenBOR (PAK) em dados
e runtime para o Sega Master System. O consumidor atual é
`SMS_projects/openbor_sms_rev1/` (pilotos GAL e Battletoads). Este diretório é
**infraestrutura do wrapper** (`tools/sms_wrapper/`), não um projeto: nenhuma
lógica de build de jogo vive aqui além do pipeline de importação/geração.

Status: **O1 (front-end neutro)** — leitor PAK, intake e front-end neutro
(extração hash-bound + IR tipado com origem) com `--self-check`. A emissão SMS
é um backend separado (O2).

## Fronteira (contrato de arquitetura)

```
PAK → dependências resolvidas → IR tipado → perfil de compatibilidade
    → dados ROM/bancos → runtime C/Z80 → ROM observada
```

- **Front-end (neutro, host):** leitura de PAK, texto de modelo/level, IR
  tipado com origem (caminho, linha, bytes/hash, unidade). Sem decisões de
  console: nenhum `SPR_*`, DMA, H40, WINDOW/BG_A/BG_B, 4 paletas ou budget MD.
- **Backend MD (doador, NÃO portado como SMS):** `semantics.py` (contratos
  inteiros/budgets MD do doador: pool 1424, VRAM 1408, célula 80, tela 320),
  `emit_slice.py`, `images.py`, `streaming.py` e `profiles.py` misturam
  decisões Mega Drive. Ficam como referência de origem/cache/ownership/testes;
  a emissão SMS é separada.
- **Runtime SMS:** C/Z80 com pools estáticos, sob as leis do SMS_GLOBAL
  (8 KiB RAM, 16 KiB VRAM, SAT64, 8 sprites/scanline, 2×16 paletas, sem DMA,
  sem float/malloc em runtime quente — SDCC).

`@script` armazenado como texto **não** é implementação: scripts desconhecidos
bloqueiam (nunca viram noop silencioso).

## Proveniência

Todo módulo portado do doador SGDK Forge
(`/mnt/sdcard/Projects/Sgdk Forge/tools/openbor2sgdk_forge/`) carrega um banner
com caminho relativo do doador, SHA-256 do arquivo doador e licença. O doador é
**read-only**: os hashes são revalidados antes de qualquer porte/leitura
(ver `data/generated/intake/donor_source_manifest_*.json` do consumidor).

- Doador MIT (SGDK-Forge `LICENSE`), OpenBOR BSD-3-Clause (pin
  `787b6770409935137579715febf80cf7a529b748`, referência semântica condicional).
- Assets de PAK: **não publicáveis**. Licença do importador não licencia
  personagens/asset redistribuição.

## Layout

```
openbor2sms/
  openbor2sms/
    __init__.py
    __main__.py     # python3 -m openbor2sms
    pak.py          # leitor PAK32/PAK64 (porte fiel do doador, sha no banner)
    intake.py       # verificação/registro de fontes: pak | sources | deps
    frontend.py     # O1: extract (hash-bound) + ir (level | models_index)
    model_text.py            # porte fiel O1 (banner com sha do doador)
    level_inventory.py       # porte fiel O1
    analyze.py               # porte fiel O1 (projeção event_ir, análise)
    reference_semantics.py   # porte fiel O1
    level_event_table.py     # porte fiel O1
  tests/            # unittest (fixtures sintéticas, sem conteúdo de módulo)
  README.md
```

## Uso

```sh
# rodar do diretório do engine (a pasta tools/sms_wrapper/openbor2sms
# sombrearia o pacote se invocado a partir de tools/sms_wrapper)
cd tools/sms_wrapper/openbor2sms
# intake de um PAK: hash + índice + histogramas (fonte explícita, sem paths implícitos)
python3 -m openbor2sms pak --path <GAL.pak> --expect-sha256 <hex> --expect-bytes <N> --out <record.json>
# manifest de identidade de fontes (docs do doador, licenses, árvore .py)
python3 -m openbor2sms sources --file <f>... --dir <d>... --tree <dir> --out <manifest.json>
# porta a matriz de dependências do doador para registro local hash-bound
python3 -m openbor2sms deps --contract <c.json> --matrix <m.json> --source-manifest <s.json> --out <inventory.json>
# extração hash-bound de membros do PAK (identidade verificada; fail-closed)
python3 -m openbor2sms extract --pak <PAK> --expect-sha256 <hex> --expect-bytes <N> \
    --member data/levels/town1.txt --member data/models.txt --destination data/source_openbor/gal_town1 --out <record.json>
# IR tipado com origem (linha/byte span/hash da linha bruta); --generated-at fixa o determinismo
python3 -m openbor2sms ir --kind level --source data/source_openbor/gal_town1/data/levels/town1.txt \
    --member data/levels/town1.txt --source-sha256 <hex> --pak-sha256 <hex> --out <ir.json>
python3 -m openbor2sms ir --kind models_index --source data/source_openbor/gal_town1/data/models.txt \
    --member data/models.txt --source-sha256 <hex> --out <ir.json>
# checagens sintéticas
python3 -m openbor2sms --self-check
```

Testes: `cd tools/sms_wrapper/openbor2sms && python3 -m unittest discover -s tests -v`

## Regras de dados (consumidor)

- `data/source_openbor/` — fontes OpenBOR sob controle explícito (recortes
  extraídos; o PAK completo não é copiado nem vira recurso `res/`).
- `data/generated/` — intermediários gerados pelo host (intake, IR, transcripts)
  **nunca** `res/`.
- Ambas registradas no `doc/artifact_registry.json` do consumidor antes de
  qualquer escrita; todo arquivo em location managed é registrado com SHA-256.

## Estados de feature (vocabulário do plano)

Toda feature tem estado `exact`, `adapted`, `blocked` ou `dropped_by_owner`,
com parser, lowering, consumidor, teste e prova por hash. Separar sempre
`parsed ≠ generated ≠ consumed ≠ observed ≠ budget_validated`.

## Lotes

O0 intake → **O1 front-end neutro (concluído: PAK/model/level IR + diffs +
casos inválidos; emissão MD separada, `semantics.py` na fronteira de emissão)** →
O2 piloto VDP → O3 combate → O4 mundo/eventos → O5 objetos/escala → O6 fluxo →
O7 segundo piloto/2P → O8 maturidade.
Plano: `doc/planejamento/openbor_sms/01-plano-openbor-sms.md`.
