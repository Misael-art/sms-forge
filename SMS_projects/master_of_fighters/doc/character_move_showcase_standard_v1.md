# Apresentação de golpes — padrão de projeto e continuidade do Dr. Social

Versão 1, direção do proprietário em 2026-11-01. **Documentado; implementação,
arte, comandos finais e validação pendentes.** Este é um padrão de Master of
Fighters, não uma técnica homologada globalmente no SMSForge. Ver
[registro de direção](decisions/character-move-showcase_owner_direction_20261101.json),
[GDD](11-gdd.md), [roteiro](12-roteiro.md), [cenas](13-spec-cenas.md) e [TDD](15-tdd.md).

## Avaliação do incremento d7a3a2d

Inspecionados memória, matriz de cobertura, contrato v2, comparativo de conflito,
manifestos de placas e imagens de conversa/versus. O lote preservou fontes,
prompts e tentativas no Git. A revisão é estática; nenhuma animação nova foi
vista rodando e não foi aberta sessão de emulador nesta revisão documental.

| Área | Estado observado/documentado | Limite de aceite |
|---|---|---|
| Jab v8 | Seis desenhos existentes reutilizados; método e provas históricas próprios. | Não é nova integração do personagem completo. |
| Bengala / bota / rapieira | BC04/K04/RL05 são chaves isoladas; sem intervalos completos. | Não demonstram velocidade, arco, antecipação ou retorno. |
| Par em luta | Guarda/bengala nos controles 69/71 px falham; tentativa de guarda em três quartos não concretizou a hipótese e não foi medida. | Não existe proposta nova medida que resolva a composição; não baixar GDD automaticamente. |
| Conversa | Atenção/fala em placas indexadas com glifos e área de palco de diagnóstico. | Sem texto de runtime, alternância observada ou quatro expressões restantes. |
| Versus | Três placas candidatas: neutro, vitória, derrota; rival ainda é área vazia. | Estados estáticos não equivalem aos ciclos previstos nem à tela com dois personagens. |
| Restante do personagem | Matriz ainda registra muitos estados não iniciados e respostas visuais não desenhadas. | Sem pacote integral, arranjo compilado de todos os assets ou qualidade global aprovada. |

**Parecer artístico desta revisão, sem promoção:** as placas permitem reconhecer
Social, ler o texto e distinguir sorriso/abertura da boca. Nas imagens versus
ampliadas há pontos dispersos no casaco, grandes áreas com pouca separação de
volumes e alterações de enquadramento/rosto entre neutro, vitória e derrota.
Derrota permanece próxima do neutro. Isso orienta refino, não uma conclusão de
que a fonte/model sheet deva ser descartada. Comparar âncoras faciais, crop,
clusters e luz na mesma escala, em 1× e nearest ampliado; revisar a saída SMS
após quantização, sem tratar extração/maioria de bloco como acabamento final.

O personagem **não está terminado**. Não há base para dizer que todos os assets
foram compilados ou que a velocidade de suas animações foi aprovada. Não abrir
uma ROM antiga e apresentá-la como o novo pacote. Se houver nova evidência ao
retomar, conferir SHA, fontes e cobertura antes de atualizar esta conclusão.

## Intenção do padrão

O proprietário pede nome do golpe, demonstração com velocidade correta,
representação bem desenhada do controle do Master System e indicação de quais
botões/direções apertar e como executar. A referência a jogos Neo Geo orienta
clareza e apresentação; não autoriza copiar arte, comandos de quatro botões
ou criar outro sistema de luta. Possível desbloqueável futuro é uma ideia
registrada, sem regra/economia/save/desbloqueio decididos.

A cena 10, **Apresentação de golpes**, deve responder: qual ação estou vendo,
qual é sua intenção, como executá-la, quando ela acontece e quando volto ao
controle. Ela usa o personagem real. Retratos e estados sem comando ficam em
páginas de revisão apropriadas; não fingir que cada asset é um golpe executável.

## Contrato visual e de interação proposto

Fluxo proposto: selecionar ação → ler nome/comando → observar execução →
retorno à guarda → repetir ou experimentar → voltar/trocar ação. Navegação
exata depende do layout GD01; não roubar botões de luta enquanto o jogador
pratica. Sugestões de abas “Assistir”/“Praticar” são hipótese de UX da cena,
não modos extras de campanha já implementados.

