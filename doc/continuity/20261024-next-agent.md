# Próximo agente — retomar o motor SMS sem o host anterior

Abra este repositório no Codex do novo host. Leia primeiro
`doc/continuity/20261024-start-here.md`; execute o bootstrap e o doctor antes
de iniciar produção. O contexto canônico está no Git, não no histórico do chat
ou em um banco pessoal de memória.

Copie este pedido para a nova tarefa:

```text
[Contexto SMS Carregado]
Retome o desenvolvimento do SMSForge/luta_mugem_rev2 pelo pacote de continuidade
de 24/10/2026. Leia AGENTS.md, RTK portátil, o guia start-here, os documentos
autoritativos do projeto e o diagnóstico Mugenesis→rev2. Execute o prompt
doc/curation/2026-10-24_prompt_concluir_engine_sms.md e acompanhe os 55 IDs do
backlog JSON. Antes de alterar o motor, confira o ambiente e os hashes; preserve
as baselines e o histórico. Esta tarefa autoriza implementar o escopo vigente
na fábrica e no consumidor, testar e registrar os lotes. Não autoriza cortar
movimentos, reautorar arte, reduzir escala/escopo ou aprovar AAA por conta própria.

Comece por ID01, R01/R02/R03/R05/R06/R09: identidade da build e apresentação
completa dentro do prazo e VBlank, sem atacar a fonte artística para esconder
o defeito. Separe fato, hipótese e decisão humana. As capturas e selos antigos
não qualificam o novo ambiente. Faça uma interação completa em ROM antes de
ampliar conteúdo, continue pelos ramos causais seguros e não encerre após
apenas um relatório ou milestone. Atualize memória e evidências por SHA.
```

Pontos de atenção: common1 ausente; FSM de papéis não é CNS completo; matcher
de especial sem entidade não implementa projétil; payload/facing e contato da
pose residente precisam ser qualificados; fundo sólido é escopo; P1 de sprites
é compartilhada; os 7 eixos e época visual delivery devem convergir na mesma
ROM. Primeiro feche runtime e qualidade mensuráveis; ambição AAA não é selo.

## 2026-10-28 — interrupção de ataque, composição ainda reprovada

A candidata `out/candidates/20261027_attack_interrupt_v2/`, ROM SHA
`7523bd0c3976263b6187681a536ea29f9faedaa72b24b94027a671e907749054`,
invalida no schema 7 o ataque da vítima atingida e preserva a maior pausa em
troca não letal. A QA nativa observou dano 112 mas reprovou a sobreposição
visual; uma sessão adicional com input natural observou P1 atingido durante
ataque, `hit_done` 0→1 e recover. O framebuffer próximo ao evento não permite
identificar os dois corpos; o caso espelhado e o efeito contrafactual de caixas
continuam sem prova. KO simultâneo continua aberto. Detalhes e evidências no
memory bank do consumidor.

O ritmo NTSC medido foi 21,57/24,48 atualizações/s; o selo de pior quadro
registrou 1759 derrames, mínimo 2, com preparação em stepping e sem HUD/FX/
música. São reprovações, não orçamento de entrega. O host passou 292 testes
rev2 (150 deselecionados), selftest 135/135 e 75 medidores. Nenhum ID dos 55
foi fechado. Próximo blocker: distinguir o custo e a legalidade da composição
real da latência de publicação e integrar uma alternativa que preserve ambos
os lutadores e o contato, com carga representativa.

Recuperação local verificada em 24167 arquivos:
`.runtime/backups/luta_mugem_rev2-runtime-20261028-attack-interrupt.tar.gz`,
SHA `6cbe8fec90572d8adb9537dcaa979a6204f9a0b375e6bfb8bf83963c0b18d891`,
com manifesto `.json` homônimo. A cópia compartilha o disco do owner e não
constitui proteção externa.

## 2026-10-27 — guarda e acerto na mesma candidata

A ROM `7f530db3…` agora tem os dois eventos em stepping, sem rebuild.
Sessão `b615f99a…`: HP de Ryu, 112 de dano, recover 21 depois do pause
16. Sessão `ff3ce3ecc6da4ff3af5ca0786fd6d0c8`: a mesma pose 34 contra
P2 agachado (pose 69), kind 1, vidas 1000/1000, recover 21, impulso de
guarda de 5 px. O botão 1 foi segurado seis frames de lógica só depois
do beat 3. A duração não separa guarda e acerto neste HitDef; kind e
vida separam. Os dois framebuffers mostram dois lutadores no fundo
preto. Não houve troca de lado, HUD nem prazo. R06 e os 55 IDs seguem
abertos. Detalhe no memory bank.

