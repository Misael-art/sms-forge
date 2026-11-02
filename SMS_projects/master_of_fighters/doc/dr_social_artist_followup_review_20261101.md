# Dr. Social — revisão da produção inicial e prompt de continuação

> **Direcionamento vigente:** ver a revisão de `07e4bce` e o prompt ao fim de
> [Apresentação de golpes](character_move_showcase_standard_v1.md).
> GQ03 é candidata autoral medida, ainda sem aceite de continuidade visual ou
> animação. GQ02 permanece diagnóstico. O texto abaixo preserva os
> checkpoints anteriores e não deve ser copiado como o próximo prompt.


## Histórico — retorno de escala e portraits

O retorno recebido agora é o do artista. Ele distingue corretamente estudos,
conversão, limites do controle Ken, fontes rejeitadas e ausência de ROM. A
frase “duas escalas que o adaptador emite” é tecnicamente incorreta: o schema
v2 aceita `extra_scale=[numerador,denominador]`, com 0 < razão ≤ 1, comum às
poses. `convert_poses` aplica primeiro o encaixe CPS2→SMS e depois essa razão.
1/1 e 4/6 são dois casos testados, não o domínio da ferramenta. O estudo
isotrópico 35/52 direto não equivale a colocar 35/52 como segundo passe.

### Verificação adicional do coordenador

Self-checks do adaptador e simulador passaram antes da leitura. Sem editar
ferramenta, pixels ou GDD, foram usadas as mesmas fontes, paleta, pivôs,
posições e referência da receita `dr_social_cps2_keys_measure_v1_extra46b.json`.
Apenas `extra_scale` mudou nos dois controles principais:

| Extra | Altura opaca da guarda | Pico guarda / BC04 | SAT guarda / BC04 | Resultado |
|---|---:|---|---|---|
| 7/9, modo 8×16 | 69 px | 9 / 10 | 36 / 38 | Ambos reprovados |
| 4/5, modo 8×16 | 71 px | 9 / 10 | 40 / 42 | Ambos reprovados |
| 7/9, modo 8×8, mesma fonte | 69 px, mesma escala | 10 / 10 | 58 / 60 | Ambos reprovados |
| 7/9, modo 8×16, fase (3,9) nas duas poses do ator | 69 px, mesma escala | 9 / 10 | 36 / 37 | Ambos reprovados |

Altura é bbox opaca da guarda; nessa fonte os extremos coincidem com coroa e
sola, sem arma mais alta/baixa. Não aplicar essa equivalência a qualquer pose.
As duas saídas principais têm 34 px de largura opaca total. Os testes mudam
parâmetros de representação, não constituem aprovação artística da transformação.
O adaptador terminou com erro por composição ilegal e preservou `conversion.json`;
o simulador oficial confirmou as reprovações. Nenhum gate foi contornado e
nenhum desses pares deve ser buildado como candidato de aceite.

Receitas, logs e relatórios estão em
`out/diagnostics/social_scale_review_20261101/`: `summary.json`,
`packing_checks.json`, `config_*.json`, `adapter_*.log`, `conversion.json` e
`audit_*.txt` por variante. A exploração é limitada: não varre todas as fases,
não troca Ken pelo elenco, não testa outras faces/cantos, não mede FPS/VBlank
nem mostra descarte numa ROM. Um pico do simulador não deve ser narrado como
observação de sprites caindo no emulador.

**Conclusão:** o adaptador alcança a faixa GDD; as composições testadas não
cabem. Não demonstram inviabilidade universal de 66–72 px. Tampouco justificam
aceitar 60 px, onde a bengala já falha. Recomenda-se manter o alvo vigente
até comparar alternativas concretas de atuação/composição, sem fechar o
tradeoff pelo proprietário. O próximo ramo não é refazer a mesma medição.

### Portraits observados

As duas pranchas de conversa foram inspecionadas: texto fora do rosto, nome
separado, expressão de fala com boca aberta e área reservada ao palco. Isso é
avanço de layout. O palco vazio não testa contraste/concorrência do cenário.
Rosto/texto têm suavização de estudo; origem truecolor e Liberation Sans não
são defeito automático de concept, mas não pagam acabamento/glyphs/paleta SMS.
Atentar para consistência de idade/rosto entre busto, model sheet e sprite;
parecer ainda estático, sem aprovação de animação labial ou cena completa.

### Prompt histórico — substituído pelo padrão de apresentação

