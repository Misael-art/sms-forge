# Prompt para continuar o OpenBOR para Master System após M6

Você é o coordenador de implementação do OpenBOR para Master System no SMSForge. Continue o projeto existente, preservando o aprendizado, a rastreabilidade dos assets e os registros do M6. Entregue combate responsivo e uma arquitetura de importação que possa evoluir por dados. Trabalhe até fechar o lote corretivo e avance para o próximo ramo seguro autorizado.

## Workspace e objetivo

- Workspace: `/mnt/sdcard/Projects/SMSForge`.
- Consumidor: `/mnt/sdcard/Projects/SMSForge/SMS_projects/openbor_sms_rev1`.
- Ferramentas de importação/emissão: `/mnt/sdcard/Projects/SMSForge/tools/sms_wrapper/openbor2sms`.
- Doador somente leitura: `/mnt/sdcard/Projects/Sgdk Forge/SGDK_projects/OpenBOR_Demo [VER.001] [SGDK 211] [GEN] [GAME] [BEAT_EM_UP]`.
- Produto imediato: recorte GAL/TOWN1, Ax jogador e Long inimigo, profundidade, movimento, ataque, dano, queda, recuperação, morte, cenário/scroll e HUD. **Este beat em up inclui cenário**; não herde a exclusão de cenários do MUGEN.
- Meta regional: loop NTSC próximo da frequência nominal e PAL quando medido, comandos responsivos, ação legível, qualidade visual/sonora compatível com o hardware. Meça fluidez, cadência e integridade da arte como eixos próprios.

Comece com `[Contexto SMS Carregado]`. Leia AGENTS aplicáveis e `/home/misael/.codex/RTK.md`. Prefixe comandos shell com `rtk`. Leia a arquitetura central, SMS_GLOBAL e os workflows atuais; não sobrescreva `.agent` local.

## Leituras obrigatórias e baseline

Leia nesta ordem no consumidor: `doc/10-memory-bank.md`, `11-gdd.md`, `13-spec-cenas.md`, `00-diretrizes-agente.md`, `.mddev/project.json`, `15-tdd.md`, escopo `doc/artifacts/o3_combat_scope_20261016.json`, registro de artefatos e evidência M6. Confronte divergências com os arquivos reais.

Leia o parecer `/mnt/sdcard/Projects/SMSForge/doc/planejamento/openbor_sms/07-parecer-m6-20261018.md`, o registro 09 dessa pasta e os planos 01/02. Os M1–M8 do escopo O3 são subtarefas de combate; O0–O8 do plano geral incluem mundo, objetos, menus e generalização.

Baseline inspecionado:

```text
commit: da86de303bca969a393032d270c9d245d4055180
ROM: SMS_projects/openbor_sms_rev1/out/rom/openbor_sms_rev1.sms
bytes: 131072
sha256: 76cdbee3f10a58a07199b9012ff6dbe53df372d7532d6a8aa324089824425e73
```

Reconfira HEAD, status, ROM, manifests, toolchain e saúde dos caminhos. Se outro agente avançou, preserve o baseline histórico e avalie o delta atual antes de editar. Não descarte WIP alheio, não reconstrua sobre evidências sem congelar seus vínculos. Não acessar o projeto MUGEN com EIO como dependência; um diretório novo não repara o cartão. Não faça commit/push sem autorização vigente.

## O que já funciona e deve ser preservado

- Front-end OpenBOR, PAK/IR e emissor SMS já existem; os 87 testes host passaram na revisão de 18/10.
- D13 corrigiu `guard` que nunca diminuía; o contador deve avançar no relógio declarado mesmo se a pose estiver aguardando upload. Há oito hits 50→0 e DEAD no histórico.
- Input causal, perseguição em z, pulo e knockdown têm traços reais. Reaproveite-os como baseline sem atribuí-los à ROM modificada.
- MRP histórico: 59,48/59,66/59,78 NTSC. MWF: 3.000 quadros selados, vovf zero. São recortes medidos, não autorização para extrapolar carga/PAL/game feel.
- Poses são 80×96, TALL 8×16; slots duplos, BG232 e HUD424 no plano O3. Confirme o plano atual e os registradores na nova ROM.
- A pose Ax `a105_right` no still [92,68] passou estruturalmente e, na revisão, em comparação indexada dos 959 pixels opacos. Não há prova global de zero-glitch.

## Lote A Corrigir identidade e documentação sem parar no relatório

Faça uma correção curta e rastreada:

