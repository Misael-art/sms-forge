# 17-asset-spec — contrato de assets de arena_nocturna

> Documento de ENCOMENDA + estado. Os slots marcados como residentes já são
> consumidos pela ROM; os slots marcados como futuros são contrato de produção,
> não evidência de implementação. Cada item tem nome, dimensão e orçamento
> fixos. Trocar pixels dentro do slot é drop-in; mudar dimensão ou contagem de
> tiles exige atualizar `src/game.h`, o manifest e os gates.

## 0. A restrição que decide tudo: VRAM está cheia

A VRAM de tiles do SMS tem **512 slots de 32 bytes**, e o SMS usa metade
para sprites quando `SMS_useFirstHalfTilesforSprites(1)` está ligado. O mapa
atual:

| faixa | tiles | ocupante | livre |
|---|---|---|---|
| 0–63 | 64 | fonte do `SMS_autoSetUpTextRenderer` | 0 |
| 64–191 | 128 | `arena_bg` (cenário) | 0 |
| 192–239 | 48 | hero, hero_walk, tiro, counter, impacto, boss ×2 poses | 0 |
| 240–255 | 16 | **livre** | 16 |

**Sobram 16 tiles.** Isso é meio quadrante de boss. Portanto:

> **Não peça mais tiles. Peça melhores tiles, e peça animação por
> streaming.**

### Streaming de tiles é o método, não um truque

Uma pose nova **não** ocupa uma faixa nova de VRAM. A pose vive na ROM e é
copiada para o **mesmo slot** com `SMS_loadTiles()` na transição de estado,
dentro da janela VBlank medida. O custo é ROM (barata; o alvo linear atual é
48 KB) e não VRAM (esgotada). O runtime já faz isso para idle/passo do hero e
normal/telegraph do boss; a medição instrumental do pior VBlank ainda é
pendente.

Consequência prática para quem desenha: **cada pose de um personagem tem de
usar exatamente a mesma contagem de tiles da pose base.** Hero = 4 tiles por
pose. Cada quadrante de boss = 4 tiles por pose. Sem exceção.

---

## 1. Geometria — o modo é ZOOMED, e isso não é negociável agora

`SMS_setSpriteMode(SPRITEMODE_ZOOMED)`: **cada pixel do PNG vira 2×2 pixels
na tela.**

| ator | PNG (autoral) | tela | tiles |
|---|---|---|---|
| hero (cada pose) | 16×16 | 32×32 | 4 |
| boss (cada quadrante, cada pose) | 16×16 | 32×32 | 4 |
| boss inteiro | 4 quadrantes | **64×64** | 16 |
| tiro / counter / impacto | 8×8 | 16×16 | 1 |
| cenário `arena.png` | 256×192 | 256×192 | ≤128 após dedup |

Duas consequências que **precisam** guiar o traço:

1. **Não existe detalhe de 1px em sprite.** Ele vira um bloco de 2×2 na
   tela. Desenhar cílios, rebites finos ou hachura de 1px é desperdiçar o
   orçamento — some ou vira ruído. Trabalhe em massas de 2px ou mais.
2. **O cenário NÃO é zoomed.** BG e sprite convivem na mesma tela com
   resoluções aparentes diferentes: o fundo tem pixel fino, os personagens
   têm pixel grosso. Isso é uma escolha estética, e a única forma de ela
   parecer intencional é o **cenário adotar a mesma escala de forma** —
   massas grandes, poucos detalhes finos, contraste por bloco. Um fundo
   cheio de textura fina ao lado de um hero de pixel 2× lê como erro.

---

## 2. Paletas — os 32 bytes que o jogo inteiro tem

SMS: duas subpaletas de 16 cores, 6-bit (`--BBGGRR`), índice 0 transparente
nos sprites. Valores atuais em `src/main.c`.