| Elemento | Intenção e critérios observáveis |
|---|---|
| Nome | Nome legível e estável do movimento; ID interno apenas na revisão técnica. O nome final precisa aprovação, sem inventar título canônico. |
| Palco | Corpo e equipamento inteiros na escala de jogo; chão claro, rival quando necessário à consequência. Espaço de recuperação e objetos preservado. Não ampliar/encolher ator para parecer melhor nesta tela. |
| Controle | Ilustração autoral do controle SMS de dois botões, direcional à esquerda e 1/2 identificáveis. Referência de modelo físico registrada antes da arte. Sem botão Start obrigatório, AB/CD ou alavanca Neo Geo. |
| Sequência | Ícones de direção/botão ordenados, etapa atual destacada por forma/contorno além de cor. Distinguir apertar, manter, soltar, simultaneidade e sequência; só exibir operações usadas pelo comando real. |
| Resultado | Preparação, ação, consequência e recuperação visíveis. Demonstrar sucesso e, quando implementado, erro/guarda; sem explosão de acerto quando não houve contato. |
| Navegação | Ação selecionada e retorno claros. Input mantido ao trocar página não dispara golpe acidental; replay não duplica objeto/recurso. |

Proposta inicial de layout para storyboard, não budget fechado: nome na faixa
superior; palco no centro; controle e sequência na faixa inferior, fora da
silhueta dos lutadores. Medir conteúdo máximo, margens, golpes largos e texto
mais longo em 256×192 antes de fixar retângulos. Nome, comando e atuação são
prioritários; um portrait grande não deve expulsar a luta do espaço útil.

A arte do controle, botões, setas, marcadores e molduras exige identidade
visual comum, contorno/contraste legíveis e proveniência. Fonte com acentos e
hierarquia real em tamanho nativo. Sem peças genéricas provisórias promovidas
por estarem dentro da paleta. BG para UI é uma proposta a medir: não constitui
orçamento gratuito nem permite recolorir a P1 compartilhada dos lutadores.

O controle desenhado mantém sua orientação física quando o lutador troca de
lado. As setas demonstradas refletem a tradução real de frente/trás para o lado
atual. Não espelhar os rótulos 1/2. Se o comando muda durante troca de lado,
a apresentação deve seguir a mesma regra do reconhecedor do jogo.

## Comando e velocidade: uma fonte de verdade

A lista de movimentos de Social está aprovada em design; **o mapa competitivo
de dois botões e seus parâmetros ainda dependem GD01/GD02**. Não preencher a
interface com quarto de lua, carga ou combinação inventada para torná-la bonita.
Enquanto isso, a página de revisão deve declarar “comando em definição” e
reproduzir somente animação diagnóstica, sem alegar ensino/teste de execução.

Para cada movimento, contrato proposto, integrado aos dados existentes:

- ID da ação e nome exibido; fonte da decisão e revisão do comando.
- Entradas semânticas (direções relativas, press/hold/release, simultaneidade),
  limites temporais, contexto/postura, recursos e precedência do reconhecedor.
- Referências às poses/tracks reais, ordem e duração por pose; objetos e seus
  tempos de vida; começo, terminais de sucesso/erro e retorno.
- Versão de regra/arte/receita e evidência. Campos não decididos ficam pendentes;
  nunca herdar números de drafts, de outro personagem ou de animação diagnóstica.

UI, demonstração e prática consultam essa mesma definição. Na demonstração
funcional, entradas programadas passam pelo reconhecedor de comandos do motor;
não se chama uma animação diretamente e se apresenta isso como comando aceito.
No modo de prática, o destaque de input lê a entrada observada/consumida e o
resultado lógico, não um cursor que sempre completa a receita.

**Velocidade normal é a do runtime da luta.** A cena não tem tabela paralela de
holds “cinematográficos”, nem retarda o golpe para o jogador ler os botões. O
jogador lê a receita antes; depois assiste ao ritmo real e, se desejar, repete.
A duração do preparo antes de cada demonstração é UI, separada da preparação
do golpe. Marcador de fase e input devem estar sincronizados ao estado real;
latência de submissão/apresentação é registrada, não escondida.

