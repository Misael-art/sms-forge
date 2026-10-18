# 11-gdd — luta_mugen

> Design e escopo. **Autoridade #2 — "se não está no GDD, não entra."**
> Aprovado por Misael em 2026-09-25 (caminho A: conversor com classes de
> fidelidade + runtime interpretador de tabelas). Briefing de origem:
> `Mugenesis/BRIEFING_AGENTE_LUTA_MUGEN_MEGA_DRIVE.md` — técnica doada para
> MASTER SYSTEM; o alvo aqui NÃO é Mega Drive.

## Pitch (1 frase)
Um MOTOR que consome arquivos MUGEN reais (`.def/.sff/.air/.cns/.cmd/.act/.snd`)
e produz lutadores, palcos e som jogáveis no Master System — provado com
`ken_masters_adv` vs outro lutador por dados, melhor de três rounds, sem tocar
no C do núcleo.

## Gênero declarado
fighting
(eixos congelados: hitboxes, startup_active_recovery, hitstop, rounds, specials, guard)

## Loop central
Aproximar/afastar → escolher normal ou especial → o oponente guarda ou leva
hitstop/knockback → barra de vida cai → KO → próximo round → melhor de 3.
Em cima deste loop: **loop de autoria** — trocar o arquivo de dados de um
lutador muda sprites, paletas, animações, frame data e especiais no build, sem
editar o runtime.

## 5 Leis Fundamentais — como este jogo atende
- **Agência**: d-pad move/pula/agacha, B1 soco, B2 chute, recuar = guard; cada
  input produz transição de estado legível no lutador comandado.
- **Feedback**: hitstop (frames congelados, valor por tabela de dados), faísca
  de impacto em sprite, SFX PSG no mesmo frame do contato, barra de vida caindo.
- **Fluxo**: no MVP, adversário dummy/espelho (IA mínima); a difficulty curve
  completa é pós-MVP declarada. O fluxo de autoria sobe: S2 (1 parse) → S5
  (luta) → S6 (contrato provado).
- **Consistência**: o mesmo arquivo de dados compila tabelas byte-idênticas
  (conversor determinístico com `--self-check`); o mesmo comando no mesmo
  estado produz o mesmo startup_active_recovery, sempre.
- **Recompensa**: round ganho → melhor de 3 → tela de resultado com revanche;
  no plano do motor: ver seu arquivo MUGEN virar lutador jogável.

## O que é o produto (contrato do motor)

```
tools/sms_wrapper/mugen2sms/   ← O MOTOR (lógica de build/transformação só vive aqui)
  inventory → parsers → ir → analysis → converters → generators → validate → reports
SMS_projects/luta_mugen/       ← CONSUMIDOR: runtime Z80 que INTERPRETA tabelas compiladas
```

- **IR não conhece SMS; generators não leem MUGEN.** (regra herdada do
  `mugen2sgdk_forge` do workspace Mega Drive, provada nas etapas E0–E3.)
- Parsers/IR do forge MD são **copiados** no S0 com SHA registrado
  (`doc/provenance_doacao_md.md` + `rascunho/`); a partir daí o fork SMS evolui
  próprio. Nenhum material ativo aponta para o workspace vizinho.
- **Não é VM de CNS.** O conversor destila estados CNS→tabelas por padrão
  reconhecido (estados, physics, command→special). O que não destila é
  classificado `manual` ou `unsupported` no relatório de fidelidade — gap
  visível, nunca silêncio.
- Classes de fidelidade obrigatórias em TODO recurso:
  `direct | approximate | manual | unsupported` (gate novo:
  `mugen2sms/analysis/fidelity.py` (relatório; não existe auditor standalone com aquele nome)).
- Núcleo do runtime não conhece nomes: estados, frames (duração, metasprite,
  offset), clsn1/clsn2 → hurtbox/hitbox, janelas startup_active_recovery,
  comandos (buffer QCF+etc → specials), paletas e SFX vêm de tabelas
  compiladas offline dos arquivos MUGEN.