**BG (`bg_palette`)** — Dark Deco orbital:
```
0x00 preto      0x3F branco     0x10 navy       0x00 (livre)
0x11 cobalt     0x15 aço        0x21 brass      0x2A ouro
0x3F branco     0x0C magenta    0x18 ciano      0x24 âmbar
0x30 azul-claro 0x3C ciano-claro 0x16 verde-mar 0x06 vermelho
```

**Sprite (`sprite_palette`)** — índice 0 é transparente; índice 1 é preto
opaco de contorno (`0x00`). Eles compartilham o mesmo valor físico, mas não a
mesma função: nunca use índice 0 para pixel desenhado.

### Encomenda de paleta (item de trabalho real)
Devolva as duas paletas revisadas como uma tabela `índice → valor 6-bit →
para que serve`, respeitando. Esta é a proposta de rampas para revisão visual;
os valores continuam sujeitos ao `audit_luma_floor.py`:
- Índice 0 de sprite = transparente, obrigatório.
- **Rampa de 4 tons por material** (escuro → luz), não gradientes soltos.
  Com 15 cores cabem ~3 rampas + 3 acentos.
- Contraste fg/bg acima do piso medido por `audit_luma_floor.py`. **Meça
  antes de entregar** — "alto contraste" sem número é reprovação por §36.
- Uma cor reservada **só** para o telegrafo do boss. Hoje a pose de carga se
  distingue por desenho; ela precisa se distinguir por **cor**, que é o que
  o olho lê em 20 frames.

#### Proposta de sprite palette

| material/uso | escuro | meio 1 | meio 2 | luz |
|---|---:|---:|---:|---:|
| metal ciano do hero/shot | `0x10` | `0x20` | `0x30` | `0x3C` |
| metal brass do boss | `0x06` | `0x16` | `0x26` | `0x3F` |
| energia magenta do counter | `0x01` | `0x11` | `0x21` | `0x31` |
| contorno/acento | `0x00` | — | — | `0x3F` |

`0x2A` fica reservado **somente** ao telegrafo do boss: não pode aparecer no
hero, shot, counter ou impacto. A tabela final precisa manter as 16 entradas,
com índice 0 transparente, e ser comparada com a captura real; uma rampa
desenhada no documento sem essa medição não é aceite.

---

## 3. Slots existentes — o que trocar

Substituir o pixel, manter nome e dimensão. Todos em `res/sprites/`, PNG
indexado, índice 0 transparente.

| arquivo | 16×16 | papel | o que está faltando hoje |
|---|---|---|---|
| `hero.png` | ✓ | VANTA-9 parado | aprovado como base; falta ciclo idle authored |
| `hero_walk.png` | ✓ | passo de caminhada | pose 0 de ciclo de quatro; variantes vivem na ROM e são streamadas |
| `boss_tl/tr/bl/br.png` | ✓ ×4 | guardião, pose base | aprovado no recorte/fidelidade; falta costura visual final |
| `boss_charge_*.png` | ✓ ×4 | pose de telegrafo | pose streamada para os slots normais; leitura por ciano/magenta dedicado |
| `shot.png` | 8×8 | tiro do hero | horizontal ciano/branco com núcleo claro; validado no framebuffer nativo |
| `counter.png` | 8×8 | contra-ataque | diagonal magenta/violeta com núcleo âmbar; sem ciano compartilhado |
| `impact.png` | 8×8 | FX de acerto | frame legado; ciclo ativo usa `impact_0..2` |
| `res/bg/arena.png` | 256×192 | cenário | ver §1.2 |

**Prioridade 1 — resolvida nesta revisão (afeta jogabilidade, não só beleza):** `counter.png` tem de
ser inconfundível em relação a `shot.png` — cor diferente, forma diferente,
direção diferente. O jogador precisa saber num frame o que vem na direção
dele. Isso é legibilidade, não decoração.

---

## 4. Slots novos — encomenda para streaming