Replay lento e avanço de quadro são facilidades de revisão **identificadas**;
não aprovam a velocidade normal, não alteram o arquivo aprovado nem o relógio
do combate. Não acelerar emulador. Preservar holds/timing aceitos dentro de
seu escopo; 2/1/1/1/1/3 do jab de estudo não vira frame-data competitivo.

Para Laudo Final, mostrar condição de barra cheia e alvo elegível; separar
attempt/hit/whiff sem criar três comandos. O roteiro da demonstração programa
o ataque adversário necessário; não “ganha” o counter por ativar diretamente
o ramo de sucesso. Reset de uma repetição restaura atores, relógios, recursos
e objetos de forma explícita. Em jogo normal esses resets não existem.

## Integração, evidência e completude

Um arranjo compilado pode carregar páginas/ações por demanda. “Todos os assets
integrados” significa que a ROM os referencia e os apresenta corretamente no
percurso de revisão, não que todos estejam residentes simultaneamente em VRAM.
Usar banking/residência/loader existentes, sem motor paralelo ou build no jogo.
Manifesto lista cada asset e a rota para encontrá-lo, com estados ausentes
explicitamente pendentes. Catálogo incompleto serve a diagnóstico, não a aceite
integral. Animação de um único ator não aprova composição do duelo com rival.

Primeiro piloto: jab atual, se reaproveitável no escopo diagnóstico, para
verificar UI/timeline/reentrada. Esse piloto não resolve o par a 66–72 px nem
aprova Social completo. A demonstração funcional com comandos só se torna
aceitável quando o reconhecedor e o mapeamento estiverem decididos/integrados.
A implementação da cena é trabalho posterior ao contrato; neste lote não há
nova ROM ou arte do controle sendo apresentada como pronta.

Aceite futuro por ação e pelo pacote:

1. Mesmo ID, poses, durações e regra no duelo e na cena; prova no mesmo SHA,
   sem comparar somente GIFs ou screenshots. Observar todo ciclo normal e retorno.
2. Entrada correta executa o golpe; errada/incompleta não produz falso sucesso;
   hold, simultaneidade, lado oposto e falta de recurso obedecem à regra real.
3. Nome/ícones correspondem à ação. Corpo, arma, FX, rival e UI continuam legíveis
   no pior frame, cantos e casos de maior simultaneidade.
4. Repetição/skip/troca de ação/saída não deixam hitbox, projétil, áudio, estado
   ou input residual. Não confundir controle de navegação com comando de ataque.
5. Instrumentos com self-check, recursos/scanline/paletas/VRAM/RAM e VBlank
   medidos; FPS funcional alvo60/piso58 por janela, sem arredondar, com input e
   lógica reais. Áudio/captura e cleanup da sessão privada conforme pipeline.
6. Revisão humana de qualidade e compreensão: jogador identifica nome/comando,
   distingue demonstração de prática e consegue reproduzir a ação. Não declarar
   playtest humano apenas porque um script acionou a tecla.

Futuro item desbloqueável: reaproveitar conteúdo e cena, deixando ponto de
entrada/condição separado dos movimentos. Não implementar moeda, save,
conquista ou esconder instruções essenciais sem decisão do dono. É possibilidade,
não requisito imediato nem permissão para ampliar conteúdo por inferência.

## Prompt de continuidade — copiar daqui até o fim

Atue como artista de personagem em colaboração com a integração oficial de
Master of Fighters. Diga [Contexto SMS Carregado]. Trabalhe no checkout único
`/home/misael/Projects/SMSForge`, consumidor `SMS_projects/master_of_fighters`.
Leia AGENTS/continuidade, memória/GDD/roteiro/spec/TDD vigentes, o prompt
`doc/dr_social_complete_character_artist_prompt_v1.md`, o direcionamento
`doc/dr_social_artist_followup_review_20261101.md`, a matriz de cobertura, o
contrato v2 e este padrão. Use RTK/run_host; preserve o trabalho alheio.