O próximo ramo é a composição real das poses já vistas (34 com 60 e 34
com 69) e o prazo com HUD e áudio como carga, ainda nesta linha de
candidata. Não reconstruir `20261027_present_hit` nem a nominal.

## 2026-10-27 — recover medido; guarda desta ROM ainda aberta

A candidata `7f530db3357bffd170286e332bdfd55e4bd0504d08ac28382859c583831d79dc`
(`out/candidates/20261027_hit_recover/`) aplica o schema 7: pause do
HitDef e recover do defensor depois do pause. Na sessão privada
`b615f99a3d864c8d9aaf9fad72fa10b2`, stepping, o HP de Ryu (atacante P1,
pose 34) tirou 112 de P2 (vida 1000→888) com a pose submetida igual à
lógica. Pause 16/16 e recover 21; a soma dos degraus do log é 21. P2
ignorou o agachar da IA até o recover chegar a 0 e P1 voltou a andar a
3 px por frame de lógica. O framebuffer `hit.png` mostra os dois
lutadores no fundo preto. Não houve guarda, troca de lado, HUD nem
medição de prazo. O tick do trace é 52 e o `probe_frame` da amostra é
53: topo do laço seguinte, pause ainda cheio. R06 e os 55 IDs seguem
abertos. A nominal não foi sobrescrita. Detalhe no memory bank.

Esse parágrafo era o plano seguinte. A sessão `ff3ce3ec…`, acima,
executou a guarda. Não reconstruir `20261027_present_hit` nem regenerar
o corte de facing.

## 2026-10-27 — acerto pela pose submetida

O caminho de produção agora resolve guarda e dano pela pose submetida na
sombra da SAT do mesmo frame (`LUTA_PRESENT_HIT`). A candidata
`5c5c6144ffd5b76f6e0f53bbcdf29785832238a0d3aeb0a51f6109ee99574991` registrou,
em stepping, uma guarda coerente na pose 34 e um acerto de 76 em P1 com as
poses 36/77 iguais no cursor, na residência, na submissão e na apresentação.
A guarda foi recapturada com o framebuffer no mesmo tick 84
(`guard.png`, sessão `656ccc85…`). Isso não fecha R06: o acerto de 76 não
tem o framebuffer do próprio tick, e seguem abertos scanline, prazo e
hitstun. ID01 e os 55 IDs seguem abertos. A nominal não foi sobrescrita.
Detalhe e sessão no memory bank do consumidor.

## 2026-10-27 — carga PSG diagnóstica, estado mais recente

`LUTA_DIAG_PSG=1` é opção diagnóstica, zero por padrão; acerto e guarda
acionam dois streams autorais genéricos, sem reivindicar identidade MUGEN ou
áudio final. A fonte é
`2c04013962615edc4dcfc1a51cff54822eb0ec12b13c34dbdfa1bcdbc6c71739`;
a ROM com PSG é `a89a38972e1b65ef9395db7e51118abd607f27959190c7f36e546f6356560dfb`
e o controle da mesma fonte é
`70c03939306d0fe1d624d08e08734b9cb2d2b2b11251b2e2f56932613684de4f`.
Em sessão privada, dois acertos e uma guarda produziram três pedidos à PSGlib
e sinal isolado; o controle repetiu os totais de combate e ficou silencioso.
As janelas sem eventos sonoros foram 26,58/25,72 e 26,70/25,70 atualizações/s,
respectivamente: ambas reprovam. Com P1 mantendo direita, o selo de 3000
iterações registrou 863 derrames, mínimo 7, e ao menos um SFX dentro da janela;
sem HUD/FX/música, não aprova prazo. Ver memory bank para sessão, falha do primeiro
roteiro, colisão intermediária de sondas e limites. Música, escuta e sincronia
áudio/imagem continuam abertas; nenhum dos 55 IDs foi encerrado.
Código `579bf46`; 278 testes `rev2` passaram. A cópia local
`.runtime/backups/luta_mugem_rev2-runtime-20261027-diag-psg.tar.gz` tem SHA
`eb52e60c63a2d304badb9540becc8416181bee706c5a764e29d2bcac200f761a` e
verificou 22776 arquivos com o manifesto associado; permanece no mesmo disco
do owner e não substitui proteção externa.

