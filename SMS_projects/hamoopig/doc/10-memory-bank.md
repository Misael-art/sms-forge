# 10-memory-bank — hamoopig

> ESTADO OPERACIONAL REAL. Autoridade #1.

## Última atualização
2026-09-25 — **Piso de qualidade de áudio medido (L078/L079):** os streams
deste projeto são byte-idênticos aos do arena_nocturna (mesmo gerador
compartilhado) e reprovam igual — 10 violações por faixa (uníssono triplo a
16 Hz, ruído periódico colado, loops < 2 s); SFX 4/4 passam. Artefato:
`out/logs/psg_quality.json`; dívida no `doc/psg_quality_ledger.json`.
2026-09-19 — **v014: `capture_video` dos ciclos dos dois.** Framebuffer 256×192, gate PASS.

ROM `out/rom/hamoopig.sms` **131072 B**, SHA-256
`4a0807ed9792de25c67ac3384436bded015b1a78924fe2e73b6cb978b806e67a`
(changelog `build_v014`).

## Eixos
| Eixo | Status | Prova |
|------|--------|-------|
| build | buildado | 131072 B, SHA `4a0807ed…` |
| validation_report | buildado | procedência 45 PNGs; semantics OK |
| boot | testado_em_emulador | `title.png` / `select.png` |
| gameplay | testado_em_emulador | `ryo_cycles.mp4` + `musgo_cycles.mp4` |
| fps | não re-medido | |
| áudio | trilha no vídeo Ryo | peak 16511; eixo de mix continua `capture_audio` |
| memory bank | documentado | este arquivo |

## Vídeos (canvas VDP)
| Arquivo | Duração | Motion | O que mostra |
|---------|---------|--------|----------------|
| `out/evidence/ryo_cycles.mp4` | 22.43 s, 1344 f | 27.7% | P1 Ryo (gi laranja) + P2 Musgo; ROUND/FIGHT |
| `out/evidence/musgo_cycles.mp4` | 13.40 s, 803 f | 28.1% | **P1 Musgo** (select Left); P1 anda à direita |

Stills extraídos: `ryo_cycles_f00..f07.png`, `musgo_cycles_f00..f07.png`.
Soco não é óbvio nos 8 stills; o mp4 é a prova temporal.

`ready_for_aaa` de **fábrica** continua false (7 eixos + `delivery`). A **régua de jogo** é AAA: ver diretrizes.

## Animação
| Lutador | idle | walk | punch | special | hit | ko | jump |
|---------|------|------|-------|---------|-----|----|------|
| Ryo | 4 | 4 | 3 | 3 | 2 | 2 | 2 |
| Musgo | 4 | 4 | 3 (102.png) | 3 (710.png) | 2 | 3 | 3 |

## Handoff
1. worst-frame v014
2. Throw / B2
3. Olho no mp4 para o soco (still não fecha)

## Ciclo 2026-09-25 (3) — recomposição conforme o piso + re-selagem

- Música recomposta contra o piso estendido (M7, LOOP_MIN 250 — L080):
  0/6 streams reprovados medidos em disco.
- ROM fd458699afa8… reconstruída; evidências refatas: boot+semântica PASS,
  fps 58.6 (55–60) constante, runtime probe PASS, áudio isolado
  `hamoopig_v3.wav` 23.0 s com audit PASS. Bundle: `out/evidence/evidence_bundle.json`
  (6 artefatos posteriores à ROM). Provas de input/worst-frame antigas seguem
  datadas de ROMs anteriores — reivindicar apenas após re-medida.

## 2026-10-05 — Provas por sessão privada
`tools/prove_walk.py` e `tools/prove_punch.py` migrados para `session_consumer` (frames, RAM, sem DAP/teclado). ROM atual SHA fd458699…4af: walk dx=12 px; soco hp P2 64→57 com `probe_keys` sem reter B1 (comando provado por estado/hit_used/hp). Pendentes: prove_basic/guard/throw/special e capture_scenes/cycles (ver `doc/matriz-consumidores-sessoes-privadas.md`). SHAs fixos antigos dos scripts originais não valem para esta ROM.
