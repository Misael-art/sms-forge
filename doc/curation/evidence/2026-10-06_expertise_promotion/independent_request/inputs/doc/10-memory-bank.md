# 10-memory-bank — laboratorio_01

> ESTADO OPERACIONAL REAL. Autoridade #1.

## Última atualização
2026-08-31 — jogador promovido a METASPRITE 16x16 (§25/L006) + correção da raiz
profunda do L006 no conversor de tiles. Eixos de runtime REBAIXADOS pelo próprio
build (§26: ROM relinkada invalida evidência anterior) — recaptura pendente.

## Eixos de entrega (7)
| Eixo | Status | Prova |
|------|--------|-------|
| build | **buildado** | `out/rom/laboratorio_01.sms` 16.384B; `TMR SEGA` @espelho 0x7FF0, checksum 0x5ABB |
| validation_report | validado (pre-gates) | recursos+procedência pass; record em out/build_record.json |
| boot no emulador | **testado_em_emulador** | `out/evidence/evidence.json` PASS (viewport var 3715); Emulicious 2026-03-27 |
| gameplay | testado_em_emulador (VITORIA capturada) | frame de VITORIA em gameplay_cena02_vitoria.png (texto legivel); logica provada por simulacao + execucao real |
| 60/50 fps | testado_em_emulador | fps.json: 6 amostras 58-60 (media 59.0), constante_50_60=true — eixo FECHADO |
| áudio | implementado (evidência audível pendente) | blip SN76489 porta 0x7F no movimento (v6); confirmação humana via ./run.sh |
| memory bank atualizado | sim | este arquivo (auditoria 2026-08-30) |

## Decisões registradas
- Header SEGA embutido via macros oficiais (`SMS_EMBED_SEGA_ROM_HEADER_16KB` +
  SDSC auto-date), confirmadas em SMSlib.h:429–485.
- Toolchain instalado rootless via `tools/sms_wrapper/ensure_toolchain.sh`
  (SDCC 4.6 portátil; SMSlib/PSGlib RECONSTRUÍDAS do fonte — lição L004).

## Cena 01 "boot_interativo" (2026-08-26)
- v003 buildada com pre-gates verdes (recursos+procedência no próprio build).
- Rota BG para o cursor (desvio documentado — L006: sprite com pixels índice-0,
  causa-raiz aberta; readvram/repl do Emulicious é a ferramenta de fechamento).
- Evidência de boot v1 segue válida; gameplay parcial (ver eixos acima).

## Sessão 2026-08-26 (parte 2)
- F2 fechada: fps.json 58-60fps constante.
- F3 implementada: blip PSG no movimento (sem degradação de fps).
- L006 avançou: travamento isolado DENTRO de SMS_loadTiles (L009).

## F4 cena02 (2026-08-29)
- GDD cena02, spec, storyboard, contrato criados (pipeline aaa_scene_v1 S0-S4).
- Runtime: bloco 2x2 empurrável, alvo, vitória + reinício, colisão AABB, beep/fanfarra.
- Build v012 OK, tela limpa capturada.

## FPS FECHADO (2026-08-30)
- 59.3fps MEDIDO via contador de frames na tela (0x012F->0x01AD = 126f/2.125s). Eixo fps_constante=true.
- Audio: IMPLEMENTADO (PSG porta 0x7F); comprovacao audivel limitada pelo host (L012: Java do Emulicious nao roteia no Pulse). Eixo audio=false, honesto.

## Cena 04 "corredor estelar" (2026-08-30)
- Combina sprites (L006) + musica battle rica (PSGlib 4 canais) + scroll + HUD + HP/gameover.
- Prova: cena04_sprites.png (jogador sprite visivel, 60fps) + audio_battle.wav (96% ativo, peak 9936).
- Musica gerada por probes/gen_music.py (formato .psg do PSGlib); inc/music_battle.h.

## Próximo passo declarado
- Fechar fps/audio medidos no emulador (F2/F3 ja implementados; medicao no emulador).
- F1: L006 sprite (probe; VRAMmemcpy + SPRITEMODE_NORMAL 8x8).
- Atualizar build_record com eixos provados.
- F1: resolver L006 sprite (probe em probes/).
- Reconstruir build_record com eixos provados (nao por edicao).
- F1: resolver L006 sprite via VRAMmemcpy (probe em probes/).
- Reconstruir build_record com eixos de runtime provados (não por edição).


## Sessão 2026-08-31 — metasprite 16x16 e a raiz profunda do L006