O próximo blocker permanece R06: medir contato versus pose efetivamente
submetida/apresentada em fronteiras do golpe antes de mudar a política de
colisão. Continue também HUD/FX/música como carga representativa e prazo real.

## 2026-10-27 — candidato híbrido

A fonte `dd1a7cb532fe62c6dd0e0e244f87c2e84ddb407e8c59bd90ea7aefc5fcb86cf6`
inclui as opções `LUTA_BG_ACTOR` e `LUTA_BG_CAMERA` apenas para diagnóstico;
ambas são zero por padrão. Câmera e ator BG não foram aprovados: o limite de
scroll deixa uma coluna mascarada, há conflitos de enquadramento no modelo,
a troca de facing não foi alcançada e não há HUD/FX/PSG. A variante com câmera
`3be79abe6c5edd3d44616b53c357999d25591756492db328522edb873fc6af4a`
preservou duas poses em uma captura de borda e teve pico SAT 4 por linha nas
30 fronteiras observadas; reprovou FPS 26,05/24,20 e pior quadro com 1759
derrames. O mapa de VRAM passou no escopo registrado. A build da mesma fonte
com opções desligadas é `8968b847cdb825ba346ae9a5687838c58a9b17bdf8d2b11e7d0741df4b11d309`;
ataque foi observado, FPS 26,70/25,69 reprovou. Sessões e limites completos
constam no memory bank do consumidor. Os 55 IDs continuam abertos.
Código `c64a6fe`; 275 testes `rev2` passaram no host. A cópia local
`.runtime/backups/luta_mugem_rev2-runtime-20261027-bg-hybrid.tar.gz` tem SHA
`b75f22cf9027acfa20d64bf8601de4cc4fde293876920a2263432fc882ca3f39` e
verificou 22537 arquivos pelo manifesto associado; está no mesmo disco do
owner e não substitui backup externo.

Próximo ramo seguro: integrar uma carga PSG diagnóstica rastreável aos eventos
reais de combate, sem promovê-la a identidade sonora, e medir na mesma ROM.
Continuam indispensáveis consistência contato/apresentação, facing BG,
prazo sob carga completa e decisão humana para eventual mudança de viewport.

## 2026-10-27 — avaliação e melhoria da capacidade produtiva

Lote de fábrica `f5d3dcb777554b7bceb309abe45e1bb98856ecb0` na branch
`codex/host-bootstrap-continuity-20261024` (base `651284c`); parecer em `doc/curation/2026-10-27_production_capability_review.md`.
Maestria agora exige custódia de artefatos; 32 claims de texto livre foram
preservados em `legacy_claim` e reconciliados para `mapped` até reindexação.
Não significa refutação das provas históricas. Pipeline incorpora slice e
checkpoint conjunto; skills orientam design, câmera, teste humano e áudio PSG.
Correção de compatibilidade Pillow no gate de poses, agora coberto no selftest.
Validação no host: 135/135 selftests, 75/75 medidores e gates de maestria,
documentação, aprendizado e hardware passaram. Consultar
`doc/curation/evidence/2026-10-27_production_capability/validation.json`.
Nenhuma ROM/asset foi alterada nem gameplay/qualidade de jogo requalificados.
Próximo owner continua `luta_mugem_rev2`: ID01, R01/R02/R03/R05/R06/R09,
R10/IN05 no backlog existente. Reindexar provas históricas separadamente de
provar a build atual. Não ampliar elenco ou criar engine paralela.

## 2026-10-27 — lote de identidade, cache e temporalidade

Código nos commits `ca921dd` e `792cef6` da mesma branch. O manifesto nominal
e a ROM histórica `087df676…` foram preservados; `build_record.json` nominal
continua de outro SHA, portanto ID01 e os 55 IDs seguem abertos. A receita
versionada de diagnóstico é
`SMS_projects/luta_mugem_rev2/.mddev/candidates/pose_budget_pair_20261027.json`;
os bancos gerados vêm do pacote de recuperação de 24/10, não do Git. O recibo
do candidato inclui os hashes de entradas e ferramenta. A ROM do lote é
`20d0c6e0efdfaeffcc9ad11b0cfe729d8edf3c02df8215998e62411c8f222f99`;
seu fonte SHA `2a27905e…` está no Git e no snapshot do candidato.

