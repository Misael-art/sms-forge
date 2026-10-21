# Contrato de animação — Dr. Ferdinand Social

**Versão:** 1 · **Estado:** proposta de exercício, aguarda decisão do dono e
orçamento técnico · **Contrato machine-readable:**
[`dr_social_animation_contract_v1.json`](dr_social_animation_contract_v1.json)

Este documento inicia o fluxo canônico de animação para o personagem. Ele
descreve estados e quadros a desenhar; **não é uma sprite sheet**, não aprova
moveset, não fornece pixels finais e não foi validado em ROM/emulador.

## Fonte e limite do que foi pesquisado

O walkthrough de *Master of Darkness* registra ataque primário, subarma com
`Up + Button 1`, salto com `Button 2` e movimento no direcional. Ele lista faca,
espada, martelo e machado como armas primárias; arma de fogo, bomba, bumerangue
e estaca como subarmas. O guia também descreve o bumerangue como um arremesso em
arco que retorna quando erra o alvo. [Guia de Master of Darkness para SMS](https://gamefaqs.gamespot.com/sms/588099-master-of-darkness/faqs/44643).

Outra fonte de gameplay usa nomes diferentes para parte das armas primárias,
incluindo bengala e rapieira. A ficha mantém essa divergência aberta para
confronto com o manual escaneado e a ROM original; não cristaliza nomenclatura
controversa. O original é um action-platformer, sem lista de golpes de luta ou
frame-data competitiva documentada. Portanto, os quatro golpes de luta e os
números abaixo são **propostas autorais**, não movimentos atribuídos ao jogo.
Veja também o [walkthrough de PrinceWatercress](https://princewatercress.blogspot.com/2019/11/princewatercress-plays-master-of.html),
que descreve faca/cana/rapieira/espada, bombas e bumerangues.
O [manual escaneado de Master of Darkness para Master System](https://bdjogos.com.br/manuais/58-master-of-darkness-master-system-manual-bra.pdf)
fica como fonte primária para conferência visual posterior.

## Inventário da primeira proposta

O número na coluna “poses-fonte” é a quantidade de desenhos de pose distintos
proposta para a sequência. Ele não é o número de objetos de hardware 8×8/8×16
na tela. A quantidade de objetos metasprite, tiles únicos e carga por quadro
depende dos pixels finais e segue `pending` até rodar os medidores SMS.

| ID | Sequência | Poses-fonte propostas | Ciclo | Estado inicial → final | Entidades | Princípios aplicados |
|---|---|---:|---|---|---|---|
| idle | Idle comum | 4 | loop | Guarda neutra, pés plantados e arma baixa. → Retorna ao eixo neutro; reinício de ciclo sem salto. | dr_social | Staging, Pose a pose, Follow-through, Arcos, Secundária, Timing, Desenho sólido, Appeal |
| walk_forward | Andar para frente | 8 | loop | Guarda neutra com peso centrado. → Conclui um ciclo e mantém vetor para frente. | dr_social | Antecipação, Staging, Pose a pose, Follow-through, Slow in/out, Arcos, Timing, Desenho sólido, Appeal |
| walk_backward | Andar para trás | 8 | loop | Guarda com quadril sobre o apoio. → Completa o passo e segue protegendo o rosto. | dr_social | Antecipação, Staging, Pose a pose, Follow-through, Arcos, Secundária, Timing, Desenho sólido, Appeal |
| jump | Pulo e aterrissagem | 8 | transição | Guarda no chão, eixo controlado. → Pés aterrissam e o personagem recupera controle. | dr_social | Squash/Stretch, Antecipação, Staging, Pose a pose, Follow-through, Slow in/out, Arcos, Secundária, Timing, Exagero, Desenho sólido, Appeal |
| crouch | Abaixar e retornar | 5 | transição | Guarda em pé, pés sem deslizar. → Guarda em pé estável. | dr_social | Antecipação, Staging, Pose a pose, Follow-through, Slow in/out, Secundária, Timing, Desenho sólido, Appeal |
| dash_run | Corrida curta / dash | 8 | transição | Guarda com base separada. → Pé ancora e velocidade cai a zero sem deslize. | dr_social | Squash/Stretch, Antecipação, Staging, Pose a pose, Follow-through, Slow in/out, Arcos, Secundária, Timing, Exagero, Desenho sólido, Appeal |
| knockdown_fall | Queda por impacto | 8 | transição | Recebe hit dentro da reação contratada. → Caído em pose estável, sem auto-recuperação. | dr_social | Squash/Stretch, Antecipação, Staging, Pose a pose, Follow-through, Slow in/out, Arcos, Secundária, Timing, Exagero, Desenho sólido, Appeal |
| tech_roll_getup | Rolar e levantar | 8 | transição | Estado caído dentro da janela de recuperação. → Guarda recuperada, vulnerabilidade encerrada. | dr_social | Squash/Stretch, Antecipação, Staging, Pose a pose, Follow-through, Slow in/out, Arcos, Secundária, Timing, Desenho sólido, Appeal |
| guard | Defesa alta | 4 | loop | Guarda neutra. → Permanece defendendo enquanto input ativo; ao soltar transita para idle. | dr_social | Antecipação, Staging, Pose a pose, Follow-through, Arcos, Secundária, Timing, Desenho sólido, Appeal |
| victory_01 | Vitória 1 — inspeção do caso | 8 | transição | Round encerrado, arma segura. → Retorna ao idle após o hold. | dr_social, cane | Staging, Pose a pose, Follow-through, Slow in/out, Secundária, Timing, Exagero, Desenho sólido, Appeal |
| victory_02 | Vitória 2 — juramento de justiça | 8 | transição | Luta encerrada; rapieira em posição segura. → Volta à guarda sem lâmina cruzar o corpo. | dr_social, rapier | Staging, Pose a pose, Follow-through, Slow in/out, Arcos, Secundária, Timing, Desenho sólido, Appeal |
| defeat_timeout | Derrota por tempo | 8 | transição | Sinal do timer; personagem ainda de pé. → Pose composta de derrota, sem KO físico. | dr_social | Staging, Pose a pose, Follow-through, Slow in/out, Secundária, Timing, Exagero, Desenho sólido, Appeal |
| draw | Empate | 8 | transição | Round termina sem vencedor. → Neutro pós-round, sem derrota individual. | dr_social | Staging, Pose a pose, Follow-through, Slow in/out, Arcos, Secundária, Timing, Desenho sólido, Appeal |
| taunt_01 | Provocação 1 — ajuste dos óculos | 8 | transição | Guarda neutra, olhar atento. → Retorna à guarda. | dr_social | Antecipação, Staging, Pose a pose, Follow-through, Slow in/out, Secundária, Timing, Exagero, Desenho sólido, Appeal |
| taunt_02 | Provocação 2 — desafio com a bengala | 8 | transição | Bengala plantada com ponta redonda íntegra. → Bengala volta à posição de combate. | dr_social, cane | Antecipação, Staging, Pose a pose, Follow-through, Arcos, Secundária, Timing, Exagero, Desenho sólido, Appeal |
| intro_01 | Apresentação 1 — investigador entra em guarda | 10 | transição | Fora do enquadramento, arma segura. → Guarda no ponto de luta. | dr_social, cane | Antecipação, Staging, Pose a pose, Follow-through, Slow in/out, Arcos, Secundária, Timing, Desenho sólido, Appeal |
| intro_02 | Apresentação 2 — rapieira e juramento | 10 | transição | Rapieira embainhada, mão fora do cabo. → Rapieira alinhada com guarda de duelo. | dr_social, rapier | Antecipação, Staging, Pose a pose, Follow-through, Slow in/out, Arcos, Secundária, Timing, Desenho sólido, Appeal |
| versus_neutral | Retrato versus — atenção | 6 | loop | Rosto frontal/¾ em neutral. → Retorna à expressão inicial. | dr_social | Staging, Pose a pose, Follow-through, Slow in/out, Secundária, Timing, Desenho sólido, Appeal |
| versus_win | Retrato versus — vitória | 6 | transição | Retrato focado. → Sorriso discreto estável. | dr_social | Staging, Pose a pose, Follow-through, Slow in/out, Secundária, Timing, Exagero, Desenho sólido, Appeal |
| versus_loss | Retrato versus — derrota | 6 | transição | Retrato focado. → Compostura pós-derrota. | dr_social | Staging, Pose a pose, Follow-through, Slow in/out, Secundária, Timing, Desenho sólido, Appeal |
| basic_cane_tap | Normal leve — toque de bengala | 8 | transição | Bengala em guarda baixa e mão fechada no cabo. → Guarda reestabelecida, sem deslocamento involuntário. | dr_social, cane | Antecipação, Staging, Pose a pose, Follow-through, Arcos, Timing, Desenho sólido, Appeal |
| rapier_lunge | Especial candidato — estocada de rapieira | 12 | transição | Guarda, ambos os pés em contato com solo. → Pé dianteiro ancora; lâmina recolhida, guarda recuperada. | dr_social, rapier | Squash/Stretch, Antecipação, Staging, Pose a pose, Follow-through, Slow in/out, Arcos, Timing, Exagero, Desenho sólido, Appeal |
| cane_riposte | Especial candidato — contragolpe de bengala | 10 | transição | Guarda estável antes do ataque. → Guarda após sucesso ou falha. | dr_social, cane | Antecipação, Staging, Pose a pose, Follow-through, Slow in/out, Arcos, Secundária, Timing, Desenho sólido, Appeal |
| boomerang_throw | Especial candidato — bumerangue de aço | 14 | transição | Bumerangue preso à mão/cinto conforme concept. → Captura se erra; fica sem item se acerta, adaptação proposta. | dr_social, boomerang, violet_trail | Squash/Stretch, Antecipação, Staging, Pose a pose, Follow-through, Slow in/out, Arcos, Secundária, Timing, Exagero, Desenho sólido, Appeal |

Os nomes/IDs de quadros, holds provisórios e trilhas de cada entidade estão no
JSON. Todo objeto animado (bengala, rapieira, bumerangue e rastro) tem estado
inicial, estado final, contagem de poses própria e uma trilha alinhada aos
quadros da sequência. Cada track também declara seu relógio: sincronizado à
sequência, ou independente. O bumerangue tem 24 ticks de ida + 24 de retorno
em miss; o rastro violeta dura no máximo quatro ticks. Ambos são propostas,
com tempos ainda não medidos.

## Propostas de combate para discussão

Os valores numéricos são apenas um ponto inicial comparável, em ticks de lógica
e unidades de dano ainda sem escala de vida aprovada. Não podem entrar no
moveset selado antes de validar alcance no pixel, hitbox/hurtbox, startup,
active, recovery, vantagem em hit/bloqueio/erro, recursos e respostas do
oponente.

| Golpe candidato | Startup / ativo / recovery (ticks) | Alcance / dano candidato | Relação e contrajogo |
|---|---:|---:|---|
| light_cane_probe | 4 / 2 / 8 | 18 px / 20 | Alcance curto exige aproximação; bloqueio reduz recompensa e whiff consome recovery. |
| medium_rapier_lunge | 7 / 3 / 15 | 36 px / 45 | Linha previsível; defesa, salto ou recuo evitam; whiff/bloqueio deixam punição; sem invulnerabilidade. |
| cane_riposte | 4 / 3 / 18 | 20 px / 50 | Não captura ataques baixos/projéteis/retardados; adversário pode atrasar/fintar; falha é punível. |
| steel_boomerang | 10 / 32 / 18 | 96 px / 35 | Startup visível, arco previsível e recuperação deixam respostas; acertar consome o item na adaptação. |

### Critérios de física e balanceamento

- Alcance de golpe corpo a corpo deve caber na cadeia ombro → cotovelo → punho →
  mão → pegada → arma. A hitbox termina onde a arte mostra contato; não se
  estende por conveniência de balanceamento.
- Impulso, salto, queda e recuo devem produzir deslocamento contínuo. O modelo
  de movimento registra posição e velocidade por tick; gravidade/integração
  deve usar inteiros ou Q8.8 no runtime Z80, nunca `float`/`double`.
- Armas rígidas preservam eixo, guarda, ponta e pegada. follow-through move
  roupa/cabelo e não dobra bengala, rapieira ou bumerangue.
- Quanto maior alcance, dano ou cobertura, maior o custo de startup, recovery,
  recurso ou vulnerabilidade. Toda proposta especifica pelo menos uma resposta
  justa: bloquear, esquivar, saltar, interromper, recuar ou punir o erro.
- O bumerangue é um objeto com trajetória, rotação, colisão e retorno próprios.
  Apenas um pode ficar ativo. A adaptação candidata o consome ao acertar e o
  devolve após errar; regra, velocidade e duração ainda precisam de decisão e
  teste. O brilho violeta é efeito visual breve, sem hitbox independente.
- Testes de balanceamento precisam comparar hit, bloqueio e whiff com o mesmo
  baseline/ROM; números deste rascunho não são prova de equilíbrio.

### Modelo físico candidato

O rascunho propõe velocidades em Q8.8 por tick lógico, com valores ainda não
medidos: avanço 8 px/16 ticks; recuo 6 px/16 ticks; dash 24 px/16 ticks com
limite de pico de 2 px/tick; pulo 24 px de altura em 24 ticks, ápice no tick
12; rolagem 16 px/17 ticks; avanço corporal da estocada 8 px em 6 ticks. Eles
estabelecem relações para prototipar — avanço > recuo, dash > marcha —, não
valores finais de jogo.

No eixo vertical com pixels de tela crescendo para baixo, o modelo discreto é
`x[n+1]=x[n]+vx[n]`, `y[n+1]=y[n]+vy[n]` e `vy[n+1]=vy[n]+g`. O pulo escolhe
velocidade inicial e gravidade para passar pelo ápice e pousar no tick
contratado; a queda deriva o `vx` do impulso do hit que a causou. O dash usa
aceleração e frenagem limitadas; a soma dos deslocamentos por tick precisa
coincidir com a distância proposta. A trajetória do bumerangue usa tabela
determinística inteira: 24 ticks de ida até 96 px, arco de 12 px e 24 ticks de
volta quando não acerta. Isso é uma aproximação de gameplay, não uma simulação
aerodinâmica. NTSC/PAL, gravidade, velocidade, colisão e janela de controle
continuam pendentes de teste na ROM.

## Fluxo canônico de produção de folha animada

1. Selecionar concept aprovado por caminho e SHA; confirmar roupa, rosto,
   morfologia, mão dominante e cada equipamento.
2. Selar este contrato por sequência: gatilho, inicial/final, loop, poses
   numeradas, duração proposta, entidades animadas, física, hitboxes e pelo
   menos sete princípios efetivamente aplicados. Revisar os 12: os demais
   recebem razão explícita para não aplicação.
3. Revisar independentemente as chaves e as trajetórias de personagem/objeto.
   Corrigir falhas de anatomia, identidade, encaixe ou encenação antes de
   desenhar intervalos.
4. Produzir frames numerados, mantendo pivô, baseline, canvas múltiplo de 8,
   paleta SMS, recorte limpo e equipamento inteiro. Separar layers/tracks de
   personagem, arma/projétil e efeitos quando forem animados de forma distinta.
5. Executar `audit_animation_contract.py` para cobertura do contrato e
   `audit_animation_semantics.py` para a sequência de imagens real. São gates
   diferentes: o primeiro não inspeciona pixels; o segundo não decide física,
   anatomia ou qualidade artística.
6. Revisar cada quadro em 1× e nearest-neighbor; conferir movimento, hitbox e
   pose. Rodar gates de paleta, recursos, recorte/material, roster e prova de
   asset aplicáveis.
7. Medir tiles compartilhados/residentes, SAT, limite de oito sprites por
   scanline, RAM/ROM/banking e pior VBlank. O hardware não define máximo
   universal de quadros por folha; não fixar esse teto antes da medição.
8. Integrar apenas após aprovação humana, build e execução em emulador. Uma
   ficha aprovada ou gate de contrato não substitui evidência de ROM.

## Princípios Disney

Cada animação avalia os 12 princípios no contrato. No mínimo sete devem ser
aplicados com uma pista visual planejada ligada a quadros específicos; os
demais recebem justificativa contextual. Como os quadros ainda não foram
desenhados, todas as pistas estão marcadas `planned_not_rendered`: são intenção
de encenação, não evidência visual nem aprovação.

## Fonte de verdade e estado técnico

- GDD: catálogo obrigatório, conceitos de movimento e status das propostas.
- TDD e `13-spec-cenas.md`: custo e limites do runtime por cena.
- JSON vinculado: estados, IDs/contagens de poses, tracks, princípios e
  propostas de golpes.
- `audit_animation_contract.py`: valida campos declarados; não autentica a
  fonte, a imagem ou a verdade artística.
- Contagem metasprite, tiles, paleta P1 compartilhada, VBlank e frame data
  continuam pendentes até conversão, medição e teste em emulador.
