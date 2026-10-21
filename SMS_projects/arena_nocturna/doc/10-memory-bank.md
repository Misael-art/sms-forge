# 10-memory-bank — arena_nocturna

> Estado operacional observado. Esta página só declara o que foi buildado,
> executado e medido no ROM citado abaixo.

## Última atualização

2026-09-25 — **Piso de qualidade de áudio medido (L078/L079, gate
`audit_psg_quality.py`):** as duas faixas (`music_battle.psg` `ce050926…`,
`music_title.psg` `95ee4bc7…`) reprovam com 10 violações cada — os 3 canais
de tone tocam a MESMA nota a cada frame a atenuação 1 e há ruído PERIÓDICO
colado por baixo (assinatura literal do "ruído péssimo" reportado pelo
humano); loops de 1,9 s e 1,0 s. Causa isolada no gerador compartilhado
`tools/sms_wrapper/make_psg_assets.py`. SFX 4/4 passam. Ver
`out/logs/psg_quality.json` e `doc/psg_quality_ledger.json`.

2026-09-09 — ROM final da revisão: `out/rom/arena_nocturna.sms`, 32.768 bytes,
SHA-256 `f86c4fae3826699c39a231f4ff33761f7d54adf5e08bc20ec3d341d04504d7d8`.

## Eixos de entrega

| Eixo | Status | Evidência fresca |
|---|---|---|
| build | buildado | `out/rom/arena_nocturna.sms` — SHA acima |
| validation_report | validado_budget | 30 sprites + 2 BG; procedência; modo ZOOMED; 22 sprites; pico 8/linha; luma; marcadores; constantes SMS |
| boot no emulador | testado_em_emulador | `arena_title_final_v10.png` e `arena_transition_final_v1.mp4`; o recapture automático de `audit_deterministic_boot.py` foi `FAIL_AMBIENTE` porque o script aceita canvas 256/300 e o Emulicious desta sessão abriu em 512 px |
| gameplay da atração | testado_em_emulador | `arena_showcase_final_v9.png`, `arena_shot_video_final_v1.png`, `arena_counter_video_final_v1.png`, `arena_impact_final_v5.png`, `arena_transition_final_v1.mp4` |
| FPS | testado_em_emulador | `fps_final_v6.json`: 6 amostras, 60 fps em todas |
| loop da ROM | testado_em_emulador | `frame_advance_final_v10.json`: 232 amostras, 60.0 fps estimado, 9 transições, aprovado |
| áudio | testado_em_emulador | `audio_psglib_final_v21.wav`: peak 7475, 92% ativo; `audit_audio` passou |
| memory bank atualizado | documentado | este arquivo |

## O que foi corrigido

- Hero: quatro poses autorais de caminhada, pose esquerda sem flip de sprite e
  pose `hero_walk_3` streamada enquanto `shot_on`, dando postura inclinada e
  braço projetado ao ataque.
- Boss: metasprite modular de 64×64, ao menos o dobro da massa do hero, com
  telegraph, recuo, hurt e dead sem piscar/apagar a silhueta.
- Tiro: velocidade de 4 px/frame, `shot_prev_x` + `shot_x` em colisão swept;
  o tiro é removido no cruzamento, e o FX surge na borda de contato.
- Impacto: três frames em `IMPACT_TILE`, 12 VBlanks e hitstop de 4 VBlanks;
  ordem da SAT deixa o burst legível na frente do boss.
- Leitura visual: arena em navy/baixo detalhe e personagens em ciano,
  magenta, brass e branco; shot horizontal ciano/branco com núcleo claro e
  counter diagonal magenta/violeta com núcleo quente não compartilham a mesma
  leitura.
- Áudio: PSGlib com música em execução e SFX nos canais 2/3, sem roubar o
  canal 0 da melodia.

## 12 princípios de animação

O registro completo está em `doc/animation/animation_production_record.json`.
Os princípios foram aplicados às poses, timing, spacing, staging, pivôs,
antecipação, recuo, follow-through, arcos, ação secundária e impacto dentro do
orçamento SMS. Isto não é uma alegação de 12 imagens independentes: o runtime
faz streaming de poses autorais em slots fixos de VRAM.

O estudo experimental `rascunho/hero_attack_v3_source.png` foi rejeitado como
asset de produção porque o matte removido apagava detalhes brancos legítimos.
O ataque oficial usa a pose nativa 3 e o projétil ciano; a rejeição está
registrada para impedir a promoção de um recorte inferior.

## Limitações honestas

- A atração automática prova a coreografia e a execução, mas não prova
  controle humano. O harness de teclado não fechou o caminho de input; o gate
  recusa usar `--press` enquanto `g_demo_mode` estiver habilitado.
- O gate automático de boot não foi promovido nesta revisão: sua captura de
  canvas rejeitou a janela configurada em escala 2× (`512 px`). A title e o
  vídeo de framebuffer atuais comprovam execução da ROM, mas não se declara
  aqui um PASS de determinismo automático para esta sessão.
- O worst-frame de escrita VRAM ainda é orçamento provisório; os assets e a
  SAT passaram as medições disponíveis, mas não há claim de VBlank validado.
- A medição de FPS é do Emulicious e o frame advance é do contador da própria
  ROM; ambos são mantidos separados para não confundir emulação com loop.

## Gates reexecutados

`audit_validate_resources`, `audit_provenance`, `audit_sprite_mode`,
`audit_sprite_line_sim`, `audit_luma_floor`, `audit_debug_markers`,
`audit_hardware_constants`, `audit_render_fidelity` para `shot.png`,
`capture_video --self-check` e captura real de framebuffer,
`capture_evidence --self-check`,
`measure_frame_advance --self-check`, boot determinístico real, FPS real,
captura/auditoria de áudio e captura visual real.

## Próximo passo

Para qualquer alteração de código ou asset: rebuild, recapturar as provas
contra o novo SHA e selar novo bundle. Não usar os bundles anteriores, pois
eles pertencem a ROMs diferentes.

## Ciclo 2026-09-25 (3) — recomposição conforme o piso + re-selagem

- Música recomposta contra o piso estendido (M7 respiro >= 8 frames,
  LOOP_MIN 250 — L080): 0/6 streams reprovados medidos em disco.
- ROM 90d5d7e77f90… reconstruída; evidências refatas: boot+semântica PASS,
  fps 59.8 (59–60) constante, runtime probe PASS, áudio isolado `arena_v3.wav`
  23.0 s com audit PASS. Bundle novo: `out/evidence/sealed_bundle_final_v7.json`
  (6 artefatos posteriores à ROM). Os bundles anteriores pertencem a ROMs
  diferentes — não usar.