Estes entram por **streaming** (§0), reusando os mesmos tiles. Entregue como
PNGs adicionais; o wiring em C deve copiar a pose para o slot ativo somente na
troca de estado. Não reservar uma faixa nova para cada arquivo.

### 4.1 Ciclo de caminhada do hero — 4 poses
`hero_walk_0.png` … `hero_walk_3.png`, 16×16 cada, 4 tiles cada.
Ciclo fechado: contato → passagem → contato oposto → passagem. Troca a cada
~8 frames. **O `hero_walk.png` atual vira a pose 0.**
Estado: implementado. Quatro poses autorais trocam a cada 8 frames no mesmo
slot `HERO_TILE`; a pose esquerda é uma tradução nativa separada.

### 4.2 Hero virado — espelho não basta
`hero_left.png`, `hero_walk_left_0..3.png`. O SMS **tem** flip por atributo
de tile no BG, mas **não em sprites** — sprite não tem bit de flip. Virar o
hero exige tiles espelhados de verdade na ROM. Se o orçamento apertar,
entregue só `hero_left.png` (pose parada) e o ciclo fica sem virada.
Estado: implementado para a pose parada esquerda; o runtime escolhe
`hero_left.png` quando `facing=1`. O ciclo de caminhada esquerda completo fica
fora do escopo medido desta fatia.

### 4.3 Impacto — 3 frames
`impact_0.png`, `impact_1.png`, `impact_2.png`, 8×8. Nasce apertado e
brilhante, abre, dissipa. Hoje é um frame estático por 12 frames, que lê
como um adesivo colado na tela.
Estado: implementado. `impact_0..2` são streamados no mesmo `IMPACT_TILE` em
12 frames, com hitstop sem apagar o boss.

### 4.4 Boss: pose de dano e pose de morte
- `boss_hurt_{tl,tr,bl,br}.png` — recuo/contração, 1 pose.
- `boss_dead_{tl,tr,bl,br}.png` — colapso, 1 pose.
Hoje o dano é uma piscada de sprite ligado/desligado, e a morte é o boss
sumindo instantaneamente da tela. Ambos são o mesmo defeito: **evento sem
representação**.
Estado: implementado. O boss permanece visível em `BOSS_HURT` e `BOSS_DEAD`,
com pose autoral streamada nos mesmos 16 tiles até a conclusão do evento.

### 4.5 Tela de título
`res/bg/title.png`, 256×192, **≤128 tiles após dedup**. Precisa caber na
mesma faixa 64–191, então é carregada no lugar da arena e a arena é
recarregada ao entrar em jogo (display desligado — o código já tem o
estado `ST_TITLE`, hoje mostrando a arena com uma faixa de texto).
Logotipo em **tiles de BG**, não em fonte: a fonte é 8×8 monocromática.
Estado: implementado. `title.png` usa 5 tiles únicos na faixa BG 64–191; a
entrada em jogo recarrega `arena.png` com display desligado.

---

## 5. Áudio — o que existe e o que falta

`inc/music_battle.h` e `inc/music_title.h` são streams autorais PSGlib que
tocam no emulador. `src/audio.c` processa `PSGFrame()` e depois
`PSGSFXFrame()`, mantendo a música nos quatro canais e arbitrando SFX nos
canais 2/3.

### Encomenda
Quatro efeitos em **formato PSGlib SFX** (`.psg` autoral compatível com o
formato consumido por `PSGSFXPlay()`), gerados por
`tools/sms_wrapper/make_psg_assets.py`:

| id | evento | duração alvo | canal |
|---|---|---|---|
| `SFX_SHOT` | hero dispara | ≤8 frames | tom |
| `SFX_HIT` | tiro acerta o núcleo | ≤10 frames | tom + ruído |
| `SFX_HURT` | hero leva dano | ~16 frames | ruído |
| `SFX_DOWN` | guardião cai | ~30 frames | ruído |

Restrição dura: os quatro juntos **não podem usar o canal 0**, que é onde a
melodia vive. Um SFX que rouba a melodia deixa o silêncio mais audível que
o efeito.

