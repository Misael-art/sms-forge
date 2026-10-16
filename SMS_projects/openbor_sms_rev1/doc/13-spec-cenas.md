# 13-spec-cenas — openbor_sms_rev1

> Budget REAL por cena. **Autoridade #3.**
> Regra: **"estimado" é proibido neste arquivo.** Todo número aqui é medido,
> com o método da medição citado. Folga não medida é timidez (§18).
> **Estado: O2 fechado medido** (2026-10-16, ROM build #5 `b0eb624f…`); cena 02
> segue fora do escopo de medição (O7).

## Contrato de hardware (fixo, não negociável)
| Recurso | Limite físico |
|---------|---------------|
| Tela | 256×192 |
| VRAM | 16 KB |
| RAM | 8 KB |
| Sprites por scanline | 8 |
| Sprites na SAT | 64 |
| Subpaletas | 2 × 16 (índice 0 transparente nas duas) |
| Cores úteis simultâneas | 30 |
| Janela VBlank | ~4.5 ms (NTSC) — **não existe DMA** |
| ROM sem mapper | 48 KB |

## Cena 01 — TOWN1 (recorte)
### Layout de VRAM declarado (plano `sms_vram_plan_v1`, MEDIDO)
Fonte: `data/generated/plans/o2_vram_plan_20261016.json` (`fa4c9a2a…`).

| Região | Faixa (tiles) | Tiles | Bytes | Uso |
|--------|---------------|-------|-------|-----|
| patterns sprite | 0..243 | 244 | 7808 | atores (122 pares TALL 8×16) |
| patterns BG | 244..435 | 192 | 6144 | dicionário do cenário (k-medoides, K=192) |
| patterns HUD | 436..438 | 3 | 96 | trilho + barras do HUD de piloto |
| **total de padrões** | 0..438 | **439/448** | 14048 | margem 9 |
| name table | `$3800` (`name_base` 14336) | — | 1792 | PNT 32×28 (linhas 0..1 = HUD) |
| SAT | `$3F00` | — | 128 | atores/HUD |
| janela de sprite (reg6) | `$FB` | — | — | $0000..$1FFF (256) — sprites na metade baixa |
| name table extra (reg2) | — | — | — | **nenhuma** (`extra_name_tables: []`) |
| sobras reclamadas | — | — | — | **nenhuma** (`pockets: []`; margem 9 não reclamada) |

Veredito: `measure_vram_map.py --plan … --snapshots <sessão>` **aprovado**
(0 blockers, 2 snapshots de sessão BlastEm; cross-check de reg6/reg5).
Registradores no boot: r0=64 (M4+LEFTCOLBLANK+LOCKHSCROLL), r1=62, r2=FF,
r6=FB (`audit_blastem_sms` ok, escopo `record_consistency_only`).

### Orçamento worst-frame (MEDIDO — política da máscara D10)
| Item | Valor medido | Método da medição |
|------|--------------|-------------------|
| sprites na SAT | 33–36 (≤ 64) | `audit_sprite_line_sim.py` sobre as 6 poses (pior caso z=180 sobreposto) |
| pico de sprites/linha | **8** (= limite 8; sem omissão além do corte declarado) | idem |
| cortes do inimigo | no encontro (z=180): 5 (idle) / 2–3 (walk); pior caso em toda a faixa de pz: 7 células (idle, pz 181+) | máscara `inc/o2/enemy_mask.h` (3 B/entrada; 6 poses × 73 pz; todas as 438 entradas cortam ≥1 célula) |
| escrita de PNT por passo de 8 px | 1 coluna × 24 linhas = 48 B | `sms_emit` (colunas) + verificação 1:1 do framebuffer |
| ritmo do loop (ROM) | **1.0 loop/frame** em idle e caminhada completa (300/300 e 520/520) | `measure_runtime_probe.py` (`probe_frame` 1:1 com o frame do emulador) |

- **Total worst-frame**: o quadro inteiro (SAT + PNT por passo + lógica) cabe em
  1 quadro NTSC com folga de loop (1.0); o defeito anterior (contagem de linha em
  runtime, ~2.07 frames) foi eliminado pela máscara pré-computada na emissão.
- **Headroom**: 12853 B de ROM livres (conteúdo até `0x4DCA` em 32768 B);
  9 tiles de VRAM não reclamados.
- **Método**: `measure_runtime_probe.py` (janelas de frames da própria ROM via
  DAP) + `audit_sprite_line_sim.py` + verificação pixel 1:1 do framebuffer.
  `measure_worst_frame.py` é **incompatível** com o plano atual deste lote
  (declarado, não contornado) — a prova de orçamento deste lote é a dupla
  acima, nunca uma estimativa.
- **Degrau seguinte medido**: decisão D10 registrada no escopo O2 rev2
  (`doc/artifacts/o2_vdp_pilot_scope_20261016.json`).

### Sprites por scanline (pico) — MEDIDO
Manifestos `data/generated/emit/o2_sprite_scene_*_20261016.json` (6 poses):
33–36 entradas na SAT, pico 8/linha, cortes 2–5. Modo **SPRITEMODE_TALL
(8×16)** obrigatório (8×8 estoura a SAT: ~94 objetos > 64 — medição do rev1).
Espelho = padrões próprios (VDP do SMS não tem flip de sprite).

### fps observado — MEDIDO (NTSC)
Janelas do `measure_runtime_probe`: 59.58 / 59.73 / 59.57 (sessão publicada
`586141…`) e 59.41 / 59.72 / 59.42 (sessão de calibragem) — nominal
59.92274340431231, ≥5 amostras. **PAL declarado (idle 4 / walk 6 frames) e não
medido; fora dos claims do O2.**
Substituição declarada: `measure_fps.py` (lê o título da janela do host) e
`measure_frame_advance.py` (exige dígito-contador em tela; o HUD do O2 não tem
texto) são **N/A** na sessão isolada sem janela — os eixos de pacing são
cobertos pelas janelas do probe + ritmo de loop 1.0.

## Cena 02 — bt_rescue (segundo piloto, O7)
Fora do escopo de medição imediata. Pré-flight herdado do doador (não é mediação
SMS): nativo rejeitado (1158 tiles vs 896 aceitos), legado 880 tiles cobrindo
512 de 2390 px com 3 slots de inimigo — **a reconfirmar por medição própria
apenas se o perfil mudar** (assets/budget).
