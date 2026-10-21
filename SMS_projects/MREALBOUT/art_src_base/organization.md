# Regras de organização da biblioteca RBFFS (espelha MSSF2T)

## Nome de arquivo

```
<o_que>_neogeo_rbffs_v1.<ext>
<o_que>_<psx|gb>_v1.<ext>       (ports: mesmo jogo, outra plataforma)
<o_que>_vgmuseum_v1.<ext>       (apenas bônus fora do TSR)
```

- `<o_que>`: lutador (`terry`, `white`, `mai_posing`, `mai_variousNN`,
  `yamazaki_posing`), tela (`victory_portraits`, `boot_loading`,
  `portraits_exclusives`, `vscpu_loading`, `select_player`,
  `vsselect_player`, `versus_portraits`, `title_gb`, `sgb_border`),
  `ending_terry_NN`, `terry_frames_inventory` (derivado).
- Plataforma: `neogeo` (arcade/MVS), `psx` (port Dominated Mind),
  `gb` (port Game Boy). Sempre explícita.
- `<ext>`: formato REAL (`png`, `gif`, `zip`, `txt`).
- Asset multi-arquivo (ZIP do Terry) vive em **pasta** com o mesmo nome
  do ZIP (`terry_neogeo_rbffs_v1/`): ZIP = artefato-fonte preservado,
  pasta = cópia de trabalho organizada (role `derived` no manifest).
- `_v<n>`: versão de sourcing (v1 = coleta 2026-09-06).

## Onde mora cada categoria

| Categoria | Diretório |
|---|---|
| Lutadores e poses | `sprites/` |
| Cenários | `backgrounds/stages/` (vazio — lacuna) |
| Telas | `title/screens/` |
| HUD, fontes | `hud/` (vazio — lacuna) |
| Endings | `endings/scenes/` |
| Música (só índice) | `audio/music/` |
| Roster e notas | `manuals/docs/` |

## Proibido (igual MSSF2T)

Arquivo de 0 bytes; binário de áudio como asset; promover referência a
`res/` sem o fluxo canônico (`rascunho/` → contrato → model sheet → gates).
