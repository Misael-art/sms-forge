# 11-gdd — master_of_fighters

> **DECISÃO VIGENTE DO PROPRIETÁRIO — 04/11/2026: SOCIAL IN-GAME CONGELADO.**
> Os sprites e animações atuais do Dr. Social não devem ser continuados,
> retocados, convertidos, integrados ou promovidos. Retomada futura: novo desenho
> do zero, a partir do concept/model sheet e das referências de tamanho mantidos.
> A cena D01 fica experimental. J.J. e Hayato/Kenseiden permanecem validados no
> recorte realizado. [Registro do congelamento](dr_social_ingame_freeze_20261104.md).
> As orientações anteriores para produzir o Social ficam históricas/suspensas.

A direção futura do jogo permanece documentada. As tarefas de desenho e
integração do Social descritas abaixo estão suspensas por esta decisão; o
congelamento não elimina o personagem do elenco ou muda sua identidade.

## Apresentação de golpes — direção do proprietário, 2026-11-01

Nova direção documentada: cena 10 apresenta nome do golpe, animação à velocidade
correta, controle do Master System e sequência visual dos botões/direções, com
acabamento gráfico coerente. Referência Neo Geo é de clareza/apresentação, sem
copiar arte ou seu esquema de botões. [Padrão e prompt](character_move_showcase_standard_v1.md)
e [decisão](decisions/character-move-showcase_owner_direction_20261101.json).

É padrão de implementação/revisão do personagem proposto para este projeto,
ainda não implementado ou validado. Assistir e experimentar são sugestões de
fluxo; comandos competitivos continuam em GD01/GD02. Não inventar quarto de
lua, carga ou associação a 1/2 para preencher a tela. Nomes finais e ícones
seguem a mesma definição de ação/comando usada pela luta. Timing diagnóstico
não vira frame-data e replay lento não aprova a velocidade normal.

Cena 10 reutiliza assets e runtime reais; piloto parcial é identificado como
diagnóstico. O pacote Dr. Social continua incompleto no incremento d7a3a2d:
três chaves novas, jab reutilizado, portraits candidatos; sem ROM integral.
A cena não autoriza ignorar composição do par, reduzir 66–72 px ou chamar uma
galeria de sprites de combate pronto. Possível desbloqueável futuro permanece
ideia aberta: gatilho, persistência e acesso pelo título/menu não decididos.

## Direção de fã e campanha — proprietário, 2026-11-01

**Estado: direção documentada para desenvolvimento futuro; não implementada.**
[Decisão e limites](decisions/fan-campaign-and-character-expression_owner_direction_20261101.json).
Este pedido amplia o design anterior: História, Versus, abertura/título/opções,
progressão de Alis, apresentações contextuais, cenário de Kenseiden, três
magias de Shadow Dancer SMS e participações de Alex Kidd. As restrições antigas
de não inventar essas telas/conteúdos não impedem o escopo agora solicitado.
Não se reabrem pixels/tempos das amostras aprovadas nem se promove runtime.

O alvo do dono é um jogo de fã excepcional, com ambição **AAA no Master
System**: atuação memorável, combate legível, cenários vivos, áudio reconhecível
e transições cuidadas. É objetivo de qualidade, não certificação. Cada efeito
deve servir à identidade, à narrativa ou à leitura; cada promessa ainda precisa
de orçamento e prova no SMS. “Carinho” se manifesta também na derrota, no
skip, no retorno ao controle e na segunda partida, não apenas na primeira intro.

### Modos e continuidade

| Modo | Direção vigente | Proposta do designer / ponto a fechar |
|---|---|---|
| História | Ruptura entre universos, encontros com diálogo, viagens por mundos, chefes/subchefes e encerramento; Alis evolui durante a campanha. | Campanha por personagem, com encontro inicial específico e nós posteriores compartilhados. Ordem, extensão, antagonista, continue/save e elenco de subchefes ficam pendentes; não criar elenco novo por inferência. |
| Versus | Duelo sem ganho de níveis durante a partida; Alis deve chegar equilibrada. | Usar configuração competitiva fixa de Alis, independente do save da História, com equipamento/guardas definidos para esse perfil. Não escolher arbitrariamente um nível intermediário como garantia de equilíbrio. Multiplayer local e fluxo de duas confirmações precisam contrato próprio; não implica online/link. |
| Arcade existente | Fluxo 03 preservado no histórico. | Decidir se será percurso rápido separado ou apresentação reduzida da História. Até essa decisão, não manter duas campanhas duplicadas nem aplicar níveis ao Arcade por inferência. |

IDs 01 seleção, 02 duelo, 03 progressão permanecem. Novos contratos:
04 abertura, 05 título, 06 opções, 07 cena narrativa, 08 vitória/evolução de
Alis e 09 encerramento. O cenário Kenseiden pertence à 02; apresentações e
vitórias são fases das cenas, não modos novos. D01 continua diagnóstico.

### Alis — evolução que expressa Phantasy Star

**Pedido do dono:** nível visível perto de vida ou especial; crescimento ligado
à performance; após vencer uma luta, pose de vitória e música de Phantasy Star
acompanham escolha rápida entre Vida, Defesa, Ataque e Magia. Melhorias devem
ser perceptíveis; Defesa pode mudar o sprite de guarda com escudo, Ataque pode
enriquecer a leitura do corte. Ganhar 1–2 ou 1–3 níveis é alternativa aberta,
não regra aprovada. Fragilidade inicial foi apresentada como possibilidade;
o dono também exige equilíbrio inicial e final.

**Recomendação do designer, ainda hipótese:** testar 1–2 níveis por vitória de
duelo, não por round. Ganho-base por vitória e bônus de performance limitado
por encontro; reduzir vantagem cumulativa de quem já venceu com folga. Não
usar apenas dano recebido, tempo ou perfect: isso pode recompensar fuga,
farm ou excluir estilos defensivos. Examinar decisões ofensivas/defensivas
reais, sem incentivar repetir a mesma ação para pontuar. Fórmula, limites,
recompensa de derrota/continue e pontos por nível continuam abertos.

Alis começa funcional contra todo o elenco. Ser esguia não prova fragilidade
canônica nem impõe HP menor; uma menor tolerância a erros, se escolhida pelo
dono, exige vantagens de alcance, mobilidade ou flexibilidade medidas. O jogador
não deve precisar sobreviver a uma personagem ruim para finalmente poder jogar.

| Atributo | Intenção e proposta de efeito | Manifestação e limite a testar |
|---|---|---|
| Vida | Aumentar vida máxima da configuração de campanha. | Vida total e ganho explicitados na escolha; definir como a barra representa a nova capacidade. Não conceder cura de round duplicada ou vantagem no Versus. |
| Defesa | Tornar a defesa bem executada mais forte. Recomendo redução limitada de chip/empurrão ao bloquear, antes de redução passiva de todo dano. | Guarda com escudo ganha atuação/feedback próprios no marco aprovado; nunca autoblock, imunidade ou eliminação do contrajogo baixo/agarrão por padrão. Regra exata de mitigação ainda depende do dono. |
| Ataque | Aumentar recompensa de golpes confirmados, com teto. | Corte pode ganhar acento visual autoral; efeito não aumenta alcance/hitbox ou cria onda/projétil sem contrato específico. Não acelerar startup silenciosamente. |
| Magia | Desenvolver a faceta mágica de Alis, sem copiar o kit de outro herói. | Escolher qual magia autorizada melhora e se altera dano, custo ou utilidade. “Magia +1” não pode ser escolha sem efeito; lista de feitiços e interação com Super ainda pendentes. |

**Escudo e arte aprovada:** concept v4 já inclui escudo leve. Está em discussão
se o marco de Defesa melhora a guarda com o equipamento existente (recomendado)
ou libera seu uso apenas depois. Até a escolha, preservar concept/poses e
registrar a variante de guarda como futura; não apagar escudo, alterar roupa
ou gerar duas versões completas. Marcos não significam um novo atlas por nível.

**Equilíbrio e persistência propostos:** tetos por atributo e por campanha,
ganhos moderados, sem crescimento multiplicativo irrestrito entre Vida e
Defesa. Comparar especializações puras, distribuição equilibrada e combinações
extremas em começo/meio/fim, inclusive desempenho mínimo e máximo. Não compensar
excesso escondendo escalonamento de inimigos. Uma mesma vitória não paga duas
vezes; continue/repetição precisa política antifarm explícita. Persistência
entre rounds, encontros, nova campanha e desligamento são decisões diferentes.

HUD recomendado: `LV` junto ao nome/vida, afastado do medidor de Super para não
parecer recurso consumível. Ao vencer: resultado → pose/cue musical → painel
curto com pontos e prévia antes/depois → confirmar → continuar. O painel pode
ser rápido sem timeout que gaste pontos sozinho. Cancelar desfaz a prévia;
confirmar aplica uma única transação. Com zero pontos ou atributos no teto,
mostrar estado claro e saída. Esses comportamentos são proposta de UX a testar.

