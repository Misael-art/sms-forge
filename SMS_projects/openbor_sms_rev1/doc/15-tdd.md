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

## Máquina de estados
Pendente (O3): FSM por fonte com startup/active/recovery; hitstop como pausa
curta com orçamento; transições de queda/getup/morte declaradas com testes.

## Banking
- Alvo inicial: **48 KB linear sem mapper**.
- Se exceder: mapper Sega (páginas 16 KB, regs 0xFFFE/0xFFFF), código restrito
  a 32 KB, dados bancados a partir do bank 2.
- Status (O2): ROM build #5 = 32768 B, conteúdo até `0x4DCA` (19915 B usados,
  **12853 B livres**), sem mapper. `audit_probe_corridor` verde.

## Áudio
- Driver: PSGlib (`sdk/devkitSMS/PSGlib/PSGlib.h` é a autoridade).
- Áudio do PAK (WAV/BOR/OGG) é fonte a classificar/adaptar; **não** converte
  automaticamente para PSG; reautoria/transcrição rastreável e aprovável.
- Arbitração música×SFX (4 canais) declarada quando existir conteúdo; noise
  bit2=1 branco, 0 periódico; preview/FFT/pico não certificam composição.

## Orçamento de frame
Medido no O2: o quadro inteiro (SAT 33–36 entradas + PNT 48 B/passo de 8 px +
lógica) roda com **1.0 loop/frame** em idle e caminhada completa
(`measure_runtime_probe`, janelas 59.4–59.7 NTSC; `audit_sprite_line_sim`: pico
8/linha, cortes 2–5 no encontro). `measure_worst_frame.py` é incompatível com o
plano atual (declarado) — a prova do lote é o probe + simulações + verificação
1:1 do framebuffer. FPS regional: NTSC medido; **PAL não medido** (declarado).
Janela VBlank ~4.5 ms sem DMA permanece o contrato de O3+.

## Testes
- Host: `python3 -m unittest discover -s tests` em
  `tools/sms_wrapper/openbor2sms/` (fixtures sintéticas; nenhum conteúdo de
  módulo nos testes) + `--self-check` das ferramentas.
- Integração: parametrizada por `--project`, sem caminhos hardcoded no doador.
- Replay de tabela, pool cheio, stale handle, liberação de espera, same-pass,
  interrupções e restart são regressões obrigatórias (O4+).
