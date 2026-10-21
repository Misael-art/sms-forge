# Biblioteca de referência — Real Bout Fatal Fury Special (Neo-Geo, SNK 1997)

> **Status: `reference_only`.** Nada aqui é arte de entrega.
> Mesma doutrina da biblioteca-irmã `MSSF2T/art_src_base/`: a arte final
> da ROM será pixel art autoral SMS-nativa (§15/§39 do `SMS_GLOBAL.md`).

## Cobertura real (honesta: RBFFS tem pouca ripagem pública)

- **Terry Bogard COMPLETO**: `sprites/terry_neogeo_rbffs_v1.zip` — 1378
  frames + Effects/Palettes/Portraits (TSR, Terminetor566) + inventário.
- **Mai**: 9 poses variadas + 1 posing (vgmuseum, Chance) — BÔNUS parcial.
- **Yamazaki**: 1 posing (vgmuseum, Chance) — BÔNUS mínimo.
- **Telas**: victory portraits, boot, portraits exclusivos do port,
  VS CPU loading (TSR, Magma MK-II).
- **Ending do Terry**: 16 quadros 320×224 (vgmuseum) — referência de cena final.
- **LACUNAS GRANDES**: 17 dos 20 lutadores sem nenhum sprite; TODOS os
  stages sem sheet; HUD/fonte sem sheet; endings dos demais; áudio PSG
  futuro. Detalhe em `asset_list.md`.

## Estrutura (igual à MSSF2T)

```
sprites/  terry (zip+inventário), mai, yamazaki
backgrounds/stages/  VAZIO (lacuna — ver asset_list)
title/screens/  victory, boot, portraits, vscpu
hud/  VAZIO (lacuna)
endings/scenes/  ending_terry_01..16
audio/music/  tracks.md (só índice, sem binário)
manuals/docs/  roster_rbffs.md (checklist 20 lutadores + stages)
```