No Emulicious privado, a ROM aceitou movimento e botão 1, com vida de P2
1000→888; isso não qualifica guarda, som, contato ou gameplay completo. A
atração reprovou FPS (23,48/20,64 atualizações/s) e o selo de VBlank
(`vline_min=13`, `vovf_delta=1719` em 3000 iterações; 21 vieram de stepping
de boot e não há HUD/FX/PSG). Os bundles foram checados e as sessões fechadas.
PNT/VRAM/SAT foram inspecionadas em cinco fronteiras da ROM anterior `d8de0ad…`;
os 93 descritores do candidato `20d0c6e…` têm duas faces dentro dos bancos e
186 trechos coincidem com a ROM. Esses fatos não aprovam a composição ou a
seleção da face em runtime. Veja `SMS_projects/luta_mugem_rev2/doc/10-memory-bank.md`
para cada sessão, hipótese descartada e limites.

O host passou 260 testes rev2 (150 deselecionados), 135 selftests e 75
ferramentas de medição. Doc sync, hardware, corredor e aprendizado passaram;
correções Python 3.11/Pillow e o reparo dos hashes das rotas foram registrados
após as falhas. O contrato `pose_budget` passou como planejamento, sem aprovar
arte nem entrega. ROMs e mídias do lote estão no `out` do owner e uma cópia
local fica em `.runtime/backups/luta_mugem_rev2-runtime-20261027-engine-lot.tar.gz`
(SHA `7a745b7e5e843381cab4b91c7264cd8c5b991e36ba8fc889e86c0c8581fc5cb3`),
com manifesto `.runtime/backups/luta_mugem_rev2-runtime-20261027-engine-lot.json`.
O `recovery_bundle.py` verificou 5693 arquivos; ambas as cópias dependem do
mesmo disco.
A release de 24/10 protege os insumos anteriores, não a mídia nova. Não
publique assets ou evidência privada no repositório público.

Próximo ramo: usar as faces já empacotadas por pose, com chave de cache que
inclua orientação e metadados correspondentes; validar offsets e limites antes
do upload, reproduzir a troca real por input, registrar imagem/SAT/estado e
medir o custo. Continuam sem solução a coerência entre contato e pose
apresentada, limite por scanline, starvation, VBlank sob carga real e AIR
N+1 em ROM. Não chame uma pose residente ou uma captura isolada de entrega.

## 2026-10-27 — complemento: face, mapper e receita atual

O diagnóstico seguinte encontrou alias de bancos na imagem de 28 bancos;
em BlastEm, a cópia preenchida para 32 bancos corrigiu os 14 spans observados.
O manifesto atual seleciona o pacote `pose_budget_facing_20261027`, exigido
pelo GDD, e `-pp`. O gerador declara o contrato de faces e o runtime recusa
headers antigos sem ele. O candidato do manifesto atual tem ROM SHA
`ad0e148c3b1f12a2981f17b02a8d9fa9f42642137e734d9bb9bcc0422e6a3eea`;
travessia e ataque foram novamente observados em sessões privadas após a build.
O selo anterior da mesma ROM reprovou VBlank (`vline_min=7`, `vovf_delta=1749`)
e FPS (22,87/19,88); não é evidência fresca para um rebuild posterior. O
histórico de 49 bancos e a ROM nominal anterior não foram sobrescritos.