Continue a produção completa do Dr. Social conforme o prompt inicial e o
contrato v2. Preserve o que produziu, as reprovações e os hashes. O designer
verificou seu retorno; não há aprovação de redução do GDD para 60 px.

1. Corrija o registro da capacidade do adaptador: ele aceita razões adicionais
   configuráveis. Use os resultados do coordenador de 69/71 px; não repita
   1/1, 4/6 ou essas variantes idênticas como novo progresso. A faixa de altura
   é alcançável; o par testado falha na composição. Não confundir o passe
   uniforme extra com a escala direta 35/52 nem alterar o encaixe silenciosamente.
2. Trate o gargalo em termos de largura por faixa corporal, células emitidas,
   grade e simultaneidade com o adversário. Reutilize a rota oficial. Compare
   cobertura opaca com intervalos físicos para distinguir limite da arte de
   desperdício de representação. Outras fases só justificam teste se houver
   hipótese concreta; exigir reconstrução exata dos pixels e relato do ganho.
   Uma fase histórica de J04 não é solução universal para outra pose.
3. Prepare propostas gestuais curtas de guarda/toque que preservem corpo,
   bengala, pegada, terminal e intenção de controle frontal. Explore apoio,
   rotação e perfil corporal antes de rigidez ou corte de arma. São propostas
   de atuação para revisão, não autorização de mudar alcance, altura lógica do
   golpe ou identidade. Compare chaves no par real do projeto quando disponíveis;
   Ken continua controle técnico, não aprovação do elenco. Não feche intervalos
   de uma pose ainda ilegal. Não gaste outra rodada repetindo a instrução de
   ponta alta que já trocou a identidade da arma duas vezes.
4. Se persistir conflito, entregue um comparativo concreto: função preservada,
   mudança proposta, fontes/poses, escala, alcance visível, par, pico/SAT e
   impacto estético. O dono decide mudanças de alvo/alcance/identidade. Separar
   arma em objeto, esconder células, apertar largura isoladamente ou adotar
   flicker não são soluções automaticamente autorizadas. Não atribuir a arte
   antiga de curadoria a causa sem demonstrar a ligação.
5. Não interrompa o pacote independente: complete estados cuja composição possa
   ser provada e avance portraits. Antes de multiplicar quatro expressões,
   traduza atenção/fala pelo pipeline de BG/paleta/glyphs adequado à cena,
   com comparação 1×/4×. Reutilize o layout candidato, testando texto mais longo,
   acentos e contraste com palco representativo. Preserve rosto/idade e não
   traga suavização/ruído da redução para arte final. Use caracteres reais da
   interface; rasterizar Liberation Sans no mockup não prova o texto runtime.
6. Continue até o personagem completo; este checkpoint não substitui o objetivo.
   Faça uma ação completa assim que chaves/representação estiverem viáveis;
   falta de solução da bengala não cancela atuação, portraits e estados
   independentes. Marque cada dependência com resultado concreto esperado.
7. Preserve matrizes e receitas, complete proveniência e proteja o trabalho útil
   pelo fluxo Git/recuperação vigente, com seleção explícita dos próprios arquivos.
   Não deixar fontes únicas sem proteção nem incluir alterações de outras tarefas.
   Não publique referências privadas. Quando houver ROM legal, faça QA privada
   por SHA, input→sequência→terminal→reentrada, ambas as faces/cantos, métricas e
   cleanup. Até lá, “simulado” e “observado no emulador” continuam distintos.

Entregue ao coordenador evidências e pendências sem autoaprovação; outro
personagem continua condicionado à revisão e à decisão do proprietário.

---

## Histórico da primeira revisão

Data: 2026-11-01. Escopo: inspeção documental e visual estática das chaves,
sem nova animação, conversão, build ou emulador. Não é aprovação artística final.
O anexo recebido nesta solicitação contém MT5X/Super ATR, não o relato do
artista. As conclusões abaixo derivam dos arquivos locais identificados;
não atribuem ao artista afirmações do texto anexado nem avaliam uma fala ausente.

## Evidência examinada e parecer

Foram lidos a memória, o diff do contrato v2, o prompt inicial, a matriz
`dr_social_coverage_matrix_v1.json`, o `lineage_v1.json` e os cinco prompts em
`data/source_art/sprite_studies/dr_social/review_drafts/cps2_keys_v1/`.
Foram inspecionados visualmente o model sheet v4, a prancha `keys_sms70_board_4x.png`
e as fontes nativas BC04/RL05. A bota foi inspecionada na prancha ampliada;
sem parecer de movimento, profundidade ou aceitação independente por quadro.

