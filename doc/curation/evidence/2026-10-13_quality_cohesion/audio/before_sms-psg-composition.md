# skill: sms-psg-composition — padrão mínimo de áudio do agente

## O que o chip É

SN76489: 3 canais de tone (square puro, atenuação 0–15 onde 0 é o MAIS ALTO
e 15 é mudo) + 1 canal de ruído (branco ou periódico; R3 latch `0xE0|fb|per`,
**fb=bit2 → modo ≥ 4 é PERIÓDICO = assobio tonal, não percussão**).
 Não existe filtro, não existe sample nativo, não existe dinâmica de timbre
além do volume por passo de 2 dB. YM2413 (9 canais FM) é extensão OPCIONAL e
regional (JP/Tectoy): o jogo funciona sem FM, sempre, e o claim FM exige
declaração explícita.

O som "cheio" dos jogos que marcaram a plataforma NÃO vem do chip — vem de
três truques que exploram o multiplex temporal do Z80:

1. **Arpejo ultrarrápido multiplexado** (Streets of Rage): 3–4 notas do
   acorde tocadas em rotação a ~30 Hz num só canal = acorde sustentado
   percebido. A nota de cada passo vive 2–3 frames, nunca 1.
2. **Envelope de volume** (Koshiro/Sonic 1; Master of Darkness): a vida do
   canal 3 como baixo pizzicato — ataque no volume alto, queda em 3–5
   frames. Eco de mão esquerda: canal 2 repete a nota do 1 atrasada 2–4
   frames a atenuação +4–6. Sem mudança de volume NÃO EXISTE ataque, e sem
   ataque square wave é buzina de órgão.
3. **Ruído como percussão** (Sonic 1): branco (mode 0–3) — curto com decay
   rápido = caixa, longo = prato, gateado em semínimas = bumbo. Metálico
   LEGÍTIMO é periódico (Kenseiden: espada) — em música, percussão
   periódica é assobio, não bateria.

Estratégias de preenchimento: contraponto (Wonder Boy III — a melodia
transita entre ch0/ch1 enquanto ch3 faz baixo melódico que completa o
espectro do acorde); motor rítmico de baixo em colcheias com contratempo em
oitava; SFX com driver de prioridade que NÃO mata a música (Asterix — SFX
entra no canal menos ativo ou escondido no ruído; PSGlib faz isso via
máscara de `PSGSFXPlay` + `PSGSetMusicVolumeAttenuation`).
Pitch-bend de ataque em SFX (Kenseiden: nota nasce aguda e cai na afinação
em 3–5 frames) — o gerador de `sfx_shot` já faz; SFX estacionário é clique.
PWM/voice sampling (RoboCop vs Terminator) é TETO declarado, não piso:
captura o Z80 inteiro, exige medição de frame budget antes de qualquer
tentativa.

## O piso — medido, não opinião

`audit_psg_quality.py` decoda o .psg (formato PSGlib confirmado em
`sdk/devkitSMS-upstream/PSGlib/src/PSGlib.c`) e reprova:

| Cláusula | O que mede | Por que existe |
|---|---|---|
| M1 ritmo | ≥ 2 frames entre notas por canal ativo | troca a cada frame = 16 Hz = chiado; arpejo legitimo roda em 2–3 |
| M2 dinâmica | ≥ 2 atenuações ≠ mudo por canal com ≥ 8 notas | volume constante = sem ataque, sem eco |
| M3 registro | uníssono total ≤ 50% dos frames multi-canal | 3 canais na mesma nota é buzzer, não acorde |
| M4 ruído | ≥ 50% dos eventos ch3 brancos + envelope | periódico em música = assobio |
| M5 loop | ≥ 125 frames (2,5 s @ 50 Hz) | loop de 1 s em batalha é tortura |
| M6 canais | ≥ 2 canais de tone soando | 1 canal = chip subusado |
| S1 decay | SFX termina mais baixo que começa | sem fade = clique |
| S2 duração | SFX ≤ 45 frames | SFX longo pisa o próximo evento |

Consequência operacional: **um frame por nota em três canais simultâneos não
é "arranjo denso", é o defeito M1+M3 composto** — foi exatamente o que os
geradores do acervo produziram (medido 2026-09-25: os 7 streams de música do
corpus reprovam; ver `doc/psg_quality_ledger.json`).

## Como compor dentro do piso

- Partitura antes de bytes: grade de compassos (ex.: 1 compasso = 16 frames
  @ 50 Hz), notas com duração ≥ 2 frames, cada canal com papel declarado:
  lead (envelope de ataque), arpejo/contraponto, baixo (pizzicato ou
  motor em colcheias), percussão (branca, gateada).
- O frame do PSGlib só carrega o que MUDA; sustenção é `WAIT`/hold
  (`0x38`–`0x3F`), não repetição da nota.
- Loop: `0x01` marca o loop point; `0x00` volta. Duração ≥ 2,5 s exige
  ≥ ~8 compassos de material — se não há material, escreva mais, não
  repita frames byte a byte (L051).
- SFX: 1 canal declarado no manifesto de proveniência (L041), pitch-bend de
  ataque no tom, decay de ≥ 6 passos de atenuação, ≤ 45 frames.
- Ao tocar música com SFX constante, reserve o canal: `PSGSFXPlay` com
  máscara rouba o canal MAS a música continua avançando — preveja o
  sumiço (atenuação via `PSGSetMusicVolumeAttenuation` se a lib expuser).

## Reproduzir

```bash
python3 tools/sms_wrapper/audit_psg_quality.py --project SMS_projects/<p> \
    --json SMS_projects/<p>/out/logs/psg_quality.json
python3 tools/sms_wrapper/audit_psg_quality.py --self-check
```

Evidência auditiva continua: `capture_audio.py` + `audit_audio.py` (presença)
— agora E `audit_psg_quality.py` (qualidade). Presença sem qualidade não
sustenta o eixo `audio` do claim de entrega.