A build final isolada é `out/candidates/20261027_integrated_final/`; seu
recibo vincula fonte, dados e builder atuais, com a mesma SHA acima. A
regeneração repetida com o gerador atual preservou os bancos e headers;
somente os caminhos de saída mudaram no manifesto. Emulicious privado repetiu
golpe (vida P2 1000→888, sessão `ea1c3a68547f4a4995695fb6e6f60c28`) e
travessia (`3d3f42be0ec64ad68ae3905a7be101cd`), com bundles verificados e
cleanup. No BlastEm, a SAT viva do mesmo binário excedeu 8 entradas por linha
em 13 das 30 fronteiras amostradas no roteiro de ataque; consulte
`out/evidence/20261027_attack_sat/`. A suíte rev2 passou 265 testes com 150
deselecionados; selftest 135/135, 75 ferramentas de medição, sincronismo
documental, constantes, aprendizado e corredor passaram. O contrato do GDD
passou apenas como planejamento. Esses resultados não aprovam o gameplay.
Os dados e evidências deste lote foram empacotados e verificados em
`.runtime/backups/luta_mugem_rev2-runtime-20261027-facing-mapper.tar.gz`
(SHA `e9cebc77881f34362ba563e060fe68ec9dfcde2548c9b319d6dc1d6716ae1c12`,
10392 arquivos); o manifesto tem o mesmo nome com extensão `.json`. Essa
cópia e o `out` original residem no mesmo disco: não há backup externo novo.

Se `SMS_projects/luta_mugem_rev2/out/generated/pose_budget_facing_20261027`
não existir, regenere-o uma única vez, no checkout e ambiente oficiais, sem
apagar nem substituir dados existentes:

```sh
rtk proxy tools/sms_wrapper/run_host.sh python -m mugen2sms.generators.versus_scene_cut \
  --p1-source SMS_projects/luta_mugem_rev2/data/source_mugen/ryu/ryu.zip \
  --p1-config SMS_projects/luta_mugem_rev2/doc/continuity/config/ryu_pose_budget.json \
  --p2-source SMS_projects/luta_mugem_rev2/data/source_mugen/ken/Ken_Majik_.zip \
  --p2-config SMS_projects/luta_mugem_rev2/doc/continuity/config/ken_pose_budget.json \
  --out SMS_projects/luta_mugem_rev2/out/generated/pose_budget_facing_20261027
```

Os bancos esperados têm SHA `ec22ad12f88b8fa720e7bbcf9cb63f3072f359af019f53e80d924f7348375423`,
o header `b63069e7cd28ebb053a4ad31fe1011591cf8094eb56e838d315864cb8c2de0c8`
e `fight_runtime_data.h` `7caabed2f1e4c11a98614c5f99e81634f4637b54aca4ad2a938b9ac6ac9590d1`.
Uma nova ferramenta, data SDSC, fonte ou configuração pode mudar o resultado;
registre hashes e repita build/QA, sem promover evidência histórica. O
próximo problema dominante é publicar poses/contato com deadline e composição
legal sob carga representativa; essa correção não autorizou cortar golpes nem
declara qualidade de jogo.

## 2026-10-27 — cursor de IA e limite do watchpoint

O candidato `out/candidates/20261027_ai_clock/` usa um cursor sequencial em
lugar das divisões de 16 bits por tick da IA. A consulta pura permanece para
acesso aleatório e o teste C cobriu todas as fases nas duas faces e no wrap.
ROM `cac3d8fba8634fb5db7a35f5b4f7799169972c5ce607ad35dc280fbd67878985`;
o movimento e um ataque foram vistos em Emulicious privado. O FPS em duas
janelas foi 23,35/20,63 e o selo de 3000 iterações derramou (min 7, delta
1749), sem carga completa e com stepping inicial: nem deadline nem entrega
foram pagos. Veja o memory bank para sessões, baseline e cobertura. A suíte
rev2 passou 266 testes, 150 foram deselecionados.

A sequência de ataque anterior ganhou snapshots VDP unitários na sessão
`blastem-sms-bb9133dc24964708a94c8795ea33467a`: a submissão coincidia com
o pedido na fronteira 899 e o dano já aparecia na 900. Os watchpoints sobre
life/hit não dispararam apesar da mudança nos dumps; não alegar timing exato
de contato ou funcionamento da sonda para essas instruções. Continuar pela
identidade da pose efetivamente comprometida, colisão e composição, com
instrumentação que associe causa e frame; preservar também a reprovação de
scanline e o custo de VBlank. A cópia local deste lote foi verificada em
`.runtime/backups/luta_mugem_rev2-runtime-20261027-ai-clock.tar.gz` (SHA
`e70ac6112719abf7a1050e4817b25c09f4b9741880cf6286f8b59bbbad01c68f`,
11562 arquivos); o manifesto correspondente termina em `.json`. As duas
cópias continuam no mesmo disco, sem backup externo novo.