**RAIZ PROFUNDA ENCONTRADA (mais funda que o modo de sprite):**
`png_to_sms_tiles.py` emitia **2 planos de bits (16 B/tile)** enquanto
`SMS_loadTiles` copia para `tilefrom*32` — caminho **4bpp, 32 B/tile**
(SMSlib.h:130 é a autoridade; para 2 planos existe `SMS_load2bppTiles`).
Cada par de "tiles" de 16 B era lido como UM tile de 32 B: quadrantes e planos
embaralhados. **A arte 16x16 nunca chegou íntegra à VRAM.** O sintoma foi
atribuído por semanas ao modo de sprite; o modo era só a camada de cima.

Consequência concreta: `hero_tiles` tinha 64 B (2 tiles) em vez de 128 B (4).
O jogador desenhava o tile 128 e os "inimigos"/projétil desenhavam os tiles
129..131 — que eram **fragmentos da arte do herói**.

**Feito nesta sessão:**
- `png_to_sms_tiles.py` corrigido para 4bpp real (32 B/tile, 4 planos, cores 0..15);
  self-check com regressão: cor 15 precisa acender os 4 planos.
- `inc/hero_tiles.h` regenerado: 128 B = 4 tiles (128..131 = TL,TR,BL,BR).
- Jogador = `SMS_addMetaSprite` com formato autoritativo lido em
  `devkitSMS/SMSlib/src/SMSlib_metasprite.c`: triplas (dx, dy, tile) + `METASPRITE_END`.
- Declaração de sprites passou a ser **por frame** (`SMS_initSprites` → adds →
  `SMS_copySpritestoSAT`): `SMS_addMetaSprite_f` não devolve handle.
- Inimigo e projétil ganharam tiles próprios (132, 133) com assets declarados
  em `res/sprites/` — saíram dos quadrantes do herói.
- `star_tile` corrigido de 16 B para 32 B (mesmo bug do conversor).
- Física ajustada a 16x16: colisão AABB e limites de tela.

**Orçamento SAT:** 4 (metasprite) + 5 inimigos + 1 projétil = **10 de 64**.
Pico por scanline continua sob o teto de 8, mas o jogador agora ocupa **2**
sprites por linha nas suas 16 linhas — margem menor que antes.

**Verificado estaticamente:** round-trip `hero.png → 4 tiles → arte` idêntico,
e o header casa byte a byte com o conversor. Build OK (16384 B).

**VISTO RODANDO (2026-08-31)** — a sessão tinha emulador; minha afirmação
anterior de que não tinha estava errada. Ao rodar, apareceram MAIS DUAS causas:

**Quarentena:** `enemy.png` e `shot.png` são PLACEHOLDERS (`role: outro`), assim
como `block.png` e `target.png`. Nenhum pode ir para entrega sem arte autoral ou
aprovação estruturada — `audit_placeholder_quarantine.py --check-release` bloqueia.


## L006 FECHADO COM EVIDÊNCIA — três defeitos empilhados

Rodar no emulador revelou que a arte 16x16 correta **ainda** saía como ruído.
Duas causas adicionais, achadas nesta ordem:

1. **Name table nunca limpa.** O runtime só preenchia `4..27 x 4..24`; o resto
   exibia lixo de VRAM. É a moldura de ruído presente em TODA captura desde a
   cena 04 — inclusive na evidência que sustentou a F6.
2. **Base de tiles de sprite (§27) — A CAUSA-RAIZ REAL.** Sem
   `SMS_useFirstHalfTilesforSprites(1)`, o VDP lê os padrões de sprite na
   SEGUNDA metade da VRAM: `SMS_addSprite(...,128)` lê o tile **384**, nunca
   escrito. Assinatura do erro: **BG limpo + sprite corrompido**.

Somadas às duas já corrigidas (conversor 2bpp→4bpp e a geometria §25), eram
**quatro** defeitos sobre o mesmo sintoma. Por isso "corrigir a causa" nunca
limpava a tela, e por isso o L006 foi declarado RESOLVIDO em 2026-08-30 com a
tela ainda em ruído.

### Estado dos eixos (contra a ROM atual, bundle selado)
| Eixo | Status | Prova |
|------|--------|-------|
| build | buildado | 16384 B |
| validation_report | pass | pre-gates verdes |
| boot_emulador | **testado_em_emulador** | `out/evidence/evidence.png` — tela limpa, HUD legível, campo de estrelas, metasprite 16x16 com cruz atravessando os 4 quadrantes; `bundle.json` selado |
| fps_constante | **testado_em_emulador** | `out/evidence/fps.json` — 6 amostras, 60/60/60, `constante_50_60=true` |
| gameplay | **testado_em_emulador** | `evidence.json`: `sprite_dx=+89px` após `Right` — bloco de 96px rastreado entre capturas; `sprite_displacement_proven=true` |
| audio | **testado_em_emulador** | `out/evidence/audio_metasprite.wav` — peak 5039, 91% ativo, gravado ISOLADO do emulador (sink dedicado) e posterior à ROM |
| memory_bank_atualizado | este arquivo | — |

