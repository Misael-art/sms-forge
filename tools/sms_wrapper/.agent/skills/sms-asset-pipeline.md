# skill: sms-asset-pipeline

## Fluxo canônico

Organização de estudos e derivados: `workflows/artifact-organization.md`.
Registro de navegação não substitui o manifesto de assets integrados. Resolva
concept/model sheet, fonte animada e prova de conversão por papéis distintos.
Para sprite sheet exportado, faça preflight do arquivo salvo com
`audit_source_raster.py` antes de quantizar/empacotar; não impor contrato SMS
à arte bruta de conceito nem promover um PASS de alpha a qualidade artística.
```
rascunho/<original> (com sha256 registrado)
  → contrato de asset (asset_contract_v1)
  → model sheet (personagem/inimigo/cenário)
  → prova técnica de pose/conversão aprovada
  → PNG indexado 8-bit sem perda, grid 8×8, índice 0 transparente, ≤15 úteis
  → gates: validate_resources + luma_floor + provenance
  → conversor adequado ao tipo: png_to_sms_tiles (tile) ou
    pack_sms_metasprite (pose composta por objetos 8×8)
  → ROM diagnóstica + comparação do framebuffer + binding por SHA
  → revisão humana, paleta/budget por cena e integração em res/ROM de produção
```

## Proveniência (gate audit_provenance.py)
- Todo PNG de res/ tem entrada em `doc/asset_provenance_manifest.json`.
- origin aponta arquivo real em rascunho/; sha256 bate.
- `tool:"code"` é proibido para personagem/inimigo/boss/cenário_final.

## Conversão
Foto/truecolor → `prepare_sms_pixel_art.py` (paleta mestra SMS, grid 8×8)
antes de `res/`. Skill: `sms-pixel-translate.md`. Não use preset NES/SNES.
Para uma única imagem física 8×8/8×16/16×16, PNG indexado no contrato →
`png_to_sms_tiles.py` (4bpp / 32 B por tile). Para uma pose grande feita de
vários objetos, use `pack_sms_metasprite.py`, depois simule SAT/scanline e
construa uma ROM diagnóstica. Siga `sms-asset-to-rom.md` (L121): inventário
de tiles não prova render correto; compare o framebuffer capturado com o PNG
fonte e vincule ROM e captura por SHA. Essa prova não promove o asset para
produção nem fecha paleta global ou budget da cena.

## Uma fonte para o tamanho
`#define FOO_SIZE` e `foo[N]` (e o mesmo define em dois headers) coincidem.
Header-índice escrito à mão diverge da folha e o streamer lê além do array
(L052). Gere o header; rode `--check`. Gate: `audit_symbol_size_sync.py`.