## 2026-10-27 — pusher no chão, ainda candidato

Na baseline `cac3d8fb…`, P1 atravessou P2 enquanto ambos estavam no chão;
o caso foi reproduzido em RAM de BlastEm com o mesmo input. A candidata
`out/candidates/20261027_ground_push/`, ROM
`b5c83830392fae1bc1bc85784101e4126a7b74195a8d67bcc263ee6d6cfbc5b0`, usa
as larguras frontais Q8.8 emitidas para os dois atores e preservou sua ordem
nas fronteiras observadas nos dois emuladores, inclusive junto à borda. Um
golpe ainda reduziu a vida de P2 de 1000 para 888. As sessões e limites estão
no memory bank: `Width`/`PlayerPush`, costas e push aéreo permanecem fora da
aproximação; não promovê-la como equivalência MUGEN completa.

A SAT viva da candidata excedeu 8 sprites/linha em 8/30 fronteiras do ataque
e os quadros de aproximação mostram sobreposição. FPS NTSC de duas janelas
foi 26,48/25,24; o pior quadro selado derramou (mínimo 7, delta 1749; stepping
inicial, sem HUD/FX/PSG). Os 55 IDs continuam abertos. Próximo trabalho deve
atacar composição e orçamento sem esconder partes ou confundir uma largura
de colisão válida com integridade visual. A suíte rev2 passou 267 testes,
com 150 deselecionados.
A cópia local do runtime e das evidências foi verificada em
`.runtime/backups/luta_mugem_rev2-runtime-20261027-ground-push.tar.gz`
(SHA `90b4327fefff5a9b95ec3f0564dd088c7148efda78ad14d805d218fd3096dcd5`,
13792 arquivos; manifesto com o mesmo nome e extensão `.json`). Tanto a cópia
quanto o owner estão no mesmo disco; não há backup externo novo.

## 2026-10-27 — quotas e medição por ator

Em candidatos isolados, quotas de 1/2/4/8 pares por lado produziram
respectivamente 21/2019/2787/1749 derrames no selo de 3000 iterações, todos
reprovados, com 25–26 iterações iniciais em stepping e sem carga completa.
No roteiro de 340 frames VDP, a espera de P1 foi 167/168, 157/164, 114/161 e
54/158 ticks de input; a vida de P2 caiu somente na quota 8. Relógios e
trajetórias diferem: não atribuir o resultado do golpe só à quota. Não
promover o menor número de derrames como solução de apresentação.

O builder aceita `toolchain.defines` numéricos somente em `--build-dir`;
inclui as mesmas flags no SDCC de dependências e de compilação e as registra
no recibo. Exemplos versionados:
`.mddev/candidates/upload_trace_chunk4_20261027.json` e
`.mddev/candidates/upload_trace_chunk8_20261027.json`. As candidatas
correspondentes estão em `out/candidates/20261027_upload_trace{4,8}/`. O
anel diagnóstico mede pares por ator/tick e adiciona trabalho ao VBlank;
seus resultados e auditoria de janela estão em
`out/evidence/20261027_upload_trace{4,8}_case/`. A ROM com trace desligado
está em `out/candidates/20261027_trace_disabled/`, SHA `ec6fd175…`; seu FPS
foi 26,48/25,23 e o selo derramou (min 7, delta 1749), ambos reprovados e
sem carga completa. Seguir a análise de residência seletiva com os
pares novos/tempo AIR e o serviço realmente observado, sem publicar uma
pose especulativa antes do pedido ou desalojar um ator urgente.
O fechamento passou 269 testes rev2 (150 deselecionados), 135 selftests
(probe opcional não executado), 75 ferramentas de medição e os checks de
documentação, hardware, aprendizado e corredor; o contrato é de planejamento.
A cópia local da continuidade deste lote foi verificada em
`.runtime/backups/luta_mugem_rev2-runtime-20261027-upload-trace.tar.gz`
(SHA `097ec3af5830c937d8ae5dfe1432916002b115c2c7770226ff4c5a228329540c`,
15812 arquivos; manifesto com o mesmo nome e extensão `.json`). O pacote e o
owner estão no mesmo disco, sem proteção externa nova.

## 2026-10-27 — antecipação de pose sem promoção (candidato)

