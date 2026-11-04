# 13-spec-cenas — master_of_fighters

> **DECISÃO VIGENTE DO PROPRIETÁRIO — 04/11/2026: SOCIAL IN-GAME CONGELADO.**
> Os sprites e animações atuais do Dr. Social não devem ser continuados,
> retocados, convertidos, integrados ou promovidos. Retomada futura: novo desenho
> do zero, a partir do concept/model sheet e das referências de tamanho mantidos.
> A cena D01 fica experimental. J.J. e Hayato/Kenseiden permanecem validados no
> recorte realizado. [Registro do congelamento](dr_social_ingame_freeze_20261104.md).
> As orientações anteriores para produzir o Social ficam históricas/suspensas.

A cena D01 é somente um experimento preservado de composição. Sua captura
contém o Social antigo congelado; não autoriza usar esse sprite como arte final.
Cenas e storyboards abaixo continuam nos seus estados próprios de projeto.

## Cena 10 — apresentação de golpes

Direção do dono em 2026-11-01; [contrato completo](character_move_showcase_standard_v1.md).
**Documentado, sem implementação/budget/aceite.** Não altera IDs 01–09/D01.

- Finalidade: reconhecer nome/função e aprender o comando real observando ação,
  consequência e retorno. Entrada: acesso de revisão; acesso de produto/menu
  ainda pendente. Saída: retorna ao chamador em estado conhecido, input limpo.
- Ações propostas: selecionar, assistir/repetir, experimentar, voltar; comandos
  de navegação aguardam GD01, sem competir com botões durante prática.
- Hierarquia: nome/receita → atuação no palco → resultado → navegação. Controle
  SMS com direcional/1/2, sequência e etapa ativa legíveis; forma acompanha cor.
  Controle não espelha seus números; setas respeitam o lado lógico do lutador.
- Simultâneos: ator, rival quando exigido, arma/objeto/FX do golpe, piso/fundo,
  nome, sequência, controle, feedback e áudio pertinente. Retrato grande/HUD
  completo não são obrigatórios. Medir simultaneidade de UI+golpe, não somar
  aprovações isoladas. Planejar P0/P1, tiles/fontes, SAT/linha, RAM/ROM, VRAM,
  transferências e pior frame; todos os valores integrados estão pendentes.
- Extremos/falhas: nome/comando longo, acentos, etapas simultâneas, hold/release,
  lado invertido, canto, resource vazio, input errado, replay/skip durante objeto,
  troca de ação e retorno. Fonte/comando ausente não gera demonstração falsa.
- Qualidade: controle autoral reconhecível, contraste e tipografia consistentes,
  sem sobreposição a rosto/arma; playback normal não desacelerado para caber texto.
  Legibilidade em 1× e movimento contínuo. Arte/clareza exigem revisão humana.
- Aceite: comando da UI e reconhecedor iguais; entrada → ação → resultado →
  recuperação na mesma ROM; vídeo+estado/input, orçamento, áudio e piso58 por
  janela sem arredondamento. Modo lento/step explicitamente revisão. Catálogo
  parcial não aprova o personagem completo. Desbloqueio futuro fora deste lote.

## Cenas da direção de fã — 2026-11-01

