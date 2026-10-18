# Trilhas-alvo — port SSF2T SMS (`audio/music/`)

> A ROM de Master System toca **PSG (SN76489 via PSGlib)**, não MP3: o que
> entra no cartucho é stream PSGlib. Referências externas (MIDI de fã,
> gravação) vivem em `reference/` COM proveniência registrada (URL + sha256
> no README.md ao lado) e servem só de molde para transcrição —
> `reference_only`, nada delas entra na ROM. Partitura PSG emitida por
> `tools/gen_music_ken_ref.py` (transcrição) ou por geradores autorais;
> proveniência de cada blob em `doc/audio_provenance_manifest.json`.
> Arbitragem música×SFX vai no TDD do projeto.

## Temas necessários (ordem de prioridade do teste)

1. **Guile Stage** — tema do cenário pedido (prioridade máxima: é o palco do teste).
2. **Character Select** — tela de seleção.
3. **Versus / VS screen jingle** — antes da luta.
4. **Title / attract** — abertura (quando a lacuna de arte da title fechar).
5. **Continue / Game Over / Ranking** — fluxo de telas.
6. **Ending (Ken, Guile)** — cenas de final.
7. **SFX**: hit, block, KO, Hadouken, Sonic Boom, Flash Kick, Shoryuken,
   select cursor, round call ("ROUND 1 / FIGHT!" via texto + jingle).

> **Ken Stage — FEITO**: `res/audio/music_ken_stage.psg` (917 B, stream
> PSGlib) é transcrição do tema do Ken Stage (SSF2T) feita por
> `tools/gen_music_ken_ref.py` a partir da referência MIDI em
> `reference/` (proveniência no README.md). Saiu desta lista de pendências.

## Restrições SMS a respeitar na transcrição/composição

- 3 canais tone + 1 noise; música precisa funcionar sem YM2413 (FM opcional).
- Sem `float`; tabelas de nota em ROM, pools estáticos (RAM 8KB).
- Referência de escuta: MIDI de fã arquivado em `reference/` com proveniência
  (URL + sha256); gravações do arcade ficam fora do repo. A partitura PSG é
  transcrição para SN76489 e é o que entra na ROM.