O runtime ganhou antecipação opcional da próxima entrada AIR, desativada por
padrão e selecionável apenas por manifesto de candidato. Uma pose ainda não
pedida permanece no `pending`; requisições reais têm prioridade e podem
recuperar espaço especulativo sem expulsar as imagens residentes. As ROMs
quota 8 (`61efabeed3e6bb75d5ef460b9b2cea648cf66df9ef1c9730e684ca7ef9ea0bb4`),
quota 4 (`6ee09b24292b511f254b6044814b9e6d16b4d09076260b1cb8e3d88d94050873`)
e default desligado (`3414a2c959d137977b0fe31de8eabc7b6ac43c4e06380df19fc0a2a7f72f1829`)
estão em `out/candidates/20261027_prefetch_*`, com recibos e fonte por hash.

No roteiro Emulicious, as três causaram dano com input; quota 8 com
antecipação teve menos espera observada, mas as trajetórias e números de
ticks diferem. Na sessão BlastEm auditada `59aa76f50f7c4623a510777926e64e09`,
os 60 residentes e 40 pendentes carregados amostrados bateram com a ROM; a SAT
excedeu oito sprites por linha em 14/30 fronteiras. Na mesma ROM quota 8, as
duas janelas NTSC deram 25,88/23,49 atualizações/s e o selo derramou em 1871
de 3000 iterações, mínimo 7, sem HUD/FX/PSG. Todas as sessões foram fechadas.
Esses resultados não aprovam composição, contato, prazo ou gameplay completo.
O memory bank registra método, limites, contadores e caminhos dos artefatos.

O lote passou 271 testes rev2 (150 deselecionados), checks de marcadores e do
corredor. Nenhum ID do backlog foi encerrado. O próximo ramo causal é reduzir
as divisões de 16 bits no relógio de pacing e verificar inclusive o wrap de
65535→0, com nova ROM, sem supor ganho ou mudança de comportamento.

Continuidade local: `.runtime/backups/luta_mugem_rev2-runtime-20261027-prefetch.tar.gz`,
SHA `7223ccb76799f5bcf3c61348dce6eb333c8fca6ac3214e62bce841ba40eeee35`,
manifesto com mesmo nome e extensão `.json`, verificado em 17340 arquivos.
Essa cópia e o owner estão no mesmo disco; não há nova proteção externa.

## 2026-10-27 — pacing sequencial e investigação de BG

O contador da janela de 150 ticks agora conserva quociente/resto sequenciais,
sem as duas divisões por tick; o teste C percorreu duas voltas completas de
16 bits. A ROM default `0ed9ce5a119374509defe53b836630690d01849f6713845be5a4ab586d11bfdd`
observou a volta natural em sessão Emulicious `cb71abbda3d44c4a9cabade2d877c50d`,
226 amostras estáveis nas fronteiras e saturação; houve uma primeira tentativa
de cobertura incompleta por erro do roteiro, preservada separadamente.

A mesma ROM reconheceu golpe e dano e voltou a responder à esquerda depois
da recuperação (sessão `f17dc2ade956428794666f700428e9f3`, vídeo e bundle
válidos). O FPS NTSC de 26,55/25,80 e o selo de 1749 derrames/mínimo 7
continuam reprovados; não havia HUD/FX/PSG representativos. A candidata com
antecipação também repetiu o golpe e reprovou FPS. Nenhum ID foi encerrado.
A suíte passou 272 testes `rev2`, com 150 deselecionados.

Próximo experimento: um ator no BG usando scroll global e o outro em sprites,
com patterns já residentes. A análise estática encontrou pico isolado P1=6 e
P2=8 por linha; o modelo também encontrou perda de pixels na coluna esquerda
sob `LEFTCOLBLANK`. Isso é risco explícito, não solução ou decisão de mudar o
viewport. Testar ROM, movimento sub-tile, bordas, prioridade/overlap, HUD/FX,
PNT e deadline antes de qualquer promoção. Detalhes no memory bank.

Cópia local de continuidade verificada:
`.runtime/backups/luta_mugem_rev2-runtime-20261027-pacing.tar.gz`, SHA
`c12f81087eb2b953033c20d29e336ef455d6941246619e822d3623b7e7421d77`,
manifesto com mesmo nome e extensão `.json`, 18273 arquivos. Continua no
mesmo disco do owner; não é backup externo.

