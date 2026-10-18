# Mapa de controle SMS por tempo de pressão — proposta — 2026-09-30

**Status: decisão de escopo do usuário (2026-09-30: sem golpes médios, 2 tiers) com
parâmetros ainda não validados.** O GDD (autoridade #2) não foi alterado
nesta passagem; o limiar T e a responsividade exigem jogador e emulador. Origem da
ideia: o usuário, 2026-09-30 — como lutas de MS/NES, toque rápido = golpe
fraco, segurar mais uns milissegundos = golpe forte; os golpes derivam dessa
lógica.

## Fatos de hardware (autoridade #8, `SMSlib.h:296-302`)

O pad tem UP/DOWN/LEFT/RIGHT, `KEY_1` e `KEY_2` (`START` é alias de `KEY_1`).
Diagonal = duas direções juntas (o `fight.c` já usa Down+Back para a guarda).
Só direções **opostas** são impossíveis. `converters/sms_cmd.py` e `analysis/fidelity.py` herdavam "1 botão" e "diagonal
impossível" — contradizia o header. **Corrigido em L093** (`SMS_GLOBAL §78`):
diagonal passa a ser a união de duas direções no blob `_CMD_` (formato inalterado;
golden atualizado de propósito); `$F` segue fora (exige máscara). O tier por
tempo de pressão ainda não entra no blob. `audit_hardware_constants.py` reprova
as duas frases.

## Mapa

| Tecla física | Tier 0 (toque) | Tier 1 (segura ≥ T) |
|---|---|---|
| `KEY_1` | `a` soco fraco | `c` soco forte |
| `KEY_2` | `x` chute fraco | `z` chute forte |

`b`/`y` (médios) são **descartados por decisão** (`ControlMap.dropped`): comandos
que só dependem deles saem como `DROPPED`, não como falha. O mapa é
configurável (`--controls mapa.json`); 3 tiers continua suportado. Política
`release_or_threshold`: T conta ticks de pressão a partir do tick do toque,
inclusive. Tecla segurada ≥ T ticks → **forte**, emitido no tick T−1 após o
toque, sem esperar a soltura. Solta antes → **fraco**, no 1º tick com a tecla
solta. Soco+chute juntos = `KEY_1`+`KEY_2`. Dois botões da mesma tecla (`a+c`)
e `s` (Start) são inviáveis.

## Escolha de T (melhor desempenho com menor perda)

Nos dois tiers o pior caso adicionado é **T−1 ticks**; o fraco típico custa só
a duração do toque (2–5 ticks). Portanto T é o único botão de ajuste: menor T =
menos espera, mas toques deliberados mais longos que T viram forte por engano.
Padrão **T = 6** (5 ticks = 83 ms no pior caso a 60 Hz; 100 ms a 50 Hz): é o
menor valor que ainda deixa um toque de 3–5 quadros no fraco. **É estimativa,
sem dado de jogador**; `INPUT_TIER_T` e `thresholds` mudam em um lugar cada.
Disparar o fraco já no toque (latência 0) evitaria a espera, mas o forte teria
de cancelar um golpe já iniciado: muda o modelo de hitbox; não adotado.

Isto **soma** ao atraso já medido no Lote C (pose visível em 26 quadros, hitbox
em 125 para P1), ainda não aprovado. Não há medição em emulador do custo real.

## Resultado no Ken (`ken_masters_adv.zip`, 70 entradas de comando)

Leitura estática; saída em `out/local_study/study_2026-09-30/` (gitignored).

| Mapa | OK | DEGRADED | DROPPED | BLOCKED | Observação |
|---|---|---|---|---|---|
| sem mapa (`sms_cmd`, antes) | 4 | 2 | – | 64 | 44 botão além do pad, 42 diagonal |
| **2 tiers a/c x/z, T=6 (adotado)** | 19 | 19 | 27 | 5 | DROPPED = só usam `b`/`y` |
| 3 tiers a/b/c x/y/z (alternativa) | 27 | 32 | – | 11 | custo: forte a 13 ticks |

Os 5 BLOCKED: 4 acordes na mesma tecla (Ashura Senkuu, que o GDD exclui como
super) e 1 golpe do estado 12000 sem hitdef alcançável. QCF passa como duas
direções + tier. `OK`/`DEGRADED` medem digitabilidade e fidelidade de
conversão, não jogabilidade nem emulador.

## Implementação de referência

`integrada/src/input_tier.c` + `inc/input_tier.h`: classificador O(1), 4 bytes
de RAM, sem divisão. Teste diferencial com gcc (`mugen2sms/tests/test_input_tier_c.py`)
contra `classify_trace()` em 900 traces aleatórios, para T = 2, 6 e 10; uma
mutação de off-by-one no C é detectada. **Não está ligado à ROM**: não foi
compilado com SDCC, o custo em ciclos Z80 não foi medido.

## O que falta para isso virar jogo

1. Atualizar o GDD com a decisão (2 tiers) e validar T com jogador.
2. Ligar `input_tier` ao runtime (hoje dispara no flanco de subida, `K_LP`/`K_HP`;
   `main.c` ainda lê B2 como guarda). Exige estados e poses de golpe forte:
   o corte atual do Ken tem só soco e chute, e o pool está em 125/128 pares.
3. Emitir o tier nos padrões de comando (muda o formato do blob `_CMD_`).
4. Medir em emulador a latência adicionada e o worst-frame do `input.c`.