Vínculo: [GDD](11-gdd.md#direção-de-fã-e-campanha--proprietário-2026-11-01),
[roteiro](12-roteiro.md) e [TDD](15-tdd.md#campanha-apresentação-e-progressão--contrato-futuro-2026-11-01).
**Contratos documentados; implementação, orçamento e aceite em emulador
pendentes em todos os itens desta seção.** IDs 01/02/03 preservados; 04–09
são novas cenas autorizadas pela direção, não telas que já existem.

### Regras comuns de composição e transição

Informação principal de cada fase deve poder ser compreendida em 256×192,
em escala nativa e em vídeo contínuo. Fonte legível, contraste, ordem de
leitura e foco não dependem apenas de cor ou áudio. Repetição não deve tornar
as apresentações um obstáculo: skip/avanço convergem a endpoints limpos;
botão mantido não atravessa páginas e começa um golpe sem intenção.

Nenhum budget numérico novo é presumido. Para cada fase, engenharia deve
preencher RAM/ROM, tiles BG, tiles de atores atuais/próximos, PNT, SAT/pico
por scanline, cores P0/P1, uploads e pior VBlank, ciclos/áudio e janelas FPS
no SHA do teste. Medir transições além do estado estável. Enquanto a medição
não existe, o valor é **pendente**, nunca zero ou “cabe porque é cutscene”.
Palco encenado com três atores, retratos e efeito não herda budget de duelo
com dois. Roteiro permite escalonar aparições, mas mudança de função/qualidade
é tradeoff registrado, não corte silencioso.

### Cena 04 — abertura

- **Finalidade/informação:** apresentar elenco e ruptura com empolgação; logo
  conclui a montagem. Beats A1–A5 no roteiro são proposta executável a revisar.
- **Entrada/saída:** boot válido → sequência; término ou skip → 05 título.
  Replay e política de exibição inicial dependem FC02. Reset volta ao boot
  determinístico, sem estado parcial da montagem.
- **Ações/feedback:** avanço/skip com comando definido em GD01/FC02; feedback
  discreto e inequívoco, sem consumir a confirmação também no título.
- **Hierarquia/simultâneos:** uma composição focal por beat; retratos/corpos,
  ambiente, ruptura e música conforme timeline; logo substitui o foco anterior.
  Mostrar nove heróis ao longo da sequência, não exigir nove sprites juntos.
  Sem HUD de combate. Elenco/cena que não estiver residente precisa carga selada.
- **Extremos/falhas:** skip durante upload, logo, efeito e música; som desligado;
  repetição; botão mantido. Fonte ausente ou quadro corrompido bloqueia build,
  não vira tela preta longa chamada “suspense”.
- **Aceite:** reconhecer elenco, ameaça e nome; ritmo funciona sem áudio;
  montagem tem preparação, contraste e encerramento. Vídeo completo/skip,
  memória/VDP/FPS e áudio integrado na mesma ROM. Não aprovar só screenshot do logo.

### Cena 05 — título e acesso

- **Finalidade/informação:** identidade do jogo e próximo passo claro.
- **Entrada/saída:** de 04 ou retorno de percurso; início abre escolha de modo;
  História/Versus → 01 seleção; opções → 06; disponibilidade de Arcade depende
  FC02. Repetir abertura é proposta, não opção obrigatória ainda.
- **Ações/feedback:** foco legível, navegar, confirmar, voltar conforme contrato
  de dois botões. Sugestão “APERTE 1 OU 2”; não depender de botão Start ausente
  no controle SMS. Não usar Pause do console como substituto obrigatório.
- **Hierarquia/simultâneos:** logo, convite/menu e fundo autoral; eventual movimento
  não compete com foco. Música de título/cursor/confirmação com prioridade definida;
  sem HUD nem lutadores de combate simultâneos por inferência.
- **Extremos/falhas:** seleção mantida, extremos da lista, modo não implementado,
  retorno de opções e repetição. Protótipo pode sinalizar indisponibilidade;
  entrega não pode apresentar modos prometidos como links vazios.
- **Aceite:** jogador identifica modo escolhido e entra uma vez; foco e opção
  correspondem; logo permanece íntegro; teste inclui todos os retornos.

### Cena 06 — opções

- **Finalidade/informação:** ajustar comportamento real com estado atual visível.
- **Entrada/saída:** 05 → 06 → mesmo foco em 05. Lista exata pendente FC02;
  sugestões para discutir: volume/música/SFX, dificuldade e velocidade de texto.
  Nenhuma sugestão autoriza menu sem efeito ou mudar velocidade do emulador.
- **Ações/feedback:** selecionar item, modificar, comparar valor, voltar; política
  aplicar/cancelar/resetar precisa decisão. Texto explica efeito concreto.
- **Hierarquia/simultâneos:** nomes/valores/foco/instrução; fundo discreto, sem
  atores necessários. Prévia sonora não pode sobrepor canais ou continuar ao sair.
- **Extremos/falhas:** mínimos/máximos, mudo, repetição de input, saída/reentrada,
  reinício. Persistência explicitada; não prometer save sem solução implementada.
- **Aceite:** cada opção altera algo verificável; estado mostrado corresponde
  ao estado aplicado; player consegue restaurar/recuar sem ficar preso.

### Cena 07 — narrativa no palco e diálogos

- **Finalidade/informação:** compreender quem chegou, por que lutam e o que muda
  após o duelo. H1–H7 e cameo têm contratos distintos no roteiro.
- **Entrada/saída:** nó da campanha → setup de palco → encenação/diálogo → estado
  competitivo inicial da 02; após resultado → conversa/03/próximo nó ou 09.
  No cameo, entrada da 02 → sequência → mesmo estado inicial sem dano.
- **Ações/feedback:** avançar página, completar texto se revelação gradual for
  escolhida, skip para endpoint definido. Corpo indica reação enquanto retrato,
  nome e caixa identificam falante. Comando exato pendente; não adivinhar texto
  a partir de balão fora da tela.
- **Hierarquia/simultâneos:** no diálogo, fala/rosto/falante são foco e palco
  contextual permanece claro; em ação, retirar caixa que oculta ameaça. Piloto
  prevê Hayato+monstro, chegada do visitante com presença potencial dos três,
  portal/raios, depois retrato/caixa; cada combinação exige budget próprio.
  Cameo prevê rival+meteoro, rival+Alex+balão, fumaça/transição, rival+Shinobi;
  não manter Alex e Shinobi residentes sem justificar custo. Música, SFX e voz
  são trilhas com prioridades, não promessa de tocar tudo simultaneamente.
- **Extremos/falhas:** texto longo/acento/nome, páginas repetidas, skip no impacto,
  mudança de falante, input mantido, rival com guarda diferente, borda, som mudo.
  Monstro/cameo não participa de placar, IA competitiva ou seleção por acidente.
- **Aceite:** entender motivação sem explicação externa; super encenado atinge
  monstro e não o futuro rival; sequência e skip resultam em mesmos lutadores,
  posições, recursos e controle. Ver ação → consequência → conversa → round
  → resultado → conversa, com todos os resíduos eliminados.

### Cena 08 — vitória e evolução de Alis

- **Finalidade/informação:** celebrar desempenho e decidir crescimento de forma
  rápida e informada, sem quebrar a personalidade da heroína.
- **Entrada/saída:** duelo vencido na História e resultado único → pose/cue →
  ganho de nível/pontos → prévia de atributos → confirmar → destino da campanha.
  Versus e outros personagens não entram aqui. Derrota/continue dependem FC01.
- **Ações/feedback:** navegar quatro atributos; acrescentar/reverter proposta;
  conferir antes/depois; confirmar uma vez. Sugerir saída com pontos guardados
  somente se regra for aprovada; até lá skip nunca descarta/gasta pontos em
  silêncio. Teto, pontos disponíveis e efeito precisam leitura inequívoca.
- **Hierarquia/simultâneos:** primeiro vitória/Alis; depois nível/pontos e opções;
  pose pode permanecer em repouso legível. Não exigir rival animado atrás do
  painel. Retrato/ícones só se necessários e orçados. Cue Phantasy Star tem
  proveniência/versão pendentes; animação, texto e sinal sonoro concordam.
- **Extremos/falhas:** zero pontos, todos os tetos, múltiplos níveis, 1–2 versus
  1–3 em testes de balanceamento, confirmação repetida, retry, último chefe,
  reset, texto de ganho e valores máximos. Se não houver outro combate após
  o chefe final, decidir recompensa/epílogo em vez de forçar escolha sem efeito.
- **Aceite:** jogador sabe o que ganhou e como a próxima luta muda; prévia não
  altera stats antes de confirmar; prêmio nunca duplicado. Testar início/meio/
  fim, builds puras e mistas, habilidade variada e ausência de influência no Versus.

### Cena 09 — encerramento

- **Finalidade/informação:** resolver ameaça e recompensar o percurso com epílogo
  coerente com o herói, retomando motivo da abertura.
- **Entrada/saída:** último confronto resolvido → desfecho FC04 → epílogo →
  retorno a 05/01 conforme FC02. Nenhum chefe extra por suposição.
- **Ações/feedback:** avanço/skip preserva resultado/desbloqueio único e destino;
  sinal claro de conclusão. Replay/créditos são propostas a fechar, não sistemas
  já aprovados automaticamente.
- **Hierarquia/simultâneos:** resultado, consequência no mundo, gesto do herói e
  mensagem final em sequência; texto, quadro/atores e música por beat, sem HUD
  competitivo esquecido nem todos os personagens obrigatoriamente em cena.
- **Extremos/falhas:** vitória final com recompensa Alis pendente, skip/reset,
  replay, derrota final/continue conforme GD04, dados de epílogo ausentes.
- **Aceite:** reconhecer o que foi resolvido e o destino do herói; partida termina
  e pode ser reiniciada sem objetos/comandos/save indevidos. Final não é só KO.

### Cena 02 — arena Kenseiden e fases de apresentação

**Direção do dono:** ambiente japonês escuro e belo, colunas, templo/castelo ao
fundo, possível estátua budista; Alex Kidd incorporado à pedra como easter egg;
papéis/fitas/selos ao vento, lanternas com luz perceptível e folhas ocasionais.
Estátua, desenho dos selos e arquitetura precisam referência identificada:
não tratar todos os símbolos religiosos como ornamentos intercambiáveis.
O rosto na pedra precisa confronto com captura da referência Kenseiden antes
da arte; memória do local exato não é prova. A presença desejada já é direção
válida do proprietário, independente dessa verificação histórica pendente.

**Composição e leitura:** chão e faixa de combate primeiro; colunas enquadram
sem cortar silhuetas, fundo dá profundidade por desenho/contraste. Easter egg
na faixa observável, sem placa/pisca/seta; reconhecível em tamanho nativo ao
observar, secundário durante troca de golpes. Não acrescenta colisão/recompensa.
Lanterna propõe luz local em BG; não alterar paleta compartilhada dos corpos
para fingir iluminação. Papéis têm peso/ponto de fixação e vento coerentes;
folhas não parecem projéteis, não cobrem rostos nem mascaram preparação.

**Simultaneidade a medir:** par de lutadores + HUD + objetos reais de combate
+ efeito autorizado + cenário animado + música/SFX; durante H1–H5, usar
composição narrativa própria. Sugerir alternância de detalhes ambientais,
sem assumir que todos animam continuamente. Se orçamento apertar, comparar
soluções BG/stream/residência antes de eliminar função; registrar resultado
visual, custo medido e decisão. Artista não recebe limite inventado de poses.

**Entrada/saída e extremos:** setup completo → apresentação contextual →
round → vitória/derrota → conversa/resultado. Repetir round não repete toda
cutscene por acidente. Testar ambos os lados, cantos, poses máximas, contraste
nos fundos claros/escuros, sobreposição dos efeitos, golpe durante fase mais
carregada da animação ambiente e saída para painel de Alis. Modo mudo mantém
ameaça compreensível; nenhum detalhe de cenário interfere com regra de combate.

**Aceite:** vídeo demonstra atmosfera viva, reconhecimento do easter egg sem
destaque artificial e leitura de luta preservada; revisão humana para anatomia,
composição e fidelidade; medições de recursos/scanline/VBlank/FPS no pior caso.
Screenshot estático não prova vento/luz/folha nem retorno de uma apresentação.

## Contratos de experiência das cenas — 2026-11-01

Vínculo: [GDD vigente](11-gdd.md#contrato-de-experiência--revisão-de-design-de-2026-11-01)
e [roteiro de interação](12-roteiro.md). Estas cláusulas são intenção e
critérios de teste; **não são budgets medidos**. Sistemas adicionais autorizados na direção de fã
acima seguem seus próprios contratos; este recorte anterior não os implementa.
Seleção = 01, duelo = 02, arcade = 03. D01 identifica somente a placa de
leitura do duelo cujo nome técnico histórico é `cena01_duel_read`.
As telas completas ainda não existem no consumidor; sem ROM, critérios ficam
pendentes. Nenhum valor de RAM, VRAM, áudio ou timing é deduzido destas tabelas.

### Cena 01 — seleção

**Finalidade/informação principal:** escolher uma identidade de luta e entender
quem está disponível. O roster registrado é nove heróis e quatro chefes;
disponibilidade/jogabilidade dos chefes aguarda decisão GD04. Não apresentar
uma célula de chefe como selecionável antes dessa decisão.

**Entrada, saída e transições:** entrada pelo começo do fluxo e retorno de
duelo/arcade conforme GD04. Inicialização mostra foco, identidade e estado
disponível/bloqueado coerentes. Confirmar uma escolha válida prepara a cena 02;
trocar foco não inicia carga de round nem muda seleção confirmada por engano.
Cancelar/reselecionar, comportamento nas bordas e repetição do direcional
precisam de comando e política selados em GD01. Não criar uma tela de título
ou opções não previstas só para resolver esse destino.

**Ações/feedback propostos:** navegar, inspecionar nome/identidade, confirmar e
corrigir escolha antes da luta. Foco visível e confirmação visual/sonora são
distintos; escolha indisponível informa o estado e mantém navegação possível.
O jogador não depende só de cor ou som para saber qual personagem escolheu.

**Hierarquia e simultaneidade:** primeiro foco/nome/disponibilidade, depois
imagem de identidade, depois contexto. Grid, marca de foco, nomes e imagem
selecionada disputam BG/P0/P1; não assumir treze lutadores animados simultâneos.
Não exige HUD de vida/timer/Super aqui. Música de seleção e SFX de navegação/
confirmação são funções propostas; composição e canais ainda não contratados.

| Situação | Resultado esperado e critério observável |
|---|---|
| Normal | Foco e nome correspondem ao mesmo ID; confirmação leva ao lutador escolhido no lado correto da cena 02. |
| Bordas/segurar/reentrada | Não há foco perdido, escolha dupla ou input de confirmação reaproveitado como ataque. Wrap/repeat aguardam GD01. |
| Célula indisponível | Estado visual inequívoco; não inicia luta vazia, sem depender de um som de erro. |
| Identidade/asset não disponível | Bloquear promoção da build; não exibir outro lutador, arte provisória ou seleção falsa como substituto. |
| Retorno de arcade/derrota | Foco, desbloqueios e seleção seguem a política aprovada; nenhuma persistência é inferida. |

**Qualidade/aceite:** testar seleção e correção sem instrução verbal,
legibilidade a 256×192 e correspondência seleção→round. Fonte de identidade
deve continuar reconhecível no retrato e no lutador. Não há budget nem prova
de seleção nesta revisão; responsável engenharia/UI + arte, decisão GD01/GD04.

### Cena 02 — duelo 1v1

**Finalidade/informação principal:** administrar distância, ameaça e resposta,
entender a consequência e vencer melhor-de-três rounds. A leitura começa
antes do primeiro golpe e termina só depois de um resultado compreensível.

**Entrada e preparação:** receber IDs confirmados, carregar composição válida
com display desligado conforme TDD, estabelecer chão/posições/vida/estado de
round. Apresentações já contratadas não são gameplay. Distinguir visualmente
“preparando” de “controle liberado”; duração e skip dependem de decisão, sem
criar contagem falsa. Primeiro input de combate não pode vir de uma confirmação
mantida na seleção. Regras de reset de vida, posições e Super ficam explícitas
antes de implementar; barra entre rounds é GD02.

**Interação:** movimentos/guarda/especiais seguem somente os kits aprovados e
comandos futuros GD01. Para cada ação, observar input → preparação → ameaça →
hit/block/whiff → recuperação. Golpe do rival deve ter pista antes do contato;
IA não pode esconder a preparação para parecer mais difícil. Nível de reação,
frequência e padrões são hipóteses a testar, não vantagem por acesso ao input.

**Consequência/encerramento:** hit e guard produzem reação corporal/visual e
SFX distintos; whiff preserva o vazio do contato. Vida, timer e marcadores de
round devem representar estado real. Ao resolver o round, impedir dano/objeto
residual, mostrar vencedor/derrota e preparar próximo round ou cena 03.
Empate, double-KO, time-over, prioridade entre eventos simultâneos e retorno
após derrota ficam pendentes em GD04; não escolher vencedor pela ordem dos
atores no código.

**Hierarquia visual:** lutadores/arma ativa/ameaça primeiro; separação do chão
e apoio sustentam distância; nomes/vida/timer/round/Super informam estado real;
cenário apoia sem encobrir rosto, punho, ponta da arma ou leitura da guarda.
Não trocar identidade por silhuetas encolhidas nem congelar atuação para
acomodar HUD. Efeitos só comunicam eventos existentes e devem deixar contato
legível. Não usar brilho de cenário como falso hit ou ameaça.

**Simultaneidade contratável:** dois lutadores completos, BG/chão, nomes/vida/
timer/estado de round e Super quando implementado; objeto/efeito somente se
autorizado no movimento. Bumerangue de Social é uma instância ativa; a amostra
J.J. não autoriza projétil. Música, SFX de ataque/impacto/guarda e conclusão
competem nos canais PSG. Proposta de prioridade sem alocação de canais:
resultado/contato relevante acima de decoração; som interrompido deve restaurar
música sem nota presa. Nenhum asset ou canal novo foi produzido aqui.

| Situação | Teste de experiência e evidência necessária |
|---|---|
| Neutro e aproximação | Identificar quem controla, orientação, chão e distância; deslocamento corresponde ao input e à animação. |
| Hit / block / whiff | Mesmo golpe e distância controlada; ligar caixas, pose, vida/guard do rival, feedback e retorno; erro não acerta invisivelmente. |
| Face trocada/bordas/sobreposição | Preservar corpo, arma e identificação; colisão não depende da ordem de SAT nem sacrifica permanentemente um lutador. |
| Input mantido/solto/repetido | Sem ação automática não prevista, estado preso ou cancel involuntário; registrar primeiro quadro que aceita nova ação. |
| Duas ações/objeto/HUD/PSG simultâneos | Simular composição real e observar SAT/framebuffer/pior frame. Espaço livre na SAT total não garante linha livre. |
| Queda, guarda, Super e interrupção | Estado tem saída; golpe não captura baixo/projétil fora da regra; física aérea continua após hit. |
| KO/time-over/empate/último round | Resultado único e visível, nenhum ataque residual; destino correto e regras GD04 exercitadas. |
| Pose ainda não residente/asset inválido | Deadline perdido é defeito, não hitstop; não manter caixa ativa sobre pose velha nem aprovar ator omitido. Bloquear aceite e corrigir causa. |

**Qualidade/aceite:** ação compreensível e coerente com personagem, feedback
distinto, consequência correspondente ao contato, recuperação observável e
fim de round funcional. Exige a carga inteira e alvo60/piso58 por janela
válida (§133), pacing/worst-frame e áudio reais do mesmo SHA. Os pares
diagnósticos abaixo não pagam aproximação, contato, HUD dinâmico ou rounds.

### Cena 03 — progressão de arcade e retorno

**Finalidade/informação principal:** entender o resultado do duelo, o próximo
desafio e qualquer desbloqueio realmente conquistado. Hall→chefes/dificuldade
crescente pertence ao loop do GDD; ordem, critérios de liberação e persistência
ainda precisam GD04. Campanha, cutscenes e encerramento agora seguem a direção de fã acima;
não inventar suas escolhas ainda pendentes nem duplicar Arcade/História sem FC02.

**Entrada, saída e ações:** entrar com resultado único da cena 02; apresentar
resultado/próximo oponente e aguardar confirmação ou avanço conforme política
a decidir. Vitória não final prepara próximo duelo; conclusão retorna à
seleção conforme loop. Derrota/continue, cancel e recomeço aguardam decisão;
devem sempre conduzir a um estado conhecido, sem repetir concessão de prêmio.
Prévia de ameaça/identidade do oponente pode usar os retratos já previstos,
sem criar nova mecânica de scouting ou tela versus adicional.

**Feedback/hierarquia:** resultado primeiro, destino/próximo adversário depois,
recompensa só se efetivamente aplicada. Vitória/derrota não podem compartilhar
texto ou pose contraditórios. Personagens/retratos, nomes, indicador de etapa
e eventual marca de desbloqueio formam a composição; não exigir todos os
combatentes animados. HUD de luta deve ser encerrado, não congelado como se a
luta continuasse. Áudio de conclusão/transição dá respiro e prepara a próxima
entrada; duração, faixa e canais pendentes.

| Situação | Critério observável |
|---|---|
| Vitória intermediária | Resultado e próximo ID corretos; confirmação inicia o próximo duelo uma vez. |
| Último oponente | Encerramento legível e retorno à seleção; sem ID inexistente nem retorno infinito ao chefe. |
| Derrota/empate | Mensagem, pose e destino coerentes com GD04; não anunciar vitória por ausência de regra. |
| Input mantido/reentrada | Não saltar resultado sem política nem duplicar avanço/desbloqueio. |
| Recompensa já obtida | Estado permanece consistente; persistência e reinício definidos pelo dono, não presumir SRAM. |
| Dados incompletos | Não inventar adversário/prêmio para prosseguir; falha de contrato bloqueia promoção da build. |

**Qualidade/aceite:** o jogador consegue dizer o que ocorreu e como continuar;
dificuldade crescente é demonstrada por decisões/padrões legíveis, não apenas
HP aumentado. Testar um caminho completo seleção→duelo→resultado→reentrada
e os extremos antes de expandir conteúdo. Budget e implementação pendentes.

### D01 — amostra diagnóstica da leitura do duelo

**Propósito:** inspecionar o par Social/J.J., chão, nomes e medidores estáticos,
com entrada manual na animação aceita e retorno. É parte da preparação visual
da cena 02; não oferece a luta nem encerra um round.

Entrada: boot do perfil `MOF_CENA01=1, MOF_JJ_SAMPLE=2`; autoplay é ferramenta
diagnóstica. Botão 2 alterna autoplay, botão 1 solicita ação quando em guarda;
soltar/reapertar permite nova ação. Direcional não desloca os atores; não há
seleção, defesa, contato, perda de vida, timer ou transição arcade. Saída é
encerramento da sessão privada. Texto/medidores permanecem estáticos; não
apresentá-los ao jogador como HUD funcional.

Pior composição **conhecida**: par fixo em doze composições mediu pico 8 por
scanline; um objeto novo na mesma linha pode ultrapassar o limite. A placa P0
adiciona 12 padrões/384 B antes do loop; não acrescenta sprite. Não calcular
“folga para laser” de 64 menos 50 SAT: esse total não resolve scanline ou
transferência. Detalhes e fonte dos números estão na seção histórica da placa
abaixo. Aproximação/ataques simultâneos ainda não foram medidos.

QA desta revisão: ROM `90ea0f98febf4e047e6ca4637af1c454dd9ac7971e5b0bd00fec058c5ebf2405`,
sessão privada `d4d91c97840f45d1b46f85dab83e6db6`, encerrada. Duas ações
manuais e retorno/reentrada: 174/174 quadros conferidos; holds 7/4/2/3/6
preservados, guarda nos índices 102–131 e 154–173. Índices são zero-based
no vídeo stepped, não frames competitivos. Botão aplicado VDP198/250 e
preparação visível VDP201/253; intervalo ponte→imagem de três avanços, sem
medir o instante de aceite interno. Relatório/limites vinculados no memory
bank. FPS, VBlank, áudio, percepção contínua e combate permanecem pendentes.

### Passagem para arte e engenharia

Artista recebe intenção, fonte de identidade, ação inicial/final e critérios
de leitura; propõe atuação corporal e poses. Engenharia mede layout, pares
por pose/distância, P1/P0, tiles residentes/próximos, SAT/linha, RAM/ROM e
VBlank; devolve custo e causa concreta. Antes de mudar alcance, trajetória,
arma, escala relativa ou identidade para caber, registrar alternativa e
obter decisão do dono. Não reduzir silenciosamente desenhos ou função do golpe.

Primeiro negociar técnica de packing/residência e prioridade de informação,
preservando arte e comportamento aprovados. Toda alternativa tem controle,
delta, custo medido, efeito na experiência e estado de aceite. Os budgets
históricos são diagnósticos vinculados a seus SHAs; o budget integrado das
cenas 01–09 segue pendente. Conteúdo segue o GDD vigente; este documento
não fecha as decisões ainda abertas nem autoriza extensões além dele.

## J.J. — seleção aprovada pelo proprietário

A resposta “aprovado” fecha o conceptv5/fontev6, a proporção da Zillion,
os seis desenhos sem FX e o retorno apresentado com7/4/2/3/6. Preservar arte,
tempos e ROMs; decisão em `decisions/jj-zillion-character_owner_approval.json`.
Checkpointv7 registra o aceite sem inventar percepção contínua ou nova sessão.
As pendências de aceite nas seções anteriores são históricas. Objetos/FX,
combate completo, produção e homologação global continuam fora deste aceite.

## Histórico técnico anterior ao aceite

## Par J.J./Social vigente — fonte v6, dados v5 sem FX

Medição oficial das 12 composições (seis poses × duas faces): normal 8×8,
180 padrões/5.760 bytes residentes, máximo de 50 entradas SAT, pico 8/linha.
Canvas 104×88, pivô (48,80), origens X16/128 e Y64 mantêm chão visível Y143.
P1 única compartilhada de 15 códigos úteis, com os 902 pixels/índices/RGBA de
Social preservados. Sem efeito/projétil; não extrapolar esse pico para FX futuro.
Três builds32KiB, gates e QA260frames passaram. VBlank3.000frames por ROM:
base0derrame/mínimo213,stress1280derrame/mínimo224. FPS8s59,32/58,36 falhou;
confirmação20s59,79/59,84 passou, sem provar pacing porframe. Recibos em `out/diagnostics/jj_zillion_single_shot_v5/`.
A correção pontual da fonte6 tem zero delta SMS, com reuso explícito por hash.

## Histórico J.J. v1 — pulso incorporado supersedido pela direção sem FX

Amostra diagnóstica: guarda + cinco poses de disparo único, com pulso de laser finito em duas exposições, junto do Social preservado. Usar a mesma rota e escala comum do estudo anterior; paleta/material, registro de sola e grade nos dois sentidos entram no contrato desde o início. Tetos físicos 8/linha e 64 SAT; residência e pior VBlank do novo par ainda `pending`, incluindo degrau adicional. Contagens reais em `jj_zillion_single_shot_route_v1.json`; nada herdado do budget de Hayato.

## Seleção atual — fonte v4, somente tempos no perfil v7

Oito PNGs por lado e sete manifestos de cena por lado são byte-idênticos à v4.
O header inteiro difere somente na tabela8/1/2/7/2/5. Recursos e geometria são
reutilizados pela identidade dos arquivos; conversão oficial do perfil confirma
219padrões/7.008B,max53SAT,pico8. Não há distorção de lâmina, mudança de escala,
P1, posição ou equipamento. Aceite do dono: preview fonte com esses tempos.
QA nova passou260quadros nos dois sentidos, incluindo R02original e guarda.
Gravação nova480quadros exatos. FPS base59,71/59,46 em duas janelas8s;
VBlank3.000frames por ROM,0derrame,mínimo213 base/223 stress128, sessões fechadas.
SHAs v7 no memorybank; números v6 abaixo são históricos. O aceite humano da
fonte/tempos e a prova técnica desta amostra não aprovam combate completo.

## Histórico — fonte v6 rejeitada, tempo contextual e espada

Mesma cena diagnóstica, escala, P1, poses e posições da v4. Conversões
`converted_v6_left/right`: 220 padrões/7.040 bytes residentes, máximo 53
entradas SAT e pico de 8 sprites por linha nas 14 composições medidas pelo
adaptador normal 8×8. Sete PNGs por sentido são byte-idênticos à v4; somente
R02 tem delta de 110 pixels na região da lâmina. Social, corpo, sola e demais
poses preservados. Retângulo de amostragem [50,53,169,159] mantém a grade da
fonte sem mudar pixels. Componente solto da tentativa v5 foi reparado por patch
autorado da ponta, não pela remoção de pixels SMS. Todos os 16 PNGs passam
componentes min4/c8; materiais seguem revisão visual independente separada.
QA nova:260quadros exatos nos dois sentidos e480quadros de gravação real na
ROM direita. VBlank selado3.000frames por ROM:0derrame,mínimo213 base/223
stress128. FPS base59,74/59,42 em duas janelas8s. Esses números pertencem aos
SHAs v6 do memorybank; não aprovam qualidade temporal/percepção ou combate completo.

## Composição corrente — corte corporal, fonte v4

Mesmo par Hayato/Social sem cenário/HUD/áudio novos. P1 idêntica ao Socialv8,
15códigos úteis, uma única escala comum. Perfil8×8 explícito no adaptador
canônico:219padrões/7008B residentes em0..1FFF, PNT3800,SAT3F00, até53objetos
naSAT e8/scanline nas14composições. QA de ambas as orientações apresenta236quadros
exatos; vídeo nativo atual acrescenta480quadros exatos. VBlank selado3000frames:
zero derrame, mínimo213 base/223 stress128; FPS59,78/59,67 no perfil base.
Contagens estáticas, reprodução correta e throughput não aprovam expressividade.
Canvas88×88/pivô40,80, origens24/136,64 mantêm pixels na mesma tela/solo144.
Fases por pose e orientação estão nas receitas, sem omitir células visíveis.
Não aplicar budget histórico8×16 ou aprovação da guarda a esta sequência.

## Histórico: Hayato corte curto × guarda Social — diagnóstico 2026-10-29

Fonte4poses, mesma transformação x2/3,y6/7+extra2/3 e P1 da guarda anterior.
PGcanvas80×80,pivôSMS32,72;origens32,72 e144,72 invertidas noespelho.
Âncoras ópticas C01/C03/C04y126,guard/C02y127; todos osPNGs terminam72,
portanto últimaopaca143 no runtime.202patterns/6464B,33SAT máximo,pico8;
estas são contagens do emissor estático, não orçamento de VBlank observado.
Todos osframesresidentes, base atualiza sóSAT. Próximo degrau128B prefixo
residente correto, sem mudança visual. ROM e entrada/holds precisam de QA nova.
Não herdar FPS/VBlank do checkpoint estático. Fonte/previews e controles em
out/diagnostics/hayato_short_cut_v1/, próximo aceite no memorybank atual.

## Par diagnóstico Hayato + Dr. Social — 2026-10-29

GuardaHayato v2,source0b72e603…,materialmap2,registrobaseline3. Quatro pares:
guardas em ambos os lados e Socialjab contra guardaHayato nos dois sentidos.
Canvas porPNG80×80;pivôSMS(32,72);origens(32,72)/(144,72),trocadas noespelho;
solasvisíveisy143,boundary144. P1comum15códigos doSocialv8, P0fundo0x15.
Arma não entra na altura anatômica; source144×144 não é canvas obrigatório
para futuros movimentos. Mesma transformação de elenco; não normalizar altura
por bbox de equipamento. CorposSMS~58–60px no diagnóstico, sem claim de fechar
faixa absoluta68–72px da produção.

Guardas66patterns/2112B,32SAT,pico8; Social6poses contra guardaHayato
222patterns/7104B,35SAT máximo,pico8. Todasresidentes; baseSATsomenteVBlank.
Baseline3 inclui faseSocialJ04espelhado[5,9], medida após corrigir1px nos pés.
0derrame em3000frames,mínimo207; degrau+128B0derrame,mínimo218. FPSmédioNTSC
59,67/59,81 em8s. Não há prazo/streaming/dano/hitbox/açãoHayato aprovados.
Controle, revisão, SHAs, sessões privadas encerradas e índices no memorybank
atual e out/diagnostics/hayato_cps2_sample_v1/result.json. É checkpoint estático,
não cena de combate/entrega; ação própria depende da escolha já solicitada.

> Budget REAL por cena. **Autoridade #3.**
> Regra: **"estimado" é proibido neste arquivo.** Todo número aqui é medido,
> com o método da medição citado. Folga não medida é timidez (§18).

## Contrato de hardware (fixo, não negociável)
| Recurso | Limite físico |
|---------|---------------|
| Tela | 256×192 |
| VRAM | 16 KB |
| RAM | 8 KB |
| Sprites por scanline | 8 |
| Sprites na SAT | 64 |
| Paletas CRAM | 2 × 16: P0 para BG/HUD, P1 para todos os sprites; índice 0 transparente só para pixels de sprite; BG índice 0 sempre visível; P0 índice 0 é backdrop |
| Cores úteis simultâneas | 30 |
| Janela VBlank | ~4.5 ms (NTSC) — **não existe DMA** |
| ROM sem mapper | 48 KB |
| Padrão gráfico 4bpp | 8×8 px; 32 B; 512 padrões no total da VRAM |
| Janela de padrões para sprites | 256 padrões, selecionados pela base do reg. 6 |
| Objeto sprite | 8 px de largura; 8 ou 16 px de altura |
| CRAM | 32 entradas; até 15 cores comuns de sprite em P1; P0 usa 16 slots de BG/HUD, com índice 0 visível e reservado como backdrop no projeto |

Não existe limite físico universal de quadros por folha. O máximo por asset é
decisão de projeto, derivada de padrões residentes, compartilhamento, pools,
ROM/banking e upload por VBlank. O valor fica pendente no TDD até haver layout,
alocação e medição reais. Contagem de patterns da imagem não substitui
metasprite, SAT, sprites/scanline ou orçamento por cena.

### Prova de duas poses — Dr. Social (inventário, não orçamento de cena)
O padrão de escala está no GDD/TDD: *Fatal Fury Special* Game Gear, altura
proporcional ao viewport SMS e faixa-alvo do roster 66–72 px; canvas por pose
fica tile-alinhado e é dimensionado pelo conteúdo, não fixado em 96×96.

O candidato atual é
`data/source_art/asset_conversion_proofs/dr_social/dr_social_sms_keypose_proof_v4.json`.
Registra duas imagens 80×80 (10×10 tiles): idle com 42 padrões únicos; ação
com 47; união do par 89 (2.848 B brutos 4bpp). A v3 foi superada porque a
reamostragem achatava a terminação da bengala; a v4 usa o frame-fonte 06, em
que a ponta arredondada permanece legível. As duas são poses estáticas, não
quadros de animação, e mantêm pelo menos 1 px transparente em cada borda. A
contagem de padrões é inventário da arte, não alocação residente nem contagem
de objetos SAT. Metasprite, pico de scanline, pool VRAM/RAM, banking e carga
VBlank permanecem pendentes; não usar esses números para fechar o budget de
uma cena. O scan não encontrou ilhas opacas menores que 2 px; regiões por
material, anatomia, identidade visual do terminal da bengala e review artístico
seguem pendentes. A alocação de paleta runtime está em
`doc/palette_runtime_contract_v1.json`; não há 14 paletas de sprite separadas.

## Trecho diagnóstico CPS2 idle/jab — 2026-10-28

Owner e fonte: `dr_social_cps2_sample_v1.md`. ROM base SHA `f5d54b15…`,
32.768 B. Medição do pool e dos sete manifestos `scene_*.json` pelo pipeline
tall e `audit_sprite_line_sim.py`: 212 padrões/6.784 B residentes, 31 SAT e
pico8 por scanline em idle e J01–J06, zero overflow. Uma P1 comum de15 cores
úteis com o Ken autorizado. Sprites na janela0x0000..0x1FFF; tile0 vazio
compartilhado com fundo diagnóstico, PNT0x3800, SAT0x3F00. Não há cenário,
HUD, projéteis ou áudio neste inventário.

No setup, padrões/CRAM são carregados com display desligado. Em cada tick de
animação, somente SAT é copiada ao VDP; os desenhos ficam todos residentes.
Selo autônomo3.000frames no Emulicious: `vovf_delta=0`, `vline_min=207`.
Degrau medido de+128B de padrões corretos por VBlank: também zero derrames,
`vline_min=217`, em outra ROM/sessão identificada no relatório do lote.
Não há conversão desses valores em milissegundos CPU ou teto máximo.

SMRT em duas janelas8s:59,43/59,56fps; alvo NTSC passou no instrumento.
Janelas curtas anteriores falharam e permanecem registradas. Sem qualificação
PAL. Todos os números vêm de JSONs em `out/diagnostics/dr_social_cps2_sample_v1/`
e `out/evidence/sessions/`, com quatro sessões encerradas e QA visual nativa
independente1/1. Não se transporta o resultado para produção, gameplay ou
outros conteúdos. O orçamento integrado da Cena01 abaixo continua aberto.

## Trecho diagnóstico facial v5 — 2026-10-29

ROM `fc46d77b…`,32.768B: fonte v5 e receita SMS identificadas no handoff.
216 padrões/6.912B;31SAT em idle/J01/J02/J03/J05/J06 e32SAT em J04, pico8 em
todos os sete pares pelo conversor tall/simulador. Fonte larga v6 reprovou
J04/pico9 e não foi buildada. Layout/CRAM/transferências iguais à baseline,
com os novos patterns residentes. FPS8s59,62/59,79NTSC; selo3000frames,
zero derrames/mínimo207. Degrau128B medido em outra ROM SHA `a5c013a8…`,
zero derrames/mínimo217. Arte/contato/produção permanecem abertos; esses
números não pagam a Cena01 abaixo, cenário/HUD ou gameplay.

## Trecho diagnóstico contato v8 — 2026-10-29

Fonte/receita no handoff, ROM452cd565…/32.768B. Pelo conversor e sete manifestos
SAT:220padrões/7.040B,31SAT nas poses exceto J04=34, pico8 emtodos os pares.
GradeJ04(3,9)px compensada: controle idêntico nos oito PNGs mediu33SAT/pico9 e
foi reprovado sem build. O custo maior de SAT/patterns está incluído.
Performance: duas janelas8s59,62/59,74fpsNTSC; selo3000frames0derrame/mínimo207;
degrau128B,outra ROM7ce342bc…,0derrame/mínimo217. Quatro sessões encerradas;
120framebuffers independentes e21da linha temporal exatos. Esses números pagam
somente o diagnóstico residente; cenário/HUD/gameplay, PAL e produção da Cena01
continuam abertos. Não inferir orçamento pelo screenshot nem milissegundosCPU.

## Cena 01 — _(nome)_
### Layout de VRAM declarado
| Região | Faixa | Tiles | Uso |
|--------|-------|-------|-----|
| patterns BG | — | — | — |
| patterns sprite | — | — | — |
| name table | — | — | — |
| SAT | — | — | — |

### Orçamento worst-frame (MEDIDO)
| Item | Bytes/frame | Método da medição |
|------|-------------|-------------------|
| — | — | — |

- **Total worst-frame**: _(medido)_ bytes
- **Headroom**: _(medido)_ %
- **Método**: _(como foi contado — contagem instrumentada, não estimativa)_
- **Degrau seguinte medido**: _(§18: qual o próximo incremento e ele cabe?)_

### Sprites por scanline (pico)
_(rodar `audit_sprite_line_sim.py` sobre o manifesto da cena e citar o pico real)_

### fps observado
_(rodar `measure_fps.py`; ≥5 amostras, todas 50–60. Citar o JSON.)_