## Retomada 2026-10-28 — câmera de borda e composição

Raiz única `/home/misael/Projects/SMSForge`, branch
`codex/host-bootstrap-continuity-20261024`, base `69824ce4f43892db65fc0a607ccbd5846206ac42`.
A fonte atual `SMS_projects/luta_mugem_rev2/src/main.c` tem SHA-256
`05c5de7ab3cf990fb5a434e0019b5f09c2b13b38e9986d44d08573824b3088fc`.
O lote altera fonte, teste C host, memory bank, TDD, backlog e este handoff;
revisar e publicar somente esses seis arquivos.

A suíte rev2 terminou com **292 passed, 150 deselected** e o teste focal da
câmera com 2 casos aprovados. `audit_debug_markers.py` e
`audit_probe_corridor.py` passaram na fonte/candidata. Os gates documentais
`audit_doc_sync.py` e `audit_hardware_constants.py` passaram após esta revisão
do handoff. `measure_worst_frame.py --self-check` passou. A
chamada de `audit_rom_asset_binding.py` sem manifesto só confirmou que ausência
é permitida; não há prova asset→ROM neste lote.

A câmera é experimental e desligada por padrão. A ROM BG+câmera
`671ba6468ac5fa28d7e59c6f70e96adca740b38caf5dce62e9562dde525ffaac`
registrou shift −7 px, 32 aplicações e zero conflito na captura de borda; o
controle anterior `0180d1b5…` ficou em zero. A revisão visual válida da sessão
`e8ea26dce3de427d8ae422daa5c0099b` reprovou por sobreposição. Em roteiro
BlastEm de 49 fronteiras, sprite-only `7523bd0c…` excedeu oito sprites/linha
em 46 amostras (pico 10; SAT até 33); BG+câmera e BG-only
`dfe5a9c7a7de8372e50562d1a551a52e01a5d29c8eb9100d88add776339c8d1f` ficaram
em no máximo sete por linha e SAT até 16. A trajetória foi igual, mas as poses
não foram pareadas; BG-only ainda não tem revisão visual. Com BG ativo,
`LUTA_PRESENT_HIT=0`.

O frame de vídeo 228/VDP 348 foi reproduzido em duas sessões Emulicious
privadas, com PNG SHA
`5cc562b10a224d1a3b104f7aa8aa0cc3153b3c9748d11dea97b59230d7f1914a`.
RAM confirmou P1/P2 no chão em x=222/240, gap 18 px, pusher=84 e sem hitstop,
hit ou dano. `ground.front` da fonte (18+9 na escala 2/3 = 12+6 px) deixa
os contornos idle de 32 px sobrepostos. VDP 481 observou P2 no ar e
cruzamento permitido, em estado separado. Os bundles privados
`out/evidence/20261028_pusher_geometry/` passaram `check-bundle`; sessões
`3e3b6f2097e34666964aa5438d74fc2f` e
`8d3fd83a13024d85bc106323e1c8900f` foram encerradas. Não alargar colisão sem
contrato de margem visual ou decisão de design: isso altera o espaçamento
derivado da fonte.

Worst-frame selou 3000 quadros em 180 s por build: BG+câmera, sessão
`9908ac359b794dc09fd2a1adbc086e3c`, `vovf_delta=1759`, `vline_min=2`; BG-only,
sessão `60d5e84e7e764c8cabe2463d767f0fd7`, `vovf_delta=1773`, `vline_min=2`.
Fonte, gerados, toolchain e demais defines coincidem; apenas
`LUTA_BG_CAMERA` e o manifesto correspondente diferem. Uma rodada por variante
não prova que a diferença de 14 seja efeito da câmera. Ambas reprovam VBlank;
as sessões foram encerradas.

Próximo passo seguro: investigar e reduzir o derrame de VBlank por uma
hipótese mensurável, preservando baseline e orçamento. Em paralelo, obter
revisão visual do BG-only. A sobreposição depende de decisão humana entre
margem visual e fidelidade do pusher. Manter os 55 IDs abertos; este lote não
promove câmera, composição, deadline, vínculo asset→ROM ou delivery. Não
iniciar compilação ou sessão simultânea às medições.
