# Receita — Produção de assets: PNG → tiles → ROM selada (L076)

Skill-receita do SMSForge. Molde vivo: **MSSF2T** (15 vínculos
asset→símbolo) e **kage_matsuri** (12 vínculos) — os dois com binding
re-hasheado e `--require` PASS em 2026-09-25. É o caminho que separa
"tenho um PNG" de "este pixel está nesta ROM, com SHA que o prova".

Detalha o fluxo das skills `sms-pixel-translate.md`, `sms-vdp-tiles.md`,
`sms-asset-pipeline.md` e `sms-asset-to-rom.md` (L121); os gates são os
canônicos do AGENTS.md. Para poses compostas de vários objetos 8×8, a receita
específica é `sms-asset-to-rom.md`; esta receita geral de PNG→tiles não
substitui metasprite, contagem SAT/scanline, render em emulador ou comparação
exata do framebuffer.

## 1. Contrato

Todo pixel visível na ROM percorre exatamente esta cadeia, com um gate por
arco:

```
fonte com proveniência → PNG no contrato SMS → tiles 4bpp (header .h)
→ res/ + símbolo → build (pré-gates) → binding asset→ROM → SHA selada
```

- **Proveniência antes de pixel.** Fonte declarada em manifest com sha256
  (áudio idem: `audit_audio_provenance.py`); `reference_only` é régua, nunca
  fonte; pixel nascido de código não é personagem/cenário final.
- **PNG no contrato**: paleta mestra 6-bit (canal×85), índice 0
  transparente, ≤15 úteis, dimensões múltiplas de 8. Ferramenta:
  `prepare_sms_pixel_art.py` (realçar→posterizar→downscale NEAREST→
  Floyd-Steinberg; não porta paleta de outro console — L055/§8).
- **Tile é 4 planos, 32 bytes** (`png_to_sms_tiles.py`): casa com
  `SMS_loadTiles` (SMSlib.h:130). 2 planos têm caminho próprio
  (`SMS_load2bppTiles`) — misturar os dois embaralha quadrantes (L006).
- **Tamanho tem fonte única**: o `#define FOO_SIZE` nasce da folha, não de
  memória (`gen_fight_gfx.py` + `audit_symbol_size_sync.py`, L052).
- **Binding é hash, não prosa**: `doc/rom_asset_binding.json` casa
  source/res/símbolo/SHA da ROM; rebuild sem re-hash derruba o gate.
- **SHA invariante de fonte**: SDSC pinado (`SMS_EMBED_SDSC_HEADER(…)` com
  data explícita); `AUTO_DATE` muda a SHA no rebuild do dia seguinte e
  derruba todo selo (L065).

## 2. Exemplo mínimo

O arco completo de uma folha de pose no molde MSSF2T:

```
art_src_base/ (fonte, manifest com sha256)
  → tools/translate_ssf2t.py / prepare_sms_pixel_art.py   (PNG no contrato)
  → tools/author_pose_variants.py                          (variantes de silhueta)
  → tools/gen_fight_gfx.py                                 (emit tiles 4bpp + *_SIZE da folha)
  → inc/fight_gfx.h (ken_punch_tiles[], KEN_PUNCH_TILES_SIZE)
  → src/fight.c: request_pose() → SMS_loadTiles / stream 96B
  → build_inner.py --project SMS_projects/MSSF2T           (pré-gates + ROM)
  → doc/rom_asset_binding.json: entrada {source, res, symbol, rom_sha256}
```

Contrato do header de tile (de `png_to_sms_tiles.py`): por linha de 8 px,
4 bytes = plano0..plano3 dos bits do índice de cor, MSB-first. Sprite 16×16
= 4 tiles sequenciais (TL,TR,BL,BR).

## 3. Comando de reprodução

