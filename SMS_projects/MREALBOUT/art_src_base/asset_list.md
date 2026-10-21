# Índice de assets — biblioteca RBFFS (`reference_only`)

Coleta: 2026-09-06. Fontes: The Spriters Resource (5 assets — tudo que
existe lá) + vgmuseum.com (bônus). `visual` = inspecionado; o ZIP do Terry
foi validado por inventário programático (1378/1378 frames legíveis).

## sprites/ — Terry completo + bônus parciais

| Arquivo | Fonte | Conteúdo | Verif. | Notas SMS |
|---|---|---|---|---|
| `terry_neogeo_rbffs_v1.zip` | TSR 170291, Terminetor566 | 1378 frames + Effects/3 + Palettes/8 + Portraits/6 | inventário | Pedido central. Frames médios 74×93, máx 148×256 → redução ~2× + metasprite; mapear golpes na conversão (nomes são índices, não golpes). |
| `terry_neogeo_rbffs_v1/` | extração local do ZIP | 1395 arquivos organizados (frames + Effects/ + Palettes/ + Portraits/) | inventário | Role `derived`. ZIP original preservado como artefato-fonte; a pasta é a cópia de trabalho. |
| `terry_frames_inventory_v1.txt` | derivado local | lista + estatísticas | gerado | Role `derived`. Navegação sem abrir 1400 arquivos. |
| `white_psx_v1.png` | TSR 167003, Lukebarz (port PSX Dominated Mind) | sheet 3130×6056 | metadados | BÔNUS. **Exclusivo do port PSX** (ausente no arcade); mesmo-jogo-mesma-família, precedente SNES↔arcade do SSF2T. |
| `mai_various01..09_vgmuseum_v1.gif` | vgmuseum, Chance | 9 poses (78×94 a 153×172) | metadados | BÔNUS. Série Real Bout (jogo exato a confirmar); poses avulsas, não movelist. |
| `mai_posing_vgmuseum_v1.gif` | vgmuseum, Chance | 1 pose 104×129 | metadados | BÔNUS, mesma ressalva. |
| `yamazaki_posing_vgmuseum_v1.gif` | vgmuseum, Chance | 1 pose 90×97 | metadados | BÔNUS, mesma ressalva. |

## title/screens/ — telas (TSR + screenshots TFG)

| Arquivo | Dimensões | Notas SMS |
|---|---|---|
| `victory_portraits_neogeo_v1.png` | 866×1075 | Retratos de vitória — referência p/ tela de win. |
| `boot_loading_neogeo_v1.png` | 536×249 | Boot/loading do port — referência de fluxo, não arte final. |
| `portraits_exclusives_neogeo_v1.png` | 620×355 | Retratos dos exclusivos do port (EX). |
| `vscpu_loading_neogeo_v1.png` | 788×714 | Loading VS CPU — referência de composição de tela. |
| `select_arcade_shot_tfg_v1.png` + `select_arcade2_shot_tfg_v1.gif` | 304×224 | PLAYER SELECT arcade (duas capturas) — grid 4×4 + SELECT. |
| `versus_frag_shot_tfg_v1.jpg` | 559×419 | Fragmento de versus (Terry × ?) — layout parcial. |
| `win_mary_shot_tfg_v1.png` | 304×224 | Win screen Blue Mary — formato da tela de vitória. |
| `win_krauser_shot_tfg_v1.png` | 320×224 | Win pose Krauser — formato + sprite bônus. |
| `intro_mai_shot_tfg_v1.png` / `intro_joe_shot_tfg_v1.png` | 304×224 | Cartões de intro (função exata a confirmar na conversão). |
| `toplogo_tfg_v1.gif` | 500×300 | Logo oficial — referência p/ title autoral. |
| `select_player_psx_v1.png` | 588×787, Ultimecia (port PSX) | Player select do Dominated Mind — layout de seleção reaproveitável. |
| `vsselect_player_psx_v1.png` | 550×240, TrueBackLash (port PSX) | Faixa VS do select — referência de HUD de tela. |
| `versus_portraits_psx_v1.png` | 604×468, Magma MK-II (port PSX) | Versus portraits — par do victory arcade. |
| `title_gb_v1.png` | 326×187, Alxala (port Game Boy) | Title do port GB — mesmo jogo, resolução próxima do SMS (160×144 nativo). |
| `sgb_border_gb_v1.png` | 256×224, Alxala (port Game Boy) | Moldura Super Game Boy — referência de moldura, não arte. |

## endings/scenes/ — ending do Terry (vgmuseum, 320×224 nativo Neo-Geo)

16 quadros (`ending_terry_01..08.png`, `09..16.gif`) — storyboard de
referência da cena final do mascote. Endings dos demais: lacuna.

## backgrounds/stages/ — 7 screenshots TFG (composição, NÃO rips)

| Arquivo | Mostra | Notas SMS |
|---|---|---|
| `stage_korea_shot_tfg_v1.png` | Kim mirror; templo Korea | Palco Korea confirmado (2 ângulos com o próximo). Pátio + templo ao fundo; torii/portão. |
| `stage_korea2_shot_tfg_v1.png` | Tung vs Kim; mesmo palco | Confirma palco compartilhado (Tung luta no Korea). Poses bônus de Tung e Kim. |
| `stage_jungle_cheng_shot_tfg_v1.png` | Cheng vs Franco; selva | Palco do Cheng. Bônus: sprites de Cheng e Franco visíveis. |
| `stage_bridge_shot_tfg_v1.png` | Terry vs Mai; ponte vermelha/pagoda | Palco a confirmar (ponte). Composição forte p/ 256×192. |
| `stage_dark_shot_tfg_v1.png` | Bob vs Krauser; palco escuro | Germany-noite ou Geese Tower? A confirmar contra gameplay. |
| `stage_germany_shot_tfg_v1.png` | Bob vs Krauser; castelo de pedra | Germany dia (Laurence). Castelo + arbustos; símbolo no chão. |
| `stage_usabeach_shot_tfg_v1.png` | Terry vs Duck; praia USA | USA Beach (Terry/Mary/Duck): palmeiras, iate, proa. Primeiro palco do teste. |

Regra: screenshot vale **composição e paleta**; pixel final será arte
autoral. Rips de tiles de stage: lacuna permanente até captura própria.

## hud/ — VAZIO (lacuna total) | audio/music/ — só `tracks.md`

## Lacunas declaradas

1. **16/20 lutadores arcade sem sprite** (Terry completo; Mai/Yamazaki
   parciais; White só existe no port PSX).
2. **Stages: 7 composições por screenshot, 0 rips de tiles**; HUD/fonte 0;
   endings 1/20 (Terry). Wiki neo-geo.com perdeu os arquivos (galeria
   quebrada) — serviu só o mapeamento palco↔lutador.
3. MUGEN tem cobertura mas foi **rejeitado como fonte primária**:
   proveniência fragmentada (dezenas de autores, edits misturados).
4. RB1/RB2/KOF têm sprites **de outros jogos** — rejeitados como
   substitutos (precedente válido: só mesmo-jogo-outro-port: PSX, GB).