1. O índice M6 afirma whiff dz41, mas aponta apenas para `depth_f41e8c8c089042be85fd1c9643900043.json`, que mostra dz6 e dano. O negativo está em `depth_0b271ce0621a4adc914ab5c4d37be07b.json`, fora do selo. Confira ROM/journal/origem dos dois e crie um índice sucessor honesto; preserve os originais. Refaça só o que não puder ser qualificado.
2. Atualize a spec de cena para o layout/budget O3; retenha O2 como histórico. Corrija a tabela de paletas: BG índice zero visível, sprites índice zero transparente. Confirme os demais números nos headers/planos, sem transformar throughput deste build em lei de hardware.
3. Remova contradições de estado operacional: commit pendente, IA 1,5× vs Q8 320/427 e caminhada lenta sem distinguir posição de animação. Status e limites permanecem por ROM.
4. Estabeleça bundle sucessor com ROM ou referência imutável, tool/context hashes, manifests inicial/final, mídia e cleanup verificável. Não invente comprovante histórico de fechamento ausente.

Não encerre o trabalho depois dessa conciliação: o objetivo principal é corrigir o combate.

## Lote B Corrigir a semântica temporal e de apresentação

Reproduza os seguintes achados em testes focados e, quando alcançáveis, no emulador. Corrija com a menor arquitetura coerente:

### Contato e pose apresentada

`src/main.c`: `actor_advance` verifica readiness antes de `fsm_tick`, que pode avançar frame; `resolve_hits` usa o índice lógico antes da apresentação da pose nova. Trace por fronteira input, estado, facing, índice lógico/fonte, pose desejada/apresentada, slot, progresso de cópia, caixa ativa, hitstop, guard, HP e frame VDP.

Defina quando uma pose e sua caixa entram em vigor e em qual framebuffer aparecem, considerando a latência normal da SAT. Não permitir golpe de pose futura ou estado abandonado. Não corrigir isso simplesmente atrasando ainda mais o golpe sem tratar a transferência.

### Relógio da animação

O timer N atual pode consumir N+1 chamadas elegíveis. Crie casos com poses residentes e sem hitstop para separar conversão da fonte, duração de pose, primeira chamada, espera de I/O e recuperação. Confronte a referência OpenBOR pinada e as convenções de delay; não assuma que somar delays descreve o runtime. Implemente a política escolhida e registre adaptações. Validar frame inicial, todas as fronteiras e terminal, sem hits duplicados.

### Hit aéreo e continuidade

O pulo alcança 55; TOSS alcança 46. A busca atual chega ao índice36/altura2 para vítima acima46, causando salto de posição. Defina arco/offset ou integração de trajetória que preserve a continuidade exigida pela adaptação, incluindo juggle, morte e pouso.

Teste alturas 0/1/46/47/55 e estados subida/ápice/descida; só declare cobertura de gameplay dos casos que a caixa realmente alcança. Altura200 da entrada exige caso separado se colisão for alcançável. Teste de função não vira demonstração de um contato nativo.

### Upload concluído de estado antigo

`stream_update` publica `up_want` concluído mesmo quando o pedido mudou. Use geração/identidade do pedido e uma política explícita de descarte/reuso. A publicação deve corresponder ao estado atual ou a uma transição legal declarada. Teste hit, morte e troca de facing no meio de cópia/prefetch; a cópia completa nunca deve ressuscitar pose abandonada.

## Lote C Resolver o custo do uploader e o serviço aos dois atores

O baseline envia aproximadamente128 B/quadro; uma pose de1856 B pede ao menos15 quadros sem reuso. A memória declara ataque completo aproximadamente60q, mas o vídeo dedicado termina após60quadros ainda em ATTACK/frame4: meça até o retorno elegível ao controle antes de repetir esse número como duração completa. O alvo nominal declarado soma21q e também depende da correção do timer. Prioridade absoluta do jogador permite starvation do inimigo.

Instrumente com orçamento de RAM e `volatile __at` auditados: bytes úteis/transferidos, custo de preparação/cópia/commit, pose-age, espera da FSM e maior intervalo sem progresso por ator. Diferencie CPU, VBlank, atualização de SAT/PNT/HUD e serviço efetivo. Use contador/serial suficiente para excluir voltas ambíguas; não interpretar `vline_min=202` como duração máxima ou folga livre de todo frame.

Compare candidatos em sequência com a mesma cena, sem múltiplos escritores:

