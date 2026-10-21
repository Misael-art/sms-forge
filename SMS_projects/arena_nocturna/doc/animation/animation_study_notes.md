# Registro de estudo de animação — arena_nocturna

## Lacunas atacadas

- Hero: alternância idle/locomoção e estados de ataque com antecipação, contato,
  hitstop e recuperação.
- Guardião: hover em dois tempos, telegraph, recoil, hurt e dead no contra-ataque.
- Tiro: envelope de colisão estrito; o projétil é removido ao cruzar o alvo e
  gera FX de impacto separado em três poses temporais.
- Recorte: fontes mantêm alpha binário e derivados indexados; nenhum fundo é
  aceito como parte do corpo.
- Paleta: cenário permanece em subpaleta escura; personagens usam rampas
  ciano/cobalto/brass e o contra-ataque usa magenta/ciano.

## Regra de leitura

Cada frame será conferido em 1x, sem confiar apenas em zoom. Frames duplicados
usam hold de VBlank; não são copiados como novas poses. O pivot inferior central
fica estável durante walk, ataque e dano.

## Ordem canônica executada

`brief → identidade → escala/pivot/colisão → poses nativas → roster → key poses
→ staging → timing/física → autoria de frames → metasprite → QA → ROM`.

O detalhamento machine-readable está em
`doc/animation/animation_production_record.json`; o roster consumido pelo gate
de semântica está em `doc/animation/animation_semantics_manifest.json`.

## Registro pós-emulador — 2026-09-04

- `arena_showcase_final_v7.png` confirmou o recorte autoral sem o matte navy: hero
  legível à esquerda e boss circular grande à direita. A captura é da atração,
  não de controle humano.
- O hero alterna a pose idle e a pose de passo no slot `HERO_TILE` a cada 8
  VBlanks. O ciclo agora usa quatro poses de caminhada, com pose esquerda
  authored separada porque sprites SMS não têm flip horizontal. O boss carrega
  normal/telegraph/hurt/dead nos mesmos quatro slots de quadrantes; não há
  cópia residente das variantes.
- O acerto foi fechado no runtime por colisão swept (`shot_prev_x` → `shot_x`),
  com remoção do tiro, hitstop e burst independente. O bundle semântico deixa
  explícito que screenshot não prova colisão isoladamente.
- O FX foi recortado novamente com alpha preservado; a origem final é
  `rascunho/impact_source_v3.png`, registrada no manifesto de procedência.
- O impacto observado usa `impact_0`, `impact_1` e `impact_2` no mesmo tile
  ativo; a sequência abre e dissipa durante 12 VBlanks, preservando o hitstop.
- O título `arena_title_final.png` foi observado como BG-only; `title.png` usa 5
  tiles únicos e a arena é recarregada ao entrar em `ST_PLAY`.
- A dilatação morfológica foi removida do tradutor para não preencher vazios
  autorais com navy. A paleta de sprite separa a massa do hero/boss do fundo e
  mantém shot/counter com leitura distinta.
- `arena_impact_final_v4.png` confirmou o impacto separado e
  `arena_bossdown_final_v5.png` confirmou o estado final do boss.
- `arena_counter_final_v7.png` e `arena_shot_final_v5.png` são capturas frescas
  da mesma sequência de Emulicious; o gate de colisão permanece no código e
  não é inferido de uma imagem isolada.
- O gate de evidência recusa `--press` quando `g_demo_mode` está ativo; o
  teste de controle precisa de uma ROM sem atração.
- Ao disparar, `hero_walk_3` é streamada como ataque: postura inclinada e braço
  projetado, enquanto o tiro permanece um sprite independente. A pose
  experimental `hero_attack_v3_source.png` não foi promovida porque o matte
  removido pelo recorte automático apagava detalhes brancos.

## Registro pós-emulador — 2026-09-09

- A ROM atual é `f86c4fae3826699c39a231f4ff33761f7d54adf5e08bc20ec3d341d04504d7d8`.
- O tiro final passou por `audit_render_fidelity.py` no framebuffer nativo
  (`arena_shot_video_final_v1.png`, frame 220, 80% de coincidência estrutural).
- O contra-ataque foi registrado em outro frame (`arena_counter_video_final_v1.png`,
  frame 240), com diagonal magenta/violeta e núcleo quente; não é a mesma
  imagem usada para o claim do tiro.
- `arena_transition_final_v1.mp4` passou o gate de vídeo: 256×192, 289 frames,
  5,82 s, 54,2% de movimento e áudio anexado. O vídeo prova mudança temporal,
  não substitui a análise de colisão do código.
- O recorte final do impacto permanece separado em `arena_impact_final_v5.png`;
  o boss continua visível durante o burst, sem o flicker que fazia o projétil
  parecer atravessá-lo.
- A tentativa de recapturar o boot determinístico foi marcada como ambiente
  (`FAIL_AMBIENTE`): o gate filtra canvas de 256/300 px e a sessão estava em
  janela 512 px. Nenhum artefato antigo foi reapresentado como prova da ROM
  atual.