- Física (gravidade, knockback, hitstop) em inteiros/Q8.8; campos análogos do
  MUGEN (`velocity`, `changevelocity`) alimentam os dados; o resto é constante
  declarada no TDD.

## MVP — fatia golden travada

**Pilot:** `chars/street-fighter/ken_masters_adv.zip` (Ken/Chok). Autorizado
pelo usuário para **uso local** na decisão MD 2026-09-22; redistribuição segue
bloqueada.

**Direção visual (decisão de 2026-09-26):** Ken Masters ADV, baseado em sprites
ripados da CPS2 arcade, é o modelo de referência de proporção e acabamento.
O Ryu atual (`ryu_kang.zip`) vem de sprites de um bootleg de NES e permanece
somente como piloto técnico para estudo de paleta P1/P2, vínculo de metadata e
cache de animação. Ele não é referência estética nem arte final. Antes de
produzir o roster completo, substituir Ryu por outro modelo coerente com Ken
Masters ADV/CPS2. O estudo técnico com Ryu continua válido e não bloqueia o
avanço da engine.

| # | Cena | Escopo em 1 linha | Status |
|---|------|-------------------|--------|
| 01 | `probe_import` | Ken renderizado de dados convertidos, pose-por-pose em tela estática — prova tileset/paleta/metasprite | documentado |
| 02 | `ken_vs_dummy` | Ken (1P humano) vs dummy técnico Ryu: andar, agachar, pular, soco, chute, guard, dano, hitstop — prova FSM interpretador + hitboxes | testado_em_emulador parcial (T10; input range-synced e DAP 2×120 s PASS; KO/reset e partida longa pendem) |
| 03 | `golden_slice` | 2 lutadores por dados (Ken + 2º modelo visualmente coerente; seleção final após estudos técnicos), rounds melhor-de-3, timer, HUD em tiles, 1 especial cada (QCF+B1) — prova do contrato | buildado parcial (T10: dados Ken/Ryu simultâneos para prova técnica; rounds, especial de Ryu e troca só por `.def` ainda sem prova) |

**Prova do contrato (gate automatizado, não narrativa):** trocar o `.def` do
2º lutador no build muda personagem, paleta, frame data e especial sem editar
nenhum `.c` do núcleo.

## Padrão de entrega vigente — decisão humana 2026-09-26

A nova referência Sangokushi III supersede o teto universal 1:4/48 px da decisão
anterior. Norma: `../../../doc/05_technical/mugen_engine_standard.md`;
contrato executável: `engine_quality_contract.json`; revisão: `16-engine-review-2026-09-26.md`.
Piloto de escala e limites observados: `17-scale-pilot-2026-09-26.md`; o piloto
é `measured`, não libera arte completa nem aceita a cadência de combate.
O corte Ryu nesse relatório é um bootleg NES usado para estudo técnico de
paleta/runtime; não aprova sua coerência visual. A produção completa de arte
aguarda substituição por um modelo alinhado ao Ken Masters ADV/CPS2.

- Corpo idle opaco: 45–55% da área útil declarada. Perfil inicial 160 px úteis
  em canvas 256×192 → 72–88 px; exceções por pose e contexto registradas.
- Metasprite TALL 8×16, transformação uniforme por personagem/cena, pivots e
  CLSN preservados; largura/altura derivadas da arte e coreografia medida.
- SAT emitida <=64 e cada linha <=8. Testar sprites esparsos, deduplicação,
  streaming e o degrau seguinte antes de reduzir qualidade.
