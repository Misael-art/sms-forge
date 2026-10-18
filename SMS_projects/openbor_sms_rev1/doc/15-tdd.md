# 15-tdd — openbor_sms_rev1

> Arquitetura técnica. Autoridade #7.
> A API definitiva é o header (`sdk/devkitSMS/SMSlib/SMSlib.h`, autoridade #8) —
> este documento NUNCA inventa assinatura. Em dúvida: leia o header.

## Arquitetura do pipeline (contrato de conversão)
```
PAK → dependências resolvidas → IR tipado → perfil de compatibilidade
    → dados ROM/bancos → runtime C/Z80 → ROM observada
```
O host extrai/compila; o **SMS não mantém o PAK completo em RAM**. Toda feature
carrega estado `exact | adapted | blocked | dropped_by_owner` com parser,
lowering, consumidor, teste e prova por hash. Separar sempre
`parsed ≠ generated ≠ consumed ≠ observed ≠ budget_validated`.

### Host (implementado em `tools/sms_wrapper/openbor2sms/` — infra do wrapper)
| Módulo | Papel | Estado (O0) |
|--------|-------|-------------|
| `pak.py` | leitor PAK32/PAK64 (porte fiel do doador, banner com SHA) | **implementado** (19 unittest verdes com `intake.py`) |
| `intake.py` | verificação determinística de fontes (pak/sources/deps) | **implementado**, `--self-check` verde |
| `model_text.py` | parser de texto de modelo/level | O1 (porte) |
| `level_inventory.py` | inventário lexical de nível | O1 (porte) |
| `semantics.py` / `reference_semantics.py` | semântica + perfil de referência condicional | O1 (porte) |
| `level_event_table.py` | tabela estática de eventos (emissor determinístico C) | O1 (porte) |
| `analyze.py` | análise estática de capacidades/assets | O1 (porte) |
| `emit_slice.py`, `images.py`, `streaming.py`, `profiles.py` | **decisões MD** — referência de origem/cache/ownership/testes; a emissão SMS é separada | NÃO portar como SMS |
| `sms_art.py` | conversão de arte SMS: palco por dicionário de tiles, paletas 6-bit, poses TALL keyed, previews, records de conversão | **implementado** (O2), `--self-check` verde |
| `sms_emit.py` | contrato de emissão: IR + escopo → dados C + emission record com hashes + máscara de corte pré-computada (D10); `--generated-at` pinável para reprodutibilidade | **implementado** (O2), `--self-check` verde |

### Dados e locations (registro único)
- `data/source_openbor/` — subconjuntos extraídos dos PAKs (managed, hasheado).
- `data/generated/` — IR, tabelas, transcripts (managed) — **nunca** `res/`.
- `res/` — só recursos que passaram gates de produção (proveniência, recorte,
  paleta, prova técnica).

## Tipos e unidades (contrato de semântica)
- Mundo horizontal (X), profundidade no chão (Z) e altura de salto (Y)
  **separadas**; projeção/tipos/unidades declarados por campo do IR.
- Caixas/ataques usam profundidade, facing e frame ativo; sort visual não
  define colisão; física não para porque um hit mudou a FSM no ar.
- Handles/pools estáticos com geração, cleanup e invalidação de alvo/hit.
- Relógio: `delay` OpenBOR → conversão **racional** com política NTSC/PAL;
  fronteira de equivalência declarada no IR (origem desconhecida do runtime
  original é registrada, não mascarada).

## Restrições assumidas (herdadas, sempre ativas)
```
❌ float/double em runtime quente  — SDCC Z80 faz float em software; use int16/Q8.8
❌ malloc / free                   — buffers estáticos; RAM = 8 KB
❌ VRAM em massa fora do VBlank    — sem DMA
❌ >8 sprites/scanline, >64 na SAT
❌ >15 cores úteis em paleta sprite indexada (P1 índice 0 transparente)
```

## Armadilhas Z80/SDCC vigiadas neste projeto
- `int` é 16-bit signed; `char` é unsigned por padrão (SDCC z80).
- Multiplicação/divisão são caras (sem HW mul) → tabelas lookup / Q8.8.
- ISR curta: trabalho pesado fica no loop principal. Pause = NMI.
- Variável `__at()` sem `volatile` é apagada pelo SDCC (L009) — sondas seguem
  o workflow de marcadores.

## Runtime SMS observado (O2 — piloto VDP)
- **Scroll/câmera (medido):** `cam = clamp(px-120, 0, 376) & ~7` (quantizada em
  8 px); `N = (-cam) & 0xFF` no registrador de h-scroll; a tela x≥8 mostra a
  coluna PNT `cam_col + (x>>3)`; anel mod-32 de colunas
  (`[cam_col..cam_col+31]`) reescrito a cada passo de 8 px, inclusive para trás;
  `VDPFEATURE_LOCKHSCROLL` (HUD fixo nas linhas 0..1) + `VDPFEATURE_LEFTCOLBLANK`
  (x0..7); backdrop preto (`SMS_setBackdropColor(1)`).
- **Orçamento de sprites:** máscara pré-computada na emissão (decisão D10) —
  `inc/o2/enemy_mask.h[(pose_index()*73 + (pz-160))*3]`, 3 B/entrada, bit i =
  célula i da tabela ordenada do inimigo; política conservadora (todas as
  células contam, mesmo fora da tela); jogador sempre inteiro; runtime = lookup
  + `sx > 255` pula. Política antiga (contagem em runtime) consumia ~2.07
  quadros na pior pose — eliminada.
- **Poses:** idle01 + ciclo walk01/walk03 (ax), idle01 (long); espelho = padrões
  próprios. Delays: idle 8→5 NTSC, walk 12→7 NTSC (PAL declarado).
- **HUD:** linhas 0..1; trilho preto + barra verde (hp 100 → 160 px) + barra
  vermelha (hp 50 → 80 px); 3 tiles; piloto, não arte final.
- **Probe de RAM:** magic/schema (`SMRT` v1) — frame u16 @0xC7F0; estatísticas do
  jogador/câmera @0xC000. Ver `doc/13-spec-cenas.md` (medições) e o escopo
  `doc/artifacts/o2_vdp_pilot_scope_20261016.json` (rev2).

## Runtime SMS observado (O3 — combate, M5/M6)
- **FSM por ator** (`src/main.c`): idle/chase/attack/hit/drop/rise/dead; o
  ataque consome a caixa `attack2` do frame ativo (D4 — `first..last`);
  dano/knockback em `resolve_hits`; `hit_used` impede hit duplo no mesmo golpe.
- **D13 — guarda pós-hit (medida)**: `guard` (13 q) decrementa no topo de
  `actor_advance`, antes do hitstop e do gate de pose; sem isso a vítima ficava
  imune para sempre e a morte era inalcançável. Prova: traço de morte com 8
  hits 50→0 (`dead=1`, estado DEAD f114, HUD `hde=0`).
- **IA chase (D6)**: `facing = alvo.x > e.x`; velocidade máxima 1,5× a do
  jogador; decisão a cada 12 q; persegue **x e z** (`move_toward(dx,dz)` com
  acumuladores Q8.8) e ataca com `|dx|<=40 && |dz|<=15`; facing congela no
  ataque. Prova M6: e.x 299→240 (vídeo) e e.z 185→206 (traço dedicado).
- **Pulo/queda (D5)**: tabelas congeladas `o3_jump_y/x` (40 q, ápice 55,
  deriva 67 px), `o3_toss_y/x` (36 q) e `o3_entry_y` (entrada, 38 q); sem
  float no runtime. TOSS só com `alt>0` (ou dead); o knockdown do M6 termina
  em RISE f84.
- **Uploader (D8)**: dois slots por ator (29 células × 2 tiles); commit
  adaptativo em sub-chunks de 64 B, teto 320 B/ator/q, margem 22 linhas,
  prólogo 30; throughput estável medido **128 B/q** (2 sub-chunks). A pose
  seguinte é pré-carregada no slot não exibido; a troca de slot só ocorre com a
  cópia pronta. **Consequência de pacing**: durante o ataque o avanço da
  animação espera a pose ficar pronta — o ataque completo leva ~60 q, não os
  21 q nominais; o hit causal ocorre em ~16 q (≈0,27 s). O jogador tem
  prioridade e zera o budget do inimigo enquanto sobe pose.
- **Render**: células posicionadas por `(x - cam) + dx`, `z - 32 - alt + dy`;
  corte por scanline com tabela estática `o3_ax_rows` (D9-a2); HUD por delta
  (linha inteira só quando o hp desenhado muda); coluna de BG fatiada
  (`write_bg_row`/`write_bg_col`, guarda de 26 linhas).
- **Arte na tela (medida)**: a âncora do canvas autoral é `(xh-32, base-80)`;
  `audit_render_fidelity` confirma 100% estrutural na pose estável
  (`ax_a105_right` em [92,68]); poses em troca de slot do uploader não casam
  1:1 (o gate exige pose estável; declarado). Still canônico: sessão
  `598625a4…`.
- **Probe v2** (`0xC7E0..0xC7FF`): `vline` b10, `vovf` b11, `done` b14, frame
  u16 b16..17; `py` @0xC7FD = altitude do jogador, `p2state` @0xC7FE, `p2z`
  @0xC7FF. RAM medida: `pl` @0xC004 (30 B), `e` @0xC026 (30 B), câmera e
  colunas @0xC044. Corredor de sondas verificado (`audit_probe_corridor`).

## Mapa de memória (RAM)
Medido pós-link (O2, build #5): estáticas do jogador/câmera em `0xC000`
(px u16, pz, facing, anim, walk_frame, anim_timer; `cam` u16 @0xC007;
`written_col` @0xC009); `probe_frame` u16 @0xC7F0; corredor de sondas
`0xC7E0..0xC7FF` (25 sondas, folga 1796 medida). `audit_probe_corridor.py` PASS.
RAM = 8 KiB; nenhuma alocação dinâmica.

## Entidades e pools (estáticos)
O2: 1 jogador + 1 inimigo **estáticos** (sem pool dinâmico). O3+: pools com
máximos medidos (1P × 1/2/3 inimigos, depois 2P se contratado). Pool cheio
**não** autoriza apagar inimigo nem pular evento.

## Features O3 — estado de conversão
| Feature | Tag | Prova/limite |
|---|---|---|
| input causal frame-paced | `exact` | journal grava cada read (bytes de RAM); sessões isoladas |
| hit/dano/guarda (D13) | `adapted` | ticks 200 Hz → frames NTSC; guarda 13 q; traço de morte 8 hits |
| pulo/tombo/knockdown | `adapted` | tabelas por-frame; ápice 55; TOSS com windup 15 q |
| profundidade/alvo móvel em z | `adapted` | `move_toward(dx,dz)`; e.z 185→206 no traço |
| pacing do ataque | `adapted` | uploader domina: ~60 q completo; hit ~16 q (declarado) |
| render fidelity | `exact` | 100% estrutural na pose estável; slot em troca não casa |
| audit_render_glitch | `blocked` | sem renderizador legal full-frame 256×192 validado |
| PAL | `blocked` | não medido |
| áudio | `blocked` | M7 |

## Máquina de estados
Implementada (O3/M5–M6): estados `idle/chase/attack/hit/drop/rise/dead`;
`startup/active/recovery` vêm do anim (`o3_aframe` com delays e frames
ativos); hitstop é pausa curta com orçamento no loop, não recursão; queda
(TOSS com `alt>0`) e getup (RISE) são arcos tabelados; morte exige hp 0 e
`guard==0` (D13). Transições provadas por input causal no M6 (attack, jump,
knockdown, depth, death) — ver memory bank e `m6_evidence_76cdbee3.json`.

## Banking
- Alvo inicial: **48 KB linear sem mapper**.
- Se exceder: mapper Sega (páginas 16 KB, regs 0xFFFE/0xFFFF), código restrito
  a 32 KB, dados bancados a partir do bank 2.
- Status (O3/M6): ROM **131072 B** bancária (mapper Sega habilitado), 60
  blocos de pose nos bancos 2–6 (79744/81920 B); código/`DATA` restritos a
  32 KB; `audit_probe_corridor` verde na ROM atual. O2 sem mapper foi o piloto
  (32768 B); o O3 excedeu o linear por medição (D1).

## Áudio
- Driver: PSGlib (`sdk/devkitSMS/PSGlib/PSGlib.h` é a autoridade).
- Áudio do PAK (WAV/BOR/OGG) é fonte a classificar/adaptar; **não** converte
  automaticamente para PSG; reautoria/transcrição rastreável e aprovável.
- Arbitração música×SFX (4 canais) declarada quando existir conteúdo; noise
  bit2=1 branco, 0 periódico; preview/FFT/pico não certificam composição.

## Orçamento de frame
- **O2 (piloto, histórico):** quadro inteiro (SAT 33–36 + PNT 48 B/passo de
  8 px + lógica) a **1.0 loop/frame**; janelas 59,4–59,7 NTSC; pico 8/linha.
- **O3/M6 (medido):** SAT até 2×29 células com corte por linhas exatas;
  uploader 128 B/q (2×64 B) + coluna de BG fatiada + HUD por delta. MWF
  3000 quadros `vovf_delta=0`, `vline_min=202`; MRP 3×8 s
  59,48/59,66/59,78 (NTSC); stress com input até quadro ROM 3230 sem `vovf`.
  NTSC medido; **PAL não medido** (declarado). `measure_fps`/
  `measure_frame_advance` são N/A na sessão isolada (o probe mede fps/boot);
  a janela VBlank ~4,5 ms sem DMA continua o contrato.

## Testes
- Host: `python3 -m unittest discover -s tests` em
  `tools/sms_wrapper/openbor2sms/` (fixtures sintéticas; nenhum conteúdo de
  módulo nos testes) + `--self-check` das ferramentas.
- Integração: parametrizada por `--project`, sem caminhos hardcoded no doador.
- Replay de tabela, pool cheio, stale handle, liberação de espera, same-pass,
  interrupções e restart são regressões obrigatórias (O4+).
