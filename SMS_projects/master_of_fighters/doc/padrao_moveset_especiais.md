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


## Como incorporar outro repertório

1. Na ficha do novo lutador, declare os normais, o movimento do corpo, as caixas por postura, os comandos físicos e os gestos especiais. Cada gesto associa um botão ou acorde e uma sequência direcional relativa a uma ação. Uma lista vazia deixa disponível o atordoamento universal. As duas variantes de Fire compartilham a mesma entrada e se distinguem pelo tempo de pressão.
2. Defina antecipação, janela ativa, recuperação, força, custo e resposta defensiva de cada ação. O projétil conserva seu dono após a interrupção do conjurador. A reflexão transfere essa propriedade. O motor concede Reiki e reage ao contato uma vez por atacante e por passo lógico.
3. Teste nos dois lados. Dois disparos que se acertam no mesmo passo causam dano aos dois combatentes. Duas chamas do mesmo lado que atingem juntas causam um impacto, com preferência pela de maior força e, persistindo o empate, maior dano. Se as chamas alcançam o rival em passos distintos, ambos podem pontuar. Um contato físico confirmado ocupa primeiro a vaga daquele atacante naquele passo.
4. Faça a conferência do personagem de origem e a prova da ação na ROM. Registre o equipamento, a invenção específica do duelo e a reação individual do defensor. A ficha sintética usada nos testes demonstra a possibilidade de trocar repertórios. O confronto com um segundo personagem autoral precisa de arte, ficha e prova próprias.