O objetivo continua ser **Dr. Social completo e revisável**. O último commit
inspecionado, d7a3a2d, não o concluiu: bengala/bota/rapieira são chaves, estados
e especiais faltam, portraits são candidatos e não existe ROM integral desse
pacote. Não trate os estudos como aprovação nem abra ROM antiga para representar
conteúdo que ela não contém. Confira novas evidências, se houver, por fonte/SHA.

1. Faça inventário curto do que realmente está pronto, faltando e bloqueado.
   Preserve o jab v8 e as decisões de identidade/armas. Não recomece gerações nem
   repita as escalas/fases já reprovadas. O GDD permanece 66–72 px: não foi
   autorizada redução para 60, corte de arma ou ocultação de células.
2. Retome a causa dominante. A hipótese de guarda em três quartos não foi
   materializada nos dois desenhos; isso não é prova técnica de que ela falha.
   Proponha atuação que efetivamente responda à largura, respeitando corpo,
   casaco, pega e movimento; meça a proposta válida com par e representação
   oficiais. Não transforme o estudo de 32 px por faixa em anatomia artificial
   ou limite global arbitrário para todo golpe. Se precisar mudar alcance,
   identidade ou alvo, apresente alternativa concreta ao dono e prossiga nas
   peças independentes. Não gere intervalos caros de uma chave ainda ilegal.
3. Refine os portraits existentes antes de multiplicar saídas: limpar pontos
   dispersos, reconstruir volumes/contorno e alinhar âncoras faciais/crop entre
   expressões; diferenciar derrota do neutro. Conferir 1×/4× e paleta final.
   Atenção/fala e versus não são a mesma página; uma mudança de boca não fecha
   sozinha animação de fala ou os ciclos versus contratados. Complete seleção,
   demais expressões e estados previstos sem inventar arsenal ou lore.
4. Prepare storyboard e contrato visual da cena 10: nome do golpe, lutador
   executando, controle SMS 1/2 e direções/etapas legíveis. Mantenha referência
   Neo Geo como linguagem de demonstração, sem copiar arte nem quatro botões.
   Desenhe candidatos autorais de UI pelo método aprovado; texto/glyphs e
   composição precisam prova de tamanho nativo. Não é preciso um portrait grande
   no palco para cada golpe. Quantidade/residência deriva do budget medido.
5. Antes de mostrar comando, confira sua decisão e implementação. GD01/GD02
   permanecem pendentes: não atribua combinações por conta própria. Se faltar
   mapeamento, registre “comando em definição” na revisão e leve ao designer uma
   proposta explícita de controles, sem aprová-la. Nenhum botão de debug do
   viewer vira comando competitivo automaticamente.
6. Integre uma fatia funcional assim que arte/composição/comando permitirem,
   usando o consumidor, renderer, dados de animação e reconhecedor oficiais.
   Comece pequeno, prove nome/input/execução/retorno e continue até cobrir o
   personagem. Não monte outro motor ou editor. Se só houver piloto de animação,
   marque seu limite: ele não ensina comandos nem valida o pacote completo.
7. Use exatamente a velocidade normal da luta; mantenha UI de leitura separada
   dos tempos do golpe. Slow motion/step são revisão identificada, não substituto
   de observação contínua. Medir consumo de input, estado, framebuffer e retorno,
   incluindo ambos os lados, replay, erro, recurso insuficiente e troca de ação.
8. Entregue ROM identificada com catálogo de assets/ações efetivamente integrados,
   fonte→derivado→símbolo→ROM por hashes, vídeo normal/lento identificado,
   evidência de comandos e orçamento/pior frame. Sem composição legal ou motor
   funcional, declare a pendência exata e conclua o trabalho independente; não
   apresente galeria isolada como prova de combate completo.
9. Atualize matriz/lineage/memória e preserve fontes/evidência pelo fluxo vigente.
   Commit/push apenas de mudanças próprias revisadas; não publique referência
   privada ou tome alterações alheias. Não promova curadoria global, não implemente
   desbloqueio futuro nem comece outro personagem. Designer e dono validam primeiro.

Não encerre com outra coleção de poses sem explicar a causa que permanece e
sem executar o próximo ramo viável. O objetivo é pacote integrado e qualidade
observável, com diferenças entre desenho, animação, compilação e aceite claras.