### Gameplay FECHADO (2026-08-31) — e o que foi preciso
As duas razões do fracasso anterior eram reais e foram resolvidas:
- **Game over antes da captura**: settle reduzido (`--frames 5`) captura com o
  jogo vivo. Botão 1 = tecla **`z`** (descoberto empiricamente: mudou 53,9% da
  tela ao sair do game over).
- **Limiar global mal calibrado**: substituído por rastreamento do sprite (§29).
  `largest_sprite_block` acha o maior aglomerado com FORMA de sprite (6..40 px
  por lado, razão < 3 — sem isso, colunas de estrela sequestravam a medição) e
  compara com a última posição conhecida (o jogador some em frames de flash de
  invulnerabilidade).

**Prova:** `sprite_dx=+89px` após `Right`. Medição independente anterior no par
`mv.png → mv_step1.png`: mesmo bloco de 96px indo de x[54..67] para x[191..204].

### Aviso de harness (L012)
Uma captura pegou a **janela errada** (área de trabalho 2560x1080, conteúdo
pessoal) e passou no detector de vacuidade — variância 401 > 40. Foi apagada.
`screenshot_semantic_gate.py` reprovou corretamente pela regra de desktop.
Causa: instância anterior do emulador viva (`--keep`) confundiu a busca de
janela. Encerrar o emulador entre capturas é obrigatório.


## L012 — 15 capturas de desktop no acervo (privacidade + evidência falsa)

`spectacle -a` fotografa a janela ATIVA. Com o emulador sem foco (ou instância
zumbi), a "evidência" virava um screenshot da área de trabalho — que passa no
detector de vacuidade. Duas dessas comparadas entre si produziram
**"interação provada" medindo o desktop mudando**, não o jogo.

Encontradas **15** capturas 2560x1080 em `out/evidence/`, várias de sessões
anteriores (`boot_v002.png`, `gameplay_A.png`, `tela_base_final2.png`…).
Todas apagadas — podiam conter conteúdo pessoal do usuário.

`capture_evidence.py` agora: (a) recusa iniciar com outra instância viva;
(b) valida o tamanho de CADA captura (principal e de passo), descarta o arquivo
se for desktop e refaz com re-foco. Regra: SMS_GLOBAL §30.

## Estado final dos eixos: 7 de 7 fechados

Todos com artefato posterior à ROM `bacf9993f2de` e bundle selado.

### Áudio (2026-08-31) — e o falso negativo que quase virou "conserto"
Primeira captura veio **100% silenciosa**. Diagnóstico inicial: "quebrei o
áudio ao mexer nos sprites". Antes de tocar em qualquer linha, bisseccionei as
ROMs históricas do changelog:

| ROM | peak | ativo |
|-----|------|-------|
| v042 (pré-mudanças) | 5060 | 93% |
| v043 | 5096 | 92% |
| v045 | 4880 | 99% |
| v046 | 5098 | 88% |
| v047 (= ROM atual, mesmo sha256) | 4985 | 95% |

**Todas com som, inclusive a atual.** A ROM nunca esteve muda: a captura é que
estava adiantada — gravou antes de a música entrar em regime. Recaptura da mesma
ROM: peak 5039, 91% ativo. **Nenhuma linha de áudio foi alterada.**

Lição L014 / §31: antes de "consertar" o alvo, confirme a ferramenta de medição
contra um caso conhecido bom. Bissecção em artefatos históricos é mais barata
que editar código no escuro.

### Privacidade na captura de áudio
Gravar o monitor do sink padrão capturaria TODO o áudio da máquina. A ferramenta
move o fluxo do emulador para um sink NULO dedicado, grava só esse monitor e o
remove ao final (verificado: 0 módulos residuais).


## L011 fechada (2026-09-01) — corretude da tela vira medição

A dúvida que restava: "a tela mostra a arte CERTA?". Duas tentativas de detector
universal de ruído falharam e estão registradas para não serem repetidas
(riqueza de cor por bloco, entropia de adjacência, unicidade de bloco — todas
reprovam arte autoral detalhada ou não separam o ruído real).

O que funciona é comparar com a FONTE: `audit_render_fidelity.py` extrai a
estrutura de `res/sprites/hero.png` e a procura na captura.
- Capturas limpas: **100,0%** de coincidência estrutural.
- Telas de ruído: 46,1% (`tela_funcional`, a evidência da F6), 53,3%, 56,7%.

