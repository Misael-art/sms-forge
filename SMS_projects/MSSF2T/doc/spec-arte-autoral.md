# Spec — Arte autoral nativa (silhueta própria, blocker 4)

> Preparada em 2026-09-08. **Depende do banking** (`doc/spec-banking.md`) —
> a ROM v085 tem 484 B livres; 12 folhas novas de lutador não cabem sem
> páginas. Fora da execução do ciclo atual.

## O que é
Substituir as 12 folhas atuais dos lutadores (downsample+quantize das guias
`rascunho/*_guide.png`, que por sua vez derivam do material
`reference_only` em `art_src_base/`) por **desenhos nativos no canvas
travado do SMS** — silhueta própria, paleta mestra, grid 8×8.

## O que NÃO é
Não é redesenhar o SSF2T. O teto de claim do GDD ("protótipo jogável de
luta 1v1", `ready_for_aaa=false`) continua: a meta é **procedência autoral
completa** — nenhum pixel nascido de material de referência na ROM — e
legibilidade de silhueta a 32×64.

## Pipeline (o que já existe vs. novo)
1. **Model sheet nativa por lutador** (`doc/model_sheet_*.md`): anatomia do
   canvas 32×64, pontos-chave (cabeça/ombro/punho/quadril), 2 subpaletas ×
   15 cores úteis, contraste ≥ 1 degrau (gate `audit_luma_floor.py`).
2. **Novas guias em `rascunho/`** desenhadas pixel a pixel no grid (ferramenta
   `author_native_fighters.py` já gera header/PNG a partir de guia — reuso
   integral; o que muda é a ORIGEM da guia: desenhada, não derivada).
3. **Gates de fábrica que já reprovam deslize:** `audit_provenance.py`
   (origem em `rascunho/` com hash), `audit_validate_resources.py` (grid/cor),
   `audit_sprite_mode.py` (L006), `audit_render_fidelity.py` (a tela mostra a
   arte), `screenshot_semantic_gate.py` (paleta mestra).
4. **Ordem de poses:** idle → walk → punch → special → hit → ko (Ken inteiro,
   depois Guile), crouch/jump por último (derivadas hoje por
   `author_pose_variants.py` — passam a ter model sheet própria).

## Critério de aceite
- `doc/asset_provenance_manifest.json` com origem autoral nativa (sem
  downsample de `art_src_base`), 12+2+1 entradas re-hasheadas;
- `rom_asset_binding.json` re-gerado no mesmo ciclo (L064);
- re-selagem completa (cadeia única) + memory bank;
- comparação lado a lado antigo/novo no memory bank para decisão visual do
  curador (o gate de fábrica não julga estilo — julga contrato técnico).

## Estimativa honesta
12 folhas × (desenho + gates) — o desenho é o gargalo humano; os gates e o
pipeline de geração já existem e não mudam. Pós-banking.
