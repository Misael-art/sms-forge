# Régua de duelo — Alis e Hayato, revisão de perspectiva

[Prancha v2](duel_reach_reference_v2.png) · Referência para o esboço lateral.

Na primeira prancha, a normalização pela sola mais baixa transformou a
profundidade do pé da Alis em altura e largura no plano de luta. A comparação
colocava o volume de uma concept em três-quartos ao lado da guarda lateral
flexionada de Hayato. O proprietário rejeitou a escala e pediu uma verificação
independente de armas e acessórios. Os 36 px de alcance, os 4 px de avanço e
a caixa de guarda da Alis da [v1](duel_reach_reference_v1.md) ficam retirados.

## Escala do elenco e pose

Na [prancha aprovada de harmonização](decisions/roster_harmony_waku_waku_7_v01_owner_approval.json),
Alis e Hayato têm 75 U cada, relação corporal **1:1**. O manifesto registra
coroa em Y=491 e sola em Y=1090 para os dois, ou 600 px inclusivos. A v2
usa recortes das duas páginas com o mesmo fator e linha de base. A altura
corporal de pé adotada para o estudo SMS é **68 px para ambos**, no intervalo
comum das faixas do GDD. A altura visível muda conforme a postura.

No sprite lateral de Hayato em guarda, a coroa aparece a 58 px do chão e
a ponta alta da katana leva a silhueta a 66 px. A caixa equipada mede
35 × 66 px, com 18 px atrás e 16 px à frente do pivô na orientação do
rival na prancha. O perfil de Alis orienta a projeção e o encaixe das
peças. A largura em guarda e a extensão do ataque serão medidas no
esboço lateral.

## Espada e escudo

Medidas aproximadas das duas vistas do [turnaround de Alis](../data/source_art/roster_harmony_review/turnarounds/alis_turnaround.png),
projetadas para H=68 px. H é a referência corporal e fica fora do cálculo
da caixa equipada.

| Elemento | Frente | Perfil | Conferência para o próximo desenho |
|---|---:|---:|---|
| Lâmina da espada curta, da base à ponta | 23 px (~0,34 H) | 27 px (~0,40 H) | Comparar comprimento em vista equivalente à katana. Conferir base, empunhadura e ponta ao longo das poses. |
| Escudo, largura × altura | 11 × 20 px | 6 × 18 px | Conferir face, inclinação e fixação ao antebraço. A largura aparente diminui ao girar a borda para a câmera. |

Há uma discrepância a resolver no desenho. A lâmina da Alis em perfil
projeta cerca de 27 px e a katana de Hayato em R03 projeta cerca de 25 px da
saída da mão até a ponta. Essas vistas têm ângulos e fontes diferentes.
Comparar as duas armas **na mesma vista e escala**, separadas dos corpos,
antes de fixar o comprimento da espada curta e usá-lo no cálculo de alcance.
Para o cabo, a bainha, o escudo e eventuais acessórios salientes, marcar o
ponto de fixação e medir a projeção à parte.

## Salvaguardas para fechar alcance

| Verificação | Evidência necessária |
|---|---|
| Altura e proporção | Fonte aprovada e par de referência na mesma escala. Conferir linha de base, coroa, ombro, quadril, joelho e tornozelo. Usar uma calibração por lutador e reaplicá-la a todas as poses. |
| Projeção lateral | Guardas comparáveis com câmera, chão e pés de apoio marcados. Registrar quando um pé vem em direção à câmera ou aparece encurtado. Adotar um redesenho lateral quando a pose em perspectiva impedir localizar o apoio. |
| Armas e acessórios | Marcar contorno corporal e contorno equipado em trilhas distintas. Conferir espada e escudo em vistas equivalentes, dimensões de referência e continuidade das pegas. Justificar variações aparentes de comprimento e largura pelo ângulo. |
| Alcance por pose | Marcar pivô, mão e ponta, e anotar avanço do pivô, extensão local e altura. Comparar a borda do alvo **na mesma altura**, dos dois lados do palco. Confirmar a silhueta em 1× e 4× antes de fechar os números. |

No palco, usar `h = 144 − Y` e pivôs X no chão comum. A projeção no
sentido do rival é o avanço do pivô somado à extensão local até a ponta.
A régua preserva X=100 e X=139 como posição de comparação. O avanço, a
extensão, a altura da ponta e os limites corporais em guarda da Alis ficam
pendentes até o esboço lateral e a conferência das proporções. Depois disso,
retestar as distâncias próximas e distantes e distinguir na ROM acerto,
bloqueio e erro.

Hayato serve de controle de leitura. A lâmina vai até +29 px a 59–60 px do
chão em R02 e até +24 px a 3 px do chão em R03. São alcances visíveis a partir
do pivô fixo. A exposição e a ordem vêm do
[contrato da animação](hayato_animation_contract_v4.json).

## Comando do piloto

A estocada forte de Alis é um normal do **botão 1 segurado**. A orientação
do proprietário continua **toque no 1 para soco fraco, toque no 2 para chute
fraco e pressão sustentada no 2 para chute forte**. O limiar e a precedência
permanecem em GD01.

## Como repetir a medição

- **Escala.** Consultar as páginas
  [1](../data/source_art/roster_harmony_review/waku_waku_7/harmony_waku_waku_7_lineup_v1_part_01.png)
  e [2](../data/source_art/roster_harmony_review/waku_waku_7/harmony_waku_waku_7_lineup_v1_part_02.png)
  e o [manifesto da prancha](../data/source_art/roster_harmony_review/waku_waku_7/harmony_waku_waku_7_manifest_v1.json).
  Os papéis da [concept v4 de Alis](../data/source_art/concept_art/alis_landale/alis_concept_sheet_v4.png)
  são identidade, figurino e referência de gesto.
- **Equipamento.** No turnaround de 1536 × 1024, a referência frontal de corpo
  usada para converter as duas projeções foi de 924 px. Multiplicar medidas
  do desenho por 68/924 e arredondar. Lâmina (base, ponta): à frente
  (255,526) → (71,782), de perfil (1074,533) → (1312,818). Escudo (canto
  superior esquerdo, inferior direito): à frente (542,284) → (692,554),
  de perfil (1142,304) → (1224,548). Os pontos foram selecionados visualmente.
  SHA-256 do turnaround: `c5e9f1c1d91fb13c2d75239523efce636ccdb02ba4b2b44c0720e9de8e579d35`.
- **Hayato.** Usar o perfil [v7 esquerdo](../.mddev/hayato_short_cut_timing_only_v7_left.json),
  PNGs em `out/diagnostics/hayato_short_cut_v2/timing_only_v7/converted_left/`
  com pivô (40,80). A guarda tem caixa alfa X=22..56 e Y=14..79. A coroa
  começa em Y=22. Para o controle R03, a projeção aproximada da lâmina
  vai de (49,57) a (64,77). O R02 tem extremo direito X=69 em Y=20 e Y=21.

O resultado é uma revisão estática com fontes e pontos de medição
conferidos. A próxima revisão depende do par lateral em guarda e da
primeira pose lateral de extensão da Alis.
