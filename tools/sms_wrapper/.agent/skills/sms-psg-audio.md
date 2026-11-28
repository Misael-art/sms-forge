# skill: sms-psg-audio

## Verdades
- SN76489: 3 canais de tone + 1 de noise (branco OU periodico; bit2=1 (modos 4–7) e
  branco; bit2=0 (modos 0–3) e periodico; bits 1..0=3 usam tone ch2). PSGlib = driver padrão
  (`PSGPlay`, `PSGSFXPlay`, `PSGFrame`/`PSGSFXFrame`,
  `PSGSetMusicVolumeChannelsAttenuation` — confirmados no header).
- `audit_psg_quality.py` mede politicas de eventos PSGlib simples; o contrato
  e os limites estão em `sms-psg-composition.md`. PASS não aprova musica/AAA,
  e sinal positivo de `audit_audio.py` não comprova notas/mix corretos.
  Auditar proveniência, capturar e escutar trechos alinhados em runtime.
- Arbitração música × SFX declarada no TDD (4 canais só).
- SFX toca no canal **autorado** no manifesto
  (`doc/audio_provenance_manifest.json`). Canal errado derruba o mix;
  cooldown não recupera (L041). Gate: `audit_psg_channel_binding.py`.
- Samples PSG comprimidos custam ROM e timing — medir.
- PSGlib faz loop no `PSGEnd`. N cópias do mesmo frame não tocam nada
  extra. Meça redundância antes de cortar feature (L051).
  Gate: `audit_psg_redundancy.py`.
- YM2413 (FM unit/JP): opcional. Jogo precisa funcionar sem FM, sempre.
- Atualização de áudio entra no orçamento do frame junto com VRAM.

## Prova em sessão privada (§93)

`capture_audio.py --session ID --seconds 8 --out audio` captura apenas o sink
da própria sessão. Boot começa muted; rota do PID exato precisa estar
confirmada antes do som. Mute/rota ausente ou divergente reprova, sem captura
do monitor padrão. Duração efetiva deve alcançar 95% da pedida. A ponte
mantém fluxo/zeros durante pausas; feche por ID e descarregue sink após a JVM.
Vídeo por stepping não inclui áudio. Capture sinal separadamente e compare
trechos alinhados para fidelidade; peak positivo não prova música/notas certas.
Não liberar música só por gate de sinal ou teste silencioso de outra ROM.

## Eventos de combate e catálogo (L041/L058/L078–L081/L093)

Receita do Mugenesis: fila limitada, idade máxima, relógio declarado,
overflow/expiração separados e política no adaptador do consumidor. Ao
implementar no SMS, dimensionar pool/custo no Z80 e testar canal ocupado,
mute, pausa, wrap, fim de round e evento antigo. O TTL de 6 VInts do doador
não é default SMS. Grupo 0 do SND não significa voz universalmente.

Soundtest enumera entradas reais, origem/grupo/amostra e categorias vazias.
Lista textual não prova áudio integrado. BGM/SFX/cue compartilham quatro
canais; consultar PSGlib.h antes de implementar play, pause/stop ou arbitragem.
A espera de ACK do XGM2 pertence ao driver MD: copiar a distinção intenção/
estado apenas se o driver SMS realmente a exigir. Fonte e decisão:
`doc/curation/2026-10-24_mugenesis_rev2.md`.
