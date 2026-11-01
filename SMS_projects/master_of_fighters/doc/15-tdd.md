# 15-tdd — master_of_fighters

## Padrão de apresentação de golpes — contrato futuro de integração

[Padrão de projeto](character_move_showcase_standard_v1.md), cena 10. Não há
implementação neste lote. Estender dados/FSM/renderer/loader oficiais, não
criar outra engine de showcase ou tabela divergente de animação/comando.
UI lê ID/nome/comando/condições da mesma definição que o reconhecedor e luta.
Demonstração funcional envia a sequência de input por esse reconhecedor;
prática lê input consumido e resultado. Injetar pose diretamente só serve à
revisão artística identificada, nunca prova de execução de golpe.

Relógios separados: pausa de leitura/replay da UI e timeline real de movimento.
Na execução normal, mesmos IDs/holds, objetos/hitstop/recuperação da luta;
nenhum ajuste de velocidade no emulador ou duração paralela. Trace identifica
input observado, comando aceito, estado/pose submetida/apresentada, contato e
primeiro retorno controlável. Slow/step são facilidades diagnósticas rotuladas.

Reset por demonstração é explícito: posição, adversário, recurso, relógios e
objetos, sem vazar comportamento para partida normal. Super de counter usa
ataque adversário elegível e resolver normal; não forçar ramo hit. Troca de
página/saída consome navegação e limpa estados transitórios antes de liberar
controle. Preservar regras de orientação/precedência/buffer do jogo.

Catálogo compilado lista asset→ação/página→símbolo→ROM e permite carga por
demanda conforme banking existente; não exigir todos os assets residentes.
Exibir conteúdo implementado e rotular pendências em revisão; produto não
ensina comando inexistente. Critérios de aceite e extremos na spec/padrão.
Reuso futuro como desbloqueável separa elegibilidade/acesso do conteúdo, sem
implementar save/economia/recompensa antes de decisão. Alvo60/piso58, medição
integrada de UI+combate, VBlank e sessão privada continuam obrigatórios.

## Campanha, apresentação e progressão — contrato futuro, 2026-11-01

