# Comandos da Cena 02

## Perfil Alis × Alis

No espelho, P1 e P2 usam os mesmos comandos. P1 veste rosa e começa à
esquerda. P2 veste verde e começa à direita. O traje acompanha o controle
quando as duas trocam de lado. Frente e trás são relativos à adversária.

| Postura | 1 toque | 1 sustentado | 2 toque | 2 sustentado |
|---|---|---|---|---|
| Em pé | Soco de guarda com escudo | Estocada forte de espada | Chute de distância | Chute de avanço |
| Abaixada | Soco rente ao escudo | Estocada ascendente | Chute baixo curto | Rasteira lateral |
| No ar | Soco aéreo de encontro | Estocada em descida | Chute de interceptação | Chute em mergulho |

Em pé ou abaixada, solte antes da sexta leitura para o golpe fraco.
Sustente até a sexta para o forte. Para fazer o **chute baixo**, segure
**↓** e dê um toque em **2**. Mantenha **↓ + 2** para a **rasteira**.

No ar, a preparação começa ao pressionar. Solte antes da quarta leitura
para o golpe curto ou mantenha até a quarta para o forte. É possível
pressionar **↑ + 2** para armar o chute já na decolagem. Para acertar
um alvo em pé com a espada, pressione **1** perto do início da descida
e mantenha. No pouso, o agachamento e as novas pressões já respondem.
Para reutilizar o botão do golpe aéreo, solte-o antes de pressionar
novamente.

No Steam Deck com o lançador do SMSForge, **A** é o botão 1 e **B** é
o botão 2 do P1. Abra o arquivo `.sms` com **Emulicious (SMSForge)**.
No teclado do P1, use as setas, **A** para o botão 1 e **S** para o
botão 2. Para o chute baixo curto, mantenha **↓** enquanto solta
**B** no Deck ou **S** no teclado. Em outra instalação do Emulicious,
confira a atribuição em **Options → Input**.

- **Frente + 1 + 2** com as duas pressões novas na mesma leitura executa
  a Puxada com Escudo. A rival precisa estar ao alcance e no chão. Alis
  puxa pelo braço e empurra com o escudo, fazendo a rival cambalear e cair.
- **Baixo, depois frente + nova pressão de 1** continua sendo o Passo de Escudo.
- **Trás** defende em pé ou no ar. **Baixo + trás** defende na base baixa.
- **Cima**, **cima + frente** e **cima + trás** saltam nas três direções.
- Após o KO, uma nova pressão de **1** em qualquer controle reinicia o duelo.

[ROM b53 para jogar](../out/candidates/scene02_alis_mirror_b53/rom/master_of_fighters.sms) ·
[Fichas do espelho](repertorio_alis_hayato.md#produção-do-espelho-de-alis).

## Controle histórico Hayato × Alis

Na **b32**, Alis começa à esquerda no P1, o controle principal. Hayato fica no P2, à direita, para um segundo jogador. Use os direcionais e os botões **1** e **2** do Master System. No Emulicious, confira o mapeamento dos dois controles em **Options → Input**.

**Frente** é a direção do adversário. **Trás** é a direção oposta. Trás com espaço recua e defende se houver contato compatível. Toque dispara ao soltar antes do limiar. Para o golpe forte, mantenha o botão pressionado por 6 leituras na variante de 6 ou 8 na variante de 8. Solte o botão para rearmar o comando. Os normais não entram em fila nem cancelam ações em andamento.

| Comando | Família | Hayato | Alis |
|---|---|---|---|
| Frente | Movimento | Avançar | Avançar |
| Trás | Movimento e guarda | Recuar e defender | Recuar e defender |
| Toque em 1 | Soco fraco | Soco da guarda | Soco de guarda com o escudo |
| Segurar 1 | Soco forte | Corte curto | Estocada forte, uma espadada direta |
| Toque em 2 | Chute fraco | Chute de sondagem | Chute de distância |
| Segurar 2 | Chute forte | Chute de giro | Chute de avanço |

O golpe de Alis em **segurar 1** é o normal forte (`alis_landale/pe_1_longo`). Consulte a [decisão de design](decisions/scene02-normais-dois-botoes_owner_20261121.json).

## Agachamento, salto e guarda de Alis

| Comando | Alis |
|---|---|
| **↓** | Abaixar. Solte para levantar. |
| **↑** | Saltar no mesmo lugar. Cada nova pressão gera um salto. Manter ↑ após o pouso exige soltar para rearmar. |
| **↑ + frente** ou **↑ + trás** | Saltar na diagonal. A direção da decolagem determina o impulso. Perto do adversário, saltar em direção a ele permite cruzar e trocar de lado se houver espaço de pouso. |
| **Trás em pé** | Recuar com intenção de guarda. O escudo sobe no bloqueio e quando o recuo chega à borda. |
| **↓ + trás** | Assumir guarda abaixada. |
| **Trás no ar** | Defender no ar. Alis estende o corpo na subida, recolhe o escudo no arco e se estende para pousar. Solte ou reaplique trás durante o voo para trocar de guarda. |

Se você apertar ↑ ou **↑ + direção** durante a recuperação da espadada,
manter o comando inicia o próximo salto assim que Alis fica livre.
A nova pressão de ↑ no ar pode preparar um salto para depois do pouso.

O ensaio de guarda aérea aceita os golpes de botão **1** de Hayato quando
alcançam Alis. Os ataques selecionáveis para Alis pertencem à postura em pé.

## Comandos extras nas candidatas de ensaio

Na b32 de seis leituras, **baixo, depois frente + nova pressão de 1** em até oito leituras chama Saque em passada para Hayato e Passo de escudo para Alis. O comando direcional de ensaio tem precedência sobre o normal de botão 1. A espadada direta é o forte em pé da primeira tabela. A ROM abre direto no duelo local. [ROM b32](../out/candidates/scene02_alis_jump_mix_b32/rom/master_of_fighters.sms) · [Matriz de evidência](scene02_hayato_alis_qa.md#saltos-combinados-com-espadada-e-guarda).