Hashes das três fontes novas e do jab reutilizado conferem com a matriz:

| ID | SHA-256 | Estado nesta revisão |
|---|---|---|
| jab v8 | `877f6e5b232b542f29b0d5794026fe3894d469beee6c47c02e9520d5c976ae41` | Controle existente, não refeito. |
| BC04 | `ee6d32596240ebae73bec446ceff6f1df43f56ae26c6d7d907749bb0fce12b3b` | Chave candidata; o cabo voltou à mão. Movimento ainda ausente. |
| K04 | `98d72ee59779ba860aef8a7809fc74fc20adfcac9d3c001d10bd25998cd3dfcf` | Chave candidata; linha baixa sugerida, sequência ainda ausente. |
| RL05 | `14944cc00fd18bfdc4d38ebe4b23b4b778452187776146d9f17384e1bc4b8652` | Chave candidata de estocada; composição integrada pendente. |

**Compreensão demonstrada:** distingue design aprovado de arte/ROM, preserva
J01–J06, não cria terceiro especial de bengala, registra poses faltantes e
rejeita tentativas com equipamento incorreto. Identifica a discrepância entre
escala diagnóstica e alvo GDD. Declara honestamente pacote incompleto e ausência
de conversão oficial/emulador; não cabe acusá-lo de promover qualidade pronta.

**Mistura de referências:** o lineage identifica J01 v8 como entrada; os prompts
novos concordam com ela e as chaves mantêm cabelo cinza, óculos, casaco e luvas.
Não há, nesses registros, evidência de uso da folha histórica de 61 poses como
matriz nova ou de outra experiência antiga como padrão ativo. Isso não prova
qualidade final, mas não sustenta atribuir os problemas àquela folha. Rótulos
antigos dentro de pranchas também não prevalecem sobre decisão/hash posteriores.

**Correções necessárias:**

- O prompt BC04 pede mover “only that cane”, como metrônomo; o da bota pede
  mudar “only the legs”. Isso pode servir a um reparo localizado, mas é orientação
  inadequada para construir toda a ação. Não deixar preservação de identidade
  virar torso congelado. A prancha estática não demonstra transferência de peso,
  preparação, trajetória, acompanhamento ou recuperação.
- O produtor declara 7/5/15 colunas de sprite para bengala/bota/rapieira a 70 px,
  sem adversário. Não localizei recibo de simulador oficial para essas contagens
  neste pacote. São um alerta, não budget certificado. A lâmina horizontal ocupa
  espaço expressivo; provar cobertura física e par antes de gerar seus intervalos.
  Se 15 objetos simultâneos na mesma linha se confirmarem, excede o limite mesmo
  sem rival. Outro objeto/track não aumenta a capacidade daquela linha.
- A razão única 35/52 e a correção do alvo de altura são propostas consistentes
  de registro, não aprovação de escala/composição/paleta de produção. O preview
  é redução de fonte, não PNG SMS oficialmente convertido ou framebuffer.
- O lineage preserva originais JPEG e prompts, porém não registra todos os
  hashes de originais/referências nem ferramenta/recibo e receita executável
  completa da extração/paleta/registro. Melhorar rastreabilidade sem inventar
  retroativamente uma origem ou afirmar preservação pixel-local não demonstrada.
- A ausência de um retângulo de portrait ainda não impede explorar bustos e
  propor uma composição diagnóstica. `versus_*` e conversa cena 07 são papéis
  distintos; não bloquear todo retrato por uma decisão de crop de outra cena.
- O cabeçalho do prompt inicial recebeu texto duplicado/truncado. Corrigir só
  esse acidente editorial; não reescrever instruções de origem para justificar
  os resultados produzidos.

A revisão não encontrou animação completa nova nem ROM deste pacote. O ponto
seguinte é uma ação completa verificável, com trabalho independente nos demais
itens, mantendo o objetivo final de um personagem completo.

## Prompt de continuação — copiar daqui até o fim

Você continua como artista/animador do **Dr. Ferdinand Social** em
`/home/misael/Projects/SMSForge/SMS_projects/master_of_fighters`.
Não comece de novo e não mude de personagem. Releia AGENTS/continuidade, memória,
GDD, roteiro, spec e TDD vigentes, o prompt original
`doc/dr_social_complete_character_artist_prompt_v1.md`, o contrato de animação
v2 e `doc/dr_social_combat_design_proposal_v1.md`. Este direcionamento corrige
como prosseguir; preserva a missão do pacote completo e as decisões do dono.
Diga [Contexto SMS Carregado]. Use RTK/run_host e o checkout existente.