- **Decisão humana 2026-09-29 (opção 3): flicker mínimo e sem glitch é o padrão
  do motor a 72–88 px.** Zero flicker foi bloqueado por hardware com medição:
  limite inferior sprite-only 9–10 sprites/linha no par idle (VDP mostra 8) e
  lutador em BG com posição de 1 px limitado a ~12 px/s (memory bank). O VDP
  continua recebendo <=8 por linha e <=64 na SAT: o agendador multiplexa só as
  linhas onde o par disputa a cota. Aceite de imagem: `audit_render_glitch.py
  --mode flicker` PASS (nenhum pixel fora da pose legal; toda peça coberta em
  cada janela de 8 quadros; sem resíduo, sprite perdido ou flash de boot após o
  primeiro conteúdo). Em palco claro, a comparação usa placa RGB de fundo
  subtraída das imagens e do framebuffer, ignora o HUD dinâmico e registra
  cobertura por lutador; janela de 8 quadros não significa flicker zero.
  Zero flicker continua sendo meta onde a geometria permitir
  (ex.: lutadores em linhas distintas), nunca à custa da altura 72–88 px.
- **Decisões do Lote C (2026-09-30), registradas antes do código do round.**
  O runtime anterior deste projeto (`src/main.c`) já compilava o round em 99
  segundos. Não há `Time` autorado num `system.def` deste corte. O round
  integrado conta **99 segundos em quadros da ROM NTSC: 60 quadros por
  segundo**. PAL não herda 60 Hz e não está medido neste lote.
  Empate (vidas iguais no timeout) e KO duplo não marcam ponto: o vencedor
  do round fica 2. A partida é melhor de três; o primeiro a 2 pontos vence.
  Rematch: borda nova de B1 do P1 com a partida encerrada.
  Nesta fatia integrada os controles aceitos continuam **B1 = soco, B2 =
  guarda, direções mascaradas**. O mapa de produto (B1 soco, B2 chute,
  recuo = guarda) segue sendo o alvo do GDD e não é o que esta ROM lê.
  Palco deste lote: uma arena técnica estática, câmera fixa, sem scroll.
  Planta em `res/stage/planta_arena.png`; tiles em
  `res/stage/arena_tecnica.png`. Piso na linha de pixels 128, âncoras
  x=96 e x=152, HUD nas linhas 0–1 da name table, padrões de fundo a
  partir do tile 256 (a metade baixa permanece o pool dos lutadores).
  No máximo 2 células de HUD por VBlank. Arte final de cenário CPS2 não
  entra neste lote.
- Perfil 1:4/48 px do conversor atual é `legacy_probe_quarter`: preservado
  para reproduzir T10, explicitamente bloqueado para delivery.
- Capacidade alvo de ROM 1 MiB, banking Sega de 16 KiB e provas de fronteira.
  Não há obrigação de inflar cada jogo até 1 MiB; há obrigação de provar a capacidade.
- PSG com prioridades e restauração é base. H-scroll, raster, PCM e FM são
  expansões condicionadas ao ganho/custo e contexto, com fallback obrigatório.
- AAA exige resultado audiovisual/jogável aprovado; implementar técnicas não
  autoriza o claim. T10 permanece prova técnica, não atende ao piso novo.

## Pipeline verificável (E do MD → S do SMS)

| Etapa | Entrega | Critério de aceite |
|---|---|---|
| S0 | baseline + cópia doada MD registrada com SHA | inventário do que veio do forge MD |
| S1 | inventory do acervo (somente leitura) | zips lidos sem erro, determinístico, `--self-check` ok |
| S2 | parsers+IR na cópia; `ken_masters_adv` parseia inteiro; **gate de input do emulador ativo** | testes de contrato com fixtures sintéticos |
| S3 | analysis SMS: Ken medido contra VDP/RAM/VRAM/metasprite/PSG | relatório com contagem por classe; `unsupported` é número, não silêncio |
| S4 | converters+generators: Ken → tileset/metasprites/paletas/tabelas/SFX | `audit_validate_resources`, `audit_sprite_line_sim`, `audit_provenance`, `audit_luma_floor` |
| S5 | runtime: cena 02 (Ken vs dummy) ROM no emulador | boot determinístico, input provado, evidência selada ao SHA da ROM |
| S6 | cena 03 golden slice + prova do contrato | worst-frame medido dentro do orçamento, fps 50–60, claims reconciliados |

