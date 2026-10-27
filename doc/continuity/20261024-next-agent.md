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