1. Reuso de tiles/pares e cache residente por identidade, com metadados que mapeiem células a slots já válidos.
2. Deltas por transição, pré-carga de estados críticos e capacidade de invalidar/cancelar sem perder progresso útil.
3. Cópia especializada e redução de overhead C/banco, medidos contra o caminho atual.
4. Escalonamento que dê prazo/idade e serviço limitado aos dois atores; medir se a divisão continua atendendo os deadlines visuais.

Para cada candidato, registre seu SHA próprio e mantenha carga, input e configuração comparáveis, com as mesmas fontes exceto o delta declarado. Meça RAM/stack, VRAM, ROM/bancos, bytes e custo por transição, input→primeira pose→contato→recuperação, cadência de ambos os atores, derrame e defeitos visuais. Não prometa sucesso de cache/assembly antes da prova. Não usar gravação por stepping para medir throughput em tempo real.

Escolha o candidato pelo ganho medido e preserve rollback. O alvo é aproximar o combate do contrato de timing sem mudar física por congestionamento de render. Não basta liberar a FSM e deixar a imagem atrasada. Se houver limite de representação, compare alternativas mensuradas e documente a decisão de produto necessária; não reduzir escala, esconder inimigo ou remover poses essenciais silenciosamente.

## Lote D Fechar transições e perdas visuais

Antes dos cortes, o pior par chega a17sprites/linha e Long chega a9 sozinho. A política atual remove sempre as mesmas células. Compare legibilidade e máscaras em poses idle, ataque, pain, queda, morte e em ambos os facings/profundidades. Investigue contabilização antes da visibilidade horizontal e ordenação por profundidade, sem tratar oclusão correta como falha.

Mantenha dois resultados separados: legalidade técnica da SAT/composição e integridade da arte em relação à fonte. Cortes previstos por um renderer não viram qualidade aprovada.

Para `audit_render_glitch`, estabeleça um oráculo independente validado, com known-good/known-bad, pixels residuais, tiles de outro slot, pose errada e omissão permanente. Pode usar cena diagnóstica controlada para calibrar e snapshots SAT/VRAM/CRAM como cross-check; a aceitação continua no cenário TOWN1 real com scroll e HUD. Se precisar ampliar gate, implemente no wrapper com self-check e positivos/negativos; não enfraqueça o gate atual ou copie capturas como expected para aprovar a si mesmas.

Cobertura mínima: trocas completas A/B, transições atingidas durante upload, facing, oclusões, bordas da tela, deslocamento de câmera nos dois sentidos e dois atores alterando pose. Compare arte/paleta/pivô e revisão no tamanho nativo. Se o oráculo continuar bloqueado, declare a lacuna e prossiga nos ramos seguros sem afirmar ausência global de glitches.

## Lote E Integrar os consumidores de evidência e adicionar áudio

O reconciliador atual consulta `out/evidence/evidence.json` e `fps.json`; o novo bundle M6 não é consumido automaticamente. Faça um adapter/consumer derivado com schema, ROM SHA, sessões, artefatos, cobertura e escopo explícitos. Aceitação precisa de testes negativos para ROM trocada, evidência stale, sessão divergente, casos ausentes e mídia inválida. Não popular booleanos manualmente nem remover falhas para passar.

Adicione M7 interno de O3: SFX mínimos de ataque, impacto e queda, com fonte/manifests/hash rastreáveis, autoria/adaptação PSG explícita, prioridades/canais e restauração coerentes. Áudio do PAK não é PSG pronto. Confirme API no header PSGlib, banking/ISR, pausa/restart e concorrência com stream.

Capture áudio isolado, prove duração/sinal/eventos e revise a correspondência com a ação. Sinal não prova fidelidade. Refaça budget com áudio ativo e a pior carga de combate real; não use o MWF sem PSG para aprovar o mix final. Música e demais sons entram conforme GDD/contrato, sem troca silenciosa de escopo.

## QA com especialistas nativos

Use até três workers, com tarefas concretas, revisores distintos do produtor e writes exclusivos. Divisão útil: importação/tempo; Z80/VDP; QA/visual/áudio. Não deixar dois agentes compilarem ou alterarem o consumidor simultaneamente. O coordenador integra e promove.

Antes de QA, leia os workflows centrais `emulator-isolated-session.md` e `subagent-emulator-qa.md`, SMS_GLOBAL §§93–100. Congele a ROM. Prepare pedidos V2 com `session_qa.py`, contexto legível, `independent` ou `chained` correto e precondições reais do probe. Dispare os workers pela ferramenta nativa, um ID e uma sessão privada por worker. `collect` não julga qualidade: cada worker inspeciona as mídias/probes e entrega cobertura, defeitos, limites e cleanup; valide com `audit_subagent_session.py` e coteje recibos nativos.

