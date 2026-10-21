# 11-gdd — pulso_de_cristal

> Design e escopo. **Autoridade #2 — "se não está no GDD, não entra."**

## Pitch (1 frase)
Uma experiência musical dirigida no SN76489: num vale de cristais silenciosos a
canção é a física do mundo, e o jogador só dirige a progressão dos 4 atos —
a trilha autoral PSG é a entrega central e o objeto de maestria.

## Gênero declarado
`musical_experience_demo` (experiência musical dirigida). **Não há família
correspondente em `doc/game-design/matriz_genero.json`**, então `specialization` permanece
`indefinido` em `.mddev/project.json` — decisão registrada, não omissão.

## Propósito dual (explícito)
1. Entregar uma ROM que roda a 50/60fps com trilha autoral passando os gates
   de qualidade PSG (M1–M7, S1–S2) e aprovada por escuta humana.
2. Treinar a trilha `audio` do registry de maestria: técnicas L078 promovidas a
   `emulador_provado` com evidência, `arbitracao_canais` (A02) comprovada,
   emenda da skill `sms-psg-composition.md` via curadoria.

## Loop central
O jogador vê uma cena viva cujo ritmo visual vem da música → o HUD (medidor de
compasso, barras de ressonância) reage a eventos do stream → ele aperta Start
para avançar o ato, Select para excitar um cristal (SFX com arbitração medida),
Pause para silenciar (fade por atenuação) → a consequência é simultaneamente
sonora e visual → próxima cena começa pelo mesmo contrato (trilha própria).

## Controles
| Tecla | Ação |
|-------|------|
| Start | avança ato (com fade/silêncio como transição) |
| Select | dispara SFX `sfx_crystal` no cristal em foco |
| Pause (start+down não; uso: tecla Pause) | `PSGSilenceChannels` → reprise com `PSGRestoreVolumes` |

Sem input rítmico, sem timing judgment — decisão de escopo (ver Fora de escopo).

## 5 Leis Fundamentais — como este jogo atende
- **Agência**: Start/Select mudam o mundo de forma visível e audível (avanço de
  ato com transição; cristal responde com SFX dentro da arbitração declarada).
- **Feedback**: cada tecla produz mudança no HUD/stream no mesmo frame do
  handler; silêncio ≠ ausência de resposta — é resposta declarada.
- **Fluxo**: tensão musical cresce por ato (title lírico → dawn → storm → eco);
  a "competência" treinada é do agente, não do jogador.
- **Consistência**: boot determinístico; mesma ROM → mesmo stream → mesma
  sequência de eventos (streams são dados, não aleatoriedade de runtime).
- **Recompensa**: cada ato revela o motivo-âncora transformado (identidade
  motivica), recompensa perceptível a quem escuta.

## Cenas planejadas
| # | Nome | Escopo em 1 linha | Trilha | Status |
|---|------|-------------------|--------|--------|
| 01 | título | vale adormecido; tema-âncora exposto | `music_title.psg` | documentado |
| 02 | aurora | primeira luz; lirismo em colcheias | `music_dawn.psg` | documentado |
| 03 | tempestade | motor rítmico, percussão branca | `music_storm.psg` | documentado |
| 04 | eco + créditos | reexposição variada do tema; silêncio final | `music_eco.psg` | documentado |

## Trilha — contrato de composição (áudio como cidadã de primeira classe)
- 4 faixas **autorais** (origem `autoral_composicao` no manifesto de
  proveniência; sem referência externa), cada uma ≥250 frames (M5), alvo
  400–900 frames; ≥8 compassos com seções A/B.
- Papéis por canal declarados por faixa (lead / arpejo-contraponto / baixo /
  percussão) — a declaração deve ser **medida no stream** (L079), não no texto.
- Técnicas L078 obrigatórias no corpus (não necessariamente todas em cada
  faixa): arpejo multiplexado (~30 Hz), envelope de volume, percussão de ruído
  branco gateada, contraponto (uníssono ≤50% — M3), camada que respira
  (≥8 frames — M7).
- 3 SFX: `sfx_crystal`, `sfx_crack`, `sfx_chime` — decay ≥6 passos (S1),
  ≤45 frames (S2), canal literal declarado no manifesto (L041).
- Partitura JSON (superfície de composição) precede o emissor de bytes em todo
  ciclo; revisão de qualidade musical é humana — gates medem piso, não beleza.

## Fora de escopo (explícito)
- Jogo de ritmo / timing judgment de input
- YM2413/FM, samples/PCM, VGM playback
- Transcrição de MIDI/qualquer referência externa (trilha é autoral)
- Multiplayer, score, difficulty, fases repetíveis com variação procedural
- Mais de 4 faixas ou mais de 3 SFX neste vertical
- Mapper/banking (cabe em 48 KB lineares; se estourar, decisão nova + aprovação)
- Arte de personagem/combate — cristais são cenário, não elenco

## Teto de claims aprovado
`protótipo de experiência musical buildado e testado_em_emulador com trilha
autoral validada pelos gates de piso PSG + escuta humana aprovada por faixa`.
Nada acima disso: sem claim de "qualidade máxima", "AAA" ou "melhor trilha" —
gates medem piso mensurável; o teto estético é opinião humana registrada.
