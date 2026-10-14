# skill: sms-psg-composition — composição e auditoria de eventos PSG

## Hardware e fontes

SN76489/SMS: três canais de tone e um de ruído; atenuação 0 é máxima,
15 é mudo. O controle do ruído usa `0xE0 | mode`:

- **Bit 2 = 1: branco**, modos 4–7.
- **Bit 2 = 0: periódico**, modos 0–3.
- Bits 1–0 escolhem a taxa; valor 3 usa o período do tone ch2.

`PSGlib.c` envia os latches ao PSG sem inverter esse bit. A implementação
local fixada de BlastEm, `psg.c`, guarda `value & 0x4` e aplica o feedback
LFSR de ruído branco quando esse valor está ativo. Conferir fontes e hashes
no registro da curadoria; não deduzir o modo pelo nome do efeito.

Tone: frequência nominal NTSC = `3579545 / (32 * período)` para períodos
não nulos. A unidade de tempo do stream é uma chamada ao driver. Se houver
uma chamada por VBlank, um frame por escrita corresponde a 50/60 escritas/s;
não existe equivalência universal com 16 Hz ou com um timbre específico.
YM2413 é extensão opcional; declarar suporte e assegurar funcionamento PSG.

## Estratégias de composição

Declare papel por canal: melodia, harmonia/arpejo, baixo e ruído, considerando
que há só quatro canais e que música/SFX podem disputá-los. Use durações,
contraponto, mudanças de registro, envelopes de atenuação e gates deliberados.
Arpejos rápidos, uníssono, volume sustentado e ruído periódico podem ser escolhas
válidas; escuta e intenção musical determinam se funcionam naquele arranjo.
Ruído branco curto é uma opção para caixa/prato; não é requisito universal de
percussão. Mode 3/7 acopla ruído a ch2; mudanças e SFX nesse canal afetam a taxa.

A autoria vem de partitura e decisões registradas, não de um gerador passar
num predicado. Não atribuir técnicas a jogos/compositores sem fonte específica.
PCM/PWM por escritas de volume exige medir custo Z80 e budget de frame; o chip
não possui canal PCM dedicado. Não supor que essa técnica ocupa todo o Z80.

## Política medida e seus limites

`audit_psg_quality.py` avalia a primeira passagem de streams PSGlib simples.
Tone exige latch baixo + dado alto `0x40`–`0x7F` contíguos. Low-only, high-only
e dados após latch de volume/ruído são recusados: são escritas possíveis no PSG,
mas estão fora deste modelo. Substrings comprimidas também são recusadas.
Nenhum WAIT é consumido como frequência para fabricar preview ou PASS.

| Política | Métrica atual | Limite |
|---|---|---|
| M1 | Gap **médio** ≥ 2 frames entre escritas de período em canais com ≥ 8 escritas | Reescrita do mesmo período não é nota nova; não verifica gap mínimo |
| M2 | ≥ 2 atenuações não mudas por canal elegível | Cardinalidade não prova envelope/ataque |
| M3 | Uníssono ≤ 50% dos instantes com eventos e ≥ 2 tones não mudos | Não pondera duração entre instantes nem mede frames sustentados |
| M4 | ≥ 50% dos comandos de ruído em modos 4–7; variedade de volume | Conta comandos, inclusive quando ruído está mudo; não julga percussão |
| M5 | Primeira passagem ≥ 250 frames | 5 s a 50 chamadas/s ou ~4,17 s a 60; não mede loop audível |
| M6 | ≥ 2 tones com ≥ 8 escritas de período | Não prova simultaneidade ou audibilidade |
| M7 | Algum gap médio ≥ 8 frames em canal elegível | Não prova nota sustentada ou andamento percebido |
| S1 | Primeira escrita não muda versus última escrita de volume na ordem temporal | Última pode ser mudo; multicanal usa ordem global, sem provar fade de cada canal, mix ou clique |
| S2 | ≤ 45 frames | Tempo em segundos depende da cadência e intenção do efeito |

Esses limiares são política do projeto, não leis do hardware nem critérios
universais de música. Exceções exigem decisão registrada e evidência auditiva,
sem alterar números para obter um verde. **PASS de eventos não aprova música,
fidelidade, mix, gameplay ou qualidade AAA.**

## Produção e prova

- Partitura antes de bytes: notas, durações, canal, ritmo, loop e efeito desejado.
- Sustentação usa WAIT/hold `0x38`–`0x3F`; não duplicar bytes para preencher ROM.
- `0x01` registra loop point; comportamento no `0x00` depende do modo do driver
  (`PSGPlay` contínuo versus reprodução uma vez). Medir loop real e transição.
- `PSGSFXPlay` usa a máscara do canal autorado no manifesto (L041). Conferir
  header local antes de aplicar APIs de atenuação e medir a disputa com música.
- `make_psg_assets.py` é autoramento offline. Não regenerar automaticamente
  assets existentes ao corrigir o gerador; os hashes antigos ficam históricos.
  Preview WAV é modelo aproximado, não execução da ROM nem certificação PSG.

```bash
python3 tools/sms_wrapper/audit_psg_quality.py --project SMS_projects/<p> \
    --json SMS_projects/<p>/out/logs/psg_quality.json
python3 tools/sms_wrapper/audit_psg_quality.py --self-check
```

Capturar em sessão privada com `capture_audio.py`; `audit_audio.py` verifica
sinal, não música certa. Escutar trechos alinhados, comparar referência,
checar duração, notas, loop, mix e interferência de SFX. Só a combinação de
proveniência, política, escuta e runtime sustenta o eixo áudio da entrega.
