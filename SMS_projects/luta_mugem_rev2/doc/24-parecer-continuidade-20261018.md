# Avaliação do luta mugem rev2 e prioridades de continuidade

## Parecer técnico

O projeto avançou em importação, diagnóstico e provas de combate. Há uma ROM real, dados de Ken/Ryu no binário e um teste histórico que registra input, comando, papel, colisão, dano e KO. O próximo passo deve transformar essa base em **runtime de produção com apresentação coerente e prazo de frame medido**.

**O bloqueio dominante é o renderer e a organização do loop.** O código atual continua sendo um instrumento sprite-only: ele pode deixar de desenhar um lutador enquanto sua colisão lógica permanece ativa. A decisão registrada de usar híbrido BG/sprites ainda não foi implementada nem qualificada dinamicamente. Aumentar o catálogo de golpes ou montar todos os menus agora não resolve esse bloqueio.

Recomendo preservar a v031 como baseline diagnóstico e implementar uma interação curta completa no loop de produção. Depois, fechar Ken/Ken, Ryu/Ryu e os dois cruzamentos com as mesmas capacidades, retomando o plano M0–M8 sem confundir boot de um par com lutador completo.

## Baseline conferido

| Item | Estado em 18 de outubro de 2026 |
|---|---|
| Consumidor | `/mnt/sdcard/Projects/SMSForge/SMS_projects/luta_mugem_rev2` |
| ROM atual | `out/rom/luta_mugem_rev2.sms`, 851.968 bytes |
| SHA256 | `6f4a3cf5e336c20ff1dc0fb5225345270823350eada55d4d43655cdfca0b6e9a` |
| Arquivo histórico equivalente | `changelog/roms/build_v031/rom.sms`, mesmo SHA |
| Par atual | Ryu P1 / Ken P2, pacote `out/generated/ryu_ken_cross` |
| Git | Diretório do consumidor ainda aparece como untracked; não há commit próprio do rev2 para usar como identificação completa |
| Escopo de produto | Ken/Ryu, dois botões, fundo sólido em todas as telas; cenário excluído pelo GDD |

Esta rodada não reconstruiu a ROM nem iniciou emulador. Conferiu fontes, hashes, registros preservados, captura histórica e testes host. As revisões nativas de código/evidência e os resultados estão preservados em `26-verificacao-continuidade-20261018.json`. Elas não equivalem a novas sessões de QA do jogo.

## Ganhos comprovados e seus limites

### Importação e CLSN

O intake fixa os pacotes e explicita `common1.cns` ausente. O pipeline produziu pacotes para Ken/Ken, Ryu/Ryu e os cruzamentos; isso demonstra geração de dados para esses pares, com boots históricos de hashes distintos.

Na v031, o relatório posicional de CLSN registra 59 arrays comparados, 33 aliases e zero diferenças. A verificação independente por presença encontra as 194 caixas do recorte no binário. Fonte, dados e ROM estão ligados por hashes conferidos. Presença de bytes não prova o momento em que a caixa entra em vigor ou a execução dos controllers CNS. O teste posicional e o teste por presença têm alcances distintos e complementares.

### Input e combate

O relatório wave-5b registra 29/29 casos, incluindo HP humano com dano 112, guarda, IA pelo matcher e KO. O código confirma o caminho de input comum. Entretanto, a sessão `288166…` não foi preservada integralmente no projeto e já não estava disponível no temporário consultado: restam relatório e log agregados, sem o journal e as observações brutas necessários para reconstituir toda a coleta.

O resultado é um **registro histórico consistente, com custódia incompleta**. Não deve ser apagado nem promovido a nova aprovação. O próximo checkpoint deve reproduzir o núcleo desses casos com bundle privado completo.

Alguns asserts são mais estreitos que a descrição da memória: os casos de direção aceitam mudança de papel sem exigir o ID correspondente; a borda direita aceita posição dentro da faixa, sem exigir chegada a 240; a guarda admite dano abaixo de um teto, sem exigir zero; a checagem de dano da IA com algum comando na janela é correlação, não autenticação de todos os escritores. As observações reportadas podem satisfazer o caso desejado, mas o teste deve exigir o contrato antes de aprová-lo automaticamente.

### Verificações desta rodada

| Verificação | Resultado e alcance |
|---|---|
| Pytest `mugen2sms --project rev2` | **184 passed, 146 deselected**; seleção de escopo, não aprovação dos testes excluídos |
| Self-check do teste causal | Passou; valida decoder/contratos locais, sem executar o jogo |
| Self-check do teste CLSN | Passou; fixtures de bytes/sentinela/mapeamento |
| Marcadores de debug | Passaram; sondas fixas declaradas `volatile` |
| Corredor contra o `.map` atual | **77 sondas, folga 1.547 B, pass**, corredor `0xC800..0xC8FB` |
| Contrato de engine | Passou em modo planning; **bloqueou delivery**, sem aceite das 12 capacidades |
| Reconciliação de claims | Passou com boot/gameplay/FPS/áudio false no build record; não consumiu automaticamente as provas novas |