[Direção no GDD](11-gdd.md#direção-de-fã-e-campanha--proprietário-2026-11-01),
[roteiro](12-roteiro.md) e [composição/aceite](13-spec-cenas.md#cenas-da-direção-de-fã--2026-11-01).
**Documentado; sem implementação, build ou teste novo de runtime neste lote.**
Propostas abaixo definem responsabilidades e invariantes; nomes de estados
não alegam módulos existentes. Usar consumidor e motor oficiais; não abrir
um motor de cutscene concorrente ou ramificação jogável para fugir do budget.

### Estados, comando e continuidade

Proposta de fluxo: `abertura → título → modo → seleção → nó de história →
apresentação → round → resultado → recompensa/conversa → próximo nó/final`.
Versus passa de seleção/apresentação a round/resultado sem progressão Alis;
Arcade depende FC02. Separar ID da cena, fase da apresentação, modo da partida,
resultado e estado dos combatentes. Trocar sprite não muda modo ou dano.

Encenação reaproveita renderer, poses e integração do motor, com direção de
atores explicitamente roteirizada. Não injetar input de jogador sem marcador
para fingir IA/combate real. Hits narrativos têm resultado de roteiro e trilha
própria; dano competitivo não vaza para o primeiro round. Golpe do visitante
precisa ter contrato de luta aprovado antes de ser apresentado como seu super;
se ainda não existe, storyboard permanece pendente, não criar mecânica pela cutscene.

Cada trecho registra estado inicial/final, falante/texto, ações por ator,
objetos/FX, câmera/paleta, áudio, condições de avanço e skip. Uma saída central
encerra hitboxes, objetos, tracks/áudio e comandos transitórios; aplica endpoint
uma vez. Skip no meio de carregamento não libera luta com VRAM parcial.
Entrada mantida é tratada pelo adaptador oficial conforme GD01; verificar que
o primeiro comando intencional depois de liberar controle é recebido.

Na cena 07, retrato/caixa não podem consumir padrões ainda usados pelo palco.
Definir residência e recarga sem presumir dupla name table livre. Fonte/glyphs
portugueses, comprimento máximo real e paginação precisam prova no framebuffer;
texto transbordado não deve ser “resolvido” cortando fala essencial. Selecionar
variante contextual por dados autorizados de arena/par/nó, com fallback de
entrada-base contratada, não improvisar moto/cameo para qualquer condição.

### Alis: dados, isolamento e transação

Separar perfil competitivo fixo e estado da campanha. Proposta de dados
estáticos e limitados: nível, pontos livres, investimento por atributo,
identificador do encontro recompensado e etapa/resultado; limites, tipos e
custo RAM/ROM precisam medição. Inteiros/fixed point conforme necessidade,
sem float/malloc, sem overflow ao somar bônus/múltiplos níveis. Recalcular
stats a partir de base+tabelas aprovadas, não acumular multiplicações em cada
reentrada. Tetos de atributos/vida/dano e ordem de redução de dano são parte
do contrato de balanceamento, ainda abertos.

Resultado único cria recompensa pendente; painel cria prévia separada;
confirmar valida saldo/tetos e aplica uma vez, só então avança. Repetição de
evento, botão mantido, replay do resultado, continue e retorno ao painel não
podem pagar de novo. Identificador de encontro e política de retries precisam
considerar reinício de campanha; um único booleano global não basta. Se o
modo permitir adiar escolha, preservar saldo e oferecer destino aprovado.
Não presumir SRAM/save: memória volátil, persistência e reset são decisão FC01/02.

HUD lê o valor lógico e distingue HP atual/máximo, LV e Super. Vida máxima
maior não pode ser uma barra idêntica que engana sobre dano relativo; decidir
representação/feedback e testar. Defesa com escudo exige variante coerente
entre corpo, guarda, hitboxes e efeito; aparência não concede invulnerabilidade.
Conflito entre escudo já aprovado e desbloqueio visual está em FC01: nenhuma
remoção/substituição automática da concept. Magia precisa efeito funcional
do kit decidido; não criar atributo que só altera texto.

Antes de selecionar números, simular/prototipar configurações de início,
meio e fim; build pura de cada atributo, mistura e tetos combinados. Confirmar
que erro continua punível, guarda não gera bloqueio eterno, vida+defesa não
multiplicam resistência sem teto e ataque/magia não produzem derrotas sem
resposta. Comparar ganhos por diferentes estilos/níveis de habilidade, retry
sem farm e duração total do percurso. Simulação ajuda a escolher candidatos;
resultado competitivo só se fecha com duelo completo no emulador e playtest.
Versus deve produzir exatamente o mesmo perfil com ou sem campanha evoluída.

### Shinobi: três magias e voz digitalizada

As três magias são direção autorizada; a ficha futura de cada uma ainda exige
comando/custo, preparação visível, direção/área/alcance, resposta adversária,
acerto/guarda/erro, interrupção e recuperação. O rótulo original não é contrato
de hitbox. Não preencher as três com o mesmo ataque renomeado; variantes de
um super só valem se a escolha e a diferença forem perceptíveis e aprovadas.
Propostas de papel no GDD não equivalem a moveset/frame-data aprovados.

PCM via PSG é hipótese técnica compatível com pesquisa de sample playback,
não garantia de fidelidade de fala. Consultar o padrão local
[contrato de engine](../../../doc/05_technical/mugen_engine_standard.md) e registrar fonte
SMS, cue, duração original, trecho editado, taxa/formato/bytes, conversão,
hashes e perdas. [Referência técnica de sample playback](https://www.smspower.org/Development/SamplePlayback)
informa pesquisa; uso externo não substitui headers nem custo medido no alvo.
Não baixar/usar voz arcade/MD por conveniência; fala exata ainda não foi ouvida
neste lote. Fonte de áudio, autorização/proveniência e manifesto antes de `res/`.

Proposta de freeze de super: preparo → estado dramático simétrico com duração
finita declarada → execução/resolução → recuperação. Congelar timer/animação
de combate só onde o design mandar; gerenciar input/buffer e Pause/NMI
explicitamente. A fala acompanha pista visual equivalente, nunca exige som
para defender. Medir resposta após fim, ambos os lados, última unidade de
recurso, fim de round, interrupção, reset/Pause e duas chamadas próximas.

Ocupação do Z80, instruções/intervalos PSG, banking, interrupções e restauração
de áudio precisam piloto. `DI` não bloqueia NMI; não prometer que silenciar
IRQ torna toda sequência segura. Estado dos canais de música/SFX deve retornar
sem nota presa, ruído, estalo excessivo ou ritmo quebrado. A música pode ser
interrompida/atenuada por prioridade definida, não porque um registrador ficou
sem restauração. Qualidade avaliada por escuta e captura isolada, além de
integridade do stream; maior taxa sem ganho audível não é automaticamente melhor.

**Aceite obrigatório:** freeze não exclui janelas ruins nem valida apenas ISR.
Se reprodução bloqueante impede o scheduler/input e derruba o avanço funcional
abaixo de 58, a implementação reprova mesmo que a tela parada seja intencional.
Investigar reprodução cooperativa/trecho/formato e orçamento, mantendo direção
do dono; qualquer perda relevante de frase, identidade ou qualidade exige
tradeoff registrado. Não substituir silenciosamente voz por ruído PSG nem
acelerar emulador. Medir transição e retomada, além da janela PCM, com relógios
funcionais que distingam progresso programado de stall. Nenhuma dessas rotas
está comprovada nesta ROM.

### Orçamento e evidência por incremento

Planejar timeline de residência por fase antes de contratar veículo, monstro,
retratos e grandes FX. Plano deve cobrir palco, corpos, HUD, objetos, texto e
áudio realmente simultâneos; paletas compartilhadas e pico de scanline valem
em cenas não interativas também. Para lanternas/vento, comparar técnica BG,
reuso de padrões e atualização escalonada, sem pintar corpos acidentalmente
ou tirar pista de luta. Pior quadro inclui a troca de fase e o efeito mais caro.

Pilotar uma cadeia pequena e completa após o combate funcional: apresentação
→ conversa → round com resultado → vitória/Alis → próximo nó. Abrir outros
mundos depois da prova desse percurso; o conteúdo autorizado continua no GDD,
com dependências explícitas. PCM e cenário animado precisam medições próprias
e depois integradas; folga de um teste isolado não paga soma de cargas.

Cada pacote registra ROM/SHA, sessão privada/cleanup, versão de regras/assets,
inputs/precondições, vídeo framebuffer, rastreio de estados/resultado/recompensa,
áudio isolado e métricas de recursos/FPS/worst-frame. Alvo60/piso58 por janela
sem arredondar permanece obrigatório. Repetir skip, extremos e retorno em
ambas as orientações. Registrar preferência estética, defeito observado e
hipótese separadamente. Evidência antiga de seis poses de J.J. não paga estas
cenas, balanceamento, diálogo, voz ou evolução. Checklists documentais não
transformam nenhum desses eixos em PASS.

## Interface de execução do design — 2026-11-01

**Documentado, implementação pendente.** [GDD](11-gdd.md#contrato-de-experiência--revisão-de-design-de-2026-11-01),
[roteiro](12-roteiro.md) e [cenas](13-spec-cenas.md#contratos-de-experiência-das-cenas--2026-11-01)
definem o que precisa ser percebido e testado. Este lote não modifica C,
dados de runtime, assets ou ROM. Reutilizar o consumidor e o pipeline oficial;
não criar outro motor/viewer para fazer os contratos parecerem implementados.

### Movimento: separar apresentação, regra e resultado

O contrato executável futuro deve associar ID de movimento, gatilho/comando,
estado inicial, fases lógicas, ID da pose apresentada, orientação/pivô,
deslocamento, caixas, elegibilidade de contato, custo, interrupção/cancel e
endpoints hit/block/whiff. `pose_duration` artístico não é `active`; `hitstop`
é evento lógico finito com saída, não atraso de upload. Não copiar números de
`movesets_draft.json` ou MSSF2T para preencher campos abertos.

Na ROM atual, `probe_state` (C7F6) é pose submetida, `probe_keys` (C7F8) é
input observado no loop e `probe_hold` (C7F9) é exposição; não são FSM de luta,
hit confirmation ou vida. SMRT C7E0/C7F0 e selo VBlank são instrumentos
diagnósticos. Para contato, engenharia deve expor IDs/frames e resultado do
oponente sem sobrepor DATA; o protocolo concreto e o budget dessa
instrumentação ficam pendentes, com corredor auditado antes de leitura.

Traço futuro precisa distinguir: aplicação na ponte, aceite na ROM, primeira
reação visual, contato/guard/erro, alteração do rival/HUD e primeiro retorno
controlável. Captura manual da placa mediu somente ponte→imagem e terminal.
Não converter três avanços VDP observados em promessa universal de latência.

### Ownership e transições propostas

Owners lógicos propostos: FSM global é dona de cena/round/resultado;
adaptador de input é dono dos comandos/edges; FSM do lutador é dona da ação/
movimento/controle; resolução de combate é dona de contato/vida; pool de
objetos é dono do bumerangue autorizado; apresentação é dona de SAT/padrões/
PNT/paletas/scroll; áudio é dono dos canais e sua restauração. São
responsabilidades para integrar na implementação oficial, não novos módulos
obrigatórios nem prova de memória alocada. HUD lê o resultado lógico e não
altera vida por animação.

| Aresta/gatilho | Saída e entrada | Persistência, input e recuperação |
|---|---|---|
| 01→02, escolha confirmada | Encerrar foco/feedback de seleção; configurar lutadores, apresentação, chão/HUD e round. Trabalho VDP em setup com display off; bytes reais pendentes. | Transportar IDs escolhidos; política de vida/timer/Super depende GD02. Consumir confirmação e neutralizar edges antes de liberar luta, conforme GD01. Não iniciar round com carga incompleta. |
| Preparação→luta, liberação do round | Apresentações terminam; relógios/controle recebem estado explícito. | Regra de skip/entrada mantida pendente; repetir transição não inicia dois relógios ou ataques. |
| Luta→resultado de round, KO/time-over | Encerrar hitboxes, objetos, hitstop e eventos ofensivos; fixar resultado lógico e apresentá-lo uma vez. | Placar permanece; evento simultâneo/empate depende GD04. Desligar ameaça lógica antes de apagar só a imagem. |
| Resultado→preparação, próximo round | Limpar objetos e controles transitórios; reposicionar atores e reconstruir HUD coerente. | Placar da partida permanece; vida/timer e persistência do Super precisam GD02. Nenhum comando antigo ou projétil reaparece. |
| 02→03, duelo resolvido | Encerrar owners transitórios de luta/áudio e mostrar resultado/etapa. | Transportar vencedor e progresso; desbloqueio é evento único condicionado a GD04. |
| 03→02, próximo oponente | Encerrar resultado; inicializar duelo com o próximo ID aprovado. | Confirmar uma vez; fim de lista não gera ID inválido. Ordem/dificuldade dependem GD04. |
| 03→01, conclusão/retorno | Encerrar percurso e restaurar seleção válida. | Desbloqueios/persistência, derrota/continue e cancel dependem GD04; não presumir SRAM ou novas telas. |

Nenhuma dessas transições foi exercitada na ROM da placa. Reset/pausa e falhas
de carga precisam política explícita quando integrados; não criar novos modos
de jogo por checklist. Cada aresta exige vídeo + estado/SHA, repetição de
saída/reentrada e medição do pior frame de carga, sem herdar throughput do
estado estável.

### Orçamento antes de arte adicional

Para a cena 02, medir distâncias/contatos, ambas as faces e simultaneidade
real antes de derivar teto de asset. A placa usa pool de sprite já medido em
posição fixa, P0 de chão/HUD e carga de BG anterior ao loop; não demonstra
aproximação, objeto, HUD dinâmico ou PSG. Tabela P1 única não é permissão para
trocar paleta individual em luta. Valores concretos por SHA ficam na spec.

Tradeoff técnico pode alterar packing/residência sem mudar o comportamento
se a equivalência for demonstrada. Alterar alcance, preparação aceita,
recuperação, silhueta/escala, arma ou remover pista exige decisão registrada.
Preservar controle e tentativa reprovada. Engenharia deve medir próximo degrau
e carga completa; piso58 por janela, input/lógica/apresentação e worst-frame
continuam pendentes nesta ROM diagnóstica. Implementação de combate depende
GD01/GD02/GD05, não de mais conteúdo ou de outra folha.

## J.J. — seleção aprovada pelo proprietário

A resposta “aprovado” fecha o conceptv5/fontev6, a proporção da Zillion,
os seis desenhos sem FX e o retorno apresentado com7/4/2/3/6. Preservar arte,
tempos e ROMs; decisão em `decisions/jj-zillion-character_owner_approval.json`.
Checkpointv7 registra o aceite sem inventar percepção contínua ou nova sessão.
As pendências de aceite nas seções anteriores são históricas. Objetos/FX,
combate completo, produção e homologação global continuam fora deste aceite.

## Histórico técnico anterior ao aceite

## Integração diagnóstica J.J. — mesma rota e consumidor

`MOF_JJ_SAMPLE=1/2` seleciona os headers v5 nos dois sentidos no consumidor já
existente; nenhuma nova lógica de animação, projétil, render, input ou probe.
A fonte6 remove um ponto de I00 que não sobrevivia à redução: funções oficiais
recalculam o idle e comprovam igualdade de índices nos dois sentidos; 14 PNGs,
12 cenas e dois headers continuam idênticos. Fontes de ação v5 e conceito v5
mantêm as poses e corrigem só arma/pega, sem efeitos. Material-index→P1 de
Social congelado evita a regressão de 34 pixels constatada na tentativa inicial.

Canvas 104×88/pivô48,80/posições16/128,64; packing de fases medido em ambas as
faces. Pool180×32 B no primeiro meio de VRAM, PNT0x3800/SAT0x3F00, modo normal
8×8. Builds base esquerda/direita e direita stress128 têm 32 KiB; vínculos e
corredores passaram. QA2casos/260RGB e vídeo real480RGB exatos; FPS20s
59,79/59,84 após falha8s preservada. VBlank3.000frames0derrame, mínimo213
base/224stress128. Cinco sessões novas fechadas; revisão contínua/aceite humano
ainda pendentes.
O perfil só mostra poses de personagem e não implementa dano ou objetos/FX.

## Histórico J.J. v1 — proposta com pulso supersedida, não implementada

Novo estudo de tiro único reutiliza `prepare_authored_sprite_sample.py`, o empacotador oficial e o consumidor diagnóstico em `src/main.c`. Fonte autoral e pulso finito incorporados às poses; sem sistema novo de projéteis, colisão ou dano. Perfil normal 8×8, escala única e pivôs/solas/grades explícitos; selecionar apenas após medir o par nas duas faces. ROM, vínculo, QA, FPS e VBlank próprios permanecem pendentes até a execução. Rastreio em `jj_zillion_single_shot_route_v1.json`.

## Perfil atual — somente tempos v7, fonte v4 reutilizada

Seletores15/16 consomem `out/diagnostics/hayato_short_cut_v2/timing_only_v7/converted_{left,right}/sample_data.h`.
Mesma FSM, modo normal8×8, escala, P1, pivôs e fases da v4. Somente
`sample_durations` troca4/1/2/3/1/3 por8/1/2/7/2/5. Exigir igualdade dos oito
PNGs por lado e header inteiro exceto essa tabela. Fonte v4 reaproveitada sem
`sample_rect_px`; nenhum pixel é novo. Três builds32KiB e QA nova passaram;
260quadros exatos e8/1/2/7/2/5 comprovados nos dois sentidos. Vídeo real480quadros
exatos; FPS59,71/59,46 em8s. Base e stress128:3.000frames cada,0derrame,
mínimos213/223; sessões encerradas. Aceite humano pertence ao preview fonte
escolhido; a equivalência de conteúdo e exposição qualifica a apresentação
técnica da ROM, sem atribuir ao dono uma nova sessão observada.
V6 é controle rejeitado e não deve ser tratado como seleção.

## Histórico — candidata v6 com tempos e lâmina transitória

Mesma FSM, emissor, P1, escala comum e empacotador normal 8×8 da v4. Contrato
v3: 8/1/2/7/2/5 ticks. R02 admite delta de lâmina autorado, composto apenas em
regiões declaradas; índice/PLTE/alpha fora delas exatos. Cinco outras poses,
Social e guardas permanecem controles por hash. Residência, SAT e scanline
devem ser recalculados para o novo desenho nos dois sentidos, com nova ROM,
gravação real, duração apresentada, FPS e VBlank. O opt-in `sample_rect_px`
declara um recorte-fonte contendo toda a opacidade e margem transparente;
rejeita limites inválidos/corte/bool. Evita mudar a grade de redução do corpo
quando o extremo da arma altera a bbox. Defaults reproduzem header e 8 PNGs
v4 byte a byte. 26 testes do adaptador passaram, inclusive 6 casos de recorte
e amostragem estável. Conversão v6:220 padrões/7.040B,max53SAT,pico8; seletores
13/14. Sete PNGs por face idênticos à v4; somente lâmina de R02 muda. Provas
novas de ROM completas: QA260quadros exatos, holds8/1/2/7/2/5 apresentados,
480quadros exatos em gravação nativa sem stepping; decode MP4 lossless confere
com RGB bruto. FPS59,74/59,42 em janelas8s. Base/stress128:3.000frames selados
cada,0derrame,mínimos213/223. Sessões fechadas e PIDs exatos ausentes.
Força/ritmo/efeito de velocidade e aceite da candidata continuam pendentes.

## Implementação corrente — fonte v4, sprite normal 8×8

`prepare_authored_sprite_sample.py` mantém defaults v1/v2 tall. Opt-in v2
`sprite_size=8x8` registra PNGs intermediários com padding transparente,
chama `pack_sms_metasprite.pack_poses`, compensa fase no META e mantém PNGs
públicos/pivôs/escala/P1. Um blanktile reservado; janela física256padrões.
Source/PNGs não são redesenhados pelo código.20testes e self-check128tall+64normal
conferem reconstrução exata inclusive preto opaco, limite e rejeições.
Controle tall antigo reproduz header e3PNGs byte a byte; snapshot histórico
284b15b preservado em out, sem tornar-se implementação concorrente.

Main recebe seletores9/10 com headers converted_v4_left/right, macro de altura8
para `SMS_setSpriteMode(SPRITEMODE_NORMAL=0)`; fallback16 continua tall1.
Mesmo FSM/probes/input/SATemitter, poses7incluindoidle,14ticks.219padrões/7008B,
max53SAT/pico8. Dados todos residentes com displayoff; rotina normal atualizaSAT,
stress128 reenvia prefixo residente correto. Perfil atual medido: 3.000 frames
selados em cada ROM, zero derrame, mínimo213 base e223 stress128; FPS base
59,78/59,67 em duas janelas8s. Os números não são herdados do perfil anterior.
`expected_opaque_bottom_px=80` rejeita registro stale antes de publicar header.

Captura privada opt-in `capture_video.py --session ID --realtime --seconds 8`:
callback RGB24 nativo de DisplayWindow durante run livre, sem stepping. O bridge
bloqueia leitura/input/step enquanto grava; stop pausa/fecha/flush, confere bytes
contra contagem nativa, codifica lossless e preserva bruto. Emulicious.jar original
permanece intacto. Nesta ROM:480quadros/70.778.880B em8,0187s, todos coincidem com
os sete PNGs legais; decode do MP4 tem o SHA do RGB bruto. Capture overhead e
timebase nominal não certificam FPS; sonda em duas janelas separadas o mede.
7 testes de custódia/erro da captura e20do adaptador passaram. Sem hitbox/dano/áudio.

## Histórico: corte curto diagnóstico — Hayato, 2026-10-29

Mesmo adaptador oficial v2 e runtime genérico. Nenhum conversor novo, nenhuma
mudança no FSM de input ou renderer; apenas seleções5/6 e dados4poses+idle,
SAMPLE_POSE_COUNT5 e durações0,3,2,2,5. Memória/probes continuam no corredor
C7D2..C7F9,14sondas,folga1784B. ROMs32KiB,202patterns/6464B residentes no
window0..1FFF,PNT3800,SAT3F00,tall8×16. PaletaP1 e bitmapSocial preservados.
Fases conjuntas de grade foram planejadas para todos osframes em ambos os
sentidos; max33SAT/pico8. Registro da sola-fonte e registro óptico de projeção
foram conferidos antes de ROM: C01/C04 perderiam uma linha esparsa no nearest,
por isso usam sourceanchorY126 sem mudar sourcepixels/scale. C03também126;
guard/C02127. Referências/receitas/raws/assembly expõem uniform2/9raster das3
poses de apoio e C02 original byte-idêntica, sem normalização individual.

Configsativas .mddev/hayato_short_cut_sequence_v1_registered_{left,right}.json;
manifestos hayato_short_cut_v1_{left,right,right_stress128}_build.json.
Build/gates de recursos não aprovam timeline, throughput, VBlank ou qualidade.
Medição será fresh no SHA escolhido; sem palco, áudio, hitboxes ou gameplay.
A escala absoluta legada68–72px não é reclamada por este perfil diagnóstico.

## Hayato — adaptador v2 e diagnóstico do par, 2026-10-29

Estendeu-se `tools/sms_wrapper/prepare_authored_sprite_sample.py`, sem segundo
pipeline/consumidor. Schema v1 mantém IDs/tempos do Social e header/8PNGs reais
byte-idênticos. V2 aceita IDs/durações explícitos, extra_scale obrigatório para
escala comum, canvas/pivô, posições/reflexão e mapa opcional dos índices de
paleta ORIGINAIS para códigos exatos da P1. O packer/core canônicos continuam
responsáveis pelos bytes. Índice0transparente nunca pode receber override;
preto opaco continua em índice visível. Nenhum remapeamento da saídaSMS pronta.

Hayato fonte v2 SHA0b72e603… permanece sem edição. Material map5→42,13→21,26→0
corrige71RGBsSMS; o índice13 é misto e foi revisto em pele/pescoço/cabelo nesta
pose apenas. Guardas16bitsY preservam guard de offsets não negativos.
Pivô final(68,127) pela sola observada;1px abaixo da derivada anterior, sem
alterar fonte/escala. FaseHayato[0,1] nos2sentidos; SocialJ04 direita[3,9],
espelhado[5,9], medidas na composição final. Não copiar fases para outros frames.
SAMPLE_POSE_COUNT/layout emitidos pelo v2 tornam o runtime genérico; com1pose
não se dispara índice inexistente. V1 usa defaults7poses/(40,72)/(152,72).
MOF_HAYATO_SAMPLE1..4 seleciona os quatro pares diagnósticos no mesmo main.

Dados atuais *baseline_v3*: guardas66patterns/2112B/32SAT e parSocialjab
222patterns/7104B/35SAT máximo, pico8 em todas as composições. Janela física
0x0000..1FFF256patterns, PNT3800, SAT3F00, tall8×16. P1 idênticaSocialv8,
15códigos; source original→mesmo código, source/alpha/metadata registrados.
Tudo residente carregado com displayoff; base escreve SAT porVBlank, não
streaming de poses. Degrau128B reenvia prefixo correto residente, não arte nova.
SMRT/worst probes C7D2..C7F9,14sondas,folga1784B nos mapas medidos.

ROM base direita035060f9…:59,67/59,81fpsNTSC,janelas8s;0derrame/3000,mínimo207.
Stress3540539e…:0derrame,mínimo218. Isso não mede duraçãoCPU, máximo de carga,
PAL, áudio, gameplay ou fluidez percebida. Bindings porcaso usam --map explícito
em out/diagnostics/hayato_cps2_sample_v1/*baseline_v3_rom_asset_binding.json;
o binding global históricoSocial não foi reatribuído silenciosamente.
QA4/4,236framesde vídeo+capturasguardas exatos,18checks, cleanup. Guarda tem
somente endpointRAM(frame>0,pose0), não duas janelas de contagem. Fonte/material
review pass, owner/ação/animação pending. Contrato legado68–72px não é promovido
por esta escala diagnóstica. Ver memorybank/result.json e receitas .mddev.

## Grade compensada da amostra v8 — 2026-10-29

`MOF_CPS2_SAMPLE=8` seleciona o novo header;5e1 preservam as baselines.
`packing_phase_px=[3,9]` somente no J04 muda a grade tall e compensa no META.
Controle commesmos oito PNGs: pico9→8/SAT33→34/pool218→220padrões. Nenhum
pixel/escala/pivô é alterado. Defaults[0,0] geram os dados antigos idênticos.
Neste emissor, offsets negativos são recusados: Y deSMS_addSprite é16bit,
não wrap automático. Fonte/receita/replay e nove testes ficam no handoff.
ROM v8 SHA452cd565…,32.768B;120framebuffers independentes exatos;13casosRAM
confirmam ordem/holds2/1/1/1/1/3, lag1VDP na apresentação. FPS8s59,62/59,74;
selo3000frames0derrame/mínimo207,+128B0derrame/mínimo217. Quatro sessões
encerradas. Só diagnóstico NTSC, sem aprovação de playback/arteSMS/dono/produção.

## Diagnóstico facial v5 — 2026-10-29

`MOF_CPS2_SAMPLE=5` seleciona o novo header no mesmo consumidor; valor1 conserva
os dados anteriores. Manifestos/receita estão no handoff `dr_social_cps2_sample_v1.md`.
Fonte v5 parte do nativo v3 ampliado4× e extraído1/4, sem mudar escala corporal.
216 padrões/6.912B residentes, pico8;31SAT salvo J04=32. As tentativas de braço
v6/v7 não foram selecionadas; v6 reprovou composição de J04 com pico9, sem build.
ROM v5 SHA `fc46d77b…`: QA independente120/120 framebuffers exatos; FPS em duas
janelas8s59,62/59,79. Selo3000frames:zero derrames, mínimo207; stress+128B,
SHA `a5c013a8…`,zero derrames, mínimo217. Três sessões encerradas, bindings e
probes próprios. Sem herdar evidência da v3 ou aprovar arte/gameplay/PAL/áudio.
As seções seguintes descrevem a baseline v3 quando explicitamente indicadas.

## Amostra CPS2 autoral — diagnóstico opt-in de 2026-10-28

O consumidor existente seleciona a amostra com `MOF_CPS2_SAMPLE=1`, somente
via manifesto candidato e `build_inner.py --build-dir`. O esqueleto nominal
continua separado pelo preprocessor, sem outro projeto/consumidor. Fontes
candidatas vivem em `data/source_art/`; PNGs SMS, header e ROM ficam em `out/`.

O adaptador `tools/sms_wrapper/prepare_authored_sprite_sample.py` não desenha
personagens nem implementa outro conversor: faz registro explícito do raster,
carrega PNG indexado em `sff.Sprite`, aplica `display_fit.scale_sprite`,
`sms_tiles`, `runtime_format.pack_tiles_tall/build_frames` e a compactação/
paleta de `scene_cut`. O pool estático compartilha pares idênticos entre as
poses. A fonte usa 30 tons por material, fora da restrição de CRAM; a saída
usa 15 cores úteis numa única P1 compartilhada com o Ken de referência.

Receita final da candidata v3: recorte transparente justo, framebuffer
x=2/3 e y=6/7, escala corporal extra 4/6 derivada apenas do idle; cada pose
mantém seu pivô/sola registrados antes da conversão. Fonte, SHA, paleta,
parâmetros e transformações constam no JSON de configuração e na receita de
extração. J01 é também a pose idle; não se declara ciclo de idle animado.

O pool medido tem 212 padrões, 6.784 bytes; sprites tall 8×16 na primeira
metade da VRAM, índices pares, limite físico de 256 padrões. O par vazio
reservado também fornece o tile 0 do fundo diagnóstico. PNT em 0x3800 e SAT
em 0x3F00. Todos os quadros do par Social/Ken medem 31 SAT e pico 8 por linha.
Fundo sólido de diagnóstico não paga orçamento de cenário/HUD de produção.
Uploads dos padrões/CRAM ocorrem no setup com display desligado. Na animação,
somente SAT é escrita no VBlank; não há streaming para estender as durações.
`MOF_SAMPLE_STRESS_BYTES=128` reenvia um prefixo correto dos mesmos padrões
para medir o degrau seguinte sem alterar pixels ou residência.

A ROM expõe SMRT e selo worst-frame de 3.000 frames em 0xC7D2..0xC7F9,
inicializados e voláteis. Corredor: 1.784 bytes de separação no mapa candidato.
`probe_state` em 0xC7F6 registra a pose submetida após a cópia SAT; o traço
observou framebuffer correspondente no frame seguinte. Não interpretar a
leitura da sonda como apresentação instantânea. Input 1 dispara o jab;
input 2 alterna autoplay; o boot mantém idle estável antes da primeira ação.
Autoplay insere 21 ticks de idle entre jabs; a ação conserva nove ticks.
Sem colisão, dano, física de combate ou áudio novo neste diagnóstico.

ROM base observada: 32.768 bytes, SHA
`f5d54b1545aa20ec41ec7da0290b2c948aeec393c025d71c2401254b58458b8d`.
O estado de FPS/VBlank e a revisão final ficam no relatório do lote;
compilação, inventário e boot não os aprovam por inferência.

> Arquitetura técnica. Autoridade #7.
> A API definitiva é o header (`sdk/devkitSMS/SMSlib/SMSlib.h`, autoridade #8) —
> este documento NUNCA inventa assinatura. Em dúvida: leia o header.

## Restrições assumidas (herdadas, sempre ativas)
```
❌ float/double em runtime quente  — SDCC Z80 faz float em software; use int16/Q8.8
❌ malloc / free                   — buffers estáticos; RAM = 8 KB
❌ VRAM em massa fora do VBlank    — sem DMA
❌ >8 sprites/scanline, >64 na SAT
```

## Contrato técnico de arte e animação (v1)

Limites de hardware fixos para converter cada pose:

| Grandeza | Limite SMS |
|---|---:|
| Canvas | 256×192 px |
| VRAM | 16 KB = 512 padrões de 8×8 em 4bpp, 32 B cada |
| Índices lógicos endereçáveis por sprites | 256 por escolha da base do reg. 6 |
| Padrões residentes seguros no layout de revisão | 191 com base 0x2000, tile base 257 e name table em 0x3800 |
| Objeto sprite | 8 px de largura × 8 ou 16 px de altura |
| SAT / scanline | 64 objetos totais / 8 por linha |
| CRAM | 32 entradas: P0 para BG/HUD e P1 para todos os sprites; P1 índice 0 transparente; até 15 cores úteis compartilhadas em P1 |
| RAM / ROM sem mapper | 8 KB / 48 KB |
| Transferência | sem DMA; pior frame de VBlank precisa ser medido |

### Alocação de CRAM e gestão de cor de combate

O limite de duas tabelas de 16 entradas não cria duas tabelas independentes
por lutador. Neste projeto, `P0` atende cenário e HUD, e `P1` é a única tabela
compartilhada por todos os objetos de sprite: P1/P2, projéteis e efeitos.
Sprites usam até 15 cores úteis em P1; seu índice 0 é transparente. Não há uma
tabela de sprite própria por personagem.

`SMS_loadBGPalette` carrega P0 e `SMS_loadSpritePalette` carrega P1, conforme
`sdk/devkitSMS/SMSlib/SMSlib.h`. O mapa BG pode selecionar P1 por tile com
`TILE_USE_SPRITE_PALETTE`; isso reutiliza cores já carregadas e não amplia a
CRAM. Transparência do índice 0 aplica-se apenas a pixels de sprite; BG pixels
no índice 0 sempre mostram a cor selecionada, mesmo em tile que usa P1. P0
índice 0 é a cor visível de backdrop, não alpha. O contrato visual do
projeto reserva esse slot como fundo e conta até 15 cores úteis de arte em P0.

Os manifestos por personagem são paletas de referência/autoria. Os 14 perfis
atuais têm 43 RGBs distintos e não cabem como paletas de sprite separadas em
runtime. Antes de promover o elenco para assets de gameplay, definir uma tabela
P1 comum de até 15 cores e registrar o mapeamento de cada papel de material.
Esse trabalho está `pending`; a prova Dr. Social usa 12 cores locais, mas ainda
não demonstra a tabela global. P0 mantém papéis estáveis de HUD entre estágios
e usa o espaço restante para o cenário; tiles BG podem recorrer a P1 para
reutilizar cores compatíveis. O mapa exato de slots HUD fica vinculado ao
contrato visual da cena.

Carregar/trocar tabelas durante round altera cores de todos os sprites ou da
cena. A política é carregar no setup da tela/round; qualquer atualização em
jogo exige medição da escrita CRAM no pior VBlank e evidência visual. Não fazer
recolorização por personagem em runtime sem orçamento e prova. Contrato
machine-readable: `doc/palette_runtime_contract_v1.json`.

Esses tetos não definem o orçamento de um asset. Um contrato de runtime por
cena ainda precisa declarar layout BG/sprites/name table/SAT, pools estáticos,
residência por estado, padrão de compartilhamento, tamanho ROM/banking, bytes
por VBlank e resultado do simulador de objetos por scanline. Até isso estar
preenchido e medido, `max_frames_per_sprite_sheet` permanece `null`; não existe
uma quantidade física universal de quadros por folha.

O fluxo de arte exige primeiro uma prancha técnica com duas poses separadas
(idle e ação), não uma sequência animada. A v2 foi rejeitada por canvas grande e
arma cortada. A v3 resolveu o limite do canvas, mas a revisão humana identificou
que a terminação da bengala ficou achatada após a redução. A v4 usa o frame de
ação 06 da folha-fonte, cuja forma arredondada permanece clara, e mantém o idle
no frame 01. As poses têm 80×80, conversão 5/6 nearest-neighbor e 89 padrões
únicos no par. O idle em pé tem bbox opaca de 37×67 px; a ação agachada tem
58×64 px incluindo equipamento. A faixa de 66–72 px é referência para a altura
anatômica em pé, coroa–sola e sem equipamento; as caixas totais atuais incluem
itens e não provam conformidade. A caixa da ação varia com a pose e não deve ser
comparada diretamente como se mantivesse a postura em pé. A altura corporal
continua pendente de medição/review. A auditoria verifica pixels do original, transform determinístico,
tile alignment, bordas transparentes e declaração da geometria da terminação
para revisão humana. Na prova estática da v4, `pack_sms_metasprite.py` gerou
89 padrões únicos compartilhados entre idle/ação e um padrão vazio reservado
(90 carregados, 2.880 B brutos); o simulador mediu 43/49 objetos SAT e pico de
6/7 objetos por scanline. A ROM diagnóstica de 16 KiB exibiu ambas as poses e
uma auditoria exata de framebuffer reportou zero divergências de pixels
opacos/fundo transparente. Esses números pertencem somente a esse par e a essa
ROM diagnóstica. A residência com cenário/HUD/outros lutadores, paleta P1
global, RAM/ROM de produção, banking e custo VBlank continuam `pending`; a
prova não configura um orçamento de cena nem uma sequência animada.
O scan de componentes opacos não encontrou ilhas menores que 2 px;
`audit_sprite_cutout.py` mantém o resultado global pending até haver regiões
materiais auditáveis. Ver
`data/source_art/asset_conversion_proofs/dr_social/dr_social_sms_keypose_proof_v4.json`.

### Reconstrução da fonte de animação — diretiva v08 (2026-10-12)
A fonte v1 de 61 poses e a conversão v10 são registros históricos arquivados,
não referências visuais ativas. A antiga candidata v07, SHA-256
`f5c41fb2204e3b2fff9a6e824fc55a767c2456dcdd9c62d17351f76696c95dc8`, foi
rejeitada pelo dono por perda de hierarquia do casaco, cabelo inconsistente e
sombreamento granulado. Não há sprite sheet atual aprovada nem candidata ativa.

A diretriz de reconstrução está em
`doc/dr_social_sprite_rebuild_directive_v08.md`; o feedback está registrado em
`doc/curation_candidates/2026-10-12_dr_social_v07_artistic_rejection.json`.
O dono autorizou máscaras explícitas por material e clustering determinístico
restrito a cada máscara, mantendo a geometria v07 e proibindo ImageGen/difusão.
Contrato: `doc/dr_social_sprite_mask_contract_v08.json`. O conflito sobre o
amarelo nos óculos de latão ainda bloqueia o PASS semântico final.
A única autoridade de identidade segue sendo o model sheet CPS2-Alpha-Cel v4,
SHA-256 `ddce2f5a302dd679610c1b0eb915ce10718a5df852f80e4a78af18db33426644`.

A diretriz fixa uma paleta indexada e papéis por material; exige cinza constante
no cabelo, planos duros contíguos no casaco e inspeção humana de toda marca
pequena. É proibido que scripts gravem alterações de pixels por blur, média,
distância, luminância, nearest-RGB ou remapeamento global. Ferramentas podem
medir e apontar candidatos, mas a edição de cor deve ser manual, por quadro e
região semântica, com delta rastreável. A paleta, grade e contagem estruturais
da v07 não superam a rejeição artística.

Status: reconstrução v08 por máscaras autorizada; a tentativa exploratória via
gerador de imagem foi reprovada por não preservar canvas, grade e paleta
(relatório `doc/curation_candidates/2026-10-12_dr_social_v08_imagegen_trial_rejection.json`).
A nova pintura por máscaras ainda não foi produzida. Os previews obrigatórios são idle quadro 1, avanço quadro 1
e queda quadro 2 em 1×/4×, além da folha completa. A aprovação requer inspeção
dos 61 cabelos, zero pixels brancos/amarelos fora das zonas autorizadas,
revisão independente e decisão explícita do dono. Nada foi integrado em `res/`
ou ROM; hardware e runtime permanecem sem medição para uma nova fonte.
### Histórico — fonte de animação aprovada v1, 61 poses (2026-10-10)

A folha técnica de duas poses (`dr_social_sms_keypose_proof_v4`) permanece
uma prova do procedimento de conversão; ela **não** substitui uma fonte completa
de animação. A fonte que o dono designou para conversão de produção em
2026-10-10 foi `data/source_art/sprite_studies/dr_social/
historical_approved/basic_sequences_61f_owner_source_v1/
dr_social_basic_sequences_61f_owner_source_v1.png`, SHA-256
`a95fc144f6d2574a9dfb43028b7b1d1fc91108b442f03fcfebac2df3f6d56057`.
Esse registro é histórico e não torna a v1 uma referência visual ativa. A
revisão v2 acima aguarda revisão do proprietário. O registro separa aprovação
da fonte visual de aprovação técnica dos PNGs convertidos.

Ela corresponde às nove primeiras sequências do contrato de animação: idle 4,
avanço 8, recuo 8, pulo 8, abaixar 5, dash 8, queda 8, rolagem/levantada 8 e
defesa 4, total 61 poses. A conversão em `out/diagnostics/
dr_social_61_pose_review_v5/` usa a paleta SMS aprovada e 61 canvases 80×80;
o report e o manifest preservam IDs por sequência. Todas as 61 folhas passam
validação de recurso, procedência e simulação SAT/scanline. O pico medido é 8
objetos por scanline e 51 objetos na SAT por quadro.

O limite de 256 é de índices lógicos, não de padrões residentes seguros para
todo layout. Nesta revisão, a base de padrão de sprite é 0x2000, a name table
visível começa em 0x3800 e o carregamento inicia no índice 257; assim, apenas
191 padrões de 32 bytes cabem antes da name table. A fórmula, medida por
`pack_sms_metasprite.py`, é `min(256 - tile_base,
(name_table_base - (sprite_pattern_base + tile_base*32)) // 32)`. Pools maiores
carregam uma pose por vez e não podem atravessar 0x3800. Os pools de idle (169)
e defesa (182) cabem compartilhados; as outras sete sequências ficam em modo
de inspeção pose a pose. O primeiro candidato que tratou 200/246 padrões como
residentes corrompeu os rótulos da name table; essa rota foi substituída.

A ROM `dr_social_61_pose_review_v5.sms` tem 114.688 bytes, SHA-256
`501161271e6cc51a7666520128375af04f6b8dde04cfa96071a410f09a78e6db`, e é um
viewer diagnóstico da fonte aprovada, não a ROM de gameplay. O vínculo
asset→ROM de diagnóstico lista os 61 PNGs e passou em
`audit_rom_asset_binding.py --require`.

Em uma sessão Emulicious privada (`c9709fd01c0742eb8c0eaebaa01f79d6`), os 61
IDs foram navegados individualmente e comparados no framebuffer 256×192, em
`(88,56)`, com o PNG indexado de cada pose. Resultado: 61/61 correspondências
exatas; 100.333 pixels opacos e 290.067 pixels transparentes conferidos, zero
divergências. O resumo e os PNGs por pose ficam em
`out/diagnostics/dr_social_61_pose_review_v5/project/out/evidence/`; a prancha
de amostra das nove sequências está ao lado do ROM. Isso confirma a conversão
pixel a pixel nesta ROM, mas não substitui revisão artística humana.

O viewer permite avançar/retroceder poses com esquerda/direita e sequências
com cima/baixo; botão 2 retorna à primeira pose. Apenas idle (169 patterns) e
defesa (182) podem reproduzir/pausar como pool compartilhado. As outras sete
sequências excedem a janela residente de 191 patterns e ficam em inspeção
pose a pose. O viewer não prova timing contínuo dessas sete sequências,
gameplay, FPS, áudio, PAL, paleta P1 comum do elenco, residência com cenário/
HUD, pior VBlank ou hardware físico. Os budgets de cena e aprovação final do
asset continuam gates separados.

### Escala de combate de referência — Fatal Fury Special (Game Gear)

O GDD fixa como referência de escala o jogo *Fatal Fury Special* no Game Gear,
sem tratar a composição como lei do hardware. A galeria mostra captura de luta;
a resolução nativa é 160×144. A inspeção visual de um lutador em pé estima
53 px de altura no viewport. Conversão proporcional para a tela SMS:
`53 × 192 / 144 ≈ 71 px`; alvo de trabalho do roster: 66–72 px, centro 70 px.
O jogo varia a escala aparente por pose/profundidade, então a comparação usa
pose em pé no plano-base e tolerância explícita. Medir coroa–sola do corpo,
separando extensão de armas, cabelo, capa e efeitos.

Esta é uma faixa de composição, não o canvas nem um limite fixo. O canvas deve
ser o menor retângulo que comporte a pose inteira, mais pelo menos um pixel
transparente de margem nos quatro lados, arredondado para múltiplos de 8.
96×96 deixa de ser padrão automático; tamanhos maiores exigem justificativa de
escala e inventário de tiles. O estudo v3 de Dr. Social usa canvas 80×80 (10×10
tiles) e nearest-neighbor 5/6 a partir da célula 96×96. Esse transform é
declarado e reconstituído pelo auditor; filtro, antialias, escala não declarada,
equipamento que alcance a borda ou pixel opaco cortado reprovam a prova.

O limite de pelo menos 1 px vazio é requisito de integridade da prova, não um
limite VDP. A auditoria mede ausência de contato com a borda e reprodução do
transform; o revisor humano ainda confirma se toda arma/equipamento está
visualmente completo, se a escala corporal é fiel e se a pose é anatômica.

Toda animação deve registrar análise dos 12 princípios Disney no contrato do
asset e no GDD: squash/stretch, antecipação, staging, ação direta/pose a pose,
follow-through/overlap, slow in/out, arcos, ação secundária, timing, exagero,
desenho sólido e appeal. Cada um recebe status/evidência; duas poses estáticas
não provam ciclo, espaçamento, aceleração, duração de frames ou follow-through.
Uma folha completa continua bloqueada enquanto esses eixos ou o orçamento
runtime estiverem pendentes.

### Contrato machine-readable de sequência animada

Antes de desenhar a folha, cada sequência registra estado inicial/final,
gatilho, loop/transição, IDs de poses, duração provisória de cada pose e tracks
alinhados para o personagem e cada objeto/efeito animado. A revisão considera
os 12 princípios; no mínimo sete devem ter aplicação planejada e pista ligada
a IDs de quadros. Os demais precisam de justificativa contextual. Pistas
planejadas não contam como evidência visual até existirem os pixels e a revisão
temporal.

`source_pose_count` significa desenhos de pose distintos propostos/produzidos.
Ele não equivale a objetos 8×8 ou 8×16 do VDP. Cada entidade declara também
`hardware_sprite_objects` por quadro; metasprite, tiles únicos/compartilhados,
RAM/ROM, residência, SAT/scanline e VBlank são medidos separadamente. O limite
de frames por folha continua `null` até medir o degrau de runtime seguinte.
`tick_definition` precisa registrar a relação entre update lógico e 50/60 Hz
antes de converter duração para tempo de parede.

Gate de cobertura: `tools/sms_wrapper/audit_animation_contract.py --manifest
<project>/doc/<character>_animation_contract_v1.json`; self-check obrigatório
para a ferramenta: `--self-check`. Ele valida IDs/endpoints/tracks/contagens,
12 decisões e mínimo de sete princípios aplicados, e rejeita contagem de
hardware apresentada como medida sem evidência. Não lê sprites nem valida
anatomia, física ou balanceamento. `audit_animation_semantics.py` verifica a
sequência real de PNGs; os gates de recursos, recorte, arte, scanline e runtime
continuam independentes.

No primeiro exercício Dr. Social, `doc/dr_social_animation_contract_v1.json`
tem 24 sequências e 191 poses-fonte propostas; nenhuma está desenhada ou
aprovada. Os quatro golpes autorais têm números hipotéticos de startup/active/
recovery, alcance e dano com `proposal_unmeasured`. Eles só passam a frame-data
do personagem após decisão do dono, definição da escala de vida, medição da
ROM e testes de hit/block/whiff e contrajogo. Trajetórias de salto, dash, queda,
estocada e bumerangue usam posição/velocidade discreta em inteiros/Q8.8; não
teleportar objetos nem permitir hitboxes fora da silhueta aprovada.

## Armadilhas Z80/SDCC vigiadas neste projeto
- `int` é 16-bit signed; `char` é unsigned por padrão (SDCC z80).
- Multiplicação/divisão são caras (sem HW mul) → tabelas lookup / Q8.8.
- ISR curta: trabalho pesado fica no loop principal. Pause = NMI.

## Mapa de memória (RAM)
| Faixa | Tamanho | Conteúdo |
|-------|---------|----------|
| — | — | — |

## Entidades e pools (estáticos)
| Pool | Máx | Bytes/entidade | Total |
|------|-----|----------------|-------|
| — | — | — | — |

## Máquina de estados
_(estados do jogo e transições permitidas)_

## Banking
- Alvo inicial: **48 KB linear sem mapper** (B01).
- Se exceder: mapper Sega (páginas 16 KB, regs 0xFFFE/0xFFFF), código restrito
  a 32 KB, dados bancados a partir do bank 2.
- Status atual: _(linear / bancado)_

## Áudio
- Driver: PSGlib (`sdk/devkitSMS/PSGlib/PSGlib.h` é a autoridade).
- Arbitração de canais SFX vs música (só 4 canais) — declarar explicitamente:
  _(qual canal cede para qual, e quando)_
- YM2413/FM é **opcional**: o jogo tem que funcionar sem ele.

## Orçamento de frame
_(quem escreve na VRAM, quanto, e dentro de qual janela. Cruzar com 13-spec-cenas.)_

## Primeira tentativa de continuidade de sombra — Dr. Social v6

A v6 substituiu a escolha RGB isolada pela média da cobertura do pixel-fonte
dentro do footprint de cada pixel de tecido na saída e quantizou o resultado
somente para a rampa SMS existente (`#005555`, `#00AAAA`, `#55AAFF`). O relatório
mede 6.145 pixels reclassificados nas 61 poses; silhueta nearest-neighbor,
alpha e cores fora da máscara azul/ciano permaneceram intactas. A versão ficou
como candidata intermediária: resolver a rampa local não assegurou, por si só,
blocos de sombra visualmente coerentes. V7 substituiu esse resultado pela
atribuição explícita da rampa por luminância. Ver
`out/diagnostics/dr_social_61_pose_review_v6/conversion_report_61_pose_v6.json`.

## Conversão da rampa de sombra do tecido — Dr. Social v7

Na saída SMS do personagem, o tecido usa a rampa existente ordenada por
luminância: sombra teal `#005555`, base ciano `#00AAAA`, luz azul `#55AAFF`.
A correção v7 atua somente nos pixels já classificados nessa rampa: calcula a
cobertura média RGB do footprint da fonte e escolhe um dos três tons existentes
pela luminância. Máscara geométrica, alpha e demais materiais usam a classificação
nearest-neighbor original. Não há cor nova, blur ou dithering.

O relatório registra 15.690 pixels remapeados nos 61 quadros, zero mudanças de
alpha e zero alteração fora da rampa. A ROM diagnóstica
`out/diagnostics/dr_social_61_pose_review_v7/project/out/rom/dr_social_61_pose_review_v7.sms`
tem SHA-256 `b27c328d11c58ba96474b83368d8a0afcda79600b388d21cb510b812632f53c2`.
Três quadros (ID01, ID02, ID03) foram comparados exatamente no framebuffer.
Isso verifica a saída da ROM, não aprovação estética; os 61 quadros, a paleta
P1 compartilhada, a residência/upload de produção e a revisão humana continuam
pendentes. O checklist exige `material_shadow_flow_coherence` e o revisor
inspeciona todos os quadros em tamanho nativo e ampliado.

## Refinamento de cel shading — Dr. Social v8 (candidato)

O dono rejeitou v7 por ainda apresentar tons intercalados, pontos escuros e
acentos com risco de leitura como confete. V8 usa v7 como base e aplica uma
passagem conservadora apenas dentro dos materiais: maioria local 5×5 para
reagrupar ilhas interiores da rampa, conversão de marcas navy pequenas e
totalmente envolvidas pelo tecido para o teal de sombra `#005555`, e remoção de
branco/amarelo singleton somente se inteiramente cercado por tecido. A máscara
de transparência e os índices de pose permanecem idênticos; nenhum branco ou
amarelo foi alterado, pois o detector não encontrou vazamento singleton com
essa condição. Os acentos legítimos continuam sujeitos ao eixo humano de papel
semântico da paleta.

Delta v7→v8: 927 pixels em 61/61 quadros (438 ilhas da rampa e 489 marcas navy
internas), zero mudança de alpha, zero nova cor e geometria/poses preservadas.
ROM diagnóstica: `out/diagnostics/dr_social_61_pose_review_v8/project/out/rom/
dr_social_61_pose_review_v8.sms`, 114.688 bytes, SHA-256
`e641d2a44a1da2ef4c8aa1b2d768bf54822df27f7e023036cf81d3f1dfc0e50d`. Emulicious
privado comparou os 61 framebuffers pixel a pixel com os PNGs indexados: 61/61,
zero divergências, sessão `ff0b89a1501b4237aa738f299ad3ee70`; índice em
`out/diagnostics/dr_social_61_pose_review_v8/project/out/evidence/
dr_social_61_framebuffer_v8/framebuffer_capture_index_v8.json`.
O harness reprodutível desta conferência é
`tools/capture_dr_social_61_pose_review.py`; ele espera 12 quadros após a
mudança de sequência para não capturar a tela transitória de carga. Isso verifica
renderização exata, não a qualidade artística.

`pixel_clusters`, `material_shadow_flow_coherence` e
`semantic_palette_role_confinement` continuam pendentes de revisão visual
independente e aprovação do dono. Fidelidade exata confirma apenas que a ROM
mostrou os pixels v8. V8 permanece em `out/diagnostics`, fora de `res/`; paleta
P1 compartilhada, animação contínua, VBlank, cena de produção e integração
permanecem sem validação.


## Revisão semântica dos acentos e cel shading — Dr. Social v9 (supersedida por v10)

A v9 parte da candidata v8, que já havia agrupado 927 pixels dos tecidos em
61 poses (438 ilhas da rampa e 489 marcas navy internas). A revisão encontrou
que a heurística v8 — atuar apenas em pixels totalmente cercados pelo material —
ão não cobre acentos que tocam a borda. A v9 usa âncoras semânticas para amarelo:
cluster de cabelo para a região de rosto/óculos e a junção luva-haste para o
pomo da bengala. Foram reclassificados 249 pixels amarelos fora desses papéis.
Nenhum branco, pixel alpha ou cor de paleta foi alterado; a confinagem semântica
de branco permanece pendente de revisão independente. A imagem candidata
nearest-neighbor 4× é
`out/diagnostics/dr_social_61_pose_review_v9/dr_social_61_pose_converted_preview_4x.png`
(SHA-256 `99dd4a592ad223840a3d2b4cd64788239ccf0a48da6f7619c89b9537ddaf2f40`).

A ROM diagnóstica v9 foi construída com 114.688 bytes, SHA-256
`81c2e47f684b307de6d2bfa803dc7e56a6b22402f06d7ecc8d8250f2b059bfd2`. A sessão
Emulicious privada `bfb478dfae0044d4a679db5df6bce018` comparou os 61 quadros
contra os PNGs indexados: 61 pass, zero divergências. Índice hash-bound:
`out/diagnostics/dr_social_61_pose_review_v9/project/out/evidence/
dr_social_61_framebuffer_v9/framebuffer_capture_index_v9.json`
(SHA-256 `eed561b63b17582d11c564d3c87678f8b639e2cf2783080f79fe2bdb3d84e8e6`).
Isto confirma somente que a ROM diagnóstica exibe os pixels candidatos. Não
confirma qualidade artística, confinamento semântico completo, gameplay, FPS,
áudio, VBlank ou orçamento de produção.

O checklist versionado `doc/dr_social_61_pose_art_review_v9.json` mantém os dez
eixos artísticos pendentes, revisão independente sem atribuição e aprovação
do dono como `false`. V9 continua em `out/diagnostics`, fora de `res/`.



## Dupla checagem semântica do branco — Dr. Social v10 (candidata)

A ampliação da v9 revelou 70 pixels brancos isolados ou em pares em punhos e
face fora das áreas reconhecidas. V10 reaproveita o cel shading v8 e a limpeza
amarela v9; detecta segmentos retos candidatos à haste por geometria, mantém
clusters brancos maiores para revisão humana e recolore 70 pixels em singles/
pares fora da haste pelo material vizinho. Nenhuma alpha ou cor foi adicionada. O detector confirma zero singles
ou pares brancos não ancorados restantes; clusters maiores e confinamento
semântico total permanecem revisão humana obrigatória.

ROM diagnóstica v10: 114.688 bytes, SHA-256
`41879e38c8a83caec07bd97e9208ca08f00fe35ec1e927ff31feab4eb7a3c8cc`. Emulicious
privado `5e5ba2973da44f6293ef27b79429b050`: 61/61 imagens indexadas iguais,
zero divergências. Índice
`out/diagnostics/dr_social_61_pose_review_v10/project/out/evidence/
dr_social_61_framebuffer_v10/framebuffer_capture_index_v10.json`
(SHA-256 `9b5d00c8176f7ab7c5cb8b03b8872a258e1dc3ebdec9de6b6d049053c4951015`).
A arte v10 continua em `out/diagnostics`, sem aprovação artística.

## Medidor comum de Super — decisão de design aprovada (2026-10-10)

O GDD define um medidor comum ao elenco com carga independente por lutador.
O Super de Dr. Social consome a barra cheia. O valor máximo interno, rotina e
taxa de carga, retenção/reset entre rounds, HUD e regra de interrupção permanecem
pendentes; nenhum número ou implementação de runtime é inferido por esta
decisão. Quando implementado, estado e acumulação usam inteiros, sem
`float`/`double` no runtime Z80. A regra precisa entrar no contrato de cena e
passar por medição de RAM, custo de atualização e VBlank antes de produção.

O contrato vigente de sequências de Dr. Social é
`doc/dr_social_animation_contract_v2.json`. O moveset está aprovado como
direção de arte/combate, mas os oito sheets de combate continuam candidatos a
produzir golpe a golpe. `social_light_jab` é o primeiro; seu PNG não entra em
`res/` nem em ROM antes de review independente, aprovação humana, conversão
indexada e prova técnica.

A candidata visual mais recente é a v4, em
`data/source_art/sprite_studies/dr_social/review_drafts/2026-10-10_social_light_jab_v4/`.
Ela melhora a leitura dos óculos, mas falha no preflight: RGB 1536×1024,
83.402 cores e fundo quase preto não uniforme. A v5 solicitando alpha binário
retornou halo e alpha 0–254, também reprovada. O checklist da v4 falha nos eixos
de clusters, recorte e confinamento de paleta; sete eixos e as aprovações humana
e independente continuam pendentes. As tentativas permanecem em `review_drafts`;
não inferir tile count, palette budget, scanline, VBlank ou comportamento de ROM.
Conversão e ROM aguardam aprovação visual do dono, revisão artística e prova
técnica em canvas lógico 80×80.