### A. O que preservar e como escolher referências

Seu registro inicial foi útil: três chaves, tentativas rejeitadas preservadas,
jab intacto e pacote explicitamente incompleto. Não refaça J01–J06 por rotina.
Não apague BC04/K04/RL05 nem publique os estudos como aprovados.

Use uma lista positiva de referências por papel:

1. Identidade: model sheet CPS2-Alpha-Cel v4 e decisão específica; SHA
   `ddce2f5a302dd679610c1b0eb915ce10718a5df852f80e4a78af18db33426644`.
   Correções posteriores prevalecem: cabelo cinza e óculos de latão.
2. Construção/grade atual: jab v8, SHA
   `877f6e5b232b542f29b0d5794026fe3894d469beee6c47c02e9520d5c976ae41`;
   conferir também poses individuais e parecer v8. Sua aprovação não é global.
3. Método: `doc/curation_candidates/2026-10-29_dr_social_cps2_source_to_rom_method.json`,
   com workflow `original-artwork.md` e skill `sms-sprite-animation.md` centrais.
4. História: fonte v08.2 de 61 poses, conversões antigas, tentativas rejeitadas
   e comparações de curadoria ficam identificadas como histórico/controle.
   Não alimentar o gerador com todas as folhas encontradas. Não revogar seus
   aceites específicos; apenas não confundir esses aceites com a matriz atual.
5. Ken/Ryu e outras referências autorizadas mantêm seus papéis limitados.
   Não copiar roupa, corpo, golpe ou pixels. Não publicar insumos privados.

Antes de cada geração, registre exatamente quais imagens foram fornecidas,
com papel e hash. Se encontrar uma peça visual fraca, identifique arquivo,
revisão, papel e defeito; não conclua que todo o método falhou ou que a última
versão é automaticamente a melhor. Não use uma derivação técnica degradada
para fixar rosto, equipamento ou acabamento da fonte autoral.

### B. Retomar atuação corporal antes dos intervalos

Transforme o brief do golpe em preparação → execução → acompanhamento →
recuperação. Desenhe linha de ação, apoios, transferência de peso, quadril,
tronco, ombro/cotovelo/punho/pega e trajetória da arma. Identidade constante
não exige cabeça, torso ou roupa no mesmo pixel. Arma rígida não exige corpo
rígido. Quantidade de poses e deslocamento corporal decorrem da ação e do
contrato, sem copiar microdeslocamentos de outro golpe.

Para **bengala**, use BC04 apenas como candidata de contato. Compare cabo,
terminal, comprimento e espessura à arma de J01/model sheet. Crie uma carga
curta que explique a passagem da vertical à ameaça frontal, contato com apoio
e recolha que devolva peso/guarda. Não simplesmente gire uma haste em frente
ao corpo. Não acrescente projeção mágica ou outro alcance sem decisão.

Para **bota**, preserve a natureza de interrupção baixa e curta. Mostre a
perna de apoio recebendo peso, quadril/torso compensando, bota saindo e
recolhendo, pé plantando e guarda retomada. Não transformar em chute médio,
rasteira longa ou sequência idêntica ao jab com perna substituída.

Para **rapieira**, RL05 ainda não está pronta para comandar 12 intervalos.
Verifique identidade e proporção da arma na referência específica, posição de
pega, orientação do guarda-mão, apoio e silhueta. Não encurte/curve a lâmina
arbitrariamente. Se houver erro da fonte, corrija contra a referência; se a
forma fiel for tecnicamente inviável, registre o conflito de design/engenharia.
Não declarar que mover a lâmina para outro objeto resolve a scanline.

### C. Resolver o alerta de composição na rota oficial

Mantenha o GDD 66–72 px de corpo em pé, centro 70, distinguindo fonte ~104 px,
corpo inclinado e bbox com arma. A transformação 35/52 ainda é candidata:
compare-a ao adaptador oficial e ao par real, sem normalizar cada pose.

Rode self-checks antes das medições, use o adaptador vigente
`tools/sms_wrapper/prepare_authored_sprite_sample.py`, packers/simulador existentes
ou ferramenta oficial adequada ao contrato. Preserve entrada/receita/relatório.
Se suas contagens 7/5/15 vieram de procedimento exploratório, identifique-o
como tal e não o use para fechar o budget. Meça objetos emitidos e cobertura
opaca, em ambas as faces, com adversário/contato/canto e objetos previstos.