Emulicious é a rota de produção/aceitação. BlastEm complementa com diagnóstico Z80/VDP/mapper, dumps atuais e vínculo ao SHA da candidata. Não inferir suporte GDB Z80 de testes Z2 do M68K. Não usar foco, teclado do dono ou instância por título; não matar processos alheios. Medições de desempenho em tempo real usam reserva cooperativa; stepping prova sequência, não taxa.

Matriz de regressão:

- Pressionar/segurar/soltar ataque; reataque; início, ativo, recuperação e interrupção; guard expira e um golpe não dá múltiplos hits indevidos.
- Hit/whiff em x, z e altitude; dz14/15/16, sinais±, ambos os facings e vítima móvel; registrar se o input de preparação modifica a precondição.
- Pulo, hit aéreo, juggle, queda, pouso, RISE, morte e HP/HUD; limites de altura e sem publicação de pose obsoleta.
- IA recebe serviço de upload e continua legível durante o ataque do jogador; ambos os atores sob carga, sem depender de starvation para produzir knockdown.
- Câmera/scroll/PNT/HUD com atualizações simultâneas; limites da SAT, RAM/corredor/stack, VRAM por registradores atuais e upload no pior frame.
- FPS médio regional e pacing da ação; observação de combate em tempo real; PAL só aprovado com ROM/timing/teste regional próprios.
- SFX/mix/pausa/restart sob carga e ausência de interferência de input/áudio do host.

Faça testes focados por delta e os gates integrais uma vez no fechamento. Comando host conhecido, a partir do workspace:

```sh
rtk proxy env PYTHONPATH=tools/sms_wrapper/openbor2sms python3 -m unittest discover -s tools/sms_wrapper/openbor2sms/tests -q
```

Os 87 testes atuais não provam a FSM C em execução. Adicione os casos causais necessários e confira `--help`/self-check de cada ferramenta antes de confiar na medição. Não atribua a um PASS mais cobertura que a ferramenta mede.

## Continuidade para engine madura

Após resolver o lote corretivo e M7/M8 de O3, avance no plano geral:

- O4: eventos/câmera/terreno, groups/wait/spawn/lock/reset, fila fonte→IR→owner→entidade; retry idempotente e pool cheio. TEXT/ITEM/OBSTACLE não contam como inimigos.
- O5: owners de objetos, pickups/equipamento quando requeridos, obstáculos, lifecycle e escala. Antecipe owner bloqueante de O5 se a fila real exigir; não pule evento para declarar O4 completo.
- O6: fluxo e telas previstos, options/seleção/pause/continue/resultados e áudio; rota começo→combate→clear/derrota→continue/restart→menu no mesmo SHA.
- O7/O8: segundo piloto e 2P conforme contrato, perfis por dados e conversão limpa reproduzível. Nenhum deles herda orçamento do recorte1P.

Mantenha matriz por capacidade: parseada, gerada, consumida, observada, budget validado; tags exact/adapted/blocked com fonte e limites. Ax/Long hardcoded não significam engine OpenBOR genérica; generalize por necessidade comprovada. Fonte desconhecida/script essencial não vira noop.

## Entrega e aprendizado

Atualize memory bank, GDD se houver decisão de escopo, spec de cena, TDD, registro único de artefatos, evidência e compatibilidade. Ferramentas/build ficam no wrapper; assets têm proveniência e um caminho canônico por papel. Preserve tentativas em filhos versionados, com parent e registro; mantenha uma única raiz de autoridade e não sobrescreva a fonte.

Entregue comparação antes/depois por ROM: timing de cada ação, erro visual, serviço por ator, bytes/ciclos, RAM/VRAM/ROM, carga com PSG, NTSC/PAL e limites. Gate bloqueado ou qualidade não aprovada permanece explícito. Não encerrar com apenas diagnóstico quando houver correção causal segura.

Promova lições somente com reprodução, correção e teste/medidor: candidato JSON, doutrina/skill pertinente, memória e limites. Priorize invulnerabilidade que nunca expira, tempo lógico versus pose apresentada, publicação de pedido antigo e trajetória fora do envelope. Não canonize 128 B/q como limite do SMS nem supostos defeitos ainda não reproduzidos como fatos de hardware.

Relato durante o trabalho: **Resultado / Bloqueio / Próxima ação**. Relato final: o que mudou, por quê, qual ROM foi vista executando, quais casos passaram, quais limites permanecem e onde estão as evidências. “Se não foi visto rodando no emulador, não existe” continua valendo para as correções.
