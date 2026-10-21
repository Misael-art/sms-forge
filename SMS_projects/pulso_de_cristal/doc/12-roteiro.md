# 12-roteiro — pulso_de_cristal

> Roteiro e diálogos. Autoridade #6.
> Primeiro degrau da ordem de trabalho de cena: **roteiro vem antes do
> storyboard, que vem antes da arte cara.**

## Premissa
O vale de Vetrovia congelou no último acorde — seus cristais só vibram com
canção. Uma máquina antiga, a última cantora, acorda sozinha no gelo. Ela não
fala: ela **toca**. Quatro atos é o ciclo completo do vale acordando, tempestade
e memória — e o silêncio de volta como escolha, não como falha.

## Cena 01 — título: "o vale congelado"
### Beats
1. Tela preta; primeiro `sfx_chime` isolado (pergunta).
2. `music_title` entra em piano-forte por atenuação crescente (não por camada nova).
3. Name table surge linha a linha (escrita em VBlank) — gelo "derretendo" em ordem.
4. Letreiro do título; medidor de compasso do HUD pulsa no pulso da faixa.
5. Prompt "START" só quando o stream alcança o primeiro loop point.

### Diálogos
| Quem | Fala | Tiles estimados |
|------|------|-----------------|
| — | PULSO DE CRISTAL | 16 |
| — | START | 5 |

### Intenção emocional
Solidão que respira. Direção de paleta: azul profundo + branco (≤2 subpaletas).
Direção de áudio: tema-âncora nu, melodia + respiro (M7 visível aqui).

## Cena 02 — aurora
### Beats
1. Transição: fade por `PSGSetMusicVolumeChannelsAttenuation` até 15 → silêncio
   1 s (narrativa: o vale prende a respiração) → `music_dawn`.
2. Horizonte clareja por troca de paleta em rampa degrau-por-degrau (sem
   gradiente suave — códigos 6-bit).
3. Cristais entram em ressonância: cada um acende num ataque de nota do lead.
4. Select excita o cristal em foco → `sfx_crystal` com arbitração declarada.

### Diálogos
| Quem | Fala | Tiles estimados |
|------|------|-----------------|
| — | AURORA | 6 |

### Intenção emocional
Esperança lírica. Colcheias no lead, contraponto de arpejo no ch1, baixo
pizzicato real (grave ~219 Hz+) no ch2.

## Cena 03 — tempestade
### Beats
1. Entrada brusca: `music_storm` no frame seguinte ao último de dawn (sem
   transição — a tempestade não pede licença).
2. Parallax de 2 planos (céu/nuvem + estilhaços) acelerando com o motor rítmico.
3. Percussão de ruído branco gateada conduz; relâmpago = flash de paleta em
   sinc com hits do ch3.
4. `sfx_crack` em estilhaços atingidos; arbitração medida no worst-frame.

### Diálogos
| Quem | Fala | Tiles estimados |
|------|------|-----------------|
| — | TEMPESTADE | 10 |

### Intenção emocional
Tensão máxima, densidade. É aqui que M1/M3/M4 trabalharam contra o fantasma da
"metralhadora de 16 Hz" — a tempestade é rítmica, não zumbido.

## Cena 04 — eco + créditos
### Beats
1. Pós-tempestade: `music_eco` reexpõe o tema-âncora em variação (mesmo motivo,
   outro registro/instrumentação de canais) — prova de identidade motivica.
2. Cristais se apagam na ordem inversa em que acenderam (memória do estado).
3. Créditos rolam durante a última volta do loop; HUD mostra contagem de
   compassos tocados.
4. Final: `PSGSilenceChannels` no último frame do A-section → 2 s de preto →
   volta ao título (demanda: o ciclo é a estrutura).

### Diálogos
| Quem | Fala | Tiles estimados |
|------|------|-----------------|
| — | ECO | 3 |
| — | créditos: 6 linhas × ≤20 chars | ~120 |

### Intenção emocional
Nostalgia estruturada: o jogador deve **reconhecer** o tema da cena 01
transformado. Se não reconhecer na escuta, a faixa reprova — não o gate.