## Problemas a resolver primeiro

### Apresentação e colisão usam condições diferentes

Em `src/main.c`, `combat_step` recebe os frames lógicos antes de `request_pose`. Na emissão, o ator só é desenhado se `current[side].pose_global == poses_req[side]`; caso contrário, a rotina incrementa o stall e omite o ator. `request_pose` também pode expulsar o cache exibido do adversário.

Isso permite personagem invisível com ataque/colisão lógica em funcionamento. Preservar a última pose completa é uma proteção visual útil, mas não basta: estado, facing, caixas e apresentação precisam de uma política coerente, com deadlines para evitar atraso silencioso. A captura histórica da v029 já mostra omissão visual importante; ela não é uma inspeção da imagem da v031.

`probe_disp_p*` registra a pose armazenada no cache mesmo quando o ator não foi emitido. A próxima instrumentação deve distinguir desejada, residente, submetida na SAT/PNT e efetivamente apresentada; o nome do probe não autentica a imagem.

### Streaming e loop ainda são diagnósticos

O streamer copia um par TALL de 64 B por iteração, alternando lados. Os pedidos podem cancelar uploads parciais e invalidar o cache adversário. A cópia integral de uma pose e a falta de residência suficiente produzem espera, descarte e desaparecimento.

O loop começa em `SMS_waitForVBlank` e executa também lógica, montagem de metasprites e cópia da SAT antes de amostrar VCounter. Para produção, preparar lógica/SAT/filas fora da janela de transferência e fazer commits VDP limitados ao orçamento medido. Encerrar toda a lógica em VBlank não é requisito de um jogo SMS; colocar escritas VDP no prazo correto é.

Os três selos de worst-frame preservados pertencem a ROMs antigas e **todos reprovaram**: 2.758/3.000, 2.954/3.000 e 2.456/3.000 iterações instrumentadas com derrame. Nenhum desses números é o resultado da v031. Um novo selo do mesmo instrumento pode documentar o baseline atual; repetir selos sem mudar a arquitetura não fecha o budget de produção.

### O híbrido continua uma hipótese de implementação

O piloto encontrou composições sprite-only acima de oito entradas por linha dentro da faixa 72–88 px, chegando a 19 no caso com projétil/impacto a 80 px. Isso justifica parar de tentar obter zero omissões somente reorganizando a SAT nesses casos. O híbrido BG/sprites é a rota escolhida para experimentar, favorecida pelo fundo sólido do GDD.

Há duas correções importantes na leitura do piloto:

- Os 6.016–6.592 B de current+next são de **um ator**, não do par. O próprio relatório avisa que sobra espaço insuficiente para o segundo ator e FX na região de sprites de 8 KiB.
- A frase do relatório sobre padrões BG caberem na região reservada à PNT mistura domínios. Patterns, entradas da name table e SAT precisam de regiões disjuntas no plano. A banda de Ken de 1.440 B e a de Ryu de 800 B não aprovam, por si, residência simultânea ou upload.

O piloto estático não mede os dois corpos se movendo por pixels, tile compartilhado por ambos, oclusão, facing, limpeza da posição anterior, HUD, paletas e atualização de PNT. O primeiro híbrido precisa provar isso em ROM antes de generalizar.

### Tempo funcional não é latência em tempo real

Wave-5b calibra 100 passos solicitados da ponte para 45 incrementos do contador do loop e passa a segurar input até completar ticks da ROM. Isso evita encerrar um teste funcional cedo demais. **Não comprova fluidez nem inocenta o runtime de perder deadlines.**

Registrar separadamente frames VDP confirmados no ACK, iterações lógicas, avanços de animação e relógio de parede. A calibração agregada não permite inferir um FPS atual; tampouco autoriza tratar toda diferença como defeito do host. Seis ticks para forte só representam aproximadamente 100 ms quando esses ticks têm cadência próxima de 60 Hz.

O novo teste funcional deve manter a unidade lógica e também falhar quando a resposta exceder um deadline VDP declarado. Não usar espera ilimitada pelo contador para aprovar latência.

