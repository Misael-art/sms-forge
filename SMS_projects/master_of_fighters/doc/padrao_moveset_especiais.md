# Padrão de repertório especial do elenco

Cada ficha descreve o que o jogador pode tentar, o tempo para o rival responder e o prêmio por acertar. Cada personagem conserva a identidade do jogo de origem. A ficha de Alis é a primeira implementação deste padrão de design. A criação de personagens permanece com a camada de elenco do motor.

| Função no repertório de cada personagem | Critério de equilíbrio no duelo de 100 PV |
|---|---|
| Controle de espaço | Uma opção gratuita de curto ou médio alcance. A ameaça de tela inteira exige recurso ou preparação longa, tem trajetória legível e admite contrajogo. |
| Resposta à aproximação | Uma opção antiaérea com antecipação e recuperação punível. Documentar o alcance e as posturas que acertam. |
| Defesa característica | Guarda especial, esquiva ou reflexão com janela ativa finita. Definir os tipos de ataque aceitos, o efeito no erro e a propriedade do golpe devolvido. |
| Utilidade e provocação | Uma ação vulnerável para recuperar vida, posição ou recurso. Medidor máximo de oito unidades. A provocação tem intervalo para evitar repetição rápida. |
| Super 1 e especial de alto custo | Um gasto declarado e um resultado jogável com defesa e erro. O golpe de alto custo pode usar um aliado ou outra técnica própria do personagem. |
| Super 2 de finalização | Round que o atacante pode fechar, atacante em vida crítica, medidor cheio, rival vivo com menos de 25 PV e tonto. Entrada espelhada de qualquer distância, confirmação em contato, cena própria, uma vitória atribuída. |
| Leitura no controle | Frente e trás seguem a orientação. Botão 1 é o soco e corresponde ao X do comando universal. Botão 2 é o segundo ataque. Exigir borda nova, respeitar congelamento, impedir mistura com o agarrão. |
| Prova por lutador | Registrar comando dos dois lados, custo antes/depois, PV, trajetória/alcance, defesa, recuperação e confirmação. Testar limiares imediatamente abaixo e acima. Comparar confrontos com alcance inicial, recursos e duração iguais. |

Na construção de um novo personagem, a Command List deve nomear os especiais que merecem pausa de ativação e o ponto da pose que concentra energia. Para ações de suporte, registre quem recebe o recurso, o ganho efetivo, o sinal de sucesso e o que acontece se a ação for interrompida. Para combos, registre quando o contador reinicia e a primeira resposta realmente disponível ao defensor no canto. A calibração abaixo é específica de Alis.

A ficha usa ticks de lógica, separados dos quadros do VDP. Os valores abaixo são a primeira calibração de Alis. Espelhar a protagonista permite verificar simetria. O equilíbrio com outro personagem requer os confrontos correspondentes.

## Ficha de Alis Landale