## Orçamento e restrições de hardware (medir, não supor)

- **Sprite**: `SMS_addMetaSprite` (SMSlib.h:215) com `SPRITEMODE_TALL`
  (SMSlib.h:57); teto 8/scanline e 64/SAT é bloqueador no `analysis`. A arte
  MUGEN (Ken ~centenas de px por pose) será a primeira vítima real da medição;
  `approximate` (recorte/compactação) só com relatório de deformação.
- **Paleta**: 2 subpaletas × 15 cores úteis + índice 0 transparente;
  quantização 6-bit offline com piso de contraste medido.
- **ROM**: iniciar 32 KB; banking Sega mapper (padrão MSSF2T spec-banking:
  dados em bancos declarados, `SMS_mapROMBank` com ownership do slot; upload em VBlank) declarado no TDD desde o
  início, não descoberto tarde.
- **RAM 8 KB**: pools estáticos nomeados no TDD (sprite table, estado de luta,
  input buffer, stack). Zero malloc, zero float.
- **Áudio**: `.snd` inventariado; reautoria PSG declarada (não conversão fiel
  automática de WAV), prioridade/canais conforme manifesto; PCM/FM candidatos
  segundo contrato, sem integração ao runtime nesta revisão.
- **Worst-frame**: orçamento de VBlank medido com `measure_worst_frame.py` na
  cena 03 antes de qualquer claim. (Lição aberta do MSSF2T: lá derramou; aqui o
  número é contrato desde o design.)

## Fora de escopo (explícito)

- Screenpacks/lifebars/portraits/intros do MUGEN como sistema de arquivos.
- VM de CNS em runtime (caminho recusado formalmente em 2026-09-25).
- Mega Drive: o alvo é SMS; o forge MD é referência de técnica apenas.
- Team mode, multi-stage, roster além dos 2 do golden slice, select screen,
  continue/credit, SRAM, 6 botões, throws, dizzy, Super Combos.
  FM/YM2413 e PCM pertencem agora ao portfólio experimental, fora do baseline PSG.
- IA avançada (dummy/espelho bastam no MVP).
- Trilha completa; mais de um palco.
- Licença: arte real convertida nunca entra no Git nem em distribuição pública — fica em
  `out/local_study/` (gitignored); fixtures de teste sintéticos são os únicos
  dados MUGEN-like no repo.
- Números de Mega Drive afirmados como lei do SMS (gate `audit_hardware_constants`).

## Benchmarks (régua, não fonte)

- `tools/mugen2sgdk_forge` (Mega Drive): arquitetura inventory→IR→converters→
  generators e política de fidelidade/licença. Técnica doada, código cópiada
  com SHA, nada compilado aqui.
- MSSF2T (este workspace): FSM de luta em SMS, contrato de escala 32×64 /
  SPRITEMODE_TALL, banking, pipeline de evidência — e suas dívidas abertas
  (worst-frame derramado, eixo input reprovado com WIP) que este projeto
  ataca cedo por decisão de design, não por acidente.
- HAMOOPIG/SSF2T arcade: frame data, leitura de silhueta, densidade — só como
  régua de qualidade.

## Política de licença e proveniência

- `Base de Estudo/` é somente leitura; nenhum zip original entra no Git.
- Derivados de Ken/2º piloto vivem em `out/local_study/` (gitignored) até
  confirmação humana de redistribuição; `license_status` máximo: `candidate`.
- Cada ativo derivado tem entrada em `doc/asset_provenance_manifest.json` com
  `source_kind` e SHA da fonte MUGEN — proveniência declarada ou não entra.

## Teto de claims aprovado

`protótipo jogável de engine de luta MUGEN→SMS dirigida por dados` — com época
visual no máximo `technical_candidate` até o gate de evidência da S6. Acima
disso só com evidência selada. **Nunca** "MUGEN no Master System" como claim
de paridade; `ready_for_aaa` = false.