Há ainda um erro documental específico em `src/main.c:533`: o comentário atribui ao AIR uma unidade fiel de 1/100 s. A documentação MUGEN 1.0 define duração em game ticks, com 60 ticks por segundo na velocidade normal. Corrigir essa interpretação e testar fronteiras, inclusive elementos de duração 1 e terminal; não transportar a convenção temporal do OpenBOR para MUGEN. [Formato AIR da Elecbyte](https://www.elecbyte.com/mugendocs/air.html).

### Espelhamento, hitstop e alcance da IA

O diagnóstico registra uma fronteira de espelhamento de tiles: deslocar células à esquerda não substitui espelhar os pixels de cada tile. Isso exige dados/conversão e prova de pivô, cores e CLSN nos dois facings.

O pusher roda depois do combate mesmo quando o avanço dos atores está em hitstop. É necessário definir e testar o comportamento de congelamento, push e guardpush segundo a adaptação escolhida; não chamar todo deslocamento de bug sem distinguir o impulso inicial da movimentação durante a pausa.

O lado P2 usa um ciclo determinístico de inputs, útil para regressão. Ainda não há seleção equivalente de humano/IA nos dois lados, dois pads humanos consumidos no jogo ou IA adaptativa por dificuldade. O teste não comprova IA×IA para os quatro pares.

## Conversão MUGEN ainda parcial

O pacote atual tem três entradas de comando por lado: especial sem implementação, HP e HK. A máscara de normais não roteados e os conflitos de dois botões estão documentados. Não há projétil, super/power, cancels completos, hitstun de fonte, round reset, HUD, áudio ou front-end completos.

A FSM C sobre `StateDef` simplificado não executa o conjunto de estados/triggers/controllers do personagem. Mapear uma ação AIR a um papel não preserva automaticamente timing de HitDef, multi-hit, recursos ou transições CNS. O manifest já classifica dano como aproximação; o runtime deve cumprir também a política declarada de contato visível.

Os papéis comuns precisam de fonte autorizada ou de perfil de adaptação explícito. É possível continuar com um perfil próprio versionado e identificado como aproximado; não declarar `common_forge` equivalente. Walk com pose idle e action170 usada como papel terminal de Ryu continuam limitações do piloto. Action170 é a convenção de lose na documentação, não uma prova de cadeia de KO importada.

A resolução de dano percorre P1 antes de P2 e pode aplicar KO antes de avaliar o segundo ataque. A evidência de danos cruzados em janelas distintas não prova trade ou KO simultâneo. Definir a política de contatos e aplicação de efeitos, incluindo prioridades, em vez de herdar vantagem de ordem do loop.

## Dúvida CLSN com autoridade documental agora disponível

A documentação oficial da Elecbyte distingue caixas normais associadas ao elemento das caixas Default persistentes na ação. O tutorial orienta atribuir caixas ao elemento atual e oferece Default para reutilizá-las nos demais. Isso **sustenta a política de reset por elemento com fallback em Default** e não oferece fundamento para acrescentar as 27 hitboxes por carry-forward propostas na dúvida anterior. Fontes: [formato AIR](https://www.elecbyte.com/mugendocs/air.html) e [tutorial de colisões](https://www.elecbyte.com/mugendocs-11b1/tutorial2.html).

Conservar os relatórios das duas interpretações, registrar a versão documental e adicionar fixtures discriminantes: caixa só no primeiro elemento, Default persistente, override temporário, grupo de tamanho zero e transição de ação. O detalhe de cada fixture deve seguir a autoridade aplicável; uma documentação geral não prova toda peculiaridade de versões antigas do pacote. A concordância dos três parsers, sozinha, nunca foi prova do comportamento do MUGEN original.

## Coesão documental e engenharia

O TDD ainda diz “arquitetura proposta, não implementada”, a spec mantém todos os budgets pendentes e o contrato está integralmente planned. A memória contém muitos checkpoints antigos declarando ROMs diferentes como atuais. O avanço está documentado, mas falta um resumo operacional único e atualizado.

A memória também cita corredor com 60 sondas/1.781 B de folga em artefato antigo; o `.map` atual e a auditoria desta rodada dão 77/1.547 B. Isso não é invasão, mas confirma que não se deve transportar medidas entre builds.

A correção de Q8.8 é válida; a cifra da explicação histórica precisa de ajuste: 61.440 reinterpretado em signed16 é −4.096, não −3.926.

Organizar o estado atual, a matriz de capacidades e a residência do runtime sem abrir outra engine no consumidor. O núcleo de produção deve ter um owner central no wrapper e o projeto fornecer configuração/arte/dados. Os testes hoje fixam SHA e caminhos de relatório; parametrizar ROM/projeto/output, preservar tentativas e deixar o pino esperado como entrada, sem reescrever evidência anterior.

## Ordem de continuidade

1. Congelar v031, fontes e dados; reconstruir a prova causal mínima com custódia completa e dois relógios explícitos.
2. Implementar loop de produção e piloto híbrido, mantendo os dois atores legíveis e contato coerente com apresentação.
3. Fechar espelhos, residência, deadlines, input e um normal completo; validar os dois facings e alvo móvel.
4. Expandir o lowering CNS por movimentos alcançáveis e resolver os controles de dois botões com perfil concreto e testes de conflito.
5. Completar Ken/Ken; depois Ryu/Ryu; depois Ken/Ryu e Ryu/Ken com humano/IA selecionáveis por lado.
6. Completar rounds/HUD/áudio e fluxo de menus/treino, todos com fundo sólido.

Aprovação final continua exigindo os sete eixos, budget da mesma ROM, revisão independente e qualidade em movimento. Os resultados atuais sustentam um diagnóstico útil e um núcleo parcial de combate. **Taxa nominal NTSC, zero omissões e engine completa permanecem objetivos sem aceite.**