Prova registrada em `out/evidence/render_fidelity.json`: a arte autoral do
herói está na tela, em [53, 156], com 100,0%.


## L009 fechada (2026-09-01) — o instrumento é que mentia

L009 concluía que a cena travava **dentro de `SMS_loadTiles`**. Probe
`_laboratorio/loadtiles_hang` com marcadores `volatile` impressos NA TELA
(dispensa o DAP, evitando a armadilha do prefixo `$` do item 1 da própria lição):

| variante | M1 | M2 | M3 | texto |
|---|---|---|---|---|
| display LIGADO no load (condição histórica) | A1 | B2 | C3 | `LOADTILES OK` |
| display DESLIGADO | A1 | B2 | C3 | `LOADTILES OK` |

**`SMS_loadTiles` nunca travou.** O diagnóstico se inverteu porque o marcador
sem `volatile` era eliminado pelo SDCC — exatamente o item (2) da mesma lição.

`audit_debug_markers.py` entrou no pré-gate do build e encontrou **7 marcadores
sem `volatile`** neste projeto (`probe_hp/score/over` + 4 em `probes/main_demo.c`),
todos sob o mesmo risco. Corrigidos.

### Eixos recapturados contra a ROM com os marcadores corrigidos
O rebuild rebaixou tudo (§26) e a evidência foi refeita: boot limpo,
`sprite_dx=+49px`, fps média **59,8** (`constante_50_60=true`), áudio peak 4973 /
94% ativo. Bundle selado com 4 artefatos.

A captura de áudio veio silenciosa 3× e a ferramenta **se recusou a concluir**,
mandando confirmar contra ROM histórica (§31) — na repetição veio com som.
O gate preferiu não afirmar a afirmar errado.


## L007/L008 fechadas (2026-09-01) — e uma correção incômoda

**L007** tinha dois itens abertos, agora em código:
- *"próximo passo: recorte por marcador"* → resolvido melhor com
  `import -window <id>`: alveja a janela por ID, então capturar o desktop deixa
  de ser possível. E vem sem moldura (256×217 contra 283×282).
- *"foco precisa ser VERIFICADO antes de cada tecla"* → `press_keys` confere
  `xdotool getwindowfocus` e reativa até concordar; falha alto se não conseguir.

O shim de libavcodec **continua necessário**, mas só para o fallback `spectacle`
(verificado: `.62 → .63`, e o sistema só tem a `.63`). O caminho padrão não
depende mais dele.

**L008 — correção do próprio claim.** A lição afirmava *"cena 01 funcional e SEM
GLITCHES"* citando `tela_funcional.png`. É falso: essa captura é uma tela de
**ruído** — 26,8% dos blocos 8×8 com ≥8 cores e só 46,1% de coincidência com a
arte autoral. A moldura de lixo de VRAM estava lá desde sempre (name table nunca
limpa) e ninguém olhou. O claim era falso quando foi escrito, e sustentou a F6.

**Ganho colateral:** com a área de jogo derivada do hardware (canvas 256×192
ancorada sob a moldura) em vez de fração chutada, o gate de lixo passou a pegar
também o ruído FINO — `f1_sprite_visivel` foi de 2,3% (passava) para 26,1%
(reprova). Era o limite residual declarado na L011.


## Correções de governança (2026-09-01, ao fechar L007/L008)

**Colisão de IDs de lição.** As lições novas nasceram com IDs `L010..L014` que o
arquivo da fundação já usava para OUTRAS lições — citações como "§27 (L010)"
apontavam para duas coisas diferentes. Renumeradas para **L015..L019**;
`audit_doc_sync` passou a exigir unicidade de ID entre arquivos de curadoria, e
o gate imediatamente pegou uma duplicata restante (L006 nos dois arquivos, agora
fundida na original).

**§26 estava estrita demais.** Rebuild que produz o **mesmo binário** (sha256
idêntico) rebaixava os eixos — mas evidência de um binário idêntico continua
mostrando aquele executável. A demoção passou a comparar **conteúdo**, não mtime.

**Brecha fechada em `reconcile_claims`.** O eixo áudio aceitava qualquer `.wav`
posterior à ROM, mesmo **silencioso**. Eu mesmo caí nisso: marquei `audio: true`
com um wav de `peak=0` e o gate aprovou. Agora exige sinal (`peak > 0`), com
caso no self-check. Áudio recapturado de verdade: peak 5031, 93% ativo.

**Regressão pega pelo gate de grandezas.** A linha que eu escrevi no `AGENTS.md`
para descrever o próprio gate listava os números do Mega Drive como exemplos, e
o gate — corretamente — os leu como afirmação. Reescrita. Como o gate não rodava
automaticamente, entrou no `SMS_STRICT`.
