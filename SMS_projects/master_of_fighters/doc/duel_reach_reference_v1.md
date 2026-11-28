# Régua de duelo — Alis e Hayato

**Histórico. Escala rejeitada pelo proprietário.** A [régua v2](duel_reach_reference_v2.md)
substitui a calibração e retira as medidas de guarda e alcance propostas
para Alis nesta versão.

[Prancha v1](duel_reach_reference_v1.png) · Registro da primeira comparação.

A Alis fica à esquerda, de frente para Hayato, na escala de uma tela SMS
de 256 × 192 px. Os três painéis usam a mesma ampliação 5× e malha de 8 px.
O recorte mostra a faixa de combate. A linha do chão é a aresta entre as
linhas de pixel Y=143 e Y=144, a altura local é `h = 144 − Y` e o último
pixel apoiado pode ficar em Y=143. O chão continua como referência em
agachamentos, saltos e poses com equipamento acima da cabeça.

## Medidas que acompanham cada golpe

1. **Guarda.** Registre o X do pivô no chão e os extremos opacos atrás,
   à frente e acima. Use os limites inclusivos dos pixels para calcular a
   largura. Anote equipamentos salientes e onde fica o tronco do rival na
   altura que se quer testar.
2. **Execução.** Por pose, registre o avanço do pivô desde a guarda, a
   extensão local da ponta ou do membro atacante e sua altura no palco.
   Some avanço e extensão para obter a projeção horizontal desde a guarda.
   Espelhe a direção quando o lutador estiver à direita.
3. **Distância.** Registre a separação entre os pivôs e compare o alcance
   com a borda do alvo na mesma altura. A razão entre alcance e altura
   corporal de referência permite comparar personagens de escalas diferentes.
   Defina as caixas do corpo, do ataque e da defesa durante a integração.

| Guarda na prancha | Pivô X | Atrás / frente | Largura × altura da silhueta |
|---|---:|---:|---:|
| Alis, P1 voltada para a direita | 100 | 24 / 21 px | 46 × 68 px |
| Hayato, P2 voltado para a esquerda | 139 | 18 / 16 px | 35 × 66 px |

Os limites de guarda incluem as armas e o escudo. A altura de 66 px de
Hayato é a da silhueta completa da guarda no recorte v7. A faixa corporal de
68–72 px no GDD é a meta de escala do elenco. Para Alis, a prancha usa
68 px na guarda dentro da faixa corporal de 66–70 px. No desenho conceitual
há profundidade entre os pés. O esboço deve explicitar os apoios na vista de
luta, conservando a escala entre poses.

## Primeiro golpe — estocada forte de Alis

**Categoria de design** · Normal forte de espada. **Entrada** · Botão 1 segurado.
Começar na guarda com escudo, preparar brevemente, avançar e estender a espada
em direção ao tronco. A recuperação deve mostrar a recolha da arma, a passagem
do peso e a recomposição da guarda também quando o golpe ficar curto.

| Medida | Hipótese para o esboço |
|---|---:|
| Avanço do pivô | +4 px |
| Extensão local da ponta a partir do pivô avançado | +32 px |
| Projeção horizontal total desde o pivô em guarda | +36 px |
| Altura da ponta a explorar | 40–48 px, com marca de referência em 44 px |
| Alcance total em relação à altura da guarda | 36 / 68 ≈ 53% |

A ponta da pose conceitual reduzida para a régua fica em +34 px e h=60
contando o avanço ilustrado. A marca do esboço está em +36 px e h=44.
Para atingir essa marca, rever ângulo e posição da mão mantendo a geometria
da espada. Os valores são alvos para encenação e teste de alcance.

Na linha h=44, a borda do tronco escolhida para o Hayato em guarda fica 3 px
à frente do pivô dele. Com P1 em X=100 e P2 em X=139, esse plano fica em
X=136, onde a projeção de +36 px termina. No mesmo estudo, compare os três
espaçamentos sem alterar poses ou alturas:

| Distância entre pivôs | Plano do tronco desde P1 | Projeção de +36 px |
|---|---:|---|
| 35 px | 32 px | Passa o plano por 4 px |
| 39 px | 36 px | Chega ao plano |
| 43 px | 40 px | Fica 4 px aquém do plano |

São relações geométricas de revisão. A confirmação de acerto, bloqueio e
erro depende da pose ativa, das caixas, da guarda e da ROM. Usar este mesmo
teste com os papéis espelhados e repetir com o alvo em outra postura.

## Comparação com Hayato

O corte curto de Kenseiden mantém o pivô fixo. Na liberação alta R02, a
ponta dianteira chega a +29 px com h=59–60. Na pose R03 do corte descendente,
chega a +24 px com h=3. O máximo horizontal da sequência medida está em
R02. A meta de Alis tem 7 px a mais de projeção horizontal que esse máximo,
com 4 px vindos do avanço do pivô. Este é um desvio explícito para revisar
junto com a altura da ponta, a leitura do compromisso e a recuperação.
O mapa de dano do Hayato continua por definir.

## Direção dos controles

| Controle | Toque | Pressão sustentada |
|---|---|---|
| Botão 1 | Soco fraco | Golpe forte de mão ou arma. Alis usa a estocada forte. |
| Botão 2 | Chute fraco | Chute forte |

Para o teste de entrada de GD01, avaliar o disparo do fraco na soltura antes
do limiar e o disparo do forte ao alcançar o limiar. Um aperto gera uma
ação, e soltar rearma o botão. Medir a resposta do fraco e testar a borda
do limiar imediatamente antes, no limiar e imediatamente depois. A duração
do limiar e a precedência com os demais comandos continuam abertas.

## Fontes e reprodução das medidas

- Alis vem da [ficha conceitual v4](../data/source_art/concept_art/alis_landale/alis_concept_sheet_v4.png)
  com [decisão visual do proprietário](decisions/alis-landale-concept-v04_owner_approval.json).
  Recortar a figura esquerda e a direita pela transparência. A fronteira
  entre as duas é X=710 acima de Y=850 e X=745 a partir de Y=850.
  As duas poses usam a mesma redução nearest-neighbor de
  68/977 com arredondamento dos tamanhos e offsets ao pixel mais próximo.
  Pivôs didáticos na fonte (X, aresta Y): guarda (411, 988), extensão
  (1058, 983). São âncoras da prancha.
- Hayato vem dos PNGs convertidos em
  `out/diagnostics/hayato_short_cut_v2/timing_only_v7/converted_left/`,
  registrados na [configuração v7](../.mddev/hayato_short_cut_timing_only_v7_left.json).
  O canvas é 88 × 88 e o pivô é (40, 80). Medir todos os pixels com alfa
  diferente de zero. Para a guarda de P2, espelhar a imagem em torno
  do pivô. A borda do tronco em h=44 é o pixel X=43, Y=36 na imagem
  sem espelho. A lâmina em guarda está adiante desse ponto. R02 e R03
  foram medidos na orientação da fonte. O [contrato de Hayato](hayato_animation_contract_v4.json)
  documenta as poses e exposições da amostra.

Ao revisar o esboço, juntar a régua por pose, a reprodução à velocidade
normal e o registro da decisão artística. Para mudar o alcance, anotar
se mudou o avanço, a extensão local, a altura ou a duração da pose. A
prancha atual é estática e a estocada da Alis aguarda desenho e teste na ROM.