Estado observado: implementado e auditado no Emulicious em
`out/evidence/audio_psglib_final_v21.wav` (`peak=7475`, `92% ativo`). O
manifesto de procedência é `doc/audio_provenance_manifest.json`; nenhum SFX
usa o canal 0. O SDK local não contém `psgcomp`/`vgm2psg`, portanto os streams
são autoria direta no formato PSGlib, não uma alegação de conversão por essas
ferramentas.

---

## 6. Como entregar — condições de aceite

Cada asset só é aceito com:

1. **Fonte em `rascunho/`** + entrada em `doc/asset_provenance_manifest.json`
   com `origin`, `author`, `tool`, `role`, `sha256`. O gate de procedência
   bloqueia pixel sem origem declarada.
2. **PNG indexado no grid SMS**, paleta 6-bit, índice 0 transparente,
   dimensão exata da tabela. `audit_validate_resources.py` reprova o resto.
3. **Contagem de tiles igual à do slot** (§0). Uma pose de hero com 5 tiles
   não entra por streaming.
4. **Número de luma medido**, não adjetivo (§36 da bíblia artística).
5. **Leitura no Emulicious**, não só conformidade técnica. Conformidade
   técnica não prova que o counter se distingue do tiro em movimento.

---

## 7. O que NÃO encomendar

- Mais faixas de tile (§0: não existem).
- Detalhe fino em sprite (§1: vira bloco 2×2).
- Paralaxe multicamada — o SMS tem **um** plano de BG; paralaxe aqui exige
  interrupção de linha, que não está implementada e não está no GDD.
- Sprite espelhado por atributo (§4.2: o VDP não oferece isso em sprites).

## 8. Estado de integração — 2026-09-09

Implementado e observado na ROM final desta revisão (SHA registrado no memory
bank após o build):

- recorte alpha-preserving dos sprites, sem o bloco navy introduzido pela
  dilatação; palette de sprite com separação luma/visual do fundo;
- hero visível, boss gordo de 64×64, tiro horizontal ciano/branco com núcleo
  claro e counter diagonal magenta/violeta com núcleo quente; a distinção foi
  observada em `arena_shot_video_final_v1.png` e
  `arena_counter_video_final_v1.png`, frames distintos do framebuffer atual;
- título BG-only, arena recarregada ao iniciar, quatro poses de caminhada e
  pose esquerda do hero streamadas em `HERO_TILE`; durante `shot_on`, a pose
  autoral de caminhada 3 vira a pose de ataque, com braço projetado e corpo
  inclinado, sem abrir faixa adicional de VRAM;
- normal, telegraph, hurt e dead do boss streamados nos mesmos 16 tiles ativos
  após `SMS_waitForVBlank`;
- colisão swept, remoção do tiro no cruzamento, hitstop e FX separado sem
  apagar o boss em frames alternados; a transição foi registrada em
  `arena_transition_final_v1.mp4` e o impacto visual em
  `arena_impact_final_v5.png`;
- trajetória do tiro em 4 px/frame e counter em 3–5 px/frame para leitura
  durante mais VBlanks, sem reservar tile adicional;
- três frames do impacto no mesmo `IMPACT_TILE`, recursos, procedência, luma,
  modo zoomado, SAT/scanline e self-test reexecutados com sucesso.

Pendente e não mascarado: controle humano isolado no harness. A atração prova
a coreografia e a colisão visual observada, não prova input humano.

O registro dos 12 princípios é aplicado às poses e ao timing dentro do
orçamento real de sprites; não há alegação de uma tira de 12 imagens separadas.
A pose experimental `rascunho/hero_attack_v3_source.png` foi mantida apenas
como estudo e não foi promovida para `res/`, pois o recorte automático removia
detalhes brancos legítimos. O ataque oficial da ROM é a pose nativa 3 mais o
tiro ciano/branco, counter magenta/violeta e impacto separado.