O [manual de Phantasy Star SMS](https://www.smspower.org/Manuals/PhantasyStar-SMS-US)
documenta nível/experiência, ataque, defesa, HP/MP e equipamento. Distribuição
manual de pontos e progressão em fighting são adaptações autorais deste jogo,
não sistemas atribuídos ao original. O cue exato de vitória/ganho de nível
precisa identificação e escuta; não selecionar música de remake por nome.

### Shinobi — fonte definida e três magias

O dono fixa **Shadow Dancer para Master System** como fonte do personagem.
Isso resolve a dúvida de versão; não usar movimentos/vozes de Mega Drive,
arcade ou outro Shinobi como equivalentes. Preservar ID técnico
`joe_musashi` para não quebrar referências. Nome exibido ainda precisa decisão:
“Shinobi” é o rótulo usado no pedido; o material SMS consultado chama o herói
de Takashi. Não afirmar genealogia ou rebatizar arquivos automaticamente.

**Autorizadas como direção:** três magias do original adaptadas a especiais,
com chamada vocal digitalizada investigada na melhor qualidade viável. A regra
antiga de dois especiais deixa de ser teto obrigatório deste personagem;
não descartar uma das três. Organizar como três comandos ou variantes de um
Super é proposta de mapeamento ainda não decidida, sem ampliar o kit de Social.

Pesquisa preliminar identifica Tatsumaki (tornado), Fire Dog (fogo) e Butsuzo
(Buda) em [review de época de Shadow Dancer SMS](https://www.smspower.org/Reviews/ShadowDancer-SMS-SegaForce).
Nomes, execução e conteúdo exato da voz precisam confronto com fonte SMS e
captura identificada antes da arte/áudio; este texto não transcreve uma fala
inaudita. A adaptação não herda “atingir tudo” ou “não funciona em chefes” como
regra de luta, nem usa quantidade de vidas como comando competitivo.

| Magia de referência | Hipótese de função distinta | Contrajogo e contrato pendente |
|---|---|---|
| Tatsumaki | Pressão espacial por deslocamento do vento, com pista de direção. | Delimitar zona/trajetória e resposta possível; não tornar ataque inevitável de tela inteira. Objetos/multi-hit/alcance por medir. |
| Fire Dog | Compromisso ofensivo frontal reconhecível pelo fogo. | Preparação e recuperação puníveis; guarda/evasão/dano ainda a definir. Nome não autoriza um novo companheiro controlável. |
| Butsuzo | Grande momento de invocação, com silhueta e impacto distintos dos outros dois. | Definir área e janela de resposta antes de prometer cobertura; escala visual não determina hitbox. Ícone religioso/fonte e áudio precisam revisão. |

A voz não pode ser condição secreta de acerto: preparação visual equivalente
permanece com som desligado. Freeze dramático é estado explícito, finito,
simétrico e com retorno definido. A técnica PCM é hipótese de engenharia,
não permissão para parar a lógica arbitrariamente ou alegar 60 FPS por ISR.
Ver contrato de áudio e prova no TDD; nenhuma qualidade de voz está garantida.

### Carisma, participações e fronteiras

Entradas, provocações e finais precisam de intenção, atuação corporal,
reação do oponente e término. Base obrigatória de direção: cada lutador tem
uma apresentação reconhecível e um fechamento coerente; variantes contextuais
dependem de cenário/oponente e não exigem animação exclusiva para todo par.
SNK/Fatal Fury/KOF/Darkstalkers são referências de expressividade e ritmo;
Guilty Gear/SVC orientam interlocução/retrato, sem copiar pixels, falas ou lore.

J.J. pode chegar de moto, derrapar e saltar para a arena em cenário compatível;
equipamento/veículo são ativos de apresentação separados. Esta autorização não
transforma Armorater em golpe nem insere moto na folha aprovada sem FX. O anime
de J.J. continua limitado ao figurino: referências de atuação do desenho só
entram quando identificadas e autorizadas por aspecto, sem importar poderes.

Alex Kidd está autorizado **como easter egg em pedra de Kenseiden e cameo
encenado de Alex Kidd in Shinobi World**, não como lutador selecionável. Cameo:
meteoro/bola de fogo aproxima → adversário defende → ricocheteia → fumaça revela
Alex → reclama em balão → desaparece → Shinobi assume e começa a luta. Não
causa dano, gasta Super ou altera iniciativa. As falas são rascunhos do roteiro.
Psycho Fox continua fora; participação não autoriza expansão do roster.

### Cenário Kenseiden e narrativa do crossover

Arena noturna japonesa: colunas/arquitetura de templo, castelo ao fundo,
possível estátua budista, fitas/papéis/selos movidos pelo vento, lanternas com
luz percebida e folhas ocasionais. Alex gravado na pedra deve ser descobrível
no tamanho nativo, integrado ao material, sem seta, brilho de pickup ou colisão.
Pesquisa localiza relatos do rosto em parede de Kenseiden; posição/forma
originais ainda precisam captura antes da recriação autoral. Iconografia dos
selos, ornamentos e estátua deve ser pesquisada, sem tratar todo papel japonês
como o mesmo objeto ritual. Não exigir que tudo se mova simultaneamente.

A ruptura causada por uma ação maligna, heróis deslocados, desentendimento,
alianças e travessia até chefes/subchefes formam a **continuidade autoral de
Master of Fighters**. Respeitar identidades originais não torna o crossover
canônico das franquias. Vilão causador, motivo e encarnação final ficam abertos;
não resolver automaticamente a dúvida de Dark Force/PSII nem inventar poderes
canônicos dos antagonistas para justificar o portal.

O encontro Hayato/chefe encenado/herói recém-chegado é a cena-piloto solicitada,
com combate coreografado no cenário real, ruptura, chegada, golpe que derrota
o monstro, diálogo e então luta em rounds. A cena precisa mostrar por que
Hayato desconfia e por que o visitante aceita lutar, sem fazê-los ignorar
gratuitamente a ameaça comum. Encenação não ensina que aquele Super derrota
qualquer chefe competitivo em um golpe. Roteiro propõe causa e desfecho.

### Decisões abertas e ordem de execução

| ID | Questão / responsável | Próximo resultado verificável |
|---|---|---|
| FC01 | Design/dono: Alis, 1–2 versus 1–3 níveis, tetos, pontos, efeitos e escudo | Regra selada e comparação de builds de personagem em início/meio/fim; sem números herdados. |
| FC02 | Design/dono: Versus fixo, controles e relação História/Arcade | Perfis separados e reentrada sem importar atributos da campanha. |
| FC03 | Pesquisa/dono: nome Shinobi/Takashi, três magias e frase SMS exata | Fontes/capturas/áudio identificados, contrato individual e comandos. |
| FC04 | Roteiro/dono: antagonista, visitante e chefe encenado, destinos/finais | Beat sheet aprovado; novos atores não viram jogáveis. |
| FC05 | Arte/engenharia: cenário, intro, retrato, cameo e abertura | Storyboard/pose-chave → simultaneidade medida → contrato de asset → ROM, sem teto arbitrário de desenhos. |
| FC06 | Áudio/engenharia: cue Phantasy Star e PCM de Shinobi | Fonte/hash, arranjo/conversão, escuta e teste freeze→voz→retomada; fallback requer decisão, não remoção silenciosa. |

Começar pela cena-piloto e por um protótipo mínimo da escolha de Alis sobre
combate funcional; validar antes de multiplicar rotas e variantes. O pedido
atual é de documentação/direção futura, não fabricação imediata de conteúdo.
Aceite: compreensão, consequência, recuperação, áudio e pior frame na ROM;
alvo60/piso58 permanece, inclusive transições. As hipóteses acima não recebem
aprovação do dono apenas por terem sido sugeridas pelo designer.

## Contrato de experiência — revisão de design de 2026-11-01

**Histórico do primeiro recorte, anterior à direção de campanha acima.**
**Estado: documentado; interação de combate pendente.** Este recorte organiza
o design existente para artista e desenvolvedor. Não autoriza novos golpes,
personagens, arsenal, sistemas ou alteração dos desenhos/tempos já aceitos.
Decisões específicas do dono prevalecem sobre propostas antigas abaixo.
`movesets_draft.json` é histórico não aprovado; seus números não são defaults.

O jogador deve reconhecer quem ameaça, escolher uma resposta, perceber o
resultado e saber quando recuperou o controle. Público de trabalho: jogador
de luta 1v1 com controle SMS de dois botões; familiaridade e compreensão ainda
precisam de playtest. Não há evidência de diversão, acessibilidade dos comandos
ou balanceamento com público. O caminho de experiência está no
[roteiro](12-roteiro.md) e os contratos completos de telas estão na
[especificação de cenas](13-spec-cenas.md#contratos-de-experiência-das-cenas--2026-11-01).

### Vocabulário de contrato e autoridade

- **Decisão registrada:** escolha do proprietário, com fonte indicada. Não
  reabrir o mesmo aceite; qualidade de produção continua com gates próprios.
- **Hipótese de design:** comportamento proposto para discussão/teste; não
  vira tabela de runtime, hitbox ou pedido de arte final automaticamente.
- **Observação:** entrada/estado/framebuffer de ROM identificada; vale somente
  para a interação e o SHA observados. Preferência estética fica separada.
- **Pendente:** decisão, capacidade ou evidência ausente, com responsável e
  condição de fechamento. Nunca preencher com os números de outra ROM.

IDs de cenas do GDD permanecem **01 seleção, 02 duelo, 03 arcade**. O nome
histórico `cena01_duel_read`/`MOF_CENA01` identifica uma **amostra diagnóstica
da cena 02**, aqui chamada D01. Não renomear arquivos nem interpretar essa
placa como seleção implementada. Chefes estão registrados; se/quando ficam
jogáveis e como desbloquear continuam decisões abertas, apesar da antiga frase
“4 chefes desbloqueáveis” na tabela histórica.

### Identidade por personagem

“Papel a discutir” e sugestões de atuação nesta tabela são hipóteses de design,
não novas biografias canônicas. Para todos, fonte externa informa somente o
papel autorizado; pixels/poses não são copiados. Concepts aprovadas liberam
referência visual, não moveset. Escalas individuais são as do contrato de
roster abaixo; classe de peso não redefine biotipo.

| Personagem | Identidade, biotipo e atuação | Equipamento/capacidades e fronteira de referência | Papel e distinção; situação |
|---|---|---|---|
| Guerreiro de Golden Axe | Jovem aventureiro ágil, esguio; elmo com chifres, torso descoberto e capa de pelo azul da concept v2. Atuação proposta: coragem com compromisso de corpo inteiro, sem virar brutamontes. | Golden Axe Warrior SMS e [decisão v2](decisions/ga-warrior-concept-v02-sms-palette_owner_approval.json): espada e escudo. O nome Golden Axe não autoriza trocar espada por machado, cavalo ou magia. | Classe pesada do histórico é separada de massa visual. Hipótese: compromisso de espada/escudo para ganhar espaço. Moveset não aprovado. |
| Hayato | Jovem esguio; samurai, quimono branco, faixa vermelha, hakama laranja-vermelho, cabelo preso. Atuação aceita no corte: carregar, liberar, absorver e recompor a guarda com participação do corpo. | Kenseiden SMS; [concept v2](decisions/hayato-concept-v02_owner_approval.json). Katana e pergaminhos constam do GDD; magia específica não está selada. [Escolha do corte](decisions/hayato-short-cut-timing-only_owner_approval.json) preserva lâmina/traçado original. Referências de coreografia não definem roupa ou arma. | A katana descreve um arco corporal, diferente da estocada linear de Social. Só corte diagnóstico aprovado; não declarar anti-aéreo, overhead, dash ou especial. |
| Joe Musashi | Ninja de proporção humana esguia, massa de membros usada como referência morfológica. Disciplina/economia de gesto são hipóteses de atuação. | Roster cita Shinobi; decisão visual posterior aceita Joe/Takashi de Shadow Dancer SMS com acentos amarelos, registrada no memory bank e no lineage do conceito. A direção de campanha de 01/11 fixa Shadow Dancer SMS; nome exibido e continuidade de combate ainda precisam fechamento. Traje clássico de Shinobi é alterno registrado. Cão, clones, substituição invulnerável e shuriken do draft não são moveset autorizado. | Hipótese de mobilidade/engano distinta de arma laser. Fonte agora fixada: Shadow Dancer SMS; três magias autorizadas como direção na seção inicial. Nome exibido e contratos competitivos pendentes; preservar imagem aprovada. |
| Dr. Ferdinand Social | Humano, psicólogo investigativo; adulto esguio, grisalho, óculos de latão, casaco azul/ciano. Metódico e preciso, sem transformação vampírica ou controle mental. | Master of Darkness SMS + [model sheet v4](decisions/dr_social_model_sheet_cps2_alpha_cel_v04_owner_approval.json). Bengala romba, rapieira e bumerangue de aço formam o kit aprovado; violeta só no bumerangue. Armas listadas no original não autorizam novos golpes. | Duelista de alcance médio que pune erro de distância. Bengala é assinatura; luva/bota são suporte; rapieira e bumerangue os dois especiais; Laudo Final é contra-leitura. Direção aprovada em 10/10; contratos abaixo. |
| Karateca de Black Belt | Artista marcial; nome próprio e biotipo final não decididos. Hipótese: atuação direta, base e transferência de peso claras, sem imitar o jab investigativo de Social como identidade inteira. | Black Belt SMS conforme roster. Versão japonesa não autoriza importar identidade/lore por associação. Sem concept aprovada localizada para este personagem; armas e energia projetada não autorizadas. | Papel de curta distância a discutir. Nenhum dos quatro golpes do draft, inclusive multi-hit, está fechado. |
| Bruxa de Psychic World | Artes marciais e capacidades psíquicas no GDD; personalidade, nome e morfologia final pendentes. Hipótese: concentração legível antes de liberar poder, em vez de gestos idênticos aos espadachins. | Psychic World SMS. Não há concept aprovada localizada. O rótulo “bruxa” e o draft não autorizam varinha, teleporte, magia específica ou traje novo. | Papel psíquico a discutir com fonte e dono; sem dois especiais fechados. Não encomendar orbe/teleporte como se já aprovados. |
| Alis Landale | Jovem heroína, proporções humanas sem leitura chibi. Atuação proposta: determinação e guarda com escudo, não comportamento de tanque. | Phantasy Star SMS, [concept v4](decisions/alis-landale-concept-v04_owner_approval.json): família magenta/índigo/marfim, cabelo castanho-dourado, espada curta e escudo leve registrados. Referência cromática não aprova magia ou rolamento invulnerável. | Hipótese: alternar proteção e tomada de espaço próxima, distinguindo-se do compromisso pesado do Guerreiro. Moveset e personalidade detalhada ainda não selados. |
| Landau | Jovem adulto do norte, sem barba/bigode; túnica verde, couro e calça azul. Hipótese de atuação: firmeza e atenção à distância, sem envelhecer/engrossar o corpo por classe pesada. | Lord of the Sword SMS/manual US conforme [concept v1](decisions/landau-concept-v01_owner_approval.json) e memory bank: espada, arco e aljava. Sprite lateral é referência; pose de luta precisa autoria. Escudo, coroa e raio solar do draft não estão aprovados. | Distinção potencial: decisão de distância entre espada e arco, sem atribuir munição ou novos golpes. Papel/moveset pendentes. |
| J.J. | Jovem esguio e ágil, uniforme vermelho/magenta e proteções claras, cabelo azul. Atuação aceita da amostra: preparar a arma, executar uma ação e recolher à guarda. | Zillion II SMS rege identidade/cores/mecânicas; anime só esclarece figurino. [Aceite atual](decisions/jj-zillion-character_owner_approval.json): concept v5/fonte v6, Zillion longa, baixa, angular navy/cyan proporcional ao corpo; seis desenhos sem FX. Prancha Waku Waku 7 aprovada rege a correção específica da arma, não mecânicas. | Mobilidade/laser de médio alcance são proposta. Amostra aceita não emite projétil e não causa dano. Armorater, coronhada e demais ações continuam pendentes na [ficha](jj/jj_character_design.md). |
| Ninja Master | Chefe de Shinobi registrado; personalidade, biotipo e forma de atuação ainda não contratados. Hipótese: testar leitura do ninja com ameaças reconhecíveis. | Shinobi é fonte declarada; sem concept/arsenal de luta aprovado identificado. Clones, nuvem de shurikens e agarrão do draft não são autorização. | Papel de chefe precisa padrões, pista e saída testáveis. Dificuldade não pode decorrer de hitbox falsa invisível. Moveset/jogabilidade pendentes. |
| Count Dracula | Antagonista de Master of Darkness; não transferir sua identidade ao Social. Morfologia e atuação de luta ainda pendentes. Hipótese de presença ameaçadora com oportunidades claras de aproximação. | Master of Darkness, distinto do protagonista. Transformação, morcegos, bruma, cura e invulnerabilidade do draft não têm aceite individual. | Chefe a discutir; nenhum padrão ou fase aprovado. Definir limites de recuperação antes de contratar poderes. |
| Luter | Chefe de Phantasy Star registrado; nome, aparência final, personalidade de combate e equipamento requerem ficha específica. | Phantasy Star conforme roster. Draft de barreira, raio e segunda forma não aprova capacidade nem aceleração por vida baixa. | Hipótese: pressão por padrões aprendíveis. Fases, papel e desbloqueio pendentes. |
| Dark Force / Dark Falz | Entrada de chefe com identidade/fonte ainda explicitamente em aberto. Não fixar biotipo, personalidade, tentáculos ou escala antes da decisão. | GDD registra dúvida sobre encarnação/origem PSII e escopo SMS. Preservar a dúvida; não resolver por nome semelhante ou importar arte de outro console. | Sem papel ou golpes executáveis. Dono decide encarnação/fonte antes de qualquer contrato de arte, transformação, agarrão ou ataque de tela inteira. |

As diferenças de papel dos personagens sem moveset aprovado são perguntas de
design para a construção individual, não expansão autorizada. Cada futuro
golpe deve justificar **por que este corpo e este equipamento realizam esta
ação**, e demonstrar uma decisão que não se resuma a trocar a aparência de
um soco/projétil comum.

### Contratos dos movimentos com escopo atual

Social tem seis ações de combate aprovadas como direção: jab, bengala, chute
baixo, rapieira, bumerangue e Super com três ramos. Intenção, preparação,
trajetória, resposta, risco, hit/block/whiff e retorno estão em
[contratos de experiência do moveset](dr_social_combat_design_proposal_v1.md#contratos-de-experiência-por-movimento--2026-11-01).
O contrato de animação `dr_social_animation_contract_v2.json` continua sendo
a fonte dos IDs/tracks. `cane_riposte` não é um sétimo ataque nem terceiro
especial; os quatro IDs antigos do draft não competem com os atuais.

| Ação diagnóstica | Intenção, preparação e trajetória | Resposta/risco/consequência | Recuperação e aceite |
|---|---|---|---|
| Hayato — corte curto R01–R06 | Ler um único corte de katana: carga alta → liberação → corte → absorção baixa → retorno cruzado → recuperação alta. Corpo, apoio e arma trabalham juntos; artista preserva os desenhos v4 aceitos, sem smear rejeitado. Alcance competitivo e altura de ataque não definidos. | Há demonstração de arma em arco, não ameaça com colisão. Hipótese para futuro combate: o rival reconhece carga, administra distância e pune comprometimento no erro. Acertar/bloquear/errar ainda não existem nesta amostra; não atribuir dano, prioridade ou invulnerabilidade. | Volta à guarda original. Exposições aceitas 8/1/2/7/2/5 são timing artístico do perfil v7, não startup/active/recovery competitivo. Aceite artístico permanece fechado; contrajogo/contato dependem de decisão e ROM de luta. |
| J.J. — amostra de disparo I00/S01–S05 | Preparação reconhecível da Zillion, ação única e recolha; arma inteira ligada à pega. Seis desenhos e proporção da fonte v6 preservados. Não desenhar emissão, bala, sparks ou flash neste asset. | Nesta ROM o oponente permanece em guarda e nada recebe hit. Hipótese futura: alinhar a arma comunica ameaça linear e recolher comunica compromisso; alcance, altura, resposta do rival e distinção raio/projétil dependem da decisão individual. Não alegar que o tiro atual pode ser bloqueado ou evitado. | I00 → S01–S05 → I00; 7/4/2/3/6 aceitos. Testar acionamento, retorno e nova entrada na amostra; hit/block/whiff ficam pendentes no futuro contrato de objeto/combate. |

### Fronteira dos movimentos ainda não aprovados

O draft de 44 ações permanece preservado para rastreio. Cada grupo abaixo
tem a mesma disposição: **não executar como moveset; discussão individual
pendente**. Não transformar seus tempos herdados em números de combate.

| Personagem | IDs do draft a resolver com o dono; causa |
|---|---|
| Guerreiro | `axe_swipe`, `shield_bash`, `wave_of_death`, `mount_charge`: machado/cavalo/magia não derivam da espada/escudo aprovados. |
| Landau | `royal_slash`, `shield_push`, `solar_beam`, `royal_justice`: nomenclatura real/escudo/raio e overhead não aprovados para espada/arco. |
| Hayato | `katana_cut`, `diagonal_slash`, `scroll_fire`, `iai_dash`: corte diagnóstico não sela esses IDs nem suas propriedades. |
| Joe | `quick_punch`, `low_lunge`, `shuriken`, `wood_body`: conciliar fonte/identidade e decidir kit, especialmente invulnerabilidade. |
| Social | `cane_jab`, `rapier_thrust`, `occult_boomerang`, `duel_pistol`: proposta antiga superada pela direção individual de 10/10; não criar aliases automáticos. |
| Karateca | `jab`, `cross`, `flying_kick`, `lightning_kick`: derivar atuação própria; multi-hit permanece aberto. |
| Psychic World | `wand_swing`, `sweep`, `psychic_orb`, `teleport_backhit`: equipamento e poderes não selados. |
| Alis | `dagger`, `kick`, `energy_wave`, `dodge_counter`: reconciliar espada/escudo; energia e invulnerabilidade não aprovadas. |
| Ninja Master | `clone_dash`, `shuriken_cloud`, `shadow_grab`: pistas, instâncias, captura e multi-hit pendentes. |
| Dracula | `bats`, `mist_tp`, `life_drain`: capacidades, recursos e contrajogo pendentes. |
| Luter | `barrier`, `dark_bolt`, `second_form`: fase e mudança de cadência não aprovadas. |
| Dark Force | `energy_orbs`, `tentacle`, `nova`: identidade anterior ao moveset; tela inteira/multi-hit sem orçamento. |
| J.J. (arquivo separado) | `zillion_laser`, `armorater_shift` e direções de soco/chute/coronhada em `jj_moveset_concept_v1.json`: somente a amostra corporal foi aceita; nenhum especial de combate selado. |

### Decisões e hipóteses abertas para execução

| ID | Responsável e questão | Como fechar / evidência necessária |
|---|---|---|
| GD01 | Dono + design: comandos de dois botões, precedência, buffer/cancel e guarda alta/baixa | Decisão individual registrada; testar execução e neutralização nos dois lados, comando incompleto e input mantido. Botões 1/2 do viewer não são layout competitivo. |
| GD02 | Dono + design: escala de vida, dano/chip, vantagem, hitstop e economia do Super | Aprovar regras; medir hit/block/whiff, interrupção e retorno na mesma ROM, inclusive sem barra e barra cheia. Não converter exposições diagnósticas em frame-data. |
| GD03 | Dono: movesets individuais, nome exibido de Shinobi e encarnação de Dark Force | Registrar fonte e limite de cada decisão; só então roteiro/coreografia e budget de cada nova ação. |
| GD04 | Dono + design: empate, time-over empatado, continue, ordem de arcade e desbloqueio | Decidir destinos exatos; testar último round/último oponente, derrota e retorno à seleção, sem prêmio duplicado. |
| GD05 | Engenharia: ligação do consumidor ao motor e ao estado de combate | Provar entrada → comando → ação → contato/guarda/erro → estado/vida → recuperação, com IDs e frames. Contrato de integração no TDD; não substituir pela demo de poses. |
| GD06 | Arte + engenharia: composição em contato e carga simultânea | Medir ambos os atores em todas as distâncias/poses necessárias, HUD/objeto autorizado/PSG e pior frame. A posição fixa com pico 8 não prova aproximação. Preservar função do golpe; negociar mudança que afete alcance/identidade. |
| GD07 | Design + QA: clareza e controle percebidos | Playtest com tarefa sem ensinar resposta, ROM/SHA, tentativas, relato literal, frames e distinção observação/interpretação. Parecer de agente não é teste com público. |

Aceite futuro de cada movimento: preparação aparece antes da consequência;
alcance desenhado e contato concordam; defesa/erro recebem respostas distintas;
há contrajogo executável; retorno permite nova ação sem estado preso. Conferir
ambas as faces, perto/longe, borda, input mantido/solto/repetido e transição de
round. Nenhum teste sem implementação vira PASS por contrato. Áudio deve
reforçar a leitura visual sem ser sua única pista. Alvo 60 FPS, piso 58 em
cada janela válida sem arredondamento, lógica/apresentação coerentes e pior
frame medido na carga real; PAL50 não paga aceite. Resultado desta revisão e
pendências constam no memory bank, sem promoção de produção.

## J.J. — seleção aprovada pelo proprietário

A resposta “aprovado” fecha o conceptv5/fontev6, a proporção da Zillion,
os seis desenhos sem FX e o retorno apresentado com7/4/2/3/6. Preservar arte,
tempos e ROMs; decisão em `decisions/jj-zillion-character_owner_approval.json`.
Checkpointv7 registra o aceite sem inventar percepção contínua ou nova sessão.
As pendências de aceite nas seções anteriores são históricas. Objetos/FX,
combate completo, produção e homologação global continuam fora deste aceite.

## Histórico técnico anterior ao aceite

## J.J. — amostra de personagem fiel, seis quadros, sem efeitos

Fonte v6 e concept v5 candidatos corrigem somente forma/proporção da Zillion e
pega. I00/S01–S05 e poses preservados; tiro, bala, sparks e FX foram excluídos
por instrução do dono. Objeto/emissão serão separados em lote posterior, com
orçamento próprio. Tempos propostos 7/4/2/3/6 não foram reescritos para resolver
budget. QA técnica nas duas faces e vídeo real passaram; qualidade temporal e
aceite humano permanecem pendentes no checkpoint v6. Planejamento congelado em
`jj_zillion_single_shot_route_v5.json`; fonte6 corrige um ponto sem mudar SMS.

## Direção vigente do dono — proporção da Zillion, seis poses, sem FX

O proprietário corrigiu explicitamente o escopo: a Zillion está grande demais
em relação a J.J.; corrigir a proporção no concept/model sheet mantendo a forma.
**Preservar os seis quadros e as poses. Não incluir bala, tiro, sparks, flash,
FX ou objetos na folha do personagem; esses elementos serão separados depois.**
A experiência de três poses e pulso composto v4 fica histórica/supersedida,
sem ROM ou aprovação. Fonte corporal para preservar: seis poses v3. Atual:
`jj_zillion_single_shot_route_v5.json`, contrato de animação v5, equipamento v2
e `decisions/jj-zillion-proportion-and-no-fx_owner-feedback.json`. Corrigir
somente arma/encaixe da pega por ROIs, sem regenerar atuação, rosto ou figurino.
Concept individual v4 aprovado permanece intacto como controle histórico;
a correção candidata v5 terá review/aceite próprios. Nenhuma ROM de J.J. foi
construída até esta direção. Hayato permanece aprovado e intacto.

## J.J. — autoridade específica da Zillion reconciliada

O feedback do dono e a prancha Waku Waku7 já aprovada prevalecem sobre a arma
compacta do concept individual v4: usar Zillion longa, baixa, angular, navy/cyan,
com encaixe/pega contínuos e cano inteiro. A referência atual é a mesma de08/10;
ver `jj_zillion_weapon_identity_contract_v1.json` e
`decisions/jj-zillion-weapon_owner-feedback.json`. O concept v4 conserva corpo
e figurino; não autoriza reutilizar o blaster branco/azul. Plano/contrato v2
substituem o planejamento v1 deste teste. Nenhum sprite novo está aprovado.

## Novo lote autorizado — J.J., disparo único de Zillion

O proprietário pediu um terceiro personagem e uma ação curta para testar repetibilidade. Selecionado J.J. do elenco aprovado, com o concept v4 preservado. O manual de Zillion II confirma o laser; a encenação de tiro único é adaptação autoral diagnóstica. Plano e pesquisa em `jj_zillion_single_shot_route_v1.json` e `jj_zillion_single_shot_research_v1.json`; contrato em `jj_zillion_single_shot_animation_contract_v1.json`. Não sela moveset competitivo nem substitui o corte aprovado de Hayato.

## Seleção aprovada — corte sem distorção, tempos 8/1/2/7/2/5

O proprietário escolheu os desenhos v4 com novos tempos. A katana conserva
sua trajetória e forma originais; a deformação v6 foi rejeitada por mudar a
leitura do golpe. Esta é a opção artística/temporal aceita para este corte.
Contrato atual `hayato_animation_contract_v4.json`; não ampliar conteúdo neste
lote. Aceite do preview não implica áudio, dano/hitboxes, PAL, hardware físico,
qualidade global ou release. A integração do mesmo corte segue no perfil v7.

## Histórico — tempo e deformação de espada, fonte v6 rejeitada

Feedback do dono confirma a base artística v4 e pede mais leitura na preparação
e no final baixo. Mantêm-se seis poses e um corte; proposta 8/1/2/7/2/5 ticks.
Squash/stretch gráfico autorizado na lâmina de R02, a passagem mais rápida,
com pega/corpo intactos e forma canônica restaurada em R03. Nenhum contato,
impacto, dano, hitbox, efeito independente ou movimento novo é inferido.
Controle v4 preservado; novos pixels/tempos requerem conversão e ROM próprias.
V6 fecha a ponta do smear que se soltava em SMS. Conversão/ROM novas apresentam
8/1/2/7/2/5 e lâmina transitória de 1 tick, com corpo, pega e cinco outras poses preservados.
O novo ritmo e impressão de velocidade aguardam avaliação do proprietário;
nenhuma ampliação de conteúdo enquanto isso.

## Perfil corrente da reformulação — fonte v4

Corte curto continua o único escopo. R01carga alta, R02liberação, R03corte,
R04absorção mais baixa, R05retorno cruzado, R06recuperação alta e guarda.
Seis desenhos, tempos diagnósticos4/1/2/3/1/3 apresentados na ROM, sem dado competitivo. Cabeça,
ombros, quadril e joelhos participam; proporção não significa silhueta congelada.
Fonte192px fornece margem para arcos; fontes144px existentes preservadas.
Perfil diagnóstico8×8 usa a mesma escala comum e P1, sem novo consumidor.
Review da fonte estática v3 e adendo fonte/SMS v4 passaram; execução da ROM,
ordem e exposições verificadas. Julgamento de força/ritmo/leitura contínua e
aceite do dono continuam separados e pendentes. Não ampliar antes desse checkpoint.

## Histórico: reformulação autorizada do corte — 2026-10-29

Prioridade atual: corrigir coreografia e continuidade corporal do corte já
escolhido, preservando identidade/acabamento. Contrato diagnóstico atual v2:
cinco desenhos propostos, tempos4/1/2/3/3 revisáveis pelo estudo; v1 é tentativa
histórica. Referências externas orientam movimento, nunca identidade/paleta.
Sem dano, hitboxes, frame-data competitiva, elenco ou sistemas adicionais.
Aceite temporal/SMS/ROM/owner fica separado do parecer estático anterior.

## Corte curto de Hayato — recorte diagnóstico, 2026-10-29

O dono direcionou completar o teste com corte curto de katana, primeiro
comparando guarda+execução convertidas. A ação é amostra artística, sem dano,
hitboxes, cancels ou frame-data competitiva aprovados. Quatro poses C01–C04,
working3/2/2/5ticks, retornam à guarda preservada; não amplia elenco, atlas,
cenário ou sistemas. Contrato em hayato_animation_contract_v1.json.
Fonte completa gerada e buildada; qualidade, animação e ROM ainda seguem seus
reviews/gates próprios. Aceite positivo da guarda não é aprovação da ação.

## Recorte corrente Hayato — 2026-10-29

Pedido do dono: repetir a amostra CPS2 em Hayato, comparando com Dr. Social,
sem ampliar atlas/elenco/cenários/sistemas. Guarda nativa v2 e conversão do par
completas para revisão, sem promoção. Concept v2 aprovado continua identidade;
classe de combate não define tamanho/massa. Katana inteira, roupa branca e
laranja-vermelha, cabelo preso e corpo jovem esguio preservados.
A ação curta proposta (corte de katana; alternativa desembainhar/retornar)
aguarda escolha do dono; não há contrato/frames/dano/hitboxes competitivos novos.
O Social v8 é referência preservada; aceitar método/artes anteriores não
aprova esta fonte de Hayato. Guarda estática não demonstra animação.
Mesma transformação do diagnóstico Social nos dois; não se normaliza cada
corpo/arma. Relações de elenco próximas foram revisadas; faixa absolutaSMS
68–72px legada não é declarada atingida por este diagnóstico~58–60px corporal.
Estado, decisões e evidência atuais: memorybank e índice
`out/diagnostics/hayato_cps2_sample_v1/result.json`.

## Continuidade da amostra v8 — 2026-10-29

Somente idle + social_light_jab em seis desenhos: cinco quadros v5 e contato
reto J04 já autorado na v6, montados sem editar pixels. Fonte/chaves estáticas
passaram na revisão integral; fluxo temporal, simplificação SMS e dono seguem
em checkpoint humano. Sem novos personagens, estados, golpes ou atlas.
`dr_social_cps2_sample_v1.md` conserva fontes, receita selecionada e limites.

## Continuidade de 2026-10-29

O dono aprovou o método e seu encaminhamento à curadoria futura. A candidata
corrente é v5, com reparo facial aprovado em review independente no escopo da
fonte. Isso não aprova o contato J04, a simplificação SMS ou a arte completa;
o escopo continua uma pose idle + jab, sem novos movimentos ou atlas.
Detalhes, fonte/ROM e limites: `dr_social_cps2_sample_v1.md`.

## Recorte autoral CPS2 em revisão — 2026-10-28

O pedido atual autoriza somente uma pose idle e `social_light_jab` J01–J06,
com fonte em escala CPS2 e conversão posterior. O canvas 80×80 descrito no
histórico abaixo não limita a nova fonte: a candidata usa células 128×128,
corpo de aproximadamente 104 px e paleta-fonte própria. J01–J06 mantêm os
tempos propostos 2/1/1/1/1/3 ticks; balanceamento continua não aprovado.

A identidade permanece no model sheet v4, com decisões posteriores de cabelo
cinza e óculos de latão. A aprovação artística v08.2 de 61 poses existe e foi
conferida pelo SHA `4e557095…`; notas históricas de aprovação pendente estão
superadas nesse escopo. A nova variante não substitui a fonte aprovada.
Fontes, receita, revisão e limites estão em `dr_social_cps2_sample_v1.md`.
Conversão e ROM desta amostra são diagnósticas, sem promoção ao elenco,
gameplay, cenário/HUD ou entrega visual de produção.

> Design e escopo. **Autoridade #2 — "se não está no GDD, não entra."**
> **REGISTRO INICIAL (2026-10-02)** — nome provisório: **Master of Fighters**.
> GDD em construção; revisão humana pendente (workflow new-project passo 2).

## Pitch (1 frase)
Jogo de luta 1v1 fan-made para Master System com a escalação mais icônica do
console — heróis do hall e chefes lendários — rodando sobre o motor de luta
dirigido por dados MUGEN→SMS (`SMS_projects/luta_mugen` +
`tools/sms_wrapper/mugen2sms/`), com toda a arte redesenhada em pixel art SMS
e paletas CRAM compartilhadas por sprites, cenário e HUD conforme o contrato
`doc/palette_runtime_contract_v1.json`.

## Gênero declarado
`fighting` (deve bater com `specialization` em `.mddev/project.json` —
`audit_specialization.py` compara os dois.)

## Loop central
Escolher personagem → duelo 1v1 melhor-de-3-rounds → punzir/bloquear/esquivar
conforme o padrão de IA do oponente → vencer → desbloquear chefe/alterno →
escolher de novo com roster e oponentes mais duros.

## Escalação registrada (2026-10-02; expansão aprovada pelo dono em 2026-10-04)

### Hall de personagens (jogáveis)
| # | Nome | Fonte (jogo SMS) | Nota de direção |
|---|------|------------------|-----------------|
| 01 | Guerreiro de Golden Axe | Golden Axe Warrior (SMS) | **versão estilizada** — jovem aventureiro ágil, elmo com chifres e capa; sem proporção de brutamontes/tanque. Classe de jogo pesada permanece separada da morfologia visual. |
| 02 | Hayato | Kenseiden | samurai; katana + magias de pergaminho |
| 03 | Shinobi (ID `joe_musashi`; nome exibido pendente) | Shadow Dancer SMS — decisão de 01/11 | três magias como direção; traje clássico do 1º Shinobi permanece alterno registrado, sem importar seu moveset |
| 04 | Dr. Ferdinand Social | Master of Darkness (US: Demon Sword) | psicólogo vitoriano caça-vampiros; NÃO se transforma em vampiro (correção do dono 2026-10-03) — arsenal do original: bengala, rapier, faca, machado + pistola, bombas, boomerang |
| 05 | Karateca de Black Belt | Black Belt (JP: Geki Shitou) | sem nome oficial — o projeto pode batizá-lo |
| 06 | Bruxa de Psychic World | Psychic World | artes marciais + magia psíquica |
| 07 | Alis Landale | Phantasy Star | heroína; side sci-fi/fantasy do roster |
| 08 | Landau | Lord of the Sword | jovem adulto; guerreiro do norte com espada e arco (manual US); sprites originais em vista lateral, poses devem ser retrabalhadas para luta |
| 09 | J.J. | Zillion II: The Tri Formation (Master System) | jogo ancora identidade, cores e mecânicas; model sheet do anime foi consultado apenas para corrigir o figurino, por pedido do dono; lutador ágil com pistola laser Zillion; Tri-Formation/Armorater pode inspirar mobilidade, ainda em proposta |

O dono adicionou J.J. à escalação em 2026-10-04 e especificou **Zillion II para Master System** como fonte de identidade, paleta e mecânicas. Como o sprite é pequeno e o figurino difere na versão anime, referências do anime são usadas somente para a construção visual da roupa, por pedido do dono; não definem golpes, lore do fan game ou pose copiada. A classe leve e a conversão de equipamento/veículo em mecânica de luta continuam propostas, sujeitas à revisão do dono e a medição.

### Chefes (não-jogáveis por padrão; desbloqueáveis a decidir no GDD completo)
| # | Nome | Fonte | Nota |
|---|------|-------|------|
| B1 | Ninja Master | Shinobi | chefe final |
| B2 | Count Dracula | Master of Darkness | chefe final |
| B3 | Luter | Phantasy Star | chefe final de PS1 |
| B4 | Dark Force (Dark Falz) | Phantasy Star II | a confirmar: Dark Falz é o chefe final de **PS2**, não de PS1 |

## Personagens explicitamente NÃO registrados (fora até nova decisão)
- Alex Kidd continua fora do elenco jogável. A direção de 01/11 autoriza somente
  o cameo de Shinobi World e o easter egg no cenário Kenseiden. Psycho Fox
  permanece fora; participação não implica seleção ou novos movimentos jogáveis.

## Eixos de fighting (lastro de gênero — `audit_specialization.py`)
- **hitboxes**: ataque e corpo definidos por retângulos em dados (tabelas
  compiladas do pipeline mugen2sms), nunca colisão de bounding-box única;
  hitboxes desenhadas em overlay de debug durante coreografia.
- **startup_active_recovery**: cada golpe autoral documenta as três fases em
  frames (60fps NTSC / 50fps PAL) na tabela do personagem; frame data é
  contrato de balanceamento, revisado por medição, não por sensação.
- **hitstop**: congelamento curto em frames na confirmação de hit (parâmetro
  por tipo de golpe na tabela; valor inicial a medir no lote de pilotagem —
  nada é fechado sem medir o degrau seguinte).
- **specials**: meta histórica de 2 especiais por personagem, sujeitos a aceite
  individual. Shinobi tem exceção explícita de três magias na direção de 01/11.
  Rapieira/bumerangue de Social seguem seu contrato; capacidades de Hayato e
  Psychic World ainda exigem discussão própria. Especiais recebem comandos
  e orçamento de sprite/scanline medido, sem promover sugestões a moveset.
- **guard**: defesa alta/baixa com bloqueio visível (faísca de guard),
  dano de chip-documentado; Ninja Master e demais chefes usam guard IA para
  pressão legível.

### Movesets — status
Proposta temporária em `doc/movesets_draft.json` (12 entradas da escalação
anterior — 8 heróis e 4 chefes —, 44 golpes; não contém o J.J. adicionado em
2026-10-04). Seu arquivo de personagem terá uma proposta separada sem frame
data até revisão. Frame data existente ancorada no molde medido
MSSF2T/hamoopig; `balance: nao-testado`.
**O dono NÃO aprovou esta proposta** — política vigente: **cada moveset é
discutido e fechado individualmente na construção daquele personagem**, e só
o arquivo de personagem selado na discussão vale como contrato. Pendências
abertas no draft: cláusula multi-hit vs um-golpe-um-acerto, e golpes
tela-cheia condicionados a `measure_worst_frame.py`.

#### Dr. Ferdinand Social — moveset autoral aprovado (2026-10-10)

O dono aprovou individualmente a direção de luta e autorizou a produção
progressiva das folhas de golpes. Social é um duelista investigativo de alcance
médio/whiff-punisher: jab e chute baixo são normais de apoio; o toque de bengala
é seu normal de assinatura; os dois especiais são estocada de rapieira e
arremesso de bumerangue. O contragolpe de bengala integra o Super **Laudo
Final**, não ocupa um terceiro espaço de especial.

O Laudo Final consome uma barra cheia do medidor comum de Super. O sistema terá
uma carga por lutador sob regras comuns ao elenco. Ganho numérico, HUD,
persistência entre rounds, escala de dano e janela em ticks seguem pendentes de
especificação e medição; não implementar números da proposta como valores
aprovados. A captura é uma leitura curta contra ataques físicos altos/médios;
perde para baixo, agarrão, projétil, atraso ou finta. Não há transformação,
teleporte ou invulnerabilidade universal.

Os números de startup/active/recovery, alcance e dano continuam
`proposal_unmeasured`. Cada folha é produzida uma por vez, inicia em
`data/source_art/` como candidata, e precisa de revisão independente, aprovação
humana e conversão/prova SMS antes de integrar em `res/` ou ROM. A primeira
sequência autorizada para desenho é `social_light_jab`; os ramos seguintes
permanecem documentados no contrato de animação e serão desenhados na ordem
registrada na proposta.

A primeira candidata visual do jab tem seis poses legíveis em sequência, mas a
versão v2 falhou no preflight de transparência e paleta: PNG RGBA 1536×1024,
alpha parcial sem pixels totalmente opacos, sem export 80×80 ou paleta SMS
indexada. Permanece em `review_drafts`; não é arte aprovada nem recurso de ROM.

### Contrato de animação e sprite sheet — exercício Dr. Social

O contrato corrente aprovado em design está em
`doc/dr_social_animation_contract_v2.md` e no JSON vinculado; v1 permanece como
registro histórico da proposta. Ele cobre 20 estados comuns: idle, avanço, recuo, pulo/aterrissagem,
abaixar, dash, queda, rolagem/levantada, defesa, duas vitórias, derrota por
tempo, empate, duas provocações, duas apresentações e três retratos versus
(neutro, vitória e derrota). As sequências ativas de combate são jab, toque de
bengala, chute baixo, estocada de rapieira, arremesso de bumerangue e três ramos
do Super (tentativa, acerto e erro). `cane_riposte` fica apenas como registro
histórico: a ação foi absorvida pelo Super e não é um terceiro especial.

Para cada sequência, declarar estado inicial/final, loop/transição, IDs e
contagem proposta de poses-fonte, duração por pose, trilha do personagem e de
cada objeto/efeito animado, e os 12 princípios. Pelo menos sete princípios
devem ser aplicados com pista visual planejada ligada a quadros; os demais
recebem justificativa. Pista planejada não é evidência de animação renderizada.
`source_pose_count` conta desenhos de pose distintos; objetos 8×8/8×16,
metasprite, tiles únicos, SAT/scanline e custo VBlank são campos separados e
ficam pending até converter e medir os pixels.

Atualização de fonte (2026-10-12): a folha v1 anteriormente selecionada para
conversão foi arquivada em
`data/source_art/sprite_studies/dr_social/historical_approved/basic_sequences_61f_owner_source_v1/`;
serve somente como histórico. A v07, SHA-256
`f5c41fb2204e3b2fff9a6e824fc55a767c2456dcdd9c62d17351f76696c95dc8`, foi
rejeitada artisticamente pelo dono: o casaco perdeu sua hierarquia, o cabelo
varia entre cinza e tons avermelhados/castanhos e as sombras ficaram granuladas.
A identidade permanece ancorada exclusivamente no model sheet aprovado
`data/source_art/concept_art/dr_social/dr_social_model_sheet_cps2_alpha_cel_v4.png`.
Não existe sprite sheet de movimentos básicos aprovada. A v08.1 falhou no gate
de clusters. A candidata v08.2 passou a auditoria quantitativa de clusters, mas
aguarda revisão visual do dono e ainda não é fonte de gameplay.

A reconstrução v08 foi iniciada como diretriz. A tentativa exploratória de
geração de imagem foi reprovada tecnicamente: alterou o canvas para 1182×1330,
produziu fundo opaco e 287.407 valores RGBA distintos; portanto não é arte v08,
não permite comprovar os limites dos 61 quadros nem conformidade semântica. O
experimento e as métricas estão em
`doc/curation_candidates/2026-10-12_dr_social_v08_imagegen_trial_rejection.json`.
Não foram produzidos previews 1×/4× válidos. O arquivo
`doc/dr_social_sprite_rebuild_directive_v08.md` fixa uma paleta indexada, papéis
por material, cabelo em cinzas constantes e sombras de cel shading em blocos
contíguos. Blur, média, distância cromática/espacial, luminância, nearest-RGB,
ImageGen e difusão são proibidos. O dono autorizou máscaras explícitas por
quadro/material e reassociação determinística de clusters dentro dessas máscaras,
com delta rastreável. O feedback para curadoria está em
`doc/curation_candidates/2026-10-12_dr_social_v07_artistic_rejection.json`.

Em 12/10/2026, a diretriz v08.1 incorporou a autorização explícita dos óculos de
latão como zona amarela: a candidata preserva os 85 pixels faciais autorizados.
O relatório registra zero vazamentos semânticos branco/amarelo/bordô/cinza, zero
pixels pendentes e haste da bengala com 1.245 pixels brancos uniformes; alpha,
grade 8×9, paleta e 61 poses permanecem intactos. A limpeza 2×2 ainda não passou:
restam 73 singletons no cabelo, 96 no casaco e 341 na pele, além de 102/139/553
componentes abaixo de 2×2. Uma revisão da franja encontrou sombra avermelhada
fora da máscara do cabelo; a máscara recuperou 1.014 pixels dessa sombra e agora
mede zero pixels não cinza em 61/61 poses. Portanto a candidata está reprovada pelo próprio
gate de clusters e não pode ser promovida. Contrato delta:
`doc/dr_social_sprite_mask_contract_v08_1.json`; diretriz:
`doc/dr_social_sprite_rebuild_directive_v08_1.md`; relatório e amostras estão em
`data/source_art/sprite_studies/dr_social/review_drafts/basic_sequences_61f_candidate_v08_1_masks_candidate/`.

Em 12/10/2026, a v08.2 executou a reclassificação de fronteira autorizada pelo
dono. Cada componente sem quadrado sólido 2×2 recebeu a cor dominante do anel
8-conectado opaco imediato; o algoritmo processa um componente por vez e mede de
novo até ponto fixo. O contorno original e a geometria alfa foram preservados;
863 pixels de material receberam índice de contorno por essa regra explícita.
O casaco usa somente os índices 5/6 (ciano `#00AAAA` e sombra escura `#005555`).
A auditoria independente por célula confirmou zero singletons e zero clusters
sem bloco 2×2 em cabelo, casaco e pele; 61 poses, canvas 640×720, grade 8×9,
11 cores úteis, vazamentos semânticos zero, cabelo cinza em 61/61 e óculos 85/85.
A candidata e as amostras 1×/4× estão em
`data/source_art/sprite_studies/dr_social/review_drafts/basic_sequences_61f_candidate_v08_2_final_candidate/`;
contrato e registro estão em `doc/dr_social_sprite_mask_contract_v08_2.json` e
`doc/curation_candidates/2026-10-12_dr_social_v08_2_cluster_consolidation.json`.
O passe quantitativo não substitui revisão artística humana. A v08.2 não foi
promovida a `res/` nem compilada em ROM.

A folha histórica v1 contém 61 poses: idle (4), avanço (8), recuo (8), pulo (8),
abaixar (5), dash (8), queda (8), rolagem/levantada (8) e defesa (4). Esses
IDs/contagens continuam como contrato do exercício, mas não promovem a arte
histórica como fonte visual ativa. A prova técnica idle+ação de duas poses
continua validando somente o método de conversão; nunca substitui a folha
completa de animação. A ROM de inspeção v5 deriva da fonte histórica e é apenas
diagnóstica, fora de `res/`.

A aprovação de uma nova folha exige previews 1×/4× de idle quadro 1, avanço
quadro 1 e queda quadro 2; inspeção humana de cabelo em 61/61; zero ocorrências
fora das regiões semânticas; zero clusters sem bloco 2×2 em cabelo, casaco e
pele (a haste branca de 1 px é exceção semântica); revisão de casaco, anatomia e
bengala; revisão independente e aceite explícito do dono. Integração, alocação
P1 comum, tiles/SAT/scanline/VBlank, runtime e ROM permanecem gates separados e
ainda não medidos para a candidata v08.2.
A ROM de inspeção v5 deriva somente da fonte v1, hoje arquivada, e preserva
evidência histórica navegável. Ela é diagnóstica, fora de `res/`, e não valida a
candidata v2 nem fecha paleta P1 global, orçamento por cena, pior VBlank, timing
contínuo ou aprovação de asset final. Consultar os valores medidos e limites
exatos no TDD antes de qualquer integração.

Pesquisa de *Master of Darkness* separa fatos do original de adaptação: um guia
de SMS relata ataque primário, subarma com `Up + Button 1`, salto com `Button 2`
e armas primárias/secundárias. Outra fonte diverge nos nomes de algumas armas
primárias; o manual escaneado e a ROM original precisam desempatar. O original
não documenta golpes de fighting game nem frame-data competitiva. Os quatro
ciclos listados são propostas autorais; valores de startup/active/recovery,
alcance e dano são hipótese sem teste e não selam o moveset.

Regra de coerência física: deslocamento contínuo a partir de apoio/impulso,
trajetória da arma ligada à mão e alcance de hitbox limitado à silhueta real.
Quanto maior alcance/dano/cobertura, maior startup, recovery, custo de recurso
ou exposição; cada golpe deve ter contrajogo explícito. Física em runtime Z80
usa inteiros/Q8.8, sem `float`/`double`; pulo/queda usam posição, velocidade e
gravidade por tick, e bumerangue usa arco inteiro determinístico. O JSON inclui
distâncias/durações iniciais de marcha, dash, pulo e arremesso como
`proposal_unmeasured`, além de quatro linhas hipotéticas de frame data. Escala
de vida e dano continua pendente; não tratar pontos de dano como porcentagem
aprovada. A folha completa só pode ser desenhada após revisão das chaves e
orçamento TDD/spec; aprovação de contrato não prova pixel art, física,
equilíbrio ou ROM.

## Direção de arte — estilo visual (decisão humana, 2026-10-02)
**Estilo escolhido**: anime de luta anos 90 com traço e cores do exemplo
fornecido — folha SFZ2-style de Ryu,
`/mnt/sdcard/SGDKForge/SGDK_projects/Mugenesis_Demo .../res/mugen/ryu/sheets/g0.png`
(medida: 288×104, 4 frames ~72×104, **15 cores úteis + fundo magenta** —
exatamente 1 sub-paleta). Dimensão de Ryu documenta o exemplo de traço; não é
escala-alvo deste roster. Referência é `inspiration_only=true`: âncora
técnica de traço/escala de sombra, **nunca fonte de pixels** (sprites Capcom
e ROMs Sega não viram asset — proveniência manda).

### Contratos mensuráveis (tradução SMS)
| Eixo | Piso numérico | Origem |
|------|---------------|--------|
| Paleta de sprites em combate | Uma P1 compartilhada por todos os sprites, até 15 cores úteis; P0 para cenário/HUD | TDD + contrato de paletas |
| Contorno | 1 px, quase-preto da própria sub-paleta | referência |
| Sombras de material | 3 tons por material (base + sombra + sombra profunda/highlight), sem dithering em pele | referência |
| Saturação | primárias saturadas; sem "gradiente suave" (ilegal na paleta mestra) | SFZ2 + SMS_GLOBAL |
| Escala corporal de luta | **66–72 px**, centro 70 (referência Fatal Fury Special GG projetada para SMS) | `doc/11-gdd.md` + `doc/15-tdd.md` |
| Line weight | constante entre frames e entre personagens; drift = reprovação | style_drift_policy |

### Escala e morfologia do elenco (direção do dono, 2026-10-04)
O peso de gameplay não determina altura de tela. A folha aprovada de Hayato em
Kenseiden é a referência do projeto para clareza de pixel clusters, contorno e
acabamento; identidade, roupa e cores de cada personagem continuam vindo do
respectivo jogo e conceito harmonizado. O elenco deve ser revisto em conjunto,
com baseline comum e sem normalizar cada figura para a mesma altura.
Joe Musashi é uma referência separada de proporção humana esguia e massa dos
membros; o uso como âncora morfológica não aprova seu recorte atual nem autoriza
copiar identidade, roupa ou paleta. Cada âncora deve ter escopo explícito.

| Personagem | Altura de corpo-alvo SMS (px) | Direção morfológica/visual |
|-------------|-----------------------------|----------------------------|
| Guerreiro de Golden Axe | 64–68; nunca acima de Alis | Jovem e ágil; reduzir a escala anterior e seguir o conceito aprovado v2 |
| Hayato / Kenseiden | 68–72 | Âncora de escala e acabamento do roster |
| Joe Musashi / Shinobi | 68–72 | Lutador médio; proporção humana esguia, não referência de recorte |
| Dr. Ferdinand Social | 66–72; centro 70 | Mesma escala de Joe; silhueta esguia, sem parecer menor |
| Alis Landale | 66–70 | Jovem heroína; proporção de cabeça, torso e pernas sem leitura chibi |
| Landau / Lord of the Sword | 68–72 | Igualar Joe e Dr. Social; preservar design aprovado e acabamento de Hayato |
| J.J. / Zillion II | 68–72 | Igualar Hayato; jovem ágil, não chibi, proporcional ao conceito aprovado |
| Demais heróis e chefes | faixa individual no contrato visual | Medir exceções e manter os mesmos critérios de roster |

As faixas são alvos visuais do projeto, não lei de hardware. A referência de
escala é *Fatal Fury Special* para Game Gear: uma captura de gameplay foi
inspecionada em viewport nativa 160×144; uma figura em pé ocupa cerca de 53 px
de altura no quadro consultado. Projetar essa fração para a tela SMS 256×192
resulta em `53 × 192 / 144 ≈ 71 px`; o centro de trabalho fica em 70 px com
tolerância de roster. A estimativa é visual e aproximada, não uma medida de
tile ou limite físico; o jogo varia tamanho aparente por pose/profundidade.
Referências: [capturas originais Game Gear de Fatal Fury Special (160×144)]
(https://www.mobygames.com/game/10591/fatal-fury-special/screenshots/game-gear/66969/),
[galeria de gameplay](https://www.gamestar.de/galerien/fatal_fury_special_game_gear,46053.html)
e [documentação técnica da resolução Game Gear](https://docs.retrogamecoders.com/platforms/sega/).

Comparar altura corporal de coroa a sola; arma, cabelo solto, capa e efeitos
ficam registrados separadamente como extensão da silhueta. A tela não determina
canvas do PNG: escolher por pose, acrescentar borda transparente e manter
largura/altura em múltiplos de 8 para o inventário de tiles. 96×96 não é mais o
alvo padrão; canvas maior exige justificativa visual e orçamento de
tiles/runtime. O primeiro estudo técnico de Dr. Social usa 80×80, convertido em
nearest-neighbor 5/6, para aproximar a faixa de 70 px sem interpolação.

Os vínculos explícitos continuam: Guerreiro de Golden Axe ≤ Alis; Dr. Social,
Joe Musashi e Landau na mesma faixa; J.J. e Hayato na mesma faixa. Diferença de
altura não substitui a revisão humana de cabeça/torso/pernas, morfologia,
clusters, contorno, paleta e fidelidade. `audit_roster_harmony.py` mede apenas
dimensões e relações declaradas; a prancha comparativa recebe revisão artística
separada.

Contrato corrente, fontes e medidas do primeiro quadro comparativo em
`doc/roster_harmony_contract_v1.json`. O board
`data/source_art/roster_harmony_review/review_drafts/historical_comparison_candidates/harmony_sprites_frame00_candidate_v1.png`
atinge as relações dimensionais declaradas, mas o dono rejeitou sua decisão
estética: Joe tem defeito de recorte; os demais candidatos leem atarracados/chibi;
e alguns agrupamentos de cor poluem a pintura apesar dos valores de paleta
corretos. A próxima proposta precisa passar os eixos humanos registrados em
`doc/roster_harmony_candidate_review_v1.json`: morfologia, massa dos membros,
recorte, agrupamento cromático, acabamento e leitura nativa. O board de revisão
`data/source_art/roster_harmony_review/review_drafts/historical_comparison_candidates/harmony_sprites_frame00_review_v2.png`
registra a reprovação e continua fonte de estudo, não sprite aprovado. Um frame
00 não aprova animação ou integração.
Uma direção morfológica alternativa em
`data/source_art/roster_harmony_review/art_direction_studies/harmony_morphology_study_v1_finish.png`
é apenas referência para discutir corpo/finish: seus valores cromáticos ainda
não foram validados pela paleta mestra, e a tentativa de fundo transparente foi
rejeitada por franja. Não promover esses PNGs como personagem, folha ou recurso.

Em 2026-10-04, o dono apontou defeitos construtivos na prancha de sete
personagens: olhos, mãos/handedness, conexão mão→arma, articulações, fixação e
perspectiva de equipamento, pés/baseline, contorno e agrupamento de luz/material.
L106 acrescenta o workflow `tools/sms_wrapper/.agent/workflows/art-review.md`
e o checklist obrigatório `audit_art_review_checklist.py`. A nova ilustração
`data/source_art/roster_harmony_review/art_direction_studies/harmony_morphology_study_v2_review_candidate.png`
propõe as correções, mas não é pixel art SMS e aguarda parecer de arte
independente e decisão do dono; o checklist
`data/source_art/roster_harmony_review/art_direction_studies/harmony_morphology_study_v2_review_checklist.json`
mantém todos os eixos como pending. A proposta não altera nem aprova folhas de
sprites já existentes. Em sprites reais, a inspeção de cada quadro ocorre em
1× e nearest-neighbor 4×, com paleta, recorte, animação e roster verificados em
gates próprios.

### Política de prompt/geração
- Descritores técnicos neutros apenas ("90s anime fighting pixel sprite,
  1px dark outline, 3-tone shading, saturated primaries"); proibido
  "in the style of Street Fighter/Capcom/Zero 2" em prompt de geração.
- `source_kind` de todo asset final: redesenho autoral (hand_authored ou
  ai_generated pós-tradução) — ROM rip só como estudo em `out/local_study/`
  gitignored.

### Paletas de referência por personagem e alocação CRAM (2026-10-02; alocação atualizada em 2026-10-09)
Manifesto machine-readable: `doc/palettes_manifest.json`, gerado e validado por
`doc/build_palettes_manifest.py` contra `tools/sms_wrapper/sms_palette.py`
(códigos 6-bit, rampas de material ΔY ≥ 17, ≤15 úteis, índice 0 transparente).
As entradas por personagem descrevem cores de identidade e estudo de autoria;
elas não são tabelas CRAM separadas que possam ser carregadas simultaneamente.
No SMS, P1 é a única tabela de cores de sprite e todos os objetos de sprite
compartilham seus índices. As 14 entradas atuais do manifesto somam 43 RGBs
distintos; é necessário harmonizá-las numa tabela de combate P1 de até 15 cores
úteis antes de promover sprites. Esse mapeamento permanece `pending`.
P0 atende cenário e HUD. Suas cores de HUD precisam manter papéis consistentes
entre estágios, deixando as demais entradas para cenário. Tiles de fundo podem
selecionar P1 com `TILE_USE_SPRITE_PALETTE` para reutilizar cores já carregadas;
isso não adiciona cores à CRAM nem altera a tabela global de sprites.
P1 índice 0 é transparente somente para pixels de sprite. Índice 0 de BG sempre
exibe uma cor da tabela escolhida, inclusive quando um tile usa P1. P0 índice 0
é a cor visível de backdrop, não alpha; o orçamento visual do projeto o reserva
como fundo.
Composição, slots fixos do HUD e cores de cenário são definidos na tabela de
paleta do scene contract, sem carregar uma paleta nova por personagem durante
o round. A referência machine-readable é `doc/palette_runtime_contract_v1.json`.

Pares de mesma luminância e matiz diferente são aceitos **somente** separados
por contorno 1 px (política do traço SFZ2). Joe (traje clássico) é **alterno
por troca de roles no mesmo pool** — não gasta paleta extra. Dr. Social NÃO
tem forma vampira (correção do dono, 2026-10-03: a transformação é premissa
de *Vampire: Master of Darkness*, Game Gear 1993 — não do SMS).
Revisão cromática Dr. Social (2026-10-03): traje azul/ciano com sombra teal,
cabelo grisalho e botas castanhas foram conferidos no sprite original SMS;
camisa branca, cravat burgundy e óculos de latão permanecem detalhes autorais.
Contorno opaco usa navy #000055 para preservar o índice 0 transparente. Esta
paleta substitui o traje cinza da revisão anterior.

Na roupa de Dr. Social, a rampa do tecido mantém os tons SMS em ordem
sombra/base/luz: teal `#005555`, ciano `#00AAAA`, azul `#55AAFF`. A revisão da
arte convertida deve conferir a continuidade espacial desses tons pelas faces
e dobras do casaco/calça em todos os quadros. A conformidade de RGB com a
paleta não basta: azul claro isolado numa região de sombra é defeito de
`material_shadow_flow_coherence`. Este é um contrato de material para a
conversão candidata, não uma decisão sobre a paleta P1 compartilhada do jogo.
Sombras, base e luz devem aparecer em blocos contíguos de cel shading, sem
dithering ou pixels-confete. Branco, amarelo e demais acentos ficam limitados
às regiões semânticas aprovadas no concept e no contrato de paleta; pixels
isolados na roupa, cabelo ou contorno reprovam
`semantic_palette_role_confinement`. A limpeza deve preservar olhos, luvas,
gola, bengala e os demais detalhes legítimos de identidade.

Paleta candidata de J.J. (2026-10-04): derivada do sprite `J.J - Standing`
de *Zillion II: The Tri Formation* no Master System. Azul-violeta, vermelho
magenta, laranja, pele e branco foram aproximados à grade RGB canal×85; rampas
extras de sombra cel mantêm até 15 cores úteis. Preto do sprite-fonte é
substituído por navy #000055 no contorno, pois índice 0 permanece transparente.
O gerador validou a paleta individual `jj_zillion_ii` com 13 cores úteis.
Concept art v4 em duas poses completas foi aprovada visualmente pelo dono em
2026-10-04. O jogo Master System permanece como fonte de identidade, paleta e
comportamento; as referências do anime, pedidas pelo dono, só esclareceram a
construção e o mapeamento do figurino. Nenhum pixel, pose ou composição externa
foi copiado. O PNG usa os 13 tons SMS declarados para J.J., índice 0
transparente e sem dithering; os gates de recursos passaram. A aprovação libera
o estudo separado de sprites, não aprova a folha, moveset, integração em `res`
ou ROM. O estudo idle de 12 quadros segue candidato e passa por seus gates
próprios antes de revisão visual.

## Prova de conversão e regra de animação

Após o concept/model sheet aprovado, a primeira prova técnica por personagem
mostra exatamente duas poses-chave separadas: idle e uma pose de ação. Esta é
uma referência visual e um inventário de pixel/paleta/tiles; **não** é uma
animação de dois quadros nem uma folha final. A folha de animação só começa
depois da revisão humana, da semântica de movimentos e do orçamento explícito
de ROM, VRAM/RAM, SAT/scanline e VBlank no TDD e em `13-spec-cenas.md`.

Toda animação do jogo deve considerar os doze princípios: squash and stretch,
anticipation, staging, straight ahead/pose to pose, follow through/overlap,
slow in/slow out, arcs, secondary action, timing, exaggeration, solid drawing e
appeal. O contrato de cada animação registra status e evidência de cada
princípio. Uma pose estática não demonstra timing, aceleração/desaceleração,
intervalos, follow-through ou ciclo; esses eixos ficam pendentes até haver
quadros e revisão adequados.

O proof sheet técnico segue
`doc/asset_conversion_proof_standard_v4.md`; a prancha é mantida em
`data/source_art/asset_conversion_proofs/`, nunca promovida automaticamente a
`res/`. A grade de tiles aparece em mapa separado. O gate
`audit_asset_proof_sheet.py` exige correspondência exata entre recorte de
preview e PNG-fonte, e verifica cobertura de limites/paleta; revisão humana
independente julga anatomia, acabamento, fidelidade e apelo. Número de quadros
por sheet não é constante física do Master System: o teto do projeto depende
da medição de padrões residentes, pools, ROM/banking e uploads no VBlank.

### Limites de hardware que afetam os assets

- Tela 256×192; VRAM 16 KB = 512 padrões gráficos de 8×8 (32 bytes cada), com
  janela selecionada para sprites de 256 padrões.
- SAT até 64 objetos e até 8 sprites por scanline; objeto mede 8 px de largura
  por 8 ou 16 px de altura. Arte do lutador exige layout metasprite e simulação.
- CRAM tem 32 entradas em duas tabelas de 16. A tabela P1 é compartilhada por
  todos os sprites: índice 0 transparente e até 15 cores úteis comuns a todo o
  elenco ativo. P0 alimenta BG/HUD; seu índice 0 é backdrop visível. Tiles BG
  podem usar P1 via `TILE_USE_SPRITE_PALETTE`. O RGB usa canais
  `{0,85,170,255}`.
- RAM 8 KB, ROM sem mapper 48 KB, sem DMA; custo do pior frame de VBlank deve
  ser medido. Inventário de tiles não prova residência, scanline ou tempo de
  carregamento.
- O hardware não fixa um número geral de quadros por folha. Enquanto pools e
  política de carga não estiverem mensurados no TDD, registrar esse teto como
  `pending`; não inventar uma contagem máxima.

O piloto v2 foi rejeitado por arma junto à borda e canvas 96×96. A v3 também foi
retirada como proposta atual: sua reamostragem achatava o terminal da bengala e
deixava a forma ambígua. A v4 preserva duas poses independentes em 80×80 (10×10
tiles), reamostradas em nearest-neighbor a 5/6; usa o frame-fonte 01 para idle
e o 06 para ação, cujo terminal arredondado é legível no original. A bbox opaca
mede 37×67 px no idle e 58×64 px na ação, incluindo equipamento. A faixa visual
66–72 px é para altura anatômica em pé, coroa–sola e sem equipamento; a ação
agachada varia por encenação e não é um teste direto dessa altura. As caixas
totais atuais incluem itens e não provam conformidade; a altura anatômica ainda
requer medição/revisão humana. O par usa 89 padrões únicos (2.848 bytes brutos
em 4bpp). Ver
prancha e relatório
em `data/source_art/asset_conversion_proofs/dr_social/dr_social_sms_keypose_proof_v4.png`
e `.json`. A amostra mostra 12 cores no estudo-fonte, mas isso não prova o
mapeamento para a tabela global P1 de até 15 cores; essa harmonização está
pendente. O terminal da bengala também precisa de revisão humana específica,
além de anatomia, fidelidade do concept, pintura, regiões materiais, orçamento
runtime e decisão do dono. A rota de conversão está registrada em
`tools/sms_wrapper/.agent/skills/sms-asset-to-rom.md` (L121). Em 2026-10-10,
idle e ação foram empacotados como 89 padrões 8×8 únicos mais um padrão vazio
(2.880 B carregados), construídos em ROM diagnóstica de 16 KiB e exibidos em
sessões Emulicious isoladas. A comparação exata encontrou zero divergências
nos 1.483/1.556 pixels opacos e nos fundos transparentes examinados. Esse
resultado prova a conversão estática e o vínculo por SHA desta amostra; não é
integração em `res/`, aprovação visual final, animação, gameplay ou orçamento de
produção. Paleta P1 do elenco, revisão humana, orçamento completo de cena,
VBlank, áudio e aceitação de release continuam pendentes.

## Cenas planejadas
| # | Nome | Escopo em 1 linha | Status |
|---|------|-------------------|--------|
| 01 | tela de seleção | grid 9 heróis + 4 chefes desbloqueáveis | documentado |
| 02 | duelo 1v1 | round com HUD de vida/timer sobre tables do motor | documentado |
| 03 | progressão do percurso | hall → chefes; relação Arcade/História em FC02 | documentado; não implementado |
| 04 | abertura | elenco, ruptura, perigo e logo | direção documentada; budget pendente |
| 05 | título | identidade, início e acesso aos modos/opções | direção documentada; budget pendente |
| 06 | opções | ajustes com efeito e retorno claros | conteúdo de opções pendente |
| 07 | cena narrativa | diálogo/retratos, encenação no palco e transição ao duelo | direção documentada; budget pendente |
| 08 | vitória/evolução de Alis | resultado, nível e distribuição de atributos | regras FC01 pendentes |
| 09 | encerramento | resolução, epílogo e retorno | roteiro final FC04 pendente |
| 10 | apresentação de golpes | nome, controle SMS, comando real e execução na velocidade da luta | padrão documentado; implementação/validação pendentes |

## Fora de escopo (explícito)
- Paridade com MUGEN real — o teto é "motor de luta MUGEN→SMS dirigida por dados".
- Tag-team, itens de arena, estágios interativos, online/link cable.
- Uso direto de sprites extraídos das ROMs Sega como arte final (proveniência bloqueia).
- Mexer em `MSSF2T` (intocável) — engine compartilhada via tabelas compiladas, não via fork.

## Teto de claims aprovado
"protótipo jogável de jogo de luta fan Master System sobre motor MUGEN→SMS" —
nada acima disso sem medição + evidência de emulador.
