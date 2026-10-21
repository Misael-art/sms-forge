# B.2b-3b — custódia da política de SAT

Candidatos medidos em 2026-10-20/21. Nenhum foi promovido; a produção
canônica `087df676…` e o `src/main.c` `042ba22e…` foram restaurados após
cada build. Relatório legível: `reports/B2B3B_REPORT.md`; relatório
machine-readable:
`out/logs/runs/20261021T025418Z_b2b3b_sat_policy.json`.

## ROMs

| arquivo | SHA-256 | política | pacing 300 s | linha |
|---|---|---|---|---|
| `roms/v040_satpolicy_d998209b….sms` | `d998209b…` | ordem alternada | 5743 | FAIL pico 14, 78/77 linhas |
| `roms/v041_linecap_3f3dce97….sms` | `3f3dce97…` | cap whole-cell | 2055 | PASS sim. 39/8 |
| `roms/v042_rowquota_44315339….sms` | `44315339…` | quota 6+2/banda | 4483 | PASS 40/8 |
| `roms/v042_padded1m.sms` | `9009b247…` | cópia 1 MB p/ BlastEm | — | — |
| `roms/v043_rowquota_13b78bd2….sms` | `13b78bd2…` | quota escalar 5+3 | 5033 | PASS 40/8 (f002) |
| `roms/v043_padded1m.sms` | `c2eba01c…` | cópia 1 MB p/ BlastEm | — | — |

A cópia padded só corrige a máscara de bancos do BlastEm 1.0.0
(`bank &= rom_banks-1`); não é a ROM de produção.

## SAT / linha

- `sat/shadow_f001.json`, `sat/shadow_f002.json`: SAT shadow v040,
  64 sprites; pico 14; 78/77 linhas >8; `line_sim_v040_f00*.out` FAIL.
- `sat/shadow_v042_f001.json`, `sat/shadow_v042_f002.json`: SAT shadow
  v042, 40 sprites; pico 8; 0 overflow; `line_sim_v042_f00*.out` PASS.
- `sat/silhouette_v042.json`: §129 manual. P1 30 células (6/banda),
  P2 10 (2/banda). 6+2 reprova nas duas atribuições: P1 player → 6>5;
  P2 player → 2<3. O 5+3 maximiza o primário dentro do teto (5) e mantém o
  secundário no piso (3); o 4+4 também passaria, mas reduz mais o primário.
- `sat/shadow_v043_f001.json`, `sat/shadow_v043_f002.json`: SAT shadow
  v043. f001 = 25 (P2 primário 5/banda; P1 em transição, não emitido);
  f002 = 40 (P1 15 = 3/banda, P2 25 = 5/banda), pico 8; `line_sim_v043_*`
  PASS.
- `sat/silhouette_v043_f002.json`: §129 no f002 (ambos os lados) — P1 3
  ou 5, P2 3 ou 5; jogador ≥3, ataque ≤5, inimigo ≥2/≥5; **PASS** nas duas
  atribuições. O f001 não serve para §129 (P1 ausente).
- `sat/shadow_v043_sim_f001.json`: simulação 5/3 a partir da SAT v040
  (40 sprites, pico 8). Projeção, não substitui o snapshot real.

## Capturas / vídeo

- `captures/shot_v042_pair_f1020.png` e `f1021.png`: **mesmo SHA**
  (`ccdd51c5…`), e o lado cheio é oposto ao shadow SAT do snapshot 1020.
  A captura pareada está um quadro de jogo atrasada/adiantada; usar o
  vídeo e a SAT shadow. Não é prova do estado SAT do frame 1020.
- `captures/video_v042_pair.*`: 600 quadros, 133 distintos, 256×192,
  59,92 Hz, `max_from_initial_fraction=0,1158`; alternância anti-fase
  573/600.
- `captures/video_v043_pair.*`: 600 quadros, 127 distintos, 256×192,
  59,92 Hz, `max_from_initial_fraction=0,1190`; 5/3 mais equilibrado
  (cheio ~1957, faixa ~974). O par f1020/f1021 é o mesmo frame de jogo
  (`smrt_frame=254` nos dois), então não é uma alternância de 1 quadro.
- `captures/shot_v043_rowquota.*`: captura do selo 300 s (frame 18087);
  o corpo secundário pode mostrar listras da seleção “primeiras N”.
- `captures/video_v040_pair.*`: referência de 600 quadros, 179 distintos.
- `captures/shot_v042_rowquota.*`: captura do selo 300 s (frame 18084).

## BlastEm

- `blastem/v042_s1020_1021/`: sessão `blastem-sms-f2832c39…`, ROM padded
  `9009b247…`, snapshots 600/1020/1021 (`ram.bin`, `vram.bin`, `cram`,
  `vdp_regs`, `screenshots`).
- `blastem/v043_s1020_1021/`: sessão `blastem-sms-dec09ac7…`, ROM padded
  `c2eba01c…`, mesmos boundaries. `session.json` declara
  `claim_scope=diagnostic_states_only`, sem FPS/áudio/hardware.

## Limitações declaradas

- `audit_silhouette_integrity.py` é O3-específico; a contagem §129 do
  luta_mugem é manual (células por banda/linha), não pixels nem ROM.
- `present_p1/p2=65535` sob quota significa “alguma célula omitida”, não
  “corpo ausente”; a sonda não serve de gate para esta política.
- `sat_om` alto no v042/v043 é omissão **declarada** da quota, não
  overflow do SAT-64; a SAT válida é 40/64 (`SpriteNextFree=40`).
- O v043 f001 é uma transição com P1 não emitido; a amostra de política
  e de §129 é o f002 (ambos os lados).
- O selo mede o contador de frames do loop; o estado de luta (damage/KO)
  pode diferir entre candidatos. O gate é `smrt_frame >= 5745`, não o
  resultado do combate.