```bash
# 1. traduzir fonte para o contrato (foto/conceito → PNG indexado)
python3 tools/sms_wrapper/prepare_sms_pixel_art.py IN.png OUT.png --block 8

# 2. validar o recurso ANTES de res/ (os PNGs entram explicitamente;
#    --project só contextualiza o contrato — validado a frio no hamoopig, 46 PNGs)
python3 tools/sms_wrapper/audit_validate_resources.py --project SMS_projects/<p> \
    $(find SMS_projects/<p>/res -name '*.png')
python3 tools/sms_wrapper/audit_luma_floor.py --scene pares.json  # {"pairs":[{"fg":[..],"bg":[..]}]}
python3 tools/sms_wrapper/audit_provenance.py --project SMS_projects/<p>

# 3. emitir tiles com tamanho derivado da folha
python3 tools/sms_wrapper/png_to_sms_tiles.py OUT.png --name hero_tiles -o inc/hero_tiles.h
python3 tools/sms_wrapper/audit_symbol_size_sync.py --project SMS_projects/<p>

# 4. build canônico (pré-gates inclusos)
python3 tools/sms_wrapper/build_inner.py --project SMS_projects/<p>

# 5. vínculo asset→ROM + selo
python3 tools/sms_wrapper/audit_rom_asset_binding.py --project SMS_projects/<p> --require
python3 tools/sms_wrapper/seal_fresh_evidence_bundle.py --rom <rom> \
    --artifact out/evidence/evidence.png --artifact out/evidence/runtime_probe.json \
    --max-age-min 180 -o out/evidence/evidence_bundle.json
python3 tools/sms_wrapper/reconcile_claims.py --project SMS_projects/<p>
```

## 4. Caso válido / caso inválido

**Válido** (o estado atual dos dois moldes): binding com 15/12 entradas,
`rom_sha256` igual ao binário em disco, `--require` PASS, rebuild
byte-idêntico (SHA invariante), evidência fresca selada com SHA casando.

**Inválido** (cada furo já existiu e hoje tem gate):
- Header dizendo 1024 para folha de 832 → leitura 192 B além do array
  (L052; `audit_symbol_size_sync.py`).
- Emissão 2bpp consumida por `SMS_loadTiles` → arte embaralhada atribuída
  ao modo de sprite por semanas (L006; `audit_sprite_mode.py`).
- Símbolo visual em `res/` sem proveniência declarada; pixel de código como
  personagem final (`audit_provenance.py`).
- `.psg` sem entrada no manifest de áudio, sha256/bytes divergentes, faixa
  portada sem referência hasheada (L058; `audit_audio_provenance.py`).
- Stream PSG com N cópias do mesmo frame — o loop é do PSGlib, a cópia come
  ROM (L051; `audit_psg_redundancy.py`: 240 cópias × 12 B = 2881 B → 49 B).
- Rebuild com `AUTO_DATE`: SHA muda sem mudar código, selo cai (L065;
  ainda aberto em arena_nocturna/laboratorio_01).
- Binding apontando SHA antiga após rebuild — foi exatamente o que o gate
  pegou na reconciliação de 2026-09-25 nos dois projetos, e exigiu
  re-hash com arte inalterada.

## 5. Vídeo nativo

A prova de que o pixel atravessou a cadeia é a captura do framebuffer com a
arte autoral em cena:

- `SMS_projects/MSSF2T/out/evidence/recipe_combate.mp4` — palco do porto,
  HUD e lutadores autorais renderizando das folhas 4bpp (gate de fidelidade:
  `audit_render_fidelity.py` compara estrutura da fonte com a captura).
- `SMS_projects/kage_matsuri/out/evidence/recipe_combate.mp4` — rua matsuri:
  torii, multidão e Kage compostos de tiles de cena + folhas selecionadas.
- Boots informativos: `out/evidence/evidence.png` de cada projeto, incluídos
  nos bundles selados (10 e 8 artefatos).

## 6. SHA da ROM

- MSSF2T: `efd7162f8c9f829b4826047d24ac2cfed5ab163e094520ee4ca1d00521892122`
  (32768 B, 501 B livres — conteúdo termina em 0x7DF2; teto real 0x7F80).
- kage_matsuri: `f02dfd3c749ed546d4303e1938ebb41cbc08837e8c7bbd96fae08251772419f9`
  (16384 B).

Ambas constam de `doc/rom_asset_binding.json`, `out/build_record.json` e dos
bundles selados. Arte nova além da folga exige banking
(`doc/spec-banking.md`, aguardando aprovação humana) — a receita para de
"válido" no cartucho sem mapper; não claimar o degrau seguinte sem medi-lo.