Investigue grade, padding compensado e packing somente se reconstruírem todos
os pixels nas mesmas posições. A solução v8 para sobreposição de intervalos
não elimina um limite físico inferior imposto por pixels da mesma scanline.
Separar arma/FX em tracks ajuda organização, não cria capacidade de VDP.

Não esconda overflow omitindo células, reduzindo só uma pose, fragmentando
silhueta ou introduzindo flicker como escolha unilateral. BG/híbrido/flicker
são propostas de representação com custo e efeito visual próprios, sujeitas
a contrato e decisão pertinente; não são passe livre para contornar o gate.
Se o par exigir decisão de alcance/escala/atuação, apresente alternativas
visuais concretas e medidas. Enquanto isso, avance em estados, retratos e
outras peças independentes, sem multiplicar a mesma pose inviável.

### D. Completar uma sequência e seguir até o pacote

Prioridade imediata: **bengala completa**, usando a candidata de contato apenas
se passar a revisão de identidade/atuação e a composição. Produza preparação,
execução, recolha e terminal, não só mais chaves isoladas. Revise em velocidade
normal e lenta. Se a composição da bengala também exigir decisão do dono,
conclua um estado independente enquanto prepara a alternativa concreta.

Depois siga bota, rapieira viável, bumerangue/tracks e três ramos do Super;
locomoção, guardas/reações/queda/levantada, entradas, provocações, vitórias,
derrota por tempo, empate e portraits. Não crie terceiro especial
`cane_riposte`. Preserve os 28 IDs obrigatórios e as lacunas visuais registradas,
sem inventar novos comandos ou invulnerabilidades.

O objetivo segue **um personagem completo para revisão**. Não encerre a tarefa
com outro relatório de três poses se houver produção autorizada viável.
Faça checkpoints técnicos internos por sequência e prossiga. Solicite ao dono
somente mudanças reais de identidade, regra, escopo ou tradeoff não autorizado;
não peça novamente permissão para produzir o pacote já solicitado.

### E. Retratos não dependem da resolução de toda a luta

Produza busto autoral fiel ao model sheet para neutralidade/atenção e variações
expressivas necessárias ao roteiro. Não derive rosto grande ampliando o sprite
pequeno. Preserve grisalho, óculos e proporções, sem rejuvenescer ou trocar estilo.

Proponha composição diagnóstica em 256×192 com palco, portrait, nome e texto
legível; declare retângulos, cores/tiles e área de fala. Faça prova de crop
antes das demais expressões; layout é candidato reversível, não regra global
já aprovada. Diferencie conversa (cena 07), seleção e retratos versus/resultado.
Retângulo pendente da conversa não justifica bloquear todo `versus_*`.

### F. Proveniência, revisão e fim do lote

Complete o lineage com ferramenta/recibo realmente utilizados, hashes dos
originais/prompts/referências e receita reproduzível de extração, escala,
alpha, paleta e registro. Preserve JPEG recebido sem nova compressão; não
invente PNG original ou recibo ausente. Quantização não comprova acabamento.
Não chamar o preview de 30 cores de arte SMS validada; usar status de estudo.

Os 12 princípios precisam planejamento por sequência e evidência observável,
não justificativa retrospectiva de uma imagem parada. Inclinando o corpo você
não demonstrou squash/stretch; mudança de pose não demonstra follow-through.
Deixe o eixo temporal pendente até existir sequência e observação adequada.

Prepare fonte, derivado, prancha 1×/4×, animação normal/lenta e ROM diagnóstica
na mesma rota. Sessão privada, SHA exato, inputs, terminal/reentrada, ambos os
lados, composição e cleanup. Vídeo/frames correspondentes; alvo60/piso58 por
janela e pior frame medidos conforme regras. Não transformar viewer em prova
de dano, balanceamento, áudio ou conversa funcional inexistentes.

Atualize a matriz com arquivos reais, IDs, hashes e pendências; distinga o que
foi desenhado, convertido, observado e aprovado. Fontes boas e experimentos
rejeitados permanecem recuperáveis e com papéis claros. Repare o acidente do
cabeçalho do prompt original sem apagar o briefing. Preserve alterações de
outras tarefas; fontes/receitas próprias revisadas recebem continuidade Git,
sem publicar material privado nem incluir alterações alheias.

Ao concluir, entregue o pacote ao designer coordenador para revisão. Não
assine sua própria aprovação, não declare AAA atingido e não comece outro
personagem antes dessa validação e da decisão do proprietário.