A seta → significa frente. Para ↓↓ e ←←, solte o direcional entre os toques. Para 1+2, pressione os dois juntos. A janela entre mudanças de direção é de 16 ticks. O jogo de origem dá a Alis Fire, Heal e Chat. A transformação de Myau pertence à história de Phantasy Star. O efeito em combate, a cura em pontos e os comandos abaixo pertencem a Master of Fighters. [Manual de Phantasy Star](https://www.smstributes.co.uk/images/db/manual_phantasystarusa.pdf).

| Golpe | Comando | Custo e resposta |
|---|---|---|
| Fire | ↓↓ + 1 | Solte antes de seis leituras para o tiro curto, 6 de dano. Segure para o médio, 10. Sem custo. Pode defender, saltar ou refletir. |
| Fire duplo | ↓↘→ + 1+2 | 4 Reiki. Duas chamas de 7 de dano em curvas defasadas. A fase varia conforme o tick do lançamento e é reprodutível. Cada chama termina no contato ou ao sair da tela. |
| Laconian Slash | ↓↘→ + 1 | O corte envia uma onda azul de 10 de dano, cerca de 80 px. A guarda ou o espelho param a onda. |
| Rising Saber | →↓↘ + 1 | Subida com o sabre, 12 de dano e um único contato. O rival pode recuar e punir a descida. |
| Mirror Counter | ↓↙← + 1 | Reflete fogo e ondas mágicas nos ticks 3–12. A devolução troca dono e sentido. Um ataque físico vence o espelho. |
| Heal / Rest | ↓↓ + 2 | 2 Reiki por 6 PV, até 100. A cura sai no tick 21 e pode ser interrompida. |
| Chat | ←← + 2 | Alis levanta a mão e chama o rival. Ganha 1 Reiki no tick 20 se terminar a preparação. Intervalo de 100 ticks. |
| Myau e a Noz de Laerma | ↓↙← + 2 | 4 Reiki. Myau come a noz, ganha asas, sobe e mergulha uma vez. 18 de dano. O mergulho é físico e admite guarda. |
| Super 1 · Palma | ↓→↓→ + 1 | Mantém o Super de 8 Reiki do capítulo. |
| Atordoar | →←→ + 1 | Com 1–25 PV e 8 Reiki, atordoa um rival em pé e livre por até 84 ticks. Uma vez por jogador por round. Preserva o Reiki para a finalização. Um golpe comum interrompe o atordoamento. |
| Super 2 · Guardiões de Algol | ↓↘→↓↘→ + 2 | 8 Reiki. Exige 1–25 PV de Alis, rival com 1–24 PV e tonto, e uma vitória que fecharia a luta. Alis avança de qualquer distância. O corte inicial precisa alcançar o rival para confirmar a cena. |

A cena confirmada começa no olhar de Alis. Odin dispara a Laser Gun, Noah responde com Thunder, Myau come a Noz de Laerma e mergulha alado. O corte crítico da Espada Laconiana fecha o duelo. A direção usa quadros ilustrados em letterbox, mudanças localizadas de paleta, deslocamento horizontal de impacto e som PSG. O medidor e a vida crítica pulsam durante a luta. [Referência F. Anime indicada pelo proprietário](https://www.youtube.com/watch?v=HhgmTaUsqG8).


## Command List de Alis · revisão para decisão

**Base da conferência.** No Versus da R5, Rest levou Alis de 90 a 96 HP e o Reiki de 3 a 1. Chat levou o Reiki de 0 a 1 com a vida em 100. A barra de Reiki tem oito unidades lógicas e quatro segmentos inteiros. Por isso o primeiro ponto pode ficar invisível. HP corresponde aos PV da ficha. MP corresponde ao Reiki. [Observações da R5, entradas `chat_1`, `fire_forte_3` e `rest_4`](../out/qa/alis_ficha_r5/guardioes-confirmado/observations.json)

| Ação | Comportamento da R5 | Alteração proposta para discussão |
|---|---|---|
| **M03 Fire duplo**, ↓↘→ + 1+2 | Gasta 4 Reiki. As chamas nascem no tick 12. Há antecipação e hitstop quando há contato. | Ao aceitar o comando, escurecer a arena e concentrar luz na mão que lança. Hiperpausa de 8 apresentações antes de retomar a antecipação. |
| **M04 Myau**, ↓↙← + 2 | Gasta 4. A entidade nasce no tick 10 e faz seu próprio percurso. | 8 apresentações de concentração na mão de Alis, antes de aparecer a noz. |
| **F14 Investida de Palma**, ↓→↓→ + 1, e **M11 Guardiões**, ↓↘→↓↘→ + 2 | Cada um exige 8 Reiki. M11 ainda exige as condições do final. Seus sete planos começam depois da confirmação do corte. A R5 carece de hiperpausa de ativação com ponto de energia. | 10 apresentações na palma da mão para F14 e 12 na guarda da espada para M11. Uma única hiperpausa por comando. A cutscene continua condicionada ao acerto. |
| **M05 Rest**, ↓↓ + 2 | Precisa de HP abaixo de 100 e 2 Reiki. Consome o custo na entrada. No tick 21 recupera até 6 HP. Fim nominal em 32. A interrupção anterior ao ganho consome o custo e impede a cura. | Manter o ganho pequeno. No tick da cura, tocar um som ascendente de recuperação, acender uma centelha sobre Alis e fazer subir o número real recebido. De 98 para 100 aparece **+2 HP**. |
| **M08 Chat**, ←← + 2 | Com Reiki abaixo de 8 e recarga livre, ganha 1 no tick 20. Fim em 30. A recarga de 100 ticks começa na ativação e o impacto anterior ao ganho pode interromper. | Ao efetivar o ganho, tocar um timbre próprio e fazer subir **+1 MP** sobre Alis. Exibir cada unidade da barra, inclusive as ímpares. |

**Hiperpausa de ativação (super freeze).** O primeiro quadro deve coincidir com a aceitação e cobrança do comando. A arena muda de tom de uma só vez e o foco converge para o ponto da pose, espelhado conforme o lado. Ambos os lutadores, projéteis em curso, recuperações, recargas e relógio da luta aguardam. O áudio e a leitura dos controles continuam. Ao sair, restaurar as cores e considerar a guarda mantida no primeiro tick legal. A pausa acrescenta tempo visual antes do golpe e preserva os ticks de startup e os valores de hitstop por impacto. Em ativações simultâneas, mostrar os dois focos pelo maior dos dois períodos e cobrar uma vez por jogador. Rejeições por falta de recurso ou pré-condição não disparam o efeito. Fire simples, cura, Chat e normais conservam o ritmo atual nesta proposta.

**Recuperação.** Na R5, Rest, Chat e Tontura chamam o mesmo som PSG ao iniciar. Rest e Chat desenham o mesmo efeito sobre a cabeça durante a ação. Falta o sinal de que a recuperação de fato aconteceu. Na proposta, mostrar o valor durante 16 apresentações, subindo 8 px, apenas se o recurso aumentou. Comparar 90→96 e 98→100 HP, 0→1 e 7→8 MP, interrupção um tick antes do ganho e tentativa com recurso cheio. Verificar o numeral acima de P1 e P2, sem encobrir o rosto nem o contador de hits.

### Hits e proteção contra sequências infinitas

Na R5, a perda de vida incrementa a contagem da vítima. O HUD do atacante mostra o total a partir de dois. Voltar ao estado livre ou entrar em bloqueio limpa a sequência. Guarda, cura e os planos dos Guardiões não somam hits. Duas chamas do mesmo atacante no mesmo tick produzem um único impacto. Em ticks distintos, cada chama pode pontuar se causar dano antes de a vítima recuperar a defesa. O contador satura em 99. Esse limite de exibição deixa a física do combo prosseguir.

A prova de bancada e emulador do contador registrou a estocada forte → soco curto a 24 px, pelos dois lados, com 10 + 6 HP e painel em 2. A entrada atrasada atingiu depois do primeiro tick livre e iniciou outra sequência. A prova pertence à candidata `alis_combo_hits_v1`. Ela cobre essa rota. A parede pode absorver o recuo e permitir repetições que falham no centro. [Sessões, entradas e danos](decisions/2026-11-27_alis_combos_revisao.json) · [Alcance e afastamento](repertorio_alis_hayato.md#contagem-de-combo-e-afastamento)

**Regra proposta para ensaio.** Preservar o combo de dois hits. No quarto acerto confirmado do mesmo combo, aplicar o dano normal e encerrar a sequência com recuperação protegida da vítima. Antes de qualquer quinto acerto, a vítima deve ter ao menos um tick efetivo para executar guarda ou outra resposta legal. A proteção cobre contato físico e projétil já em tela, inclusive contra a parede. O KO encerra o round normalmente. A hiperpausa, o hitstop e o bloqueio visual do HUD não contam como oportunidade de defesa.

**Critério de balanceamento.** Repetir forte → curto, golpe rápido repetido, Fire duplo → físico e golpe tardio ao pousar, no centro e nos dois cantos, invertendo os controles. Registrar dano total, ordem dos hits, afastamento e primeiro input defensivo consumido. Se a rota se repetir sem resposta possível, rever hitstun, recuperação ou recuo do golpe responsável. Uma queda de dano por hit, por si só, deixa o adversário preso. O teto de quatro e os tempos da hiperpausa aguardam aprovação e prova na ROM.


### Paleta visual da Command List

A referência de identidade é o model sheet v4. Na imagem canônica, os códigos SMS 39 e 59 formam os rosas do tecido e o 37 aparece no peitoral azul-violeta. Nenhum dos três aparece nas 94 poses de P1 da R5. Na adaptação para o duelo, o rosa-avermelhado 19 (RGB 255, 0, 85) e o rosa vivo 35 (RGB 255, 0, 170) representam o traje. P2 recebe os códigos 24 e 44 para identificar o segundo controle. O ponto de revisão é a troca visível de cor **dentro do traje de P1 entre quadros de uma mesma ação**. [Model sheet v4](../data/source_art/concept_art/alis_landale/alis_concept_sheet_v4.png) · [Comparação visual](../out/qa/alis_ficha_r5/comparacao-paleta-concept.png)

| Família de P1 | Evidência nas poses | Direção para a revisão de arte |
|---|---|---|
| Normais abaixados, 30–41 | As doze poses têm de 0 a 2 pixels de rosa 35. O tecido e o escudo leem como vermelhos. | Alinhar os mesmos materiais com a postura agachada 10. Preservar sombra e contorno. |
| Ataques aéreos, 42–47 | Em 42→43→44, o rosa 35 passa de 53 para 0 e 57 pixels. Em 45→46→47, passa de 44 para 6 e 47. | Rever principalmente 43 e 46 e avaliar a transição em movimento. |
| Reações, 62–65, 67–70 e 76 | Nas defesas 65 e 66 há respectivamente 0 e 74 pixels de rosa 35. Nas poses baixas e deitadas os materiais ficam parcialmente encobertos. | Priorizar a passagem de 65 para as demais guardas e conferir saia, escudo e ombreira por região. |

As contagens são de todos os pixels opacos de P1 voltada à direita, incluindo o escudo. A conclusão por material vem também da comparação visual. Uma futura repintura deve conservar a pele, a ombreira cinza, o metal amarelo e as meias brancas. O arquivo da ROM usado nesta revisão é a R5 da ficha. [Prancha das 94 poses](decisions/2026-11-27_alis_paleta_94_poses.png) · [Recibo da revisão](decisions/2026-11-27_command_list_alis_r5.json)

## Como incorporar outro repertório

1. Na ficha do novo lutador, declare os normais, o movimento do corpo, as caixas por postura, os comandos físicos e os gestos especiais. Cada gesto associa um botão ou acorde e uma sequência direcional relativa a uma ação. Uma lista vazia deixa disponível o atordoamento universal. As duas variantes de Fire compartilham a mesma entrada e se distinguem pelo tempo de pressão.
2. Defina antecipação, janela ativa, recuperação, força, custo e resposta defensiva de cada ação. O projétil conserva seu dono após a interrupção do conjurador. A reflexão transfere essa propriedade. O motor concede Reiki e reage ao contato uma vez por atacante e por passo lógico.
3. Teste nos dois lados. Dois disparos que se acertam no mesmo passo causam dano aos dois combatentes. Duas chamas do mesmo lado que atingem juntas causam um impacto, com preferência pela de maior força e, persistindo o empate, maior dano. Se as chamas alcançam o rival em passos distintos, ambos podem pontuar. Um contato físico confirmado ocupa primeiro a vaga daquele atacante naquele passo.
4. Faça a conferência do personagem de origem e a prova da ação na ROM. Registre o equipamento, a invenção específica do duelo e a reação individual do defensor. A ficha sintética usada nos testes demonstra a possibilidade de trocar repertórios. O confronto com um segundo personagem autoral precisa de arte, ficha e prova próprias.
