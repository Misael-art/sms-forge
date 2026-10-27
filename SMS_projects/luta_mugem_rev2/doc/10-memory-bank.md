# Memory bank — luta_mugem_rev2

## 2026-10-27 — identidade, fundo e cancelamento de pose (em desenvolvimento)

Nenhum dos 55 IDs foi encerrado. A ROM nominal e o recibo históricos foram
preservados: `out/rom/luta_mugem_rev2.sms` SHA
`087df67677626bfcd61188cb5ff0a5c054eb4feb24c420434fcfbeebf5fa7a65`;
`out/build_record.json` ainda aponta para `e697e906…` e outro host. Isso mantém
ID01 aberto, mesmo com recibos de candidatos agora identificados. O rebuild do
checkout original, em `out/candidates/20261027_host_baseline/`, SHA
`06e575f1fa632e0742e594ea9db77b7ddd8dde44a397d782afbdc44f3b664e97`, passou
`verify_canonical.py`: payload idêntico, diferenças apenas em `0x7FE6`/`0x7FFA`
(data SDSC e checksum). A fonte anterior `042ba22e…` continua no Git.

O build central aceita `--build-dir` em `out/candidates/` e, somente com esse
destino, `--manifest` alternativo dentro do projeto. Não sobrescreve ROM,
recibo ou changelog nominais. A saída só recebe recibo após compile/link,
pre-gates e comparação das entradas; inclui SHA do ROM, fontes/headers efetivos,
banco de patterns, manifestos e componentes SDCC. A comparação de hashes em
duas leituras não é snapshot transacional. O candidato recusa `link_extra` e
opções makesms ainda sem custódia. Os includes de dados são selecionados pelo
manifesto, sem trocar o núcleo ou editar os headers gerados. O corte diagnóstico
`out/candidate_configs/pose_budget_pair_20261027.json` referencia o pacote
existente `pose_budget_pair_20261023` e sua imagem de 24 bancos; headers e banco
foram conferidos contra o manifesto gerado. Os insumos desse pacote estão no
asset de continuidade de 24/10 (manifesto `.runtime/downloads/`),
enquanto os novos candidatos e mídias permanecem locais em `out/`.
A receita idêntica foi preservada no Git em
`.mddev/candidates/pose_budget_pair_20261027.json` (SHA `5236f208…`); ela é
diagnóstica e não substitui o manifesto nominal nem aprova entrega.

R01: Emulicious privado reproduziu fundo estampado e P2 fragmentado na ROM
nominal, sessão `862959770d5344118789bb1c96910d98`, frame VDP 740. O código
preenchia a PNT com o tile 255 (`0x1FE0`), dentro do pool de sprites
`0x0000..0x1FFF`. O candidato `de2c51937a30f69a68610ecff7117b768f4a5094d0262cc745d861fa6185ac16`
aponta a PNT para o tile 256 zerado em `0x2000`; na sessão
`db31cb784774414b84d4988436ca9679`, o fundo ficou preto no quadro equivalente
e nas 80 linhas superiores dos 52 frames registrados durante direita/botão;
P1 foi de x=73 para x=91. Os bundles privados passaram `check-bundle` e as
sessões foram encerradas. O diagnóstico complementar BlastEm da ROM `d8de0ad…`,
sessão `blastem-sms-f7aed4ca5c7a4aa68193a13b029d77bd`, verificou em cinco
fronteiras VDP (600, 630, 720, 820 e 940) a PNT em `0x3800` com 768 entradas
`0x0100`, tile 256 zerado em `0x2000` e SAT em `0x3F00`. O bundle passou
`audit_blastem_sms.py --require-current-tool`, com limpeza confirmada; roteiro,
dumps e extração ficam em `out/evidence/20261027_blastem_vram_candidate/`.
São cinco estados de uma sequência, não prova de todas as ações/telas, ausência
de sobrescrita entre fronteiras ou correção de qualquer outra ROM; R01 continua
aberto.

O corte de 24 bancos sem gate de papéis, SHA
`a11811f47ae51676b448b07a09e343152f1916c9b3ccfdae2449548ebf3db046`, mostrou
ambos os atores na sessão `5d629c1598a14306b9bbfb0098389dfe`. Em 82 frames VDP
de direita/botão/neutro, P1 avançou x=84→114, mas `cmd_hits_p1` permaneceu 0
e ambas as vidas em 1000: não se provou ataque nem interação completa. No
frame VDP 740, P2 pedia pose 69 com 54 residente; `present`/SAT não provam
integridade visual em todos os quadros. Os dez pares históricos do corte
excedendo 8 sprites/linha continuam dívidas de R02/R03, não foram bloqueados
no candidato atual. O selo da sessão `d6599d1cb00b4d248d14f44ba3691b18`
registrou `derramou`, `vline_min=2`, `vovf_delta=1770`, `done=1`; as primeiras
20 iterações já ocorreram no boot por stepping da ponte, antes do runner de
180 s, e a carga não inclui HUD/FX/PSG. Não é janela representativa de entrega.

R05/R06: o pedido para voltar à pose já residente deixava outra pose pendente
ser promovida. O teste C compilou as funções reais e primeiro falhou; a correção
cancela a geração abandonada sem desalojar o oponente e atualiza o `Frame`
associado quando o bitmap é reutilizado. Em sessão privada com pose 0 residente,
direita e soltura antes do upload terminar, a ROM antiga `a118…` manteve pose 6
pendente e a promoveu no VDP 821 enquanto a sonda de desejo indicava 0; a ROM
corrigida `9654406b9891d562acc4f10c099911d7d2f28c229f02a426861f057b62dba0f0`
cancelou a pendência no VDP 820 e incrementou `superseded`. Sessões
`eca1fc566c1d4cfbb5d259e86061c185` e `2a06433a37d34219988c84565712abdc`,
encerradas; traces e journals em `out/evidence/20261027_pose_cancel_case/`.
Endereços de current/pending foram derivados dos `.rel`/`.sym` e conferidos
contra o `.map` de cada ROM; leituras em fronteiras VDP podem interromper o
loop e não são timestamps exatos de apresentação. Isso não prova contato
visível, deadlines nem inexistência de starvation; R05 e R06 seguem abertos.

O modelo `mugen2sms/runtime/commit_budget.py` preserva o default histórico
v033 identificado no relatório e oferece `rev2_b2_cancel_v1` explícito:
8 pares por lado, sem evictar oponente e com cancelamento. É modelo de fila,
não medição VBlank ou garantia de imagem. Commit local anterior à experiência
de agrupamento: `ca921dd` (código e testes); sem promoção de capacidade.

Experiência de upload: `SMS_VRAMmemcpy_brief` aceita tamanho em byte; agrupar
até três pares contíguos por chamada mantém o tamanho em 192 B ou menos. O
teste C comparou endereços, bytes, budget e promoção apenas após completar a
pose. O gerador prevê cada pose completa dentro de um banco de 16 KiB; a
validação exaustiva dos descritores reais e bancos-limite permanece pendente.
A ROM agrupada
`635fc1d1dc97411de44fccf02e2079ee009dadc61df0f0f88905ae5b520fca23`
repetiu o cancelamento observado na sessão `6f24a1b31b4144b29454ebab73738c34`.
Comparação diagnóstica da mesma cena e limites de 8 pares por lado: antes
`9654406b…`, sessão `60e7d6612c854f9c9b56ea82dfb0ae3e`, `vline_min=2`,
`vovf_delta=1750`; agrupada `635fc1d1…`, sessão
`69560ad3ba4b47e298e250f1f521b624`, `vline_min=13`, `vovf_delta=1720`.
Ambas selaram 3000 iterações e derramaram. O runner de 180 s começou após 20
e 23 iterações já executadas em stepping, respectivamente; a cena não inclui
HUD, FX ou áudio. A diferença observada não é budget aprovado nem demonstra
melhoria universal de fluidez. Snapshots das fontes exatas e recibos estão nos
respectivos diretórios candidatos; a versão anterior consta no commit `ca921dd`.

O contrato de escala agora declara `pose_budget` com os fatores do GDD e seu
SHA, sem reapresentar 72–88 px como alvo deste projeto. O self-check do auditor
testa GDD divergente e contratos inválidos; `contract_pass` continua apenas
planejamento. A entrega ainda exige composição, contato visível, prazo e carga
completa na mesma ROM, revisão independente e os sete eixos.

Na ROM `635fc1d1…`, sessão privada `839665d33f694c8cb31ee161dbec68d9`, P1
andou de x=84 a 139, segurou o botão 1 e soltou; `cmd_hits_p1` aumentou de 0
para 1 e a vida de P2 caiu de 1000 para 888. O vídeo nativo da sequência e o
journal estão em `out/evidence/20261027_batched_gameplay/`. O caso demonstra
entrada reconhecida e consequência nessa configuração, não equivalência CNS,
guarda, sincronização do contato, áudio ou interação vertical completa. A
sonda SMRT em duas janelas NTSC de 8 s, sessão
`b8474880e1f74ab3bd5a536cb0518d29`, mediu 23,38 e 21,02 atualizações/s,
reprovando 60 e a dispersão; esta cena não tem HUD/FX/PSG representativos.

S04: `advance_actor` entregava o elemento seguinte no tick que encerrava o
atual, encurtando sua primeira exposição lógica e pulando duração 1. O teste
C extrai e compila a função real, cobre sequência finita `[1,2,1]`, loop e
hitstop na fronteira; falhou antes e passou após a correção. A ROM candidata
`d8de0ad026b8c8a6dd7219e2b669a2fb68b56aad3170fae04f5b69c8a2f5ef00` foi
buildada; sua QA e medição são registradas separadamente. A prova completa
exige identidade AIR de fonte e ROM em N+1 fronteiras e terminal, além de
framebuffer; o teste host não paga isso. O gerador ainda normaliza duração 0
para 1 e o runtime trata hold terminal como `done`: não anunciar semântica
AIR geral ou equivalência para esses casos.

Na mesma ROM `d8de0ad…`, a sequência privada
`66ef673349d741ae8914a08064cc0dcd` registrou P1 x=84→140, uma entrada de
ataque reconhecida e vida de P2 1000→888; o vídeo por stepping não prova
throughput, guarda, áudio nem contato coerente. Duas janelas SMRT NTSC de 8 s
na sessão `e2103900f5bb47c3b1b8e1c8733ded31` mediram 23,50 e 20,64
atualizações/s e reprovaram a meta regional. O selo de 3000 iterações da sessão
`c6853d4cb3be434493689e2186cb8b49` teve `vline_min=13`, `vovf_delta=1719`:
as primeiras 21 iterações ocorreram no stepping de boot, sem HUD/FX/PSG.

Outra falha de cache foi reproduzida com as funções C reais: o contador de
época de 8 bits podia voltar ao valor de uma falha após 256 alterações do
pool, impedindo uma alocação que agora cabia. A implementação passou a invalidar
explicitamente a memória de falha dos dois lados a cada alteração; o teste
cobre o wrap, a repetição com pool inalterado e o cancelamento sem evictar o
oponente. A ROM `20d0c6e0efdfaeffcc9ad11b0cfe729d8edf3c02df8215998e62411c8f222f99`
repetiu a entrada e a consequência observadas em sessão privada
`98bb1673d29c4dad9d1c1ec428355e87`, com bundle verificado e sessão encerrada.
O caso de 256 mudanças foi exercitado no host C, ainda não como stress em ROM;
essa reprodução não encerra R05 nem aprova prazo, starvation ou composição.
O selo da mesma ROM, sessão `18ec08cf536842d6b9e13bb38273ed51`, apresentou
`vline_min=13`, `vovf_delta=1719` em 3000 iterações; as primeiras 21 foram
executadas durante o stepping de boot e a carga exclui HUD/FX/PSG. Também
reprovou e não é janela representativa de entrega.
Os 93 descritores do mesmo corte foram conferidos nas duas orientações contra
os bancos gerados e os bytes da ROM: 186 trechos respeitam as fronteiras de
16 KiB; a menor folga ao fim do banco é zero. Script e resultado em
`out/evidence/20261027_facing_bank_audit/`. É comparação estática de bytes,
não prova de seleção, imagem, mapper em execução ou orientação correta.

Hipótese descartada: remover as divisões de 16 bits usadas apenas pelos probes
de passo. O substituto foi comparado ao quociente/resto de referência por duas
voltas completas de `frame` em teste C, e seu assembly não tinha mais as
chamadas `__moduint`/`__divuint`. Na atração, janelas NTSC de 8 s da ROM
`20d0c6e0…` mediram 23,48/20,64 atualizações/s (sessão
`a5dd0b9985c749939b8f6f3b8790f405`), contra 23,38/21,25 da ROM experimental
`c06c08749cb1db357349281b37a8eea6f574379bf781becb856d24b70925ac8b`
(sessão `7bd86237e556496a9613f4e5771fe1d2`). Sem ganho demonstrável, o
experimento foi revertido no fonte; candidato, fonte e bundles permanecem em
`out/` como diagnóstico, não como aprovação de FPS ou medição sob carga completa.

A suíte `mugen2sms/tests --project rev2` primeiro não coletou três módulos por
f-strings incompatíveis com Python 3.11 em `inventory.py`; corrigida a sintaxe,
uma segunda execução acusou a API Pillow ausente no teste de transparência.
Após compatibilizar o teste com o Pillow instalado, a suíte passou: 260 testes,
150 deselecionados por escopo. A deseleção não valida o consumidor legado nem
o comportamento da ROM. Os 28 testes focados do lote também passaram, assim
como 135/135 selftests centrais; o probe opcional de build do selftest não foi
executado (a build candidata tem recibo próprio). As 75 ferramentas de medição,
doc sync, hardware e corredor de sondas passaram. O audit de aprendizado primeiro
acusou nove rotas stale após a edição do workflow BlastEm; os vínculos correntes
foram atualizados e o audit passou, sem alterar artefatos históricos.

## 2026-10-24 — continuidade sem o disco do host anterior

Pedido humano: preservar diagnóstico e trabalho pendente, preparar bootstrap
de host limpo, commit/PR e cópias recuperáveis. Isto altera infraestrutura e
documentação; não implementa os 55 itens abertos nem promove a engine.

Ponto de entrada: `doc/continuity/20261024-start-here.md` na raiz do workspace;
handoff do agente: `doc/continuity/20261024-next-agent.md`. O diagnóstico,
backlog e prompt estão em `doc/curation/2026-10-24_*`. Ler os registros de
validação da migração antes de afirmar que o ambiente novo está qualificado.

Bootstrap Ubuntu 24.04 x86_64/WSL2: Python em `.venv`, SDK reconstruído com
SDCC nativo >=4.2, emulador/licença e arquivos de runtime por SHA. Estado em
`.runtime`, sem dependência de `/home/misael` ou instalação pip global.
Preservar baselines 087df676 e 698e58ed; builds em host/toolchain novos exigem
nova evidência. A restauração inicial não reaplica snapshot sobre desenvolvimento.

Branch de continuidade: `codex/host-bootstrap-continuity-20261024`; release de
assets: `continuity-20261024`, no repositório `Misael-art/sms-forge`. A Page
privada de recuperação e os manifestos são apontados no guia. Credenciais e
configurações pessoais não fazem parte da migração. O EIO do `luta_mugen`
legado não foi reparado; o Git conserva suas versões já commitadas.

Próximo lote: identidade da build/documentos + R01/R02/R03/R05/R06/R09,
apresentação completa, streaming com prazo e orçamento VBlank. Não tratar
restauração, build ou dois idles completos como conclusão de gameplay/AAA.

## 2026-10-15b — M0 fechamento do esqueleto + wave-1 (t2 concluído)
Esqueleto do bootstrap compilado pelo build central com toolchain portável
(`sdk/sdcc-portable/bin` no PATH; sdcc 4.6.0 ausente do PATH do host).

| Eixo | Estado | Evidência |
|---|---|---|
| build | ok (esqueleto, não engine) | out/rom/luta_mugem_rev2.sms 16384B sha256 cb845e5b88a1a0afcb8246bc6a148049c3c977d746d5bb797bbc45bc74d851d3; out/build_record.json |
| boot | ok (esqueleto) | capture_evidence PASS: out/evidence/boot_v001.png, variância luma janela=5103 viewport=4274 (piso 40) |
| boot determinístico | ok | audit_deterministic_boot --runs 2 → [PASS] 2 execuções idênticas na ROM acima |
| gameplay/FPS/áudio | não iniciado | esqueleto estático; nenhum claim de engine |
| memória | este checkpoint posterior à ROM | — |

Manutenção de gate (wrapper central, autorizada pelo prompt; testada):
audit_deterministic_boot.py selectava janela por whitelist {256,300}; neste
host a janela aprovada de captura é 320×265 a 100% (medição direta com a ROM
acima). Alinhado à política de capture_evidence (`WIDTH>=256`), guarda L057
intacta. --self-check ok + veredito real na ROM = passagem da ferramenta.
A primeira reprovação FAIL_AMBIENTE foi zumbi legítimo (pid 229224, instância
do meu próprio probe) — a guarda funcionou como desenhado; encerrada a
instância identificada, o gate passou. Lição candidata: nunca deixar java de
probe vivo antes de gates por nome de janela.

Worker t2 (test_execution, envelope validado harness validate-result [OK]):
pytest mugen2sms = 325 coletados, 268 passed, 57 failed, 0 skipped. Raiz única
dos 57: `SMS_projects/luta_mugem/doc` EIO (test_donation_parity 56 +
test_build_recipe_cmd_sources manifesto). Falham por midia corrompida, nao por
rev2 — a parametrização rev2 desses testes fica pendente (lista de acoplamento
legacy em out/qa/result_t2.json; inclui testes que hoje leem o legado e ficarão
órfãos). Self-checks: validate_measurement_tools, measure_fps/frame_advance/
runtime_probe/worst_frame/vram_map, audit_blastem_sms, scale_pilot,
harness_orchestration — todos exit 0. Log: out/qa/pytest_mugen2sms.log.

Worker t1 (source_audit) CONCLUÍDO e integradodefeso envelope [OK]
harness validate-result; coordenador refez os SHA-256 dos 7 artefatos e dos
2 ZIPs (batem com intake). Fatos medidos, nada promovido (claim_ceiling
inventory_only):
- Extração íntegra: ken 10 membros, ryu 23 membros, 33 catalogados com
  bytes+sha em data/derived/members.json; fontes re-verificadas pós-extração.
- DEFs batem com intake. common1.cns ausente nos dois (só catalogado; nada
  inventado). Ken também referencia intro.storyboard de caminho absoluto
  externo D:\MUGEN (ausente). Discordância de case Ryu.snd→ryu.snd resolvida
  pelo membro real com hash; 13 resoluções case-insensitive (ACTs).
- IR do wrapper: ken 201 sprites/102 anims/411 frames/883 clsn/76 comandos/
  112 estados/27 sons; ryu 525/183/1309/1457/113/151/30.
- States próprios no CNS: ken 80, ryu 122 (o resto são 31/28 proxies
  common_forge substituição declarada, sem prova de equivalência).
  Tipos ken A29/C6/S42; ryu A44/C6/S71. ChangeState 92/115, HitDef 70/96.
- Dependências common1 ausentes (com estado chamador): ken [11,40,50,51,105,
  300]; ryu [11,12,40,130,131,132,1505,5040,5100,5200,5210]. Fronteira do
  piloto: movimentos alcançáveis só via actions próprias; esses estados
  ficam blocked até fonte autorizada/equivalência.
- Risco CMD em 2 botões: comandos com 2 botões simultâneos ken 25/ryu 21;
  3 botões ryu 4 (ex. x+y+z) exigem remapeamento declarado sem sacrificar
  especiais em silêncio. Supers por Power>=: ken 4 grupos (500–3000), ryu 4
  (500–3000); power= não declarado em [Data] de nenhum.
- AIR×SFF: ken fecha; ryu tem 3 anims com sprites ausentes (6000/6001/8400
  refs prováveis de common/fightfx) catalogados, arte não convertida.
- Defects do envelope: CLI exige PYTHONPATH=tools/sms_wrapper (invocação
  direta do __main__.py quebra import mugen2sms); 5 Statedefs duplicados em
  ken.cns (1109/806/906/1300/1310 parser manteve o primeiro).

Blocker dominante: escolha de renderer medida para 2 atores+FX (M1) e
subconjunto CNS alcançável (M2). Wave-2 despachada: t3 budget_analysis
(limite inferior exato por scanline com poses reais via scale_pilot +
conversão Ken; saída JSON em out/budget) e t4 source_audit (matriz de
alcancabilidade estados×REQUIRED_ROLES×common1×CMD-2botões em out/semantics).
Próxima ação: integrar t3/t4, decidir renderer por medição, depois ROM
diagnóstica do par.

Decisão de bloqueio cumprida — palette_contract.py QUARENTENADO (não alias):
movido a tools/sms_wrapper/mugen2sms/quarantine/palette_contract_MD_LEGACY.py
com QUARANTINE.md (motivos: import .converters.sprites quebrado reproduzido;
modelo PAL0–PAL3/15-slot é CRAM do MD; lê src/mg_gen/*.c+\.res SGDK; zero
consumidores — as ocorrências em audit_asset_proof_sheet.py são só a string de
schema mof_sms_runtime_palette_contract_v1). Verificado pós-movimento:
pacote mugen2sms importa ok e `python3 -m mugen2sms inventory --help` exit 0.
Verdade de cor SMS vigente permanece converters/sms_palette.py (6-bit,
r|g<<2|b<<4, SMSlib.h). Reparo como contrato SMS tem gatilho registrado:
após M1 decidido escala/renderer, orçar cores corpo+FX por ator na paleta de
sprite SMS com teste diferencial; aproveitáveis do legado: análise de classes
estáveis/variantes e fusão sem perda (verify_remap).

Parametrização de testes (exigência explícita do prompt; cumprida sem fabricar
doação/binding): `tools/sms_wrapper/mugen2sms/tests/` ganhou conftest.py com
opção `--project {all,donor,rev2}` (padrão all) e marcadores `donor`/`rev2` —
deseseleção é escopo, NÃO capacidade. 11 arquivos acoplados ao legado
(luta_mugen/doc EIO, integrada/src, out/local_study) marcados `donor` no módulo;
em test_build_recipe_cmd_sources.py apenas o teste de manifesto real recebeu o
decorator (fixtures tmp permanecem all-scope). Reuso de atalho: teste único de
leitura do binding foi encapsulado via re-marcação, sem duplicar corpo.
Novo test_rev2_intake_parity.py (`rev2`, 5 testes): re-hash dos ZIPs contra
doc/22-intake-doador.json, selected_def×sha, members.json 33 membros conferidos
no disco (bytes+sha), source_sha registry→ZIPs e fronteira common1 (nada de
common1.cns inventado sob o projeto; política declarada no intake).
Medições persistidas (sha256 integral dos logs):
- `--project rev2`: 184 passed, 146 deselected, exit 0 — out/qa/pytest_rev2_scope.log sha b469b7246454a27c3c6c1dcfd62108f6beafecf4459fcb854734e85d907578b8
- `--project donor`: 57 failed, 268 passed, 5 deselected, exit 1 — out/qa/pytest_donor_scope.log sha b47bc77e993fe66b1ace1c204f2968f78f3ea28bd56675d931ba11ed6e411801 (falha idêntica à medição t2: raiz EIO do mídia, não mascarada)
- `--project all`: 57 failed, 273 passed — out/qa/pytest_all_scope.log sha 4cbc0eba43f9b3ac18e85eb723deb2a1a852cbbdeba4fe7b142b7dc95443c83b (330 coletados = 325 do t2 + 5 novos; contagens batem)
Sem skipped/xfail em qualquer escopo. Os 57 falham somente no escopo donor e
seguem bloqueados pela mídia EIO — reparo de cartão é fora do escopo deste
projeto (registro preservado em out/qa/result_t2.json).

Blocker dominante inalterado: t3/t4 em execução; veredito do renderer depende
dos números de scanline/VRAM. Pré-preparo da ROM diagnóstica (ramo sem
sobreposição de lease): CLI mugen2sms expõe `generate` (pacote→artefatos SMS;
`--banked` mueve _TILES ao slot 2 de 16KB) e `versus-cut` (par P1/P2→pacote
versus com páginas de mapper distintas); self-checks [PASS] persistidos:
out/logs/selfcheck_versus_cut.log sha
47b3c392ab4607de04ed95944a985e2f32d29416a27c2396c63a07b49785c04d e
out/logs/selfcheck_quality_check.log sha
f917e23461964d02c7bfbad126d9c9d931d83d1d100594f1dccaabf9f88c3d8b.
Wave-3: taskset_m6_wave3.json + plano ok (sha
a7dd181c27253c61402c63f1d2ce6c14a47544f12263549654692a84833273cf); worker t5
(classificação SND/PCM, lease out/audio, digests t5-wave3-2026-10-15/M6prep-snd)
despachado — 3 workers ativos = capacidade máxima.
Próxima ação: integrar envelopes t3/t4/t5, decidir renderer por medição e
preparar ROM diagnóstica do par Ken/Ken.

##2026-10-15 — preparação autorizada
Novo consumidor criado pelo bootstrap central, documentos próprios. Nenhum
arquivo obrigatório copiado do docilegível do luta_mugen. Anexos preservados
emdata/intake/2026-10-15/ comSHA. Escopo humano refletido noGDD/TDD/spec.
FontesKen/Ryu doSGDK em identificação; intakecongelado ainda não convertido.

| Eixo | Estado | Evidência |
|---|---|---|
| build | não iniciado | bootstrap não ébuild deengine |
| validation_report | não iniciado | contrato de planejamento somente |
| boot | não iniciado | nenhumaROMrev2executada |
| gameplay | não iniciado | engine planejada |
| FPS | não iniciado | alvoGDD, semmediçãojogo |
| áudio | não iniciado | SNDreferência, semPSGintegrado |
| memória | documentado | este checkpoint e docs do projeto |

Blocker dominante: identificar/fixar fontes+commonstates e escolher renderer
viável para2atores grandes/FX semomissões; depois runtimepredicadosFonte.
Próximaação: executar M0 eM1 de doc/20-plano-implementacao.md, preservando
rigorosamenteparsed/generated/consumed/observed/budget_validated.

Armazenamento: novo diretório usa mesma mídia /mnt/sdcard do antigo; não é
reparo físicoEIO. /run/user/1000 estava semespaço (snapshot15out), /tmp e/home
tinham espaço. Revalidar saúde/escrita antes de build/QA; não apagar arquivos
alheios nem remount/fsck automaticamente. HistóricoEIO fica preservado.

## Intake congelado
Ken/Ryu ZIP originais copiados e SHA conferidos, sem extração/alteração.
Manifesto doc/22-intake-doador.json, registry local aprovado somente no eixo
organizacional. Ambos common1.cns ausentes; common_forge não é equivalência
provada. Fonte raw candidata não equivale a sprite convertido/aprovado.

## Conferência posterior do host
Onze documentos/manifestos próprios foram relidos comoUTF8, comSHA; escrita
e releitura4096B emout passaram e a sonda foi removida. Resultadoem
doc/23-validacao-preparacao.json. /run/user/1000 passou de0bytes livres no
primeiro snapshot para1552310272bytes livres no snapshot posterior, semlimpeza
executada por este agente. Revalidar antes do runner; não éreparo deEIO nem
prova de estabilidade física. Build/emulador/jogabilidade continuam não rodados.

## Wave-3 integração t5 + pré-leitura t3 (2026-10-15, coordenador)

### t5 SND/PCM — envelope validado, integrado (claim_ceiling inventory_only, promoted false)
`validate-result --taskset out/logs/taskset_m6_wave3.json --result out/audio/result_t5.json` → OK exit 0.
Defeito formal t5-coord-01 registrado: worker emitiu schema/artifact_kind fora
do contrato (`agent_task_result_v1`/`worker_result`); coordenador normalizou os
dois campos de cabeçalho sem alterar conteúdo, digests (t5-wave3-2026-10-15 /
M6prep-snd) nem claims. Hashes:
- out/audio/snd_inventory.json sha 78b9e922eaf91d524159bbff0b75ac1f3551c06f5baf388bd98b490337943072
- out/audio/pcm_psg_feasibility.json sha 94629f5ec7a71707ae483ddc5202a6c5666df2b3b02aa05e83ac59c2539388b3
- out/audio/result_t5.json sha (pós-normalização) 3459655ffbaa12187d7c2997a5cbe8bfcebfc478d571be8988afa7cd6121dc77

Números medidos (formato ElecbyteSnd 2 com WAVs embutidos; nenhum [Sound]
manifest nos DEF; PSGlib não toca PCM — pegada é argumento, não capacidade):
- ken: 27 definidos, 16 referenciados, 11 não referenciados, 1 referenciado-ausente (0,6); classes a=12 b=2 c=13 d=1; footprint referenciado 551.662 B.
- ryu: 30 definidos, 17 referenciados, 13 não referenciados, 4 ausentes (0,8; 30,0–2); classes a=15 b=6 c=9 d=4; footprint referenciado 1.749.470 B; (500,0)=BGM loop 8-bit 92,2 s é o driver de pegada.
- defeitos de fonte: `value = F20,0` malformado em ken.cns:3476; taxas irregulares (20182 Hz hits ken; ken 3,1 e ryu 500,0 em 8-bit).
- classes a/b/c/d = estimativa declarada por duração/ZCR/autocorrelação; **zero claim de qualidade PSG** — transcrição/reautoria exige proveniência e aprovação (M6).

### t3 — pré-leitura dos artefatos do lease (SEM envelope; não integrado)
Artefatos em out/budget/ (scale_sweep.json, scanline_lower_bound.json,
vram_upload_budget.json, m1_scanline_lower_bound.py + configs cut/cut72/cut72full) gravados 21:04–21:07. result_t3.json ausente. Números lidos diretamente, marcados como pré-integração até validação do envelope:
- modelo 8x16 SAT; escala idle 98→80 px (ratio [40,49]).
- verdicts sprite-only por scanline: a_idle_vs_idle FEASIBLE (pico 7, linhas>8: 0, SAT-proxy 32); b_punch_vs_crouch IMPOSSIBLE (12/8/44); c_both_jumping FEASIBLE (6/0/29); d_attacker_defender_projectile_impact IMPOSSIBLE (19/38/72); e_corner_a_recheck FEASIBLE (7/0/32); e_corner_d_recheck IMPOSSIBLE (15/16/59); bonus_kick_vs_guard IMPOSSIBLE (14/14/44).
- scale_sweep 72–80 px: full_fx 17–19 sprites, `all_fit_8=false` em todos os alvos → redução de escala sozinha NÃO resolve as composições impossível.
- vram_upload_budget: scale_idle_px 80; anims ken [0,12,41,120,220,280,1000,1100,1101], ryu [0,12,41,220].
Leitura parcial do worker no lease (cut72full etc.) indica experimentação de
corte — nada disso vira veredito sem envelope.

### Implicação para a decisão de renderer (coordenador, pendente envelope)
4 de 7 composições reais excedem 8/scanline em sprite-only sem omissões, e o
sweep de escala não fecha o buraco. O veredito formal será emitido só com o
envelope t3 validado; direções candidatas: híbrido BG+sprite para FX/payloads
pesados ou ajuste de arte autorizado — nunca esconder frames.

Blocker dominante: envelopes t3/t4 ainda ausentes (workers escrevem nos leases
out/budget e out/semantics). t5 fechado.
Próxima ação: aguardar/validar result_t3.json e result_t4.json, emitir decisão
de renderer por medição e derivar ken_config.json das rotas exact da matriz t4
para a ROM diagnóstica Ken/Ken.

### t4 matriz de alcancabilidade — envelope validado, integrado (claim_ceiling analysis_only)
`validate-result --taskset out/logs/taskset_m0m1_wave2.json --result out/semantics/result_t4.json` → OK exit 0; digests t3t4-wave2-2026-10-15/M1pilot+M2prep ecoados; hashes dos artefatos batem com os registrados no envelope:
- out/semantics/reachability_matrix.json sha 88e02c1838b45c4a10c33e9886c1c5c3f36c135f28db6c73fd6d08dfffff7601
- out/semantics/cmd_2button_audit.json sha 86481f6f4ca31bfafdcfedb649f8842efc887eef0c384483c80129bf289558a3
- out/semantics/m2_backlog.json sha c83f88e2a7469106104457f059333bb115708aebfc886966dc3867d635c9edf4
- out/semantics/defects.json sha 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945 (lista vazia: reconciliação 0 defeitos)
- out/semantics/audit_report.md sha abd3011b05fb4f6de540d4096335d245129fc432fcf0e4a462af5f1254adb99e
- out/semantics/result_t4.json sha 3677937d0c53472dfc90911be7965b58408563099e0a3a54de6ff17e4a891bf5

Números (catálogo de lowering, NÃO capacidade):
- Ken 80 estados próprios = 54 ok_reachable + 6 blocked_common1 + 11 needs_remap_decision + 9 unmapped (8 orphan + 1 cmd_helper; Statedef −1 vem de [State -1] do .cmd). Ryu 122 = 82 ok + 3 blocked_common1 + 4 blocked_button3 + 1 blocked_air_missing + 18 needs_remap + 14 unmapped.
- Escopo M2 (só ok_reachable): 608 instâncias de controller (ken 219 + ryu 389) em 24/26 tipos; `animelem` primitiva AOT dominante (122/136); unsupported: ryu hitoverride×3.
- common1 hard-absent SEM proxy: ken {51,105,300} (estados 460, 800/801, 900/901, 1320), ryu {1505,5040,5200,5210} (helper-chain 5030/5035/5050).
- **Fronteira dura do piloto**: papéis idle/walk_f/walk_b/jump/crouch/guard têm ZERO candidatos próprios em Ken; walk_f(18)/walk_b(19) nem proxy no forge têm (hard_absent_no_proxy); idle(0)/crouch(11)/jump(50)/guard(120) existem como `forge_proxy_unproven`. Decisão de contrato de runtime (aceitar proxy com fronteira declarada vs. recusar) precede M2 — proxy forjado NÃO é equivalência MUGEN.
- CMD 2 botões: ken 76 comandos → 41 conflitos (0 três-botões; 9 supers gateados por y/b dropado ou x+y/x+z/y+z simultâneos); ryu 113 → 78 conflitos (4 três-botões; supers 3010 e 2600 sem rota 2-botoes hoje). Nada sacrificado em silêncio: conflitos listados com estados+Power>=.
- Pré-classificação de fidelidade (proposta, exige decisão humana p/ approximate): ken normais 2 exact/16 approx/11 blocked, supers 0/4/0; ryu normais 19/6/9, especiais 14/5/9, supers 1/1/2.
- ryu bloqueados por 3 botões: 1500–1530 (entrada única SP6_*). blocked_air_missing só ryu 3900 (Explod anim 8400 ausente; AIR 6000/6001 órfãos — gap de asset, não de alcancabilidade).

Blocker dominante atualizado: envelope t3 ainda ausente (decisão de renderer pendente);
decisão de contrato dos papéis comuns (forge_proxy_unproven vs hard-absent walk) é
gate para o config Ken/Ken.
Próxima ação: validar result_t3.json, emitir decisão de renderer por medição,
registrar decisão do contrato de papéis comuns e derivar ken_config.json das
rotas da matriz t4 para a ROM diagnóstica Ken/Ken.

### Decisão de contrato dos papéis comuns (coordenador, 2026-10-15, para ROM diagnóstica Ken/Ken)
Fato apurado: REQUIRED_ROLES do gerador exige idle/walk_f/walk_b/jump/crouch/guard/...
(fight_runtime_data.py:20–377), e a matriz t4 demonstra que Ken não tem NENHUM
estado próprio para os seis papéis comuns; walk_f(18)/walk_b(19) são
hard_absent_no_proxy (nem o forge os define). Registros de animação do andar
não existem em fonte autorizada — NÃO serão inventados.
Decisão para o piloto diagnóstico (claim ceiling: diagnostic_only; não é
compatibilidade MUGEN e não promove capacidade):
- idle(0)/crouch(11)/jump(50)/guard(120): usar forge_proxy com a flag
  `forge_proxy_unproven` preservada em source_limitations do config.
- walk_f/walk_b: classify `approximate` — deslocamento Q8 do próprio motor
  (CUT_WALK_FWD_Q8/CUT_WALK_BACK_Q8 já lowering de velocidade, scene_cut.py:1124)
  renderizado com a pose idle, pois nenhuma fonte autorizada define animação de
  andar; registrado como limitação declarada, não omissão oculta.
- Se o gerador recusar mapeamento de walk para idle, a alternativa é gate humano
  para autorizar acréscimo auditado ao common_forge — NUNCA preflight silencioso.
Fronteira: supers de ryu 3010/2600 sem rota 2-botoes e os 9 supers gateados de
ken permanecem como decisões de remap explícitas (cmd_2button_audit) — nada
sacrificado em silêncio; piloto Ken/Ken usa punch/hp/special/kick/hk ok_reachable.

### t3 scanline pilot — envelope validado, integrado + DECISÃO DE RENDERER (coordenador)
`validate-result --taskset out/logs/taskset_m0m1_wave2.json --result out/budget/result_t3.json` → OK exit 0; digests t3t4-wave2-2026-10-15/M1pilot+M2prep; 6/6 hashes conferidos no disco:
- scanline_lower_bound.json sha df50e8d1d6b902ed… pilot_report.md sha 001809acac6ec2e9…
- scale_sweep.json sha eb439447d1f87620… vram_upload_budget.json sha a935c6c9752b72d3…
- m1_scanline_lower_bound.py sha 287e236044a8b6b2… preflight_selfcheck.log sha 471463d928542175… (self-check EXIT=0)
Os números da pré-leitura acima CONFIRMADOS pelo envelope, com dois acréscimos:
- sweep 72–88 px: sem fit para b/d em nenhuma escala (72px: b=11 d=17; nativo: 14/22). down-scale NÃO é alavanca suficiente.
- merged-prebake: fecha d em exatamente 8 mas falha b(9) e kick-vs-guard(11).
- híbrido BG (absorção do interior hurtband → BG, unindo clsn1∪clsn2): demanda residual de sprites ≤1 slot/linha para os dois atores — única configuração com TODOS os pixels presentes sob ≤8/linha. Piores bandas: 45 tiles Ken punch (1.440B) / 25 tiles Ryu crouch (800B); ressalva medida: banda viaja → atualizações de PNT por frame sem escalonador.
- parede de VRAM/upload: Ken full-resident 475 pares = 30.400B vs 8.192B da região de sprites (3,7×); current+next por ator = 6.016–6.592B de 8.192B; 43/43 transições AIR estouram a hipótese 64B/vblank (mediana ~2KB; pior 2.624B num único vblank); troca de pose 1.728–3.840B.
- cross-validação: o próprio gate do gerador reprova Ken HK a 80px (SAT 66/65>64); idle de 72px do runtime → ceil(48/8)=6 casas = limite medido. Bound formal 8×16 por entrada de SAT confirmada (o D-T3-1 nota: fórmula antiga ceil(w/16) subestimava ~2×).
**DECISÃO DO COORDENADOR (por medição, não preferência): renderer de entrega = HÍBRIDO BG** — corpo interior no plano BG, contornos/FX/projéteis na SAT; sprite-only sem omissões está REFUTADO em todas as escalas do contrato. A parede de streaming VRAM (43/43 transições >64B/vblank) é o próximo blocker causal a projetar (janelas current+next cabem: 6.016–6.592B < 8.192B — exige agendamento de upload por VBlank com folga medida, espelhando o plano de slots idle não periódico de scale_pilot).
ROM diagnóstica do par: autorizada como instrumento de telemetria com limites de omissão EXPLÍCITOS (sprite-only 72–80px); nenhum veredito de entrega/qualidade sairá dela.

### versus-cut Ken/Ken gerado (coordenador, dados; não ROM)
Config derivado mecanicamente da matriz t4: out/config/ken_pilot_diag.json — papéis comuns 0/20/21/41/11/120, golpes punch=250 hp=450 kick=200 hk=220 special=1000 ko=5080, escala alvo 80px (banda 72–88), paleta ken1/ken1, commands {punch:a, hp:c, kick:x, hk:z, special:fireball_x}, source_limitations declaradas.
Descoberta: o hp anim 270 tem frame 3 `unsupported` na fidelidade do gerador → usado 450 (outro candidato ok_reachable da matriz). D-T3-4 do t3 ("join insatisfazível — sem comandos nomeados LP/HP/LK/HK") é REFUTADO: ken.cmd define comandos de letra única "a".."z"; com o bloco commands o join passa.
Geração [OK]: 45 poses/lutador, 24 banks dedup P1/P2, paleta P1=1-7 P2=9-15, source hash 459fc38ab34a094e2005eaf7e716cacd5a239dbb2d93505c4abee3324083e8ea; saída out/generated/ken_ken_diag/ (header versus_scene_runtime.h). Isso é `generated`, NÃO buildado/testado_em_emulador.

Blocker dominante: consumidor C do pacote versus (runtime FSM) e scheduler de upload/streaming para o híbrido; a ROM diagnóstica exige ligar out/generated/ken_ken_diag ao src/ do projeto e buildar.
Próxima ação: localizar/materializar o runtime C consumidor do versus_scene_runtime.h, buildar ROM diagnóstica Ken/Ken (SDCC portable), captura Emulicious + gates; em paralelo abrir wave-4 para o design medido de streaming VRAM do híbrido.

### M1-diag — ROM Ken/Ken rodando com telemetria legível (coordenador; claim ceiling: diagnostic_only)
Cadeia de ROMs (458.752 B, 28 páginas, mapper -mbank:0:24:2): ef379a16… → d13fe3bd… → d6616883… (bloco-espelho) → a814eb02… (zerar sondas) → **803b41b1664a8809cbf20c12a60606001ad40e2a39da238c137f8f0253328f7d ATUAL** (boot órfão corrigido). Fonte de dados: out/generated/ken_ken_diag/ (source hash 459fc38a…), corredor 0xC800..0xC8FB auditado pass (32 sondas, folga 1616; out/logs/probe_corridor_audit_m1_bootfix.json).
Duas correções causais nesta ROM:
1. L009-L134: sondas `__at` não são inicializadas pelo crt0 → loop de zera-16-u16 no boot; sem isso contadores partem de lixo (step=30496, max_line=26553 vs físico ≤64) e a evidência nasce ilegível.
2. Boot órfão (main.c:365-387): `pending.pose_global=0xFFFF` ANTES de `stream_pending(upload_all)` fazia o upload do boot retornar cedo (main.c:155), e `current=pending` copiava o 0xFFFF de volta — 66 pares ficavam marcados no bitmap sem dono (vazamento até pool cheio) e disp ficava 0xFFFF. Fix: preencher `pending` e deixar `stream_pending` promover `current` internamente (main.c:174-177).
Evidência #1 (capacidade de boot, ROM 803b41b1, sessão 45c39cc4…): boot_fit=1, overflow=0 B — idle P1 (2.112 B = 33 pares) + idle P2 (33 pares) = 66/128 pares, 4.224/8.192 B. A expectativa anterior "fit=0/256 B" usava aritmética errada (66 pares POR pose); corrigida aqui com A0F0_FACE_SIZE medido.
Evidência #2 (parede de streaming, frame 12): uploaded=72, evict=0→71 por passo, stall=12, used_max=128, free_min=0 — com pose >62 pares livres o pool satura e a troca de pose não fecha em 150 frames a 1 par/VBlank round-robin. Confirmado na ROM o número do t3.
Evidência visual (out/evidence/bootfix_idle_120f.png, frame 120): P1 Ken idle COMPLETO na tela; P2 parcial — pose 45 ainda em stream (1 par/VBlank). Tela não-preta pela primeira vez; é instrumento com omissão declarada, NÃO promoção de qualidade.
Veredites measure_runtime_probe (out/evidence/runtime_probe_m1_bootfix.json): boot PASS, frame_advance PASS, **fps_constante FAIL janelas [15.57, 18.1, 17.05]** (~3,5 VBlank por iteração do loop) — deixado sem máscara. Telemetria de cena: max_line=14, over8=375 em 12 frames (piso por scanline do t3 revisto na ROM; composição atual viola ≤8/linha — sprite-only refutado, decisão híbrido-BG mantém-se).
Limites do instrumento: FSM hardcoded não é compatibilidade MUGEN; walk = pose idle + deslocamento (approximate declarado); sem HUD/áudio/input; pacing do loop NÃO tem causa atribuída.
Blocker dominante: custo ~3,5 VBlank/iteração do loop sem causa provada (hipóteses: emulação render-throttle vs trabalho Z80 real — roteado a BlastEm por blastem-sms- diagnostics.md) e scheduler de streaming p/ híbrido (wave-4).
Próxima ação: diferencial BlastEm (RAM/opcode) no loop da ROM 803b41b1; em paralelo wave-4 design medido do renderer híbrido + streaming com o número desta ROM (corrente+próxima 6.016–6.592 B < 8.192 B, 43/43 transições >64 B/vblank).

### Veredito causal do pacing (ROM 3b34d5c77fc59636…, probe de VBlank por iteração)
ROM 3b34d5c77fc59636681ddddf12de4002172ac85b51038045559a79e3a9a6e876 (458.752 B, atual) adiciona probe_vblank_total/prev/max em 0xC820/0xC822/0xC824; corredor reauditado pass com 35 sondas (out/logs/probe_corridor_audit_m1_vbl.json).
Medição em sessão nova (out/logs/probe_dump_vbl_*.json): frame=171, vblank_total=171, **vbl_per_iter_max=1** — cada iteração do loop consome exatamente 1 VBlank; o corpo Z80 NUNCA estoura o frame. Na mesma sessão o contador de frames do Emulicious marcava 734 (~4,3 VBlanks por iteração de parede) e measure_runtime_probe mediu fps de parede [19.36, 10.6, 16.95] (out/evidence/runtime_probe_m1_vbl.json.json; boot PASS, frame_advance PASS, fps_constante FAIL).
**Causa apurada: o déficit de fps é throttle de render do Emulicious headless no host, não custo da ROM.** Consequências: (a) BlastEm-diferencial para hipótese de ciclo Z80 é DESNECESSÁRIO e não será rodado; (b) o gate fps_constante em Emulicious headless mede o ambiente, não a ROM — a aceitação de 60fps da entrega terá que ser paga em ambiente de renderização sem throttle (ou via decisão de instrumento declarada); nenhum veredito de fps é promovido nem rebaixado por esta evidência além do registro honesto.
Telemetria adicional da mesma sessão: stall=284, uploaded=195, evict=0 — parede de streaming (evidência #2) inalterada e confirmada nesta ROM.
Blocker dominante remanescente: scheduler de streaming/VRAM p/ híbrido-BG (wave-4) + ambiente de medição de fps sem throttle para o gate de entrega.

### Wave-4 M1 — worst-frame SMRT selado na ROM Ken/Ken (coordenador; claim ceiling: diagnostic_only)
Cadeia de ROMs: … → 803b41b1… → 3b34d5c7… → **8880a5e3814cd9ffedb8894c47e0ab8013cb6287c028cb7e720a8cfb37c00339 ATUAL** (458.752 B; adiciona contrato worst-frame L061 realocado na base 0xC800: probe_vline_min@D2, probe_vline@EA, probe_vovf WORD@EB, probe_phase@ED, probe_worst_done@EE, SMRT@E0, frame@F0; 0xC8EF nunca declarado — topo de pilha aliasa F0+). Sondas de perfil opcionais NÃO declaradas: a ordem cronológica fixa do tool (wait,hud,sat,stream) não bate com o loop rev2 (wait→stream→lógica→SAT); rotulagem errada seria evidência falsa.
Medição (sessão privada c765bc6c…, 300 s sem DAP, leitura única pós-selo; out/evidence/sessions/c765bc6c…/worst_frame/wf_m1_attraction.json): **veredito=derramou, vovf_delta=2758/3000 frames, vline_min=0, frame final 4459, done=1, janela_selada=true, ROM sha confere**. Fase do snapshot=1 (lógica de passo). estado_snapshot="FIGHT" é leitura do byte bootfit (0xF6) — rótulo sem significado para esta ROM, anotado, não promovido.
Reconciliação com o veredito causal de pacing (3b34d5c7): NÃO há contradição. SMS_waitForVBlank é sensível a BORDA: um corpo que derrama no display ativo acorda no próximo VBlank e ainda conta 1 interrupção/iteração. Logo vbl_per_iter_max=1 provava apenas avanço de 1 frame lógico por iteração — NUNCA cabimento do corpo no VBlank. Doutrina: contador ISR de pacing não detecta derrame; só a leitura de VCounter no fim do trabalho prova (consistente com "contador ISR sozinho não comprova gameplay60").
Números honestos do derrame: em 92% dos frames (2758/3000) o trabalho terminou com contador <0xC0 e o término mais antigo observado foi contador 0. **CORRIGIDO PELA ATRIBUIÇÃO BlastEm ABAIXO**: o derrame é real e intrínseco à ROM, não poluição do host; mas o número ainda NÃO é orçamento de pares/VBlank — com o corpo custando ~4 períodos de VBlank por iteração, qualquer taxa de upload atual é irrisória frente ao gargalo. Budget do scheduler só após reduzir o corpo e remedir.
Gate de decisão humana para M2 (do cmd_2button_audit + matriz, sem sacrificar supers em silêncio): sem rota em 2 botões p/ acorde ou tier ausente — ken 11 e ryu 18 estados em needs_remap_decision; supers gated: sfireball→estados 1203/2100 (power 500/1000), shurricane→2000, reppa→1203/2200; motivos 'botao_sem_tier:b/y' ou 'acorde_na_mesma_tecla:a+c/x+z'. common1 HARD absent sem proxy: ken [51,105,300], ryu [1505,5040,5200,5210]; com proxy-forge (substituição declarada): ken [11,40,50], ryu [11,12,40,130,131,132,5100]. Rollups: ken 80→54 ok/6 blocked/8 órfãos; ryu 122→82 ok/3 blocked/13 órfãos.
Blocker dominante (ATRIBUÍDO — ver seção BlastEm abaixo): o custo do corpo da ROM por iteração (~4 períodos de VBlank), não o ambiente. O gate fps_constante de entrega continua exigindo ambiente de renderização sem throttle, mas o déficit principal é a própria ROM.
Próxima ação: profile regional do corpo (emissão de metasprites/SAT, espelhos, varredura do pool, passo FSM) com sondas de fase já existentes + VCounter em sub-pontos, reduzir o corpo para caber em 1 VBlank, então remedir o selo worst-frame para obter o orçamento real de pares/VBlank do scheduler do híbrido. Em paralelo, gate humano de M2: proposta de remap 2-botoes por unidade (Ken primeiro) para os 9 comandos de super sem rota + estados needs_remap_decision da matriz — decisão do usuário, não do coordenador.

### Atribuição BlastEm do derrame (coordenador; ROM 8880a5e3, sessão blastem-sms-19333b0375e9439fb05bf7ce82c3390f, audit ok:true record_consistency_only)
Roteiro sms_blastem_sequence_v1 sms1/ntsc: warmup 300 + 4×550 = 2500 frames de VDP, sem input, precondição SMRT@0xC8E0 satisfeita, pin SHA da ROM confere. Probes lidos dos snapshots de RAM nos 5 limites:
- frame(ROM)=70/237/374/512/591 vs frames de VDP=300/850/1400/1950/2500 → **~23,6%: cada iteração do loop consome ~4,2 períodos de VBlank em tempo emulado**.
- vbl_total=71/238/375/513/592 e vbl_max=1: o ISR também conta 1/iteração nos DOIS emuladores — o 1:1 anterior não provava cabimento do corpo (coalesce por design do wait por flanco).
- vovf=48/159/293/430/509 → 69–86% dos frames terminam com contador <0xC0 (mesma ordem da sessão Emulicious: 92%); vline_min 0x2F→0x0B.
- Telemetria de stream: up satura em 255 (byte), stall satura em 255, evict=0, used 51–58 — a parede de streaming continua, agora secundária frente ao custo do corpo.
Veredito de atribuição: **derrame intrínseco à ROM** — reproduzido em segunda implementação sem throttle de render; a hipótese "déficit = ambiente" fica rebaixada a agravante. Limites: ciclo a ciclo BlastEm≠hardware; números não viram FPS de entrega nem qualidade; o perfil regional do corpo é o próximo medidor.
Consequência wave-4: orçamento de pares/VBlank não pode ser derivado desta ROM; primeiro o corpo cabe em 1 VBlank, depois o upload vira budget medido.

### Atribuição regional do corpo — wave-4b (sondas de flanco ISR, 2026-10-16)

Instrumento novo (sem tocar no wrapper, sem comandos brutos de debugger):
tick real de VBlank via hook de frame da SMSlib —
`SMS_setFrameInterruptHandler` (SMSlib.h:373 = autoridade #8; esta ROM não tem
PSGlib nem outro dono do hook). Escrita/leitura de 8 bits = atômicas no Z80.
Sondas em `probe_vbl_tick` (0xC8D7) amostradas nas fronteiras stream/lógica/
emissão; somas u16 de flancos por região em 0xC8D8/0xC8DA/0xC8DC. Inicializadas
no boot (L009: `__at` não é inicializado pelo crt0). 0xC8EF segue undeclared.

- ROM desta fase: `c8fd0939857d50e319d6a5336a1fcad432323b8a0fca8961d1d00153a51f2b36` (458752 B; cadeia 8880a5e3 → c8fd0939). Build OK; `audit_probe_corridor` veredito **pass** (44 sondas, folga 1616). Rebaixada a histórica pela wave-4c (cadeia completa e vereditos lá).
- Evidência: sessão BlastEm `out/evidence/blastem_wf_regional/blastem-sms-cc643a2c265c429bb14e95680b098cfd` (script `out/logs/blastem_wf_regional.json`, sms1/ntsc, warmup 300 + 4×550 = 2500 frames VDP; precondição SMRT 51424/`534d525401`; `audit_blastem_sms --require-current-tool` ok:true, escopo record_consistency_only).
- Snapshot final (004): iterações=592, vovf=510 (86,1% derrame, igual ao padrão anterior — o instrumento novo não mudou o comportamento), vline_min=1. Flancos: **stream=0**, **lógica=244**, **emissão/SAT=1649**. Média por iteração: stream 0.00, lógica 0.41, emissão 2.79 (corpo ≈3.20 flancos); resíduo ≈607 flancos (≈1.03/iter) caiu em `SMS_waitForVBlank` — período por iteração ≈4.23, consistente com a atribuição anterior (2500/592).
- Veredito de atribuição regional: **a região de emissão domina o corpo** (87,1% dos flancos: `SMS_initSprites` + preenchimento `line_count[DIAG_FLOOR]` + `emit_frame`×2 + espelhos/pool `used_pairs` + `SMS_copySpritestoSAT`). A parede de streaming é confirmada secundária: o teto de 1 par/VBlank nunca cruzou um flanco dentro da região de upload (stream=0 em 592 iterações). Lógica FSM ≈0.41 flanco/iter.
- Doutrina rebaixada em código: `probe_vblank_total`/`vbl_per_iter_max` (0xC820/0xC824) contam **iterações wakes** (flanco coalescido), não períodos — comentário em main.c:58 atualizado; período real = soma das arestas regionais + resíduo de espera.
- Limites: granularidade é flanco-a-flanco (frame), não ciclo a ciclo; custo após `copySpritestoSAT` fica no resíduo de espera, não registrado por região; somas lidas de snapshots com a ROM pausada (sem rasgo de leitura); ciclos BlastEm ≠ hardware; nenhum destes números é FPS de entrega nem qualidade.

Próxima ação (ramo causal estreitado): sub-atribuir a região de emissão com o mesmo mecanismo de tick (fronteiras: preenchimento `line_count`, `emit_frame` por lado, `used_pairs`+espelhos, `SMS_copySpritestoSAT`) — o alvo continua ser o corpo caber em 1 VBlank; então remedir o selo worst-frame para obter o orçamento real de pares/VBlank do scheduler do híbrido. **Executado nas fases 2–3 abaixo (wave-4c).**

### Redução da telemetria de emissão — wave-4c (2026-10-16)

Sub-atribuição fases 2–3 (mesmo tick; layout final sem sobreposição: D7 tick, D8-D9 lógica, DA-DB preenchimento, DC-DD `emit_frame`, DE-DF espelhos/pool+SAT; D0-D6 reservados às ferramentas de medida; 0xC8EF nunca declarado):

- Fase 2 (ROM `a25169f722f2d7c07e6b921dc445e68aa6b4ed218b7e1cabbe1383ff88f38846`; sessão `out/evidence/blastem_wf_regional2/blastem-sms-9f00ce3f41254661811efa46e6e8adab`; `audit_blastem_sms --require-current-tool` ok:true): `SMS_copySpritestoSAT` ≈0 (1 flanco em 592 iterações); o custo está inteiro na preparação de emissão (≈2.78 flancos/iter).
- Fase 3 (ROM `a58ae0e5ec68a5530c91558189b18430dfd37a970577d9255c93ab59fcc4ea94`; sessão `out/evidence/blastem_wf_regional3/blastem-sms-6c9f003f14584e05b6682ab048e7f8a5`; ok:true; snapshots reanalisados de `ram.bin` nesta data): 592 iter, vovf 509, flancos acumulados — lógica 243 (0,41/iter), preenchimento 51 (0,09), `emit_frame` 1581 (2,67), espelhos/pool+SAT 18 (0,03) → corpo ≈3,20 + resíduo de espera ≈1,03 ≈ período 4,23. Dominante isolado: o loop interno de 16 linhas por sprite em `emit_frame` (comparações signed-int + duas probes volatile atualizadas por linha) ≈ 16×N sprites/frame.

Redução (main.c): o loop interno virou **array de diferenças** (`line_diff`: +1 na entrada do sprite, −1 na saída se ainda abaixo do chão; duas escritas por sprite) mais **uma varredura unary de 160 linhas por frame**. Semântica preservada: `probe_over8_events` passa a contar linhas com contagem final ≥9 (incremento monótonico cruza o 9 exatamente uma vez por linha) e `probe_max_line` é o máximo final. Emissão visual intocada — todos os `SMS_addSpriteClipping` permanecem; o que se cortou foi telemetria de diagnóstico, não quadro do jogo.

- ROM ATUAL da linhagem até a wave-4e: `f8a137c4d7e2d8cf899b1417c1a33ad9b2c857c8a39247a67a88231f07ba8167` (458752 B; cadeia 8880a5e3 → c8fd0939 → a25169f7 → a58ae0e5 → 860453b0 → f921b815 → f8a137c4). `audit_probe_corridor` **pass** (45 sondas, folga 1616) em todas as ROMs 4c/4d/4e. Sessões (mesmo script de 2500 frames VDP, `audit_blastem_sms --require-current-tool` ok:true): `out/evidence/blastem_wf_regional4/blastem-sms-dcdbdb0814a24c3ea44aa2ad775476e1` (860453b0), `out/evidence/blastem_wf_regional5/blastem-sms-5ea1adc7e6d7479b92853a56315413a0` (f921b815, wave-4d) e `out/evidence/blastem_wf_regional6/blastem-sms-ac6b16828fe84ed998a420d701bbf7a6` (f8a137c4, wave-4e).
- Medida (snapshot final 004): iterações=**833** (vs 592 — throughput +41% nos mesmos 2500 frames), vovf=577 (69,3% de derrame vs 86,1%), vline_min=8 (vs 1). Flancos/iter acumulados: lógica 0,86, preenchimento 0,06, `emit_frame` **0,85**, espelhos/pool+SAT 0,13 → corpo ≈1,90 (vs 3,20). Cauda (snaps 003→004, 163 iter): corpo ≈2,33 com `emit_frame` 0,45 e lógica 1,62. A telemetria era ≈2/3 do custo anterior da emissão; o que sobe em `emit_frame` é custo real de motor (caminhada de metasprite + ~40 `SMS_addSpriteClipping`/frame + varredura).
- Wave-4d (f921b815; sessão regional5): fronteira redividida sem slots novos — a varredura unary (telemetria) mudou para a região de espelhos/pool+SAT, deixando DC-DD com **caminhada de metasprite + `SMS_addSpriteClipping` apenas**. Snapshot final: iter=864, vovf=695, flancos/iter — lógica 0,83, add-only **0,46**, pool+SAT+varredura 0,53 (varredura ≈0,41; base pool+SAT 0,13 da wave-4c), preenchimento 0,06 → corpo ≈1,87. Cauda (003→004, 177 iter): lógica 1,20, add-only 0,29, pool+varredura 0,61.
- Wave-4e (f8a137c4; sessão regional6): preenchimento (0,06/iter, medido e negligível) mergeado na região de emissão; DA-DB passou a medir o **bloco de step do script** como sub-região da lógica. Consistência inter-ondas: fill+adds(4e)=446 − addsonly(4d)=394 → preenchimento 52 flancos (≈0,06/iter, reproduzido); sweep+pool inalterado (459 vs 457); iterações idênticas (864). **Resultado novo: step=0 flancos em 864 iterações** — o bloco de passo do script nunca cruzou um flanco por si só; a lógica cauda-pesada (1,28 flancos/iter na cauda 003→004) está inteira em `stream_pending` + `advance_actor` + `request_pose`/`alloc_contiguous`. O slot DA-DB (step zerado) fica disponível para a sub-atribuição FSM da próxima onda.
- Decomposição honesta do custo de motor (sem telemetria de diagnóstico): lógica 0,83 + add-only 0,46 + espelhos/pool+SAT 0,13 ≈ **1,42 flancos/iter**; telemetria responde por ≈0,47. Ou seja: mesmo removida toda a sonda de scanline, o corpo da ROM de diagnóstico NÃO cabe em 1 VBlank — o maior bloco remanescente é a região de lógica (FSM + bloco de step do script), não a emissão. **Refinamento wave-4e: dentro da lógica, step≈0; o candidato é o trio de FSM/upload por iteração.**
- Achado estrutural concomitante: `probe_max_line`=13 no pior frame — dois atores nestas poses exigem >8 sprites/scanline (limite inferior t3 confirmado na ROM); `probe_omitted_sat` acumulado 58 (SAT cheia ⇒ omissões reais já acontecem no modo atual).
- Limites: flanco-a-flanco (frame), não ciclo a ciclo; ciclos BlastEm ≠ hardware; contador de wake continua contando iterações (doutrina rebaixada); comparação cauda×acumulado é sensível à posição do script FSM; `probe_max_line` lê 0 em snapshots intermediários de ambas as execuções (leitura não confiável dentro da janela, não promovida a conclusão; só o valor final 13 é usado); nenhum destes números é FPS de entrega nem qualidade; teto da ROM permanece `diagnostic_only`.

Próxima ação: (a) wave-4f — sub-atribuir a lógica no slot livre DA-DB (candidato: `advance_actor`×2 + `request_pose`×2, com `stream_pending` por diferença), pois o step foi medido e zerado; (b) conferir na fonte upstream o custo/semântica de `SMS_addSpriteClipping` vs `SMS_addSprite` (header: o plain retorna void/-1 e trunca na borda; a troca exige teste de equivalência visual no Emulicious antes, para não esconder omissão de borda); (c) só com corpo <1 flanco refazer o selo worst-frame (`measure_worst_frame`/Emulicious) para fixar o orçamento real de pares/VBlank do scheduler do híbrido. O achado `probe_max_line`=13 (duas poses >8 sprites/scanline, com omissões reais na SAT) alimenta a decisão humana BG/híbrido vs ajuste de escala. **→ (a) e (b) executados na wave-4f abaixo; (c) segue condicionado.**

### Sub-atribuição da lógica — wave-4f (2026-10-16)

Trocada de significado do slot DA-DB: o bloco de step (medido 0 flancos na wave-4e) saiu da instrumentação (amostra `t1` removida de main.c; nenhuma mudança de comportamento além de poucas instruções) e `probe_reg_actors_edges` passou a medir `advance_actor`×2 + `request_pose`×2; `stream_pending` fica por diferença (lógica − atores, com step≈0 já medido).

- ROM ATUAL da linhagem: `c89ef55b3adbf3fd9d2c779248642478380010ec5c2ce4f61542c76c7b054a79` (458752 B; cadeia … f8a137c4 → c89ef55b). Build OK; `audit_probe_corridor` veredito **pass** (44→45 sondas inalterado, folga 1616).
- Evidência: sessão BlastEm `out/evidence/blastem_wf_regional7/blastem-sms-5d5ec96835b647eab5cda059792e1f6f` (mesmo script sms1/ntsc de 2500 frames VDP, warmup 300 + 4×550; precondição SMRT ok; `audit_blastem_sms --require-current-tool` ok:true, escopo record_consistency_only).
- Snapshot final (004): iterações=863, vovf=693 (80,3%), vline_min=3 (não promovido a conclusão — sensível à fase do coalesce). Flancos acumulados: lógica 717, **atores 716**, emissão (initSprites+preenchimento+add-only) 446, varredura+espelhos/pool+SAT 458. Por iteração: atores 0,83, adição 0,52, pool+varredura 0,53 → corpo ≈1,88 flancos/iter; período 2500/863 ≈ 2,90.
- **Veredito (diferença lógica−atores = 1 flanco em 863 iterações; cauda 003→004: 213 vs 213, diferença 0): `stream_pending` cruza ≈0 flancos — a lógica é inteiramente o avanço de atores + request de pose (`advance_actor`×2 + `request_pose`×2 + `alloc_contiguous` na troca de pose).** A parede de streaming (evidência #2) é de capacidade de VRAM/pool e de duração da fila, NÃO de CPU por VBlank no loop. Isso estreita o remediável: o bloco dominante do motor passou a ser a FSM de atores.
- Consistência inter-ondas (neutralidade do instrumento): região de emissão 446 idêntica à wave-4e; pool 458 vs 459 (4e) vs 457 (4d); iterações 863 vs 864 (−1 pela remoção da amostra t1 — micro-derriva do coalesce caótico, nenhum claim de comportamento).
- Decomposição honesta atualizada: motor ≈ atores 0,83 + add-only+initSprites+fill 0,52 + base pool/SAT 0,13 ≈ **1,48 flancos/iter** (varredura unary 0,41 é telemetria pura). Corpo continua >1 VBlank; dois blocos acionáveis: FSM de atores/pose e caminhada de metasprite com adições.
- Item (b) conferido na fonte upstream (autoridade #8): `SMS_addSprite_f` é asm `__naked` com custo documentado no comentário do próprio fonte — "// 1st sdcccall(1) ASM version: 162 CPU cycles" (SMSlib_sprite.c:130) — e só rejeita Y==0xD1; `SMS_addSpriteClipping` é C puro com 7 predicados de recorte lendo `clipWin_x0/y0/x1/y1` + `spritesWidth/Height` externs com aritmética signed 16-bit por sprite (SMSlib_spriteClip.c:27–41). Hipótese medida só em ROM: o clip é várias vezes mais caro por adição. **A troca NÃO está aprovada**: plain trunca x por `&0xff` em vez de omitir — exige teste de equivalência visual no Emulicious (sem esconder omissão de borda) antes de qualquer swap; granularidade de flanco atual não separa clip-vs-escrita.

Próxima ação (wave-4g, ramo estreitado): (a') separar `advance_actor` de `request_pose`/`alloc_contiguous` **sem slots novos** (D0-D6 continuam reservados às ferramentas) — dois builds determinísticos com o significado de DA-DB alternado, cada um medindo um dos meios e o outro por diferença, ambos reauditados no corredor e no BlastEm; (b') gate de equivalência visual Emulicious para clip→plain (só troca se nenhum sprite de borda mudar de visibilidade entre as capturas); (c) permanece: selo worst-frame apenas com corpo <1 flanco. Decisão humana pendente (BG/híbrido vs ajuste de escala) segue alimentada por maxline=13 e omitted_sat=58.

### Wave-4g-1: o bloco dominante é request_pose/alloc_contiguous (2026-10-16)

Execução de (a') pelo lado `advance_actor`: DA-DB voltou a ser reamostrado, agora envolvendo **apenas** `advance_actor`×2; `request_pose`×2 ficou fora do wrap (continua na lógica). ROM ATUAL da linhagem: `870d8078867a9cc556f97931d695f1eac68ecbe4c799dc15ab741e514aeef88f` (458752 B; cadeia … c89ef55b → 870d8078; main.c permanece neste estado 4g-1). Build OK; `audit_probe_corridor` **pass** (45 sondas, folga 1616). Sessão BlastEm `out/evidence/blastem_wf_regional8/blastem-sms-9a3b5f395fc44395a00b708927fd12f3` (`--require-current-tool` ok:true, record_consistency_only).

- Snapshot final (004): iterações=863, vovf=693, lógica **717**, atores(=advance_actor×2) **0**, emissão **446**, pool+varredura **458**, maxline 13 — lógica/emissão/pool/iterações/vovf **bit-idênticos** à wave-4f (mesmo script determinístico), o que funda a subtração entre as duas sessões.
- **Veredito:** `advance_actor`×2 cruza 0 flancos em 863 iterações; ~716 flancos (717 − 0 − 1 de stream medido na 4f) estão em `request_pose`×2 + `alloc_contiguous` + ramo do loop, pagos nos frames de TROCA de pose. O instrumento não resolve durações sub-flanco: "0" significa "nunca cruzou um flanco dentro do wrap", não "custo zero".
- Interpretação causal: o candidato mecânico é a varredura first-fit de intervalo contíguo no bitmap do pool (128 pares) a cada pose nova — O(pool) por troca, em espículas; `stream_pending` (1 flanco) e o avanço de animação (0 flancos) são inocentes em CPU por VBlank. A parede de streaming permanece parede de capacidade/duração, não de ciclo.
- Consequência para o motor (M1+): a FSM de requisição de pose precisa de alocação com cursor/executável pré-computado (runs livres cacheados, slots fixos por lutador), não varredura linear por troca. Isso é decisão de design do runtime, registrada aqui por medição — não aplicada ainda.
- (b') segue pendente como gate: clip→plain só com equivalência visual Emulicious; a hipótese de custo (asm naked 162 ciclos vs C com 7 predicados) é do fonte, não medida em ROM.

Próxima ação: (a'‑confirm) opcional: wrap direto de `request_pose` (esperado ≈716 com timing idêntico) para fechar o triangulo por medida direta em vez de subtração; (b') gate Emulicious clip→plain; depois redução real do `alloc_contiguous` (cursor/slot fixo) em candidata, remedir corpo; selo worst-frame (c) só com corpo <1 flanco. Decisão humana BG/híbrido vs escala segue alimentada por maxline=13 + omitted_sat=58.

### Wave-4h: memo de falha no request_pose — hipótese "retry futile dominante" rebaixada (2026-10-16)

Candidata de motor aplicada em main.c (nada de telemetria): memoização por `pool_epoch` (incrementado em toda liberação/ocupação real do bitmap: `cache_invalidate` que limpou bits e `alloc_contiguous` que marcou) + `fail_epoch[2]/fail_size[2]`. Se o lado falhou a escada inteira no bitmap atual e o bitmap não mudou desde então, a escada é pulada e `probe_stall_frames` continua contando o frame de stall — retry é deterministamente fútil sem mudança de bitmap, logo o memo é equivalente por construção no estado que importa.

- ROM ATUAL da linhagem: `089bdea2420bb5e49ca28f466e321101180d244ecd75797ed7b01362426f2953` (458752 B; cadeia … 870d8078 → 089bdea2). Build OK; `audit_probe_corridor` **pass** (45 sondas, folga 1616→1611 pelas 3 statics novas em DATA). Sessão BlastEm `out/evidence/blastem_wf_regional9/blastem-sms-501dc4a3b43747188fd0a0debffd6f95` (`--require-current-tool`, errors [], record_consistency_only).
- Medida (004): iterações=938 (vs 863, +8,7% no mesmo fôlego de 2500 frames VDP), vovf=929 (99% — não promovido: a fase amostral do contador de derrame mudou de posição com o throughput; só tendência), lógica 721 (0,83→**0,77 flancos/iter**, −7,5%), atores 0 (wrap 4g-1 preservado), emissão 437, pool+varredura 388 (vs 458 — re-distribuição de fase, não claim).
- **Veredito honesto: o memo NÃO derrubou a região de lógica.** Em regime estacionário o epoch muda quase toda iteração (trocas de pose bem-sucedidas + invalidações liberam bits continuamente), então o memo quase não acerta. Consequência causal: o custo de ~0,8 flanco/iter em `request_pose` **não é retry fútil de stall** — é o churn real de troca de pose (escaneamento first-fit + ladder de evict) pago em cada mudança, expressando a parede de capacidade do pool como ciclos de CPU. A redução verdadeira exige ou (i) política de alocação O(1) (slots fixos por lutador / runs cacheados) ou (ii) aliviar a saturação (poses menores via ajuste de escala, ou híbrido-BG) — ambos são **decisão humana/autorização**, não micro-otimização silenciosa.
- O memo fica no código: é equivalente-by-construction, cortou o pior caso de stall puro (sem mudança de bitmap o retry não repete a escada) e é parte do desenho que o motor M1+ vai exigir; nenhum número dele é claim de entrega. Teto permanece `diagnostic_only`.

Próxima ação: (a) levar a medição 4h/4g à decisão humana pendente — os números sustentam as duas alavancas (slots fixos por lutador no lowering de dados vs ajuste de escala/híbrido-BG) com custo medido de cada lado da balança; (b') gate Emulicious clip→plain ainda aberto; (c) selo worst-frame segue condicionado a corpo <1 flanco. Branches independentes autorizados que não dependem do corpo: M2 gameplay Ken/Ken (colisão/hitstun) na linhagem de ROM e reparo do manifest de paleta P2.

### Wave-4i: alocador por extensões derruba a região de lógica abaixo da resolução do instrumento (2026-10-16)

Troca do first-fit de bitmap (`pair_bitmap[16]`, varredura de até 128 pares por chamada, até 3 chamadas na escada) por **alocador por extensões** sobre o conjunto vivo dos 4 slots (corrente/pendente × 2 lados): candidatos = {0} ∪ {fim de cada bloco vivo}, menor candidato sem sobreposição. Equivalência por construção provada (menor início livre ou é 0 ou é o fim de um bloco) e testada por **teste diferencial offline: 200.000 casos aleatórios (layouts não sobrepostos × n∈[1,39]) — 0 divergências de base/falha** contra a simulação do bitmap antigo. (A primeira rodada do teste acusou divergências por bug na simulação Python do algoritmo antigo, corrigida e refeita antes de qualquer conclusão.) RAM: −16 B (bitmap eliminado); `used_pairs` vira soma dos slots.

- ROM ATUAL da linhagem: `e7834679f2e9c4c5558c55d17046f2dc7c39c353cbc0af4ee5fbdd782c9aeea8` (458752 B; cadeia … 089bdea2 → e7834679). `audit_probe_corridor` **pass** (45 sondas, folga 1611→1627). Build OK. Sessão BlastEm `out/evidence/blastem_wf_regional10/blastem-sms-05284f753a2f4e5784567810f67ba5be` (`--require-current-tool`, errors [], record_consistency_only; mesmo script de 2500 frames VDP das ondas 4c–4h).
- Medida (snapshot final 004): iter=**1195** (vs 938 na 4h, **+27,4%** de throughput nos mesmos 2500 frames; vs 863 na 4f, +38,5%); período 2,09 frames/iter (vs 2,67). Flancos: lógica=**0** e atores=0 em toda a sessão; emissão=505 (0,423/iter); pool+SAT+varredura=786 (0,658/iter). Duração corporal acumulada caiu de 1,66 (4h) para **1,08 flancos/iter** — o colapso da lógica é corroborado independentemente pelo throughput, não apenas pela leitura 0.
- **Leitura honesta do 0:** o instrumento não resolve durações abaixo de ~1 flanco/iter; com lógica esperada em ~200–800 ciclos/iter, 0 flancos em 1195 iterações é compatível mas o valor exato ficaria em ≈8–12 flancos acumulados — registrado como **abaixo da resolução**, nunca como custo zero.
- Veredito causal: o custo dominante de `request_pose`/`alloc_contiguous` era o **mecanismo** (varredura + marcação de bits sob saturação/fragmentação), não os resultados de alocação nem o churn em si. A parede de capacidade segue real e inalterada: `used_max`=128 já no snapshot 000, evict=32, stall=80 — os números que alimentam a decisão humana BG/híbrido vs escala permanecem os mesmos (maxline final 13; omitted_sat acumulado).
- Decomposição derivada (por subtração, NÃO medida diretamente): corpo sem telemetria ≈ emissão 0,42 + base pool/SAT (0,66 − varredura unary ≈0,41 estimada das ondas 4c/4d) ≈ **0,67 flancos/iter < 1 VBlank**. Se confirmado por medida direta, o núcleo do motor cabe em um VBlank e a condição de abertura do selo worst-frame (c) muda de estado.
- Limites: flanco-a-flanco; ciclos BlastEm ≠ hardware; contadores de amostragem sensíveis à fase; `probe_max_line` não confiável em snapshots intermediários (padrão das ondas anteriores); sweep ≈0,41 é estimativa herdada, não remedida.

Próxima ação: (a) **wave-4j** — variante com a varredura unary desligada (telemetria `over8`/`maxline` desaparece desta ROM; o achado estrutural maxline=13 já está registrado nas ondas 4c–4h) para medir o corpo não-telemétrico **diretamente** no slot livre DA-DB; corpo <1 flanco medido → abre (c) selo worst-frame/Emulicious do orçamento real de pares/VBlank; (b') gate Emulicious clip→plain segue aberto; (d) decisão humana BG/híbrido vs ajuste de escala segue pendente — agora com dado novo: a parede é de composição (limite físico ≤8/scanline com maxline=13), não mais de CPU da emissão. Ramo independente autorizado em espera: M2 gameplay Ken/Ken (colisão/hitstun).
### Wave-4j: partição completa mede o motor sem telemetria em ~0,43 flancos/iter (<1 VBlank) (2026-10-16)

Reordenação do wrap de VBlank sem mudança de comportamento: clear `line_diff` + varredura unary (telemetria `over8`/`maxline`) medidos **diretamente** no slot DA-DB; o wrap DE-DF passa a começar **depois** da varredura e mede apenas espelhos/pool + `SMS_copySpritestoSAT`; DC-DD segue sendo initSprites + caminhada de metasprite + `SMS_addSpriteClipping`. Resultado: partição completa sem dupla contagem — motor = DC-DD + DE-DF, telemetria = DA-DB.

- ROM ATUAL da linhagem: `e9a3a1bd66a97696d9b07e86977b147a4b5ec94fe9a72fa2b0195da0255fe190` (458752 B; cadeia … e7834679 → e9a3a1bd). `audit_probe_corridor` **pass** (45 sondas, folga 1627; executado da raiz do workspace). Sessão BlastEm `out/evidence/blastem_wf_regional11/blastem-sms-8974e38f17e0470094f3a4753edc3526` (`--require-current-tool`, ok:true, errors [], record_consistency_only; mesmo script de 2500 frames VDP das ondas 4c–4i). Parser rotulado persistido em `out/logs/wf_regional_parse.py`.
- Medida (snapshot final 004): iter=**1190** (vs 1195 na 4i — throughput equivalente, como esperado de uma mudança de ponto de medição, não de comportamento). Flancos acumulados: lógica=**0**; telemetria clear+varredura=**783** (0,658/iter); emissão=**504** (0,424/iter); corpo pool+SAT=**8** (0,007/iter). Soma 1,089/iter casa com os 1,08 da 4i — partição sem perda nem dupla contagem.
- **Veredito (agora MEDIDO, não derivado): motor sem telemetria = 0,424 + 0,007 ≈ 0,43 flancos/iter < 1 VBlank.** A estimativa por subtração da 4i (≈0,67) superestimou: a varredura unary vale ~0,66 (estimada 0,41) e a base pool+`copySpritestoSAT` é quase invisível ao instrumento (estimada 0,25, medida ~0,01). Leitura honesta: 8 flancos em 1190 iterações é **abaixo da resolução por iteração**, não custo zero — corroborado pelo throughput igual ao da 4i com o mesmo trabalho corporal.
- Custo dominante do frame passa a ser a **própria telemetria diagnóstica** (0,658/iter): ela existe para medir, não para jogar. A ROM de entrega sem os contadores `over8`/`maxline` fica com corpo ≈0,43 flancos/iter + lógica (abaixo da resolução desde a 4i).
- Parede de capacidade inalterada e alimentando a decisão humana: `used_max`=128 desde o snap 000, evict=32, stall=80, `probe_max_line`=13 (snap 001), over8 acumulado 19723. Composição (≤8 sprites/scanline) continua sendo o blocker estrutural; CPU de emissão está demonstradamente folgada.
- Limites: flanco-a-flanco; ciclos BlastEm ≠ hardware; contadores de amostragem sensíveis à fase; `probe_max_line` não confiável em snapshots intermediários.
- Abertura de gate: condição (c) da 4i (**corpo <1 flanco medido**) está satisfeita → selo worst-frame do orçamento real de pares/VBlank para o scheduler streaming está aberto, junto do gate (b') Emulicious clip→plain.

Próxima ação: (c) selo worst-frame/Emulicious do orçamento real de pares/VBlank; (b') gate Emulicious clip→plain antes de qualquer troca de `SMS_addSpriteClipping`; (d) decisão humana BG/híbrido vs ajuste de escala — reancorada: o gargalo é de composição, com CPU do motor medida em ~0,43 flanco/iter; ramo independente autorizado em espera: M2 gameplay Ken/Ken (colisão/hitstun).
### Wave-4k: re-selo worst-frame na ROM wave-4j — derramou; correção de unidade flanco≠VBlank (2026-10-16)

`measure_worst_frame` (`--self-check` OK) em sessão privada isolated `40755d7124f34bcf81a19c7c1ae24f7f`, ROM `e9a3a1bd…` (sha confere no artefato), janela 50 s/3000 frames, probe-base 0xC800, sem DAP global; sessão fechada após leitura. Artefato: `out/evidence/sessions/40755d71…/worst_frame/wf_m2_reseal.json`.

- **Veredito: derramou. vovf_delta=2954/3000 frames (98,5%), vline_min=1, janela_selada=true.** Emulicious rodou ~17694 frames ROM em ~350 s de parede (~50,5 fps de emulação) — sem artefato de throttle do host nesta run (ao contrário da 4a: 4459 frames em 300 s).
- **Correção honesta (reivindicação da wave-4j rebaixada):** a condição de abertura de (c) foi formulada com unidade errada. `probe_vbl_tick` incrementa na entrada de VBlank: **1 flanco = período de um frame inteiro (~16,7 ms NTSC), não a duração do VBlank (~2 ms ≈ 0,12 flanco)**. Logo "motor ≈0,43 flanco/iter" ≈ 7,2 ms/iter de corpo médio — ~3,7× a duração do VBlank. A partição 4j continua válida como medida de DISTRIBUIÇÃO de custo entre regiões (telemetria 0,658 / emissão 0,424 / pool 0,007 flancos/iter, soma 1,089 casa com throughput); o que ela NÃO prova — e o selo agora mede — é folga dentro do VBlank. As ondas 4i/4j não abrem (c); a fórmula correta do gate sempre foi o selo worst-frame direto.
- Comparação de selos na mesma janela: 4a (ROM 8880a5e3, corpo 4,2 flancos/iter): derramou 2758/3000 (91,9%), frames finais 4459 (throttle do host presente). 4k (ROM e9a3a1bd, corpo 1,089 flancos/iter): derramou 2954/3000 (98,5%), frames finais 17694 (emulação ~10× mais rápida). A queda de corpo não reduziu o percentual de derrame porque a ROM de diagnóstico faz TODO o trabalho do frame (lógica+emissão+telemetria) após `waitVBlank` — o instrumento foi construído para atribuir custo regional, não para caber em VBlank; isto é declaração de escopo da ROM, não regressão do motor.
- **Números que o selo entrega ao scheduler (orçamento real):** com telemetria removida, corpo do motor ≈ 7,2 ms/iter medidos por distribuição (1.190 iters em 2.500 frames no BlastEm, edge-resolução), ainda > VBlank de ~2 ms ⇒ o streaming precisa fatiar construção de metasprites/preparação em orçamento de VBlank por frame, não assumir o corpo inteiro por VBlank. A decisão humana (d) BG/híbrido vs escala segue alimentada por maxline=13/omitted_sat/used_max=128 — parede de composição inalterada.
- Limites: flanco-a-flanco; ciclos BlastEm/Emulicious ≠ hardware; vline_min é extremal sensível à fase; veredito do selo vale para a ROM instrumentada (`diagnostic_only`), não para a ROM de entrega futura sem sondas.

Próxima ação: (b') gate Emulicious clip→plain segue aberto; o selo em ROM de entrega só tem significado após remover a telemetria diagnóstica (variante wave-4l sem probes over8/maxline + VCounter por frame) — é a medida que fecha o orçamento de pares/VBlank do scheduler; ramo independente M2 gameplay Ken/Ken em espera; decisão humana (d) reancorada pelos números acima.

### Wave-4l: selo worst-frame na ROM SEM telemetria diagnóstica — derramou 2456/3000; gate (c) ainda fechado (2026-10-16)

Fontes: `src/main.c` com chave local `#define LUTA_DIAG_TELEMETRY 0` (evita o blocker registrado de `build_inner.py` não aceitar `-D` por projeto; curadoria de wrapper exigiria aprovação humana). Cortada do caminho quente: hook do ISR de tick, wraps de região, clear+varredura de `line_diff` (160 entradas/iter), manutenção de diffs em `emit_frame`, bloco de pacing. Mantidas as sondas do contrato de selo (SMRT/fespelho, vline/vovf/vline_min/phase/worst_done). Corredor `audit_probe_corridor`: pass, 45 sondas, folga 1787 (`out/logs/`).
ROM `ee07d9a6e06c720d884271f3f766992c0fa24dbbf4b53bd5b1e97b84f2e3635f` (458.752 B; cadeia … e7834679 → e9a3a1bd → **ee07d9a6 atual**); build intermediário 76e3d448 reprovado pelo corredor e substituído.
Selo: `measure_worst_frame` (`--self-check` OK) em sessão privada isolated `2990233e89c44c76a9d65c4c716a0a18`, 300 s sem leituras + janela 50 s/3000 frames, leitura única pós-`done=1`; artefato `out/evidence/sessions/2990233e…/worst_frame/wf_m4l_notelem.json`; `rom_sha256` do artefato confere com o disco; sessão fechada após leitura.

- **Veredito: derramou. vovf_delta=2456/3000 (81,9%), vline_min=0, janela_selada=true, frames ROM final 16073.**
- Comparação direta com 4k (mesma janela, ROM com telemetria): 2954→2456 derramou (−498 frames, −16,6 pp). Direção e ordem de grandeza consistentes com a partição 4j (telemetria ≈0,658 de 1,089 flancos/iter): a telemetria diagnóstico era ~17% dos frames derramando; o corpo restante ainda termina no display ativo em ~4 de cada 5 frames. `vline_min` 1→0 é extremal sensível à fase — não se atribui nada a ele.
- **Consequência para (c): o gate de orçamento pares/VBlank do scheduler segue fechado.** Um selo positivo não virá desta ROM: a arquitetura do instrumento executa TODO o trabalho após `waitVBlank` (declaração de escopo da 4k) e o corpo de emissão ≈7 ms (distribuição 4j) > VBlank ≈2 ms. O orçamento de pares/VBlank só se mede numa ROM com loop de entrega (trabalho no display ativo, uploads dentro de VBlank) — que É a arquitetura do híbrido-BG com scheduler, não mais uma variante deste instrumento.
- Limites: flanco-a-flanco; host com carga 8–17 sem controle pareado nesta run; veredito vale para a ROM instrumentada (`diagnostic_only`); a variante sem telemetria não vira claim de fps/entrega.
- Lições registradas (também na memória persistente do workspace): (1) SDCC descarta símbolos `__at` nunca referenciados do `.map`, e `audit_probe_corridor` lê o texto-fonte bruto (declarações dentro de `#if` desabilitado contam) → reprovação `sonda_sumida`; solução sem custo no caminho quente: um RMW único `probe_x = probe_x;` por sonda órfã, fora do loop. (2) Jamá rebuildar `out/rom/*.sms` com selo em andamento: a ferramenta recheca o SHA do arquivo em disco no fim e o selo é perdido.

Próxima ação: (b') gate Emulicious clip→plain; ramo M3-prep — derivação mecânica do config Ryu/Ryu da matriz t4 (espelho do padrão `out/config/ken_pilot_diag.json`, nunca hand-authored) e `versus-cut` host-side; M2 gameplay Ken/Ken e o budget real do scheduler permanecem na arquitetura de entrega híbrido-BG (loop com uploads em VBlank), onde o selo volta a ter significado. Decisões humanas inalteradas: remapeamento 2-botoes por unidade; escala/arte se o híbrido não bastar.

### M3-prep: pacote Ryu/Ryu derivado mecânicamente da matriz t4 — status `generated` (2026-10-16)

Fontes: `doc/22-intake-doador.json` (ryu.zip sha `6db7e29d82fff1034e8c2ddab600e500fe8377ebdeef9b626fd6b580b812300d`, def `ryu/ryu.def` sha `edb3db7714b5fc47f34f702eb06c166bfec039cc96a270288a3f8050b40a01e8`, common1_in_archive=false) + `out/semantics/reachability_matrix.json` (matriz t4 validada). Config mecânico `out/config/ryu_pilot_diag.json` sha256 `7aa3fb362a6beb03c1267ac2a2b0c585d72eedb4be356903989e68a38813968e`; produção por 1 produtor isolado em leases disjuntos (`out/config/`, `out/generated/ryu_ryu_diag/`, `out/logs/ryu_derivation_*`); `versus-cut` attempt-1 OK; sem ROM construída neste lote.

- Pares de poses mecânicos (da matriz, não hand-authored): idle st0/anim0 (forge_proxy), walk_f anim20, walk_b anim21 (st18/19 `hard_absent_no_proxy` — anims condicionais), jump st50/anim41 (via common_forge.cns), crouch st11, guard st120, punch st260/anim260 (a), hp st280 (c), kick st200 (x), hk st240 (z), special st1000/anim1000 (cmd `SP1_w` — token real do ryu.cmd, não inventado), ko st170 (unmapped_orphan do bloque LOSE). Escala target 80px em [72,88]; paleta `ryu02` (ryu.def pal1→ryu02.act; nome real, sem inventar "ryu1"); P1 entradas 1–7, P2 9–15, índice 0 transparente.
- Generado em `out/generated/ryu_ryu_diag/`: `versus_scene_runtime.h` (sha `b106b578…`; símbolos `P1_RYU_*`/`P2_RYU_*` — 2108 ocorrências ryu, 0 ken), `versus_scene_manifest.json` (sha `25c3b127…`), `fight_runtime_data.h` (sha `db3f08dc…`, prefixo neutro `P1_CUT_*`/`P2_CUT_*`), `fight_runtime_data_manifest.json` (sha `ab6f60e1…`), `fight_input_profile.h` (sha `b4fe4761…`), `versus_scene_banks_02.bin` 409.600 B (sha `03ee4d9e…`), 25 banks 16K + diretórios p1_ken/ p2_ryu/.
- Verificação do coordenador (confiança, mas checar): manifest `source_sha256` de AMBOS slots = sha do ryu.zip (prova de conteúdo Ryu nos dois lutadores); `source_def` = `ryu/ryu.def` nos dois; `bank_reuse` método `exact_16k_page_bytes` com deduplicação exata (p2→p1) — esperado num espelho Ryu/Ryu.
- **Quirk declarado do gerador (nomenclatura, não dados):** arquivos e chaves de lutador no manifest usam o rotulo `p1_ken`/`ken_scene_bankNN.bin` mesmo quando p1 é Ryu — convenção de nome hardcoded da era Ken no `versus-cut` (`mugen2sms/generators/smsdev`). Os bytes provam Ryu (shas de fonte + símbolos); nada no runtime depende do nome de arquivo além do `path` no próprio manifest. Consertar o prefixo é curadoria de wrapper → exige aprovação humana; NÃO editado. Registrado para não ser lido como dados Ken.
- Fronteras honestas herdadas: special/projétil classificado `unsupported` no manifest (`projectile entities are not implemented in the fight runtime`) e `FIGHT_CMD_SPECIAL_UNSUPPORTED` no `fight_runtime_data.h` — o comando SP1_w existe no config mas o runtime FSM atual não executa projétil; walk depende de common_forge.cns (adaptação, não equivalência); 18 estados ryu permanecem `needs_remap_decision` (gate humano 2-botões); kinks de source_limitations registrados no config.
- Status vocabulário: **generated** — NÃO buildado, NÃO testado_em_emulador; ceiling do claim `diagnostic_only`. Consumo previsto: ligar o pacote como fonte de uma ROM de diagnóstico Ryu/Ryu no mesmo padrão consumidor da Ken/Ken (M0/M1-diag), o que pertence ao próximo lote M3.

Próxima ação: (b') gate Emulicious clip→plain; ligar pacote Ryu/Ryu em ROM de diagnóstico (padrão consumidor Ken/Ken) quando houver janela de build; cruzados Ken/Ryu e Ryu/Ken após; gates humanos intactos (remepeamento 2-botoes por unidade, ambiente sem throttle para fps, escala/arte se híbrido não bastar).

### M3: ROM Ryu/Ryu v023 boots, renderiza e é determinística — veredito "boot preto" era artefato do instrumento GUI (2026-10-16)

Fontes: ROM `changelog/roms/build_v023/rom.sms` sha `e5834144…` (458.752 B; controlador A/B: v022 Ken `ee07d9a6…`); pacote gerado `out/generated/ryu_ryu_diag/` (seção M3-prep). Instrumento: sessões privadas `isolated.py` (Xvfb próprio, framebuffer 256×192 via bridge, sem compositor nem foco de janela).

- **Veredito M3: boot comprovado.** Em execução contínua (~6 s), `fb_v023.png` (sha `c59ed657…`) mostra os dois lutadores Ryu renderizados (variância de luma 1121,3); `fb_v022.png` (`67bcb20b…`, 1089,5) mostra Ken/Ken — PNGs distintos entre ROMs, prova de conteúdo real por ROM. Decode do corredor de sondas ao vivo (sessão anterior): probe_frame avançando, uploaded_pairs=227, boot_p2_fit=1, displayOn executado — coerente com a tela.
- **Determinismo não-vacuo:** três sessões independentes com `step 120` exato → framebuffer byte-idêntico `12c57d1ac3f3…` (`det120_r1/r2`, `stepcheck_f120`), variância 1117,2 (conteúdo presente, não tela congelada em frame 0). Limites: stepped prova sequência/determinismo, não fps; quadro mostra estado mid-stream do pipeline (poses ainda em upload; stall ≈1,7/frame medido no corredor) — nada aqui é claim de qualidade visual; teto `diagnostic_only` inalterado.
- **Retratação registrada (sem mascarar):** o veredito anterior "Ryu renderiza preto" e os PASS/FAIL de `capture_evidence` desta tarde foram produzidos pelo canal GUI (janela do Emulicious por nome + `import`/`spectacle`). Com ZERO outras instâncias, a MESMA Ken v022 que antes PASSAVA passou a FAILAR preta (`clean3_ken` = `clean3_ryu` = sha `2c4786a6…`): o instrumento de janela está instável sob o compositor KDE/Wayland (janela capturada sem o framebuffer do jogo). Consequência: capturas GUI desta sessão não sustentam veredito algum sobre nenhuma das duas ROMs; apenas o canal bridge é confiável nestas condições.
- **Defeitos de instrumento descobertos (curadoria de wrapper — exige aprovação humana, NÃO corrigido aqui):** (1) `capture_evidence.py` encontra janela por nome e não detecta render ausente → deveria falhar como ferramenta, não emitir veredito sobre a ROM; (2) `audit_deterministic_boot.py` estoura `TimeoutExpired` cru ao fechar o Emulicious GUI (traceback, sem veredito); (3) `isolated.py capture --name` exige sufixo `.png` e rejeita com mensagem opaca ("bridge rejected command"); (4) `isolated.py step` pode falhar silenciosamente se o chamador engolir stderr (guard de rota de áudio) — nunca redirecionar saída de step/check.
- Extensão da lição §46/L057: janelas de sessão isolada (bwrap) e capturas GUI compartilham o título "Emulicious"; sob compositor, a captura por nome pode congelar num framebuffer preto OU capturar janela alheia — evidência GUI exige hash-cross-check entre ROMs distintas antes de sustentar qualquer veredito.

Próxima ação: cruzados Ken/Ryu e Ryu/Ken (mesmo padrão bridge: step-N ×2 sessões + contínua, hashes distintos por ROM); (b') gate clip→plain deve ser re-medido pelo canal bridge, não GUI; decisão humana (d) BG/híbrido segue; curadoria wrapper (4 defeitos de instrumento acima) aguarda aprovação humana.

### M4: cruzados Ken/Ryu (v024) e Ryu/Ken (v025) — boot/render/determinismo provados via bridge; migração de header 16KB→32KB (2026-10-16)

Fontes: pacotes versus-cut derivados mecanicamente do intake congelado — `out/generated/ken_ryu_cross/` (manifest sha `8db58115…`, banks `608c81dd…`) e `out/generated/ryu_ken_cross/` (manifest sha `d2cdf2c7…`, banks `3af7a307…`); relatório de derivação `out/logs/cross_derivation_report.txt`. Cada cruzado soma os dois conjuntos de poses sem deduplicação (Ken 24 + Ryu 25 = 49 banks de 16K; 93 poses no total). ROMs: `changelog/roms/build_v024/rom.sms` sha `870da893117cc6558e581d5d6c77d99a623789e5f9d652623c931e1247423e7f` (Ken/Ryu) e `build_v025/rom.sms` sha `bd144ee613c0ed1469f933ee255d06a435ee5045b3b10f60266e06e903d71f3f` (Ryu/Ken), ambas 851.968 B = 52 páginas (2 páginas de código não-bancado + 49 banks de tiles em 2..50 + 1 página de pad), `-mbank ...:0:49:2`.

- **Descoberta de capacidade (causa do 1º build falhar):** o versus-cut compila TODAS as tabelas const de metasprite/pose na imagem linkada; com um lutador (45–48 poses) ela cabia nos 16 KB do par de header `*_16KB` (SDSC @0x3FE0), mas com dois lutadores (93 poses) o `_CODE` chegou a 0x4CBC — overflow de ~3.250 B, e o makesms recusa ihx >16 KB com "Fatal: Bank 0 overflow" independentemente de `-pm`/`-mbank`. Correção no consumidor (sem tocar wrapper/núcleo): migração para o par de header 32 KB `SMS_EMBED_SEGA_ROM_HEADER` + `SMS_EMBED_SDSC_HEADER_AUTO_DATE` (SDSC @0x7FE0; macros verificadas em SMSlib.h, autoridade #8), que é exatamente a política documentada em `sdk/README.md` ("código não-bancado restrito aos primeiros 32KB") e na skill `sms-banking-header`. `SMS_mapROMBank(n)` só move o slot $8000, portanto dados em bank 1 ($4000–$7FFF) permanecem estaticamente visíveis no boot e o streaming de tiles (leitura em 0x8000+off) é intacto. Se um roster futuro estourar 32 KB, o próximo degrau documentado é const-banking (`--constseg BANKn`), que é curadoria de wrapper/generator → aprovação humana.
- **Veredito v024 (Ken/Ryu): boot + render + determinismo comprovados.** Bridge (sessões `e50dd555…`/`33f93515…`/`8c6abd2e…`; log `out/logs/m4_bridge_proof_ken_ryu.log`): `step 120` em duas sessões novas → PNG byte-idêntico `584e6c65…` (informative, variância 978.6); contínua → `d862c7eb…` (frame 488, variância 1067.4). Evidência em `out/evidence/m4_ken_ryu/`.
- **Veredito v025 (Ryu/Ken): idem.** Sessões `47960880…`/`8211e9d1…`/`a423f438…`; log `out/logs/m4_bridge_proof_ryu_ken.log`: determinismo byte-idêntico `f59fe2f6…` (frame 240, variância 979.4); contínua `9814ced1…` (frame 667, variância 1152.0). Evidência em `out/evidence/m4_ryu_ken/`. Leitura visual honesta do cont_v025: arena preta, lutador direito totalmente renderizado, pose esquerda em meio de upload — estado mid-stream real, não claim de qualidade.
- **Instrumento vivo:** os quatro PNGs dos cruzados são todos distintos entre si e de v022/v023 (`584e6c65`≠`d862c7eb`≠`f59fe2f6`≠`9814ced1`≠`12c57d1a`≠`67bcb20b`), com `rom_sha256` de cada captura conferindo com o disco (v024 `870da893…`, v025 `bd144ee6…`); emulator sha `db185a1e…`, bridge sha `a283b542…`.
- Corredor de sondas: `audit_probe_corridor` **pass** nas duas ROMs (0xC800..0xC8FB, 45 sondas, folga 1787; artefatos `out/logs/probe_corridor_audit_m4_ken_ryu.json`, `..._m4_ryu_ken.json`).
- Limites: stepped prova sequência/determinismo, não fps; poses ainda sobem mid-frame (stall ≈1,7 pares/frame medido no corredor das ondas anteriores); quirk de rótulo do gerador persiste nos cruzados (arquivos/símbolos `p1_ken`/`ken_scene_bankNN` independentemente do ocupante — bytes provados pelos shas de fonte; conserto = curadoria de wrapper, aprovação humana pendente); teto do claim inalterado: `diagnostic_only`.
- Ordem jogável do objetivo (Ken/Ken → Ryu/Ryu → Ken/Ryu → Ryu/Ken): **os quatro pacotes agora existem e as quatro ROMs bootaram com evidência bridge** (v022 ee07d9a6, v023 e5834144, v024 870da893, v025 bd144ee6).

Próxima ação: (b') gate Emulicious clip→plain re-medido via bridge; ramos M5+ (input humano/IA no mesmo caminho, HUD/rounds) e decisões humanas intactas (remeapeamento 2-botoes por unidade, ambiente sem throttle p/ fps, BG/híbrido vs escala, curadoria wrapper: 4 defeitos de instrumento + rótulos `ken_scene` + `build_inner -D`).

### Wave-4m: gate (b') clip→plain — equivalência visual PROVADA, troca mantida; v026 é a ROM atual (2026-10-16)

Fontes (hierarquia #8 — headers/biblioteca lidos antes de usar): `sdk/devkitSMS/SMSlib/SMSlib.h:189` (`SMS_addSprite` = macro que expande `SMS_addSprite_f((y),((x&0xff)<<8)|tile)`), SMSlib.h:199 (sem `NO_SPRITE_CHECKS` — não definido no build deste projeto, grep limpo — `SMS_addSprite_f` retorna `signed char`: −1 SAT cheia, −2 Y inválido), SMSlib.h:209 (clip retorna −1 "no more sprites or clipped"), `sdk/devkitSMS-upstream/SMSlib/src/SMSlib_sprite.asm:76–116` (`SMS_initSprites` zera `SpriteNextFree`; `SMS_addSprite_f` rejeita apenas `SpriteNextFree>=64` e `y==0xD1`), `sdk/devkitSMS-upstream/SMSlib/src/SMSlib_spriteClip.c` (7 predicados; clipWin default `(0,0,255,191)`; `SMS_setClippingWindow` nunca é chamado pelo consumidor). **Análise**: o pre-guard do `emit_frame` (0≤sx<256, 0≤sy<192) torna inalcançáveis os predicados exclusivos do clip (janela, truncamento &0xff da macro, linha 0xD1); ambos os APIs rejeitam identicamente só em SAT cheia → clip≡plain neste consumidor; única diferença é custo (asm naked ~162 ciclos vs C com predicados — número do fonte, não medido). Chave local `#define LUTA_DIAG_CLIP_PLAIN 1` + ramo `#if/#else` no ponto de chamada (mesmo padrão da 4l; contorna o blocker registrado de `build_inner.py` sem `-D` por projeto; curadoria de wrapper exigiria aprovação humana).

- ROM candidata ATUAL da linhagem: `d5c416741066f51fe70e12e6547c85d5d1c73c7405605a5b677f3b0f1d481e38` (851.968 B; cadeia … ee07d9a6 → e5834144 → 870da893 → bd144ee6 → **d5c41674 atual**), stream Ryu/Ken (`ryu_ken_cross`) com emissão plain. `audit_probe_corridor`: **pass**, 45 sondas, folga 1791 (`out/logs/probe_corridor_audit_m4m_clipplain.json`, map sha `a1a0a9b1…`). Map v026: `l__CODE=0x4AE5` (19.173 B); o map da v025 foi sobrescrito pelo rebuild — **delta de tamanho de código declarado NÃO medido** (a troca deveria encolher ao remover `SMS_addSpriteClipping` do link, mas sem número honesto não se afirma).
- A/B no bridge (transcrição completa em `out/logs/m4m_clip_plain_ab.log`; rom_sha256 conferido em cada captura): sessão base `ee5840b5a257497483b48030e4942d6e` com a baseline preservada `changelog/roms/build_v025/rom.sms` (`bd144ee6…`) e sessão candidata `f849f930c2574055b7db0d21ae1d03a8` com `out/rom/luta_mugem_rev2.sms` (`d5c41674…`), sequências de comando idênticas (step 120 → captura; step 480 → captura):
  - frame 240: **ambas** `f59fe2f6a817eef54a847c42fd557333c9692d5950f4dc06c460671e6f1460d5` (informative, variância 979,4);
  - frame 720: **ambas** `9814ced147223b3d231b9c04f1c89739d096dd816374b31c1cbc1fbee1f3606d` (informative, variância 1152,0).
  Byte-idêntico entre as duas ROMs nas duas profundidades; a sessão base reproduziu exatamente os hashes gravados no M4 (instrumento determinístico entre sessões). Evidência linkada em `out/evidence/m4m_clipplain/`.
- **Veredito: gate (b') PASS.** clip≡plain demonstrado em dois níveis — analítico (predicados de recorte inalcançáveis dadas as autoridades lidas) e medido (framebuffers byte-idênticos e informativos, duas profundidades, sessões independentes com hash de ROM vinculado). A troca é mantida: `LUTA_DIAG_CLIP_PLAIN 1` permanece no fonte e v026 passa a ROM da linhagem. Semântica de `probe_omitted_sat` preservada por contrato: o plain também retorna −1 em SAT cheia (SMSlib.h:199) e é esse valor que incrementa a sonda — nenhuma contagem de omissão mudou de significado.
- Limites: a economia de custo de emissão NÃO foi medida em flanco — as ondas 4i/4j atribuem custo por região e o clip não aparece como dominante separado; o ganho declarado é a substituição de C+predicados por asm documentada no fonte da biblioteca. Equivalência medida em 2 profundidades do stream determinístico, não prova exaustiva de todos os frames — o que sustenta a generalização é a análise de predicados sobre as autoridades, explícita acima. Teto da ROM permanece `diagnostic_only`; stepped ≠ fps; ciclos de emulador ≠ hardware.
- Consequência de agenda: (b') estava registrado como pré-requisito para tocar `SMS_addSpriteClipping`; está FECHADO. Nada disso promove emissão a claim de entrega — o orçamento pares/VBlank do scheduler continua mensurável apenas no loop de entrega (declaração de escopo da 4l), e a parede de composição (≤8/scanline, maxline=13, used_max=128) segue alimentando a decisão humana BG/híbrido vs escala.

Próxima ação: ramo independente registrado — M2 gameplay Ken/Ken (colisão/hitstun na arquitetura de diagnóstico); decisões humanas intactas (remeapeamento 2-botoes por unidade, ambiente sem throttle p/ fps, BG/híbrido vs escala, curadoria wrapper: 4 defeitos de instrumento + rótulos `ken_scene` + `build_inner -D`).

### M2 wave-5a: colisão/guarda/dano/hitstop/pusher operando na ROM e convergência ROM↔simulador provada — v029 é a ROM atual (2026-10-16)

Fontes: `src/main.c:115-140` (sondas de combate + geometria), `src/main.c:445-458` (`move_x`), `:489` (walk), `:515-700` (`combat_step`, `pusher_step`, `boxes_overlap`, `clsn_*`), `:847`/`:865` (face antes do avanço; resolução de combate no loop), `:942-947` (refresh de geometria por frame); espelho offline `tests/sim_combat_wave5a.py`; dados CLSN do versus-cut (blob AIR int16 LE, sentinela −32767, seção hit antes de hurt, y negativo = para cima, origem nos pés). Sondas: `0xC826` hits, `0xC828` guards, `0xC82A/C` dano p1/p2, `0xC82E/30` life, `0xC832` hitstop, `0xC834` ko, `0xC836` checks, `0xC838` pusher, `0xC83A` flips, `0xC83C/3E` x px, `0xC840/42` face.

Cadeia de ROMs (todas 851.968 B): v025 `bd144ee6` → v026 `d5c41674` → **v027 `164ebd3b`** → **v028 `3abd46b3`** → **v029 `4c38eeb9046ba0c2651ef502b40c93d0a62b354a9275a050aeb36186eaea36cb` (atual, arquivada em `changelog/roms/build_v029/rom.sms`)**. Delta exato v027→v028 não é atribuído aqui (não medido separadamente); o que se declara é que v028 já media o defeito abaixo e v029 o corrige.

- **Blocker histórico de M2 fechado:** o `probe_hit_events=0` persistente virou `hits=3`/`guards=1`/`dmg_p1=110`/`dmg_p2=42`/`life=890,958`/`hitstop=66`/`pusher=143`/`flips=234`/`checks=146` na ROM medida. Dano ocorre **nas duas direções** (P1 também apanha), `ko=0` no ponto medido.
- **Defeito real encontrado na ROM (não era desalinhamento do simulador):** em SDCC/Z80 `int` tem 16 bits, então a borda `DIAG_X_MAX = 240 px = 61440` **não cabe em `signed int`** (vira −4096 — `0xF000` lido como `int16` assinado; transporte retificado em 2026-10-18: o texto dizia −3926). Todo clamp escrito no domínio assinado tornava-se verdadeiro para quase qualquer `nx` e teleportava os dois atores para a borda direita. Evidência visual da v028: todo o conteúdo do framebuffer nas colunas **206..255** (`out/evidence/m2_wave5a/m2_wave5a_v028_f1025.png`, sha `8d01b82c…`). Correção: `move_x()` (lado decide a subtração; nenhum valor >32767 é lido como assinado) aplicado nos três sítios de escrita de posição (walk, push do golpe, `pusher_step`); `grep "signed int)DIAG_X"` limpo.
- **Convergência medida (a prova desta onda):** ROM v029 em `probe_frame=1027` ↔ `python3 tests/sim_combat_wave5a.py 1027` — **os 15 contadores idênticos**, inclusive geometria `x_p1=110 x_p2=202 face_p1=0 face_p2=1`. Segundo ponto: sim@930 ≡ ROM@930 (`checks=49`, mesmos hits/dano/flip/x/face). O espelho offline é Python (inteiros sem limite de palavra) e por isso **não** reproduzia o bug — ele funcionou como referência correta e a ROM convergiu para ele.
- **Geometria visual restaurada:** captura selada `out/evidence/m2_wave5a/m2_wave5a_v029_f1027.png` sha `b2ab49f01574566f280c8e2601a1220926d6df7c71bec3962e76e7fb6c7322db` (+ `.json` `7458d80e…`, `rom_sha256` = `4c38eeb9…` **vínculo ok**, canvas 256×192, frame do emulador 2220): dois grupos de colunas **96..139** e **189..228**, linhas 85..161, fundo sólido preto, 11 cores distintas, variância de luma 1033,6. Leitura honesta: mid-stream do upload de poses, não claim de qualidade.
- **Gates pagos:** `audit_probe_corridor` **pass** no corredor alargado 0xC800..0xC8FB (77 sondas, folga 1547; `out/logs/probe_corridor_wave5b.json` e `out/logs/probe_corridor_report.json` — o antigo `probe_corridor_audit_m2_wave5c.json` media 60/1781 no map `31f7dba5…`, snapshot anterior; transporte retificado em 2026-10-18); `audit_debug_markers` **pass** (toda sonda `__at` é `volatile`). Build: `[BUILD OK]`, eixos restantes para entrega `boot_emulador, gameplay, fps_constante, audio, memory_bank_atualizado`.
- **Aproximações declaradas (não escondidas):** HITSTun de fonte não implementado — `hitdef time` não existe no versus-cut e os estados de hit dependem do `common1.cns` ausente (fronteira, não contorno); o pusher é constante do motor (1 px/frame), não valor importado; face esquerda ainda precisa de mudança no conversor de tiles (fronteira de curadoria); tile espelhado/`probe_omitted_sat=8` mantido como limite de composição. Scripts de teste dirigem os dois atores pelo mesmo caminho de role/estado — **ainda não é input humano nem IA**.
- **Lição nova (candidata a curadoria, exige aprovação humana; não implementei gate):** aritmética de posição Q8.8 escrita no domínio `signed int` de 16 bits é silenciosamente errada quando a constante de borda excede 32767 — um detector (`audit_*` em `tools/sms_wrapper/`) que marque clamp/`if (x > CONST)` com `CONST > 32767` em tipo assinado transformaria a regra em medição. Enquanto só existe prosa, a classe de bug se repete.
- **Quirk de instrumento observado:** a primeira `capture` de uma sessão recém-iniciada pode vir framebuffer preto total (a janela AWT ainda pintou) e o gate responde `[FAIL_AMBIENTE] uninformative or non-SMS framebuffer`. Um `step` curto antes da captura resolve. Não alterei o wrapper; registrado como 5º candidato de curadoria.
- Limites: `probe_frame` (iterações do loop da ROM) ≠ frames de VDP do emulador (1027 vs 2220) — razão ~2,1:1 é **observação de pacing do instrumento**, não fps nem velocidade de hardware; stepped prova sequência, não tempo; teto do claim continua `diagnostic_only`; nada aqui promove gameplay a entrega.

Próxima ação: teste diferencial fonte→dados→ROM dos CLSN (re-serializar do AIR pelos parsers do wrapper e comparar byte a byte com os arrays do header); depois ramos dependentes de wave-5a — input humano/IA no mesmo caminho de role e HUD/rounds sobre o estado de vida já medido. Decisões humanas intactas (remeapeamento 2-botoes por unidade, ambiente sem throttle p/ fps, BG/híbrido vs escala, curadoria do wrapper: 5 defeitos/limites + rótulos `ken_scene` + `build_inner -D` + gate Q8.8 assinado).

### M2 wave-5b: cadeia CAUSAL input→rota→papel→hitbox→dano→KO provada na ROM (humano e IA pelo mesmo anel) — v031 é a ROM atual (2026-10-17)

Fontes (hierarquia #8/#1 lidas antes de afirmar): `src/main.c:756-813` (`input_stage`: lado 0 = `SMS_getKeysStatus() & 0x3F`, lado 1 = `fight_input_ai_levels(frames, face)`) chamada **incondicionalmente todo VBlank** (`main.c:990`), depois de `facing_step()` e antes de `advance_actor/combat_step/pusher_step`; `src/main.c:1084` (sondas de x em **pixels**: `fighter[s].x >> 8`); `src/fight_input.c:78` (gate de comando: `(flags & S_CONTROL) && v->on_ground`; one-shot só reverte fora de S_CONTROL e **nunca no ar**; `if (!v->alive) return;`); `inc/input_tier.h` (T=6: FORTE no 6º tick segurado, FRACO no 1º tick solto sem forte); `inc/input.h` (`CMD_BLOB_VERSION 4`); tabela gerada `out/generated/ryu_ken_cross/fight_runtime_data.h` (índice 0 = `P1_CUT_CMD_SPECIAL` → `FIGHT_CMD_SPECIAL_UNSUPPORTED`, 1 = HP, 2 = HK; `command_count=3`, `fight_unrouted_mask=0x05`; `p1_states`: IDLE/WALK_F/WALK_B = `S_CONTROL`, CROUCH/GUARD = `S_CONTROL|S_BLOCKABLE`, JUMP = `S_AIR`, golpes = `S_HIT` com dmg 42/112/35/119, KO = 0).
ROM: `out/rom/luta_mugem_rev2.sms` sha `6f4a3cf5e336c20ff1dc0fb5225345270823350eada55d4d43655cdfca0b6e9a` = `changelog/roms/build_v031/rom.sms` (cadeia … v029 `4c38eeb9` → v030 `b5a0126b` → **v031 atual**). Instrumento: `tests/input_wave5b_rom_causal.py` sha `ad54356076db0d112161c70641ca941f300b2efbc22e1deb080c6daca78f9c06`, sessão privada `2881669466e8452ea65d9871ce3c54dc`, relatório `out/logs/wave5b_rom_causal.json` sha `58ac20403637b81921486f0ee824284dc844946017a637e40f34aa857c36e1f2`, log `out/logs/wave5b_rom_causal_run.log` sha `6d7e0693a45b2bacad7f438f61e6e7ffa8517ae1bb025cb0e68b7dd76485f3b1`. Runs intermediárias preservadas: `..._run_a.log` `227f800f…` (27/29), `..._run_b.log` `1f5f022f…` (28/29) + `wave5b_rom_causal_a.json`/`_b.json`. Sondas descartáveis mantidas em `out/tmp_wave5b/`: `trace_probe.py` `10a6b53e…` (telemetria frame a frame que produziu as constantes abaixo), `dir_probe.py` `7f60536f…` (ver retratação abaixo — sua conclusão foi superada).

- **Veredito: 29/29 casos, exit 0, ceiling `diagnostic_only`.** Cadeia completa lida na ROM, na ordem: pad → `keys_raw`/`levels_p1` bit a bit (6 máscaras de contexto: frente/trás/baixo/baixo+trás=guarda/baixo+frente/cima, todas com eco exato do bit e `role_changes_p1` +1) → tier (FORTE casa exatamente no 6º tick) → anel → **rota** (`cmd_hits_p1` +1, `cmd_last_index_p1=1` = HP, `cmd_unrouted=0`) → **papel** `ST_HP=7` sob a pressão → **hitbox** (`clsn_checks` +9) → **dano** (`damage_p2` +112 = o `StateDef.dmg` da tabela; vida 1000→888) → one-shot expira para controlável (~48 ticks, `role_changes` +3). Especial humano: `cmd_unrouted_p1` +1 com `cmd_last_index_p1=0` — casado e **contabilizado**, não sacrificado em silêncio. Bordas: clamp exato `x_p1=16` (esquerda) e `x_p1=240` (direita) na sonda de pixels. IA (lado 1) percorre o MESMO caminho: rotas não-zero e dano sobre p1 sempre acompanhados de casamento de rota — nada de dano escrito por fora do input. Guarda humana: `guard_events` +1 e `damage_p1` +0 na janela de 240 ticks. KO: drive de 12 janelas derrubou p2 (`life_p2=0`, `ko_events=1`, dano pós-KO = 0, defensor móvel atingido em 7 posições distintas, pusher 462 / flips 2).
- **Lição nova (candidata a curadoria de wrapper, exige aprovação humana; NÃO corrigi o instrumento): o `step` da ponte NÃO é o frame da ROM.** Medido: 100 steps injetados → 45 avanços de `probe_frame` (**ratio 2,222**), e esse número já era visível na wave-5a (1027 vs 2220 do VDP). Consequência prática: um orçamento escrito em steps entrega ~metade dos ticks reais da ROM. O harness anterior a esta onda afirmou "o humano nunca acha rota" porque (a) a pressão durava ~6 steps ≈ 3 ticks < T=6 e (b) a espera após o golpe era menor que o arco medido de `S_HIT` (~46-48 ticks), dentro do qual o gate de `fight_input.c:78` está **legitimamente fechado**. **Retratação registrada sem mascarar:** a conclusão do `dir_probe.py` ("botões nunca roteiam") era ausente de oportunidade, não de rota; o `trace_probe.py` frame a frame mostrou `lev_p1=0x10` estável e `cmd_hits_p1 0→1` com `role_p1 0→7` no 6º tick. Desde a reescrita, todo orçamento do teste é declarado **em frames da ROM e conferido contra `probe_frame`** (`Rig.hold` completa em chunks até a ROM contar os ticks pedidos; `bridge_steps_per_rom_frame` sai no relatório; o self-check agora amarra `tier_t == 6` e `PUNCH_ANIM_TICKS > TIER_TICKS`).
- **Dois FAILs intermediários eram janela de medição, não runtime** (cada um corrigido com evidência extra, não com claim mais fraco): (1) `G_guarda…` com `guard=0` — o humano estava na borda e a IA sem alcance; falta de ataque não é falta de guarda. Correção: `approach(24)` antes da guarda e `clsn_checks_delta` na evidência para separar "pose nunca avaliada" (distância) de "avaliada sem sobreposição" (geometria). (2) `H_simultaneidade…` — os dois lados acumulam dano, mas quase nunca na MESMA janela de ~60 ticks, porque o beat da IA (`FI_AI_BEAT_FRAMES`) é mais longo que uma iteração. A claim passou a ser **explicitamente janelada**: rotas dos dois lados na mesma janela **e** dano cruzado em janela de 3 iterações, com o delta de cada janela impresso e gravado no relatório.
- Limites honestos desta onda: o **papel terminal do lado 1 não tem sonda** (só `probe_b_role_p1` é espelhado em 0xC8FB) — KO de p2 é afirmado por `life`/`ko_events`, nunca por role; `probe_frame`/steps provam sequência, **não** fps nem velocidade de hardware; não há reset de round nesta ROM (KO é terminal na sessão medida); HITSTun de fonte continua ausente (fronteira `common1.cns`); o humano só tem rota para HP forte (K1+tier2) — HK forte é K2+tier2 e **colide** com o especial (K2+tier1), e 9 comandos de super seguem sem rota de 2 botões: isso é gate humano de remapeamento por unidade, não decisão tomada aqui. Nada promove FPS, áudio, qualidade visual nem entrega.
- Próxima ação desta linha: selar captura/evidence da wave-5b se houver pedido de prova visual do golpe; re-selo worst-frame na v031 com os dois atores (o selo atual mede um ator ocupado); inspecionar o `warning 110` do SDCC em `src/fight_input.c` (caminho da IA) no .asm gerado; re-verificar de forma independente os artefatos do worker `clsn-diff` (`tests/clsn_source_to_rom_diff.py` `b9968090…`, `out/logs/clsn_diff_report.json` `84e58a2e…`, 59/59 arrays iguais, 33 aliases, 184 checagens de sentinela) antes de integrar; relabelar `tests/sim_combat_wave5a.py` (modela o driver de script removido).

### M2 wave-5c: prova CLSN fonte→dados→ROM fechada por DOIS caminhos de autoridade disjointa — reposicionada na v031 + corroboração independente por agulha de bytes (2026-10-17)

Fontes (hierarquia #1/#8): ROM da linhagem `out/rom/luta_mugem_rev2.sms` sha `6f4a3cf5e336c20ff1dc0fb5225345270823350eada55d4d43655cdfca0b6e9a` (= `changelog/roms/build_v031/rom.sms`, 851.968 B, stream `ryu_ken_cross`); AIRs crus `data/derived/ryu/ryu/ryu.air` `15285766e257aa4de6d1fc1092fb0eb248f0da16b52b34d9d3eeb9284ab65a3d` e `data/derived/ken/ken8/ken.air` `b1f6c8d093dfd0849091035d7721a5748b59a476084bbc7ebf1ce2e1c6e7ed3a`; escopos/oráculos de contagem `out/generated/ryu_ken_cross/p1_ken/ken_scene_manifest.json` `c16d5bf0419653d0ff369b6ca9de7a107fe745949ec33fb60076b795541b386e` e `.../p2_ryu/ken_scene_manifest.json` `ba283a67e6744c971ca5926583ac5a60ed2f5f83fbe5e3d477fc8ee40d0b0110`; headers gerados `p1_ken/ken_scene_runtime.h` `40914bf4…`, merged `versus_scene_runtime.h` `19edb320…`; `.map` `83475983b2a08de33860d1970ea2cb951d653b70f3f2d4c58a0d84937ed59af0`; escala declarada nos dois manifests = **40/49** uniforme por frame (a sonda afirma e confere, não herda).
Caminho A (posicional, do worker, re-validado pelo coordenador): `tests/clsn_source_to_rom_diff.py` sha **`2f92e2d227550fabe004ac0c40828adb78b0e7eb3697358d08141f43cf5560ab`** (re-pin deliberado de `ROM_SHA_EXPECTED` para `6f4a3cf5…`), relatório `out/logs/clsn_diff_report.json` sha **`30ff632d100645149046132877d06f265670c7afb7f503143ad7d7a9dc3a26b2`** `verdict: pass`; original do worker preservado antes da regeneração em `out/logs/clsn_diff_report_worker_20261016.json` sha **`84e58a2ed107178b651ccbf73cc7d1ee2dc2b94578d9636553847c42a8d1a4c1`** (mesma estrutura, ROM `4c38eeb9…` da wave-5a, `verdict: pass`).
Caminho B (independente, deste coordenador): `out/tmp_wave5c/clsn_needle_scoped.py` sha **`a3bd2896e69be36647ae1147e0fad47cdf411410963c04ba11eece810944403e`**, relatório `out/logs/clsn_needle_scoped.json` sha **`9aae97a4b938636682d691baacacbcd7e8ad3ae0c9698f15e328b902a26b80b5`**, `veredito: pass`, rc=0. **Desenho de autoridade disjointa:** o caminho B não usa o parser do wrapper, nem o `.map`, nem o `.ihx`, nem o mapeador de endereço — lê o AIR cru com regex própria, aplica 40/49 com arredondamento half-away-from-zero por aritmética própria e procura a sequência de 8 bytes (caixa inteira, int16 LE) em **todo o binário**.

- **Números do caminho A (v031, posicional):** fonte→dados com ryu `anims=11 blobs=47 boxes=98 frames_com_clsn=47/48` e ken `anims=12 blobs=45 boxes=96 frames_com_clsn=45/45`, `byte_mismatches=0` nos dois slots, `air_reparsed_matches_generator_input=true`, `air_parity_issues=[]`, blobset recomposto com sha idêntico ao emitido (`fc17fedf…`); dados→ROM `arrays_compared=59`, `merged_aliases=33`, `byte_mismatches=0`, `rom_sha256_matches_expected=true`, prefixos `P1_RYU`/`P2_KEN8` presentes; sentinela+ordem `blobs_checked=184`, `issue_count=0`. **Premissa falsa corrigida pelo teste:** o cabeçalho de 512 bytes do makesms **não** se aplica a este `.sms` — hipótese `file_offset = 512 + address` REJEITADA (bytes de crt0 do `.ihx` em offset 0x0; `TMR SEGA` em 0x7ff0 dentro dos primeiros 32K); identidade `file_offset = address` em 0x0000..0x7FFF aceita após round-trip com os 830 registros do `.ihx` (26.269 B de imagem, 26.263 batendo; os 6 divergentes estão **todos** dentro da janela de stamp SEGA 0x7fe0..0x7fff, zero fora). Iron rule do instrumento: comparação que não compara nada é FALHA, não pass.
- **Números do caminho B (v031, independente):** **194/194** caixas no escopo têm imagem de bytes no binário, `sem_byte=0`; `contagem_divergente=0` na resolução própria de atribuição por frame nos **93** frames importados (48+45) — i.e. o meu parser independente reproduz a atribuição do gerador. Cobertura exaustiva das três convenções sobre as mesmas 194: `minmax=194`, `crua=108` (98 ryu + 10 ken), `y_trocado=50` (só ken) → **a regra é normalização `(min(l,r),min(t,b),max(l,r),max(t,b))` + escala 40/49 + int16 LE**, estabelecida por medição, não herdada de `sms_scale`. O ken cru escreve caixa com y de baixo antes do de cima (ex.: `-25,-1,18,-91`), e é por isso que a convenção crua sozinha não fecha.
- **Não-vacuidade medida (caminho B):** caixa-probe `[-31,-80,23,1]` — bytes crus **ausentes**, bytes escalados **presentes**; caixa impossível `[-31,-80,23,1]`-como-`[12345,…]` ausente; y-invertido do ken casado pela convenção `y_trocado`. Ou seja, a agulha distinguishing escala e não degenera em "tudo aparece em algum lugar".
- **FORA DO ESCOPO declarado, não mascarado:** o AIR do ryu tem 183 ações/992 linhas de caixa e só 12 ações/98 caixas entram no versus-cut (171 ações = **1.359** instâncias de caixa excluídas); o do ken tem 102 ações/786 linhas e 12 ações/96 caixas importadas (90 ações = **787** instâncias excluídas). Uma versão anterior da sonda usou o denominador errado (todas as caixas do pacote) e reportou "1.576 ausentes → FALHA": o que estava errado era o escopo, não a ROM.
- **Achado 1 — byte do fonte chegou ao binário, corroborado por caminho disjoint.** A afirmação da wave-5b ("re-verificar de forma independente os artefatos do worker") está paga: posicional e por-presença, duas autoridades sem peça compartilhada, ambas `pass` na mesma ROM com hash vinculado em cada relatório.
- **Achado 2 — questão de fidelidade ABERTA na semântica de atribuição CLSN (registrada, não resolvida por aqui):** as duas leituras possíveis divergem em **17 frames importados** (9 ryu + 8 ken) e a divergência é **exclusivamente de hitbox**: a leitura *carry-forward* (o grupo `Clsn1: n` vale até o próximo grupo da mesma seção) acrescentaria **27** instâncias de `clsn1` que a ROM não carrega (12 + 15); `clsn2` = 0 em ambas. Três implementações concordam na regra *reset-por-frame* com fallback em `ClsnXdefault` — o wrapper deste projeto (`tools/sms_wrapper/mugen2sms/parsers/air.py`: `pending[k] if pending[k] is not None else default[k]` e `pending = {"1": None, "2": None}` após cada linha de frame), o parser doador MD (`.../mugen2sgdk_forge/parsers/air.py`, logicamente equivalente) e a minha sonda independente. **Nenhuma autoridade local prova o que o próprio MUGEN faz**, e o `doc/COMPATIBILITY_PROFILES.md` do doador não trata de carry-forward de CLSN. Evidência ambígua de intenção do autor: o ryu re-declara o grupo `Clsn2` idêntico frame a frame mas não re-declara o `Clsn1`. Consequência: isto é pergunta de fidelidade com gate humano, **não** defeito declarado — mexer no conversor é curadoria de wrapper e exige fonte autorizada externa + aprovação humana.
- **Achado 3 — quirk de instrumento (6º candidato de curadoria, não corrigi):** o teste posicional hardcodou `ROM_SHA_EXPECTED`, então **cada build novo exige re-pin deliberado**; e ele escreve o relatório em caminho fixo, o que **sobrescreve a evidência anterior** se não houver backup. O backup foi feito (`clsn_diff_report_worker_20261016.json`) e a regeneração na v031 é o `30ff632d…` atual.
- Limites honestos: o caminho B é **por presença** (a sequência de 8 bytes existe no binário), não por posição — quem afirma correspondência endereço a endereço é o caminho A; o manifest é oráculo de **escopo e contagem**, não de semântica; os dois caminhos compartilham a ROM e as fontes, mas nenhuma autoridade de parsing/endereçamento; a escala 40/49 é a declarada pelo gerador — a sonda confere uniformidade e o valor, não re-deriva a decisão de escala; teto do claim inalterado (`diagnostic_only`); nada aqui toca fps, áudio, qualidade visual ou entrega.

Próxima ação: re-selo worst-frame na v031 com os dois atores; inspecionar o `warning 110` do SDCC em `src/fight_input.c:181` (`AI_BEAT_JUMP`) no `.asm` gerado; relabelar `tests/sim_combat_wave5a.py` (modela o driver de script removido). Fronteiras que pedem entrada humana, sem contorno: autoridade externa MUGEN para reset-por-frame vs carry-forward antes de qualquer mudança no conversor (curadoria: 6 candidatos agora + rótulos `ken_scene` + `build_inner -D` + gate Q8.8 assinado), remapeamento 2-botos por unidade (ken 11 / ryu 18 `needs_remap_decision`, 9 supers sem rota), ambiente sem throttle para fps, BG/híbrido vs escala/arte.

### Lote A (2026-10-18): contexto congelado e baseline causal reproduzido na v031 com protocolo reforçado

Objetivo do doc/25 (Lote A): congelar contexto, reproduzir o núcleo causal do wave-5b na v031 **antes** de qualquer mudança de runtime, parametrizar instrumentos (SHA como entrada congelada) e corrigir medidas transportadas. ROM congelada `6f4a3cf5…` (851.968 B; `out/rom` = `changelog/roms/build_v031/rom.sms`), fontes/dados por hash em `out/logs/freeze_v031_20261018.json` (`475a8689…`); rebuild check `49d95a4d…` difere da v031 só em 0x7FE6 (data SDSC) + 0x7FFA (checksum TMR) e `out/rom` foi restaurada à v031. Histórico preservado sem edição: `out/logs/wave5b_rom_causal.json` (schema 2, 29/29, sessão `28816694…`) e `out/logs/clsn_diff_report.json` (`30ff632d…`) intactos.

Artefatos novos (por corrida em `out/logs/runs/`, sem sobrescrita; manifest do lote `20261018T171426Z_loteA_manifest_6f4a3cf5e336.json`):
- `20261018T170509Z_clsn_diff_6f4a3cf5e336.json` (`50de0404…`): CLSN fonte→dados→ROM na v031 pinada = **pass** — 59 arrays comparados / 33 aliases / 0 divergências; sentinela 184 blobs / 0 issues; `.ihx` 830 registros / 26.269 B com 26.263 bytes batidos (6 divergentes, todos na janela de stamp SEGA 0x7fe0..0x7fff, zero fora). Identidade `file_offset = endereço Z80` em 0x0000..0x7FFF (premissa do header de 512 B do makesms refutada com round-trip; ver wave-5c).
- `20261018T170913Z_wave5b_rom_causal_6f4a3cf5e336.json` (`9c70dc87…`): núcleo do wave-5b reproduzido na v031 = **32/32, exit 0**, schema 3, sessão privada `30279f7b562f4ed8bc154bbe4cd2e4f1`, 26,0 s; custódia completa em `..._custody/` (session.json `ba380fce…`, commands.jsonl `52d45bb3…`, ready.json `c6855f7a…`; supervisor.log/emulator.log vazios = `e3b0c442…`). O buraco de custódia da sessão v1 fica coberto por este journal.
- Deltas do instrumento vs wave-5b v1 (9 itens, no relatório): pin `--expect-sha` como entrada congelada (antes constante de arquivo); saída exclusiva por corrida; C afirma papel EXATO por contexto; F exige clamp exato quando alcançado e, senão, pusher sustentado (nunca ruído); G exige dano zero E hit não-bloqueado zero na janela de guarda; KO terminal nos DOIS lados com contadores congelados + tentativa ativa; D2 mede deadlines input→rota→papel→apresentação→dano; quatro relógios registrados; custódia copiada.
- Quatro relógios: VDP confirmados 6219; contador lógico da ROM 2547 (observado por holds 2525); fronteiras de animação (role_changes — proxy declarado, a sonda não expõe fidx) p1 70 / p2 129; parede 25,7 s; razão do instrumento 2,222 steps VDP por frame da ROM.
- D2 (resolução do traço: 2 steps ≈ 0,9 frame ROM): input→rota 12 VDP / 7 ROM; ação e apresentação no mesmo ponto de leitura (12/7); →consequência 28 / 22; apresentação→consequência 16 / 15; ação→apresentação 0 (estado e geometria lidos no mesmo snapshot).
- Evidência causal reforçada: guarda humana `guard_total=1`, `dano_janela=0`, `hit_janela=0` com `clsn_delta=5` (contato avaliado, não ausência de alcance); KO de p2 no drive 9 com `rotas_pos_ko=1` (matcher vivo) e inscrições pós-KO `dmg=0/hit=0/clsn=0`; bordas `x_p1=16` e `x_p1=240` exatas; especial humano contabilizado (`cmd_unrouted+1`), não sacrificado.
- Correções de transporte (doc/25 §Lote A): linhas 494/497 deste arquivo e comentários de `src/main.c` — 61440 como int16 = **−4096** (dizia −3926; `0xF000`); corredor atual = **77 sondas / folga 1547** (`probe_corridor_wave5b.json`/`probe_corridor_report.json`, map `83475983…`), e o artefato antigo 60/1781 media o map `31f7dba5…`; comentário da AIR: MUGEN 1.0 = 60 ticks/s, **não** 1/100 s (unidade do OpenBOR, não deste motor).
- Deriva vs freeze (registrada no manifest do lote): `tests/input_wave5b_rom_causal.py` `ad543560…`→`3952dcc8…` e `tests/clsn_source_to_rom_diff.py` `2f92e2d2…`→`7e393d47…` (upgrades do lote, por desenho); `src/main.c` e docs do lote ganham prosa/comentário do lote (bytes da ROM não mudam; sem rebuild; v031 intacta).
- Limites: papel terminal do lado 1 continua sem sonda; stepped ≠ fps; sem reset de round; fronteiras de animação = proxy; D2 com resolução ~1 frame ROM; simultaneidade cotejada em janela; teto `diagnostic_only` inalterado.

Próxima ação: Lote B — perfil de produção no mesmo sistema (uma autoridade de runtime), núcleo reutilizável com extensão `runtime/` registrada em `tools/sms_wrapper/mugen2sms`; lógica/input/CNS/cache/SAT/filas separados dos commits VDP no VBlank com limite medido, recuperação de fila e overflow; primeira cena jogável com os dois atores reais e fundo sólido; híbrido BG corpo + partes/FX na SAT; probes desejada/residente/submetida/apresentada; worst-frame sem DAP com carga representativa; Emulicious produção, BlastEm diagnóstico. Decisões humanas intactas (remapeamento 2-botões por unidade + 9 supers, curadoria do wrapper com os candidatos já registrados nas ondas, autoridade externa MUGEN para reset-por-frame vs carry-forward, ambiente sem throttle p/ fps, BG/híbrido vs escala/arte).

### Lote B.1 (2026-10-18): perfil de produção v033 fecha a fatia de VBlank em worst-frame; provisão visual caracterizada (flicker/omissão = loteria de emissão) e teto de lógica aberto para B.2

Fontes: `src/main.c` (`LUTA_PROFILE` linha 72; helpers `vblank_account`/`logic_tick`/`sprites_build`/`worst_sample`; dois laços no fim); `doc/25` §Lote B; triagem `out/evidence/blackscreen_triage_20261018/README.md`; custódia `out/evidence/loteB1_20261018/` (fonte pré-cirurgia, script e narrativas de corrida).

- **Cirurgia de perfil único (mesmo sistema, uma autoridade).** Cadeia de `src/main.c`: `0b52af68…` (Lote A) → `cb1428bf…` (chave `LUTA_PROFILE` + comentário; 52.446 B) → **`10af677d…`** (cirurgia: helpers extraídos + dois laços `#if LUTA_PROFILE`; 53.945 B). O bloco de sondas `__at` é **idêntico** antes/depois da cirurgia (comparação linha a linha). `LUTA_PROFILE 0` = ordem histórica congelada (upload e lógica DEPOIS de `SMS_waitForVBlank`; SAT ao fim da emissão — o instrumento v031); `1` = produção (lógica/input/cache/metasprites no display ativo; só `stream_pending` + `SMS_copySpritestoSAT` dentro do VBlank pedido, janela registrada por `probe_phase` e `vline/vovf`). Nenhuma função duplicada: as MESMAS funções nas duas ordens; profundidade de pipeline = 1 frame (declarada no TDD).
- **ROMs.** v032 `49d95a4d…` (rebuild-check do Lote A: difere da v031 só em data SDSC 0x7FE6 + checksum TMR 0x7FFA); **v033 `14381bf4…`** produção (é a `out/rom` atual; cópia em `changelog/roms/build_v033/`); v034 `c0a5adab…` = mesmo fonte com `LUTA_PROFILE 0` (controle da ordem histórica); v031 `6f4a3cf5…` preservada como referência diagnóstica.
- **Worst-frame (sem DAP na janela, selado por SHA).** 1ª tentativa (sessão `e468a5ad…`, espera de 90 s): `sem_lastro` — selo `done=0` em `probe_frame=2281`, janela de 3000 iterações não completou; refeita sem tocar na ROM. 2ª (sessão `0139ba8b…`, espera de 300 s): **pass** — `vline_min=197`, `vovf_delta=0`, 3000 amostras, `frames_rom_final=9210`, estado FIGHT; `worst_frame.json` `01138596…`; bundle f900 `0b91a729…` (PNG `3ec83602…`, variância de luma do bridge 939,1). Leitura comparativa da triagem: v033@300 `vline 212/min 197/vovf 0` vs v031@300 `125/0/52` e v034@16980 `88/0/2335` ⇒ **na produção os commits VDP fecham dentro do VBlank; na ordem histórica derramam** (vovf cresce).
- **Fps efetivo por journal (não por assert).** Em free-run do Emulicious, medido nos journals de sessão: 17.973 frames/300,02 s, 5.393/90,02 s e 30.061/501,75 s = **59,91 fps** (nominal 59,9227); janelas curtas de 3,02–3,03 s/180 frames = 59,47–59,55. Sessões que usam `step` andam ~400–560 frames/s (fast-forward) e não medem fps. Isto é fps de EMULAÇÃO relatado pelo contador de frames do bridge — não cadência de hardware; a prova de orçamento é o selo worst-frame acima. Recibos (journals) copiados para `out/evidence/loteB1_20261018/journals/`.
- **Matriz causal reproduzida e reancorada.** v031 32/32 (sessão `541dc6af…`; D2 completo 12/7→28/22); v033 **31/32 ×2** (`734a2d3d…`, `d9f2d8e2…`; falha só D2, `input_to_consequence=null` com rota 14/7); v034 **30/32 ×2** (`b6cd3484…`, `6a8f73f8…`; D2 + G com `guard_total=0`, `clsn_delta=0`, `x_p1=205 x_p2=122` — fora de alcance, não perda de mecanismo; em v031 o mesmo caso passa com `guard_total=1`, `clsn_delta=5`). Interpretação: classe **janela/distância/fase** do instrumento (D2 lê a cada ~1 frame ROM; G depende do beat da IA e da distância acumulada), não regressão — o mecanismo está no traço (rota 0→7, `clsn_checks`, `dmg=112`). Uma tentativa inicial da corrida v034 (custódia `20261018T175016Z_…`, sessão `bc298232…`) foi abortada sem relatório — declarada, não apagada. Reancorar D2/G na ordem de produção = B.2.
- **Tela preta caracterizada (com retificação).** O "preto" inicial/final é **omissão de emissão**: o gate de `sprites_build` só desenha o ator quando `current[side].pose_global == poses_req[side]` (senão `probe_stall_frames++`); o upload anda 1 par de patterns por VBlank (round-robin) e o pool satura (`used_pairs_max=128/128`) ⇒ as janelas visíveis são coincidências de sincronia ("loteria"), reproduzíveis; não há corrupção de pixel nem regressão (v029 pré-Lote-A mostra o mesmo hoje). Capturas pós-KO em frame alto são preto com `life=0/ko=1` — amostra, não varredura. **Retificação medida** (README da triagem): as capturas f900 de v031/v033 divergem em 1.064 px em `dx=0` (região do P1) e **zero em `dx=1`** — mesmo desenho com o P1 deslocado +1 px (consistente com a profundidade de pipeline de 1 frame), P2 e resto idênticos; a frase anterior "pixel a pixel equivalentes" era imprecisa e fica retratada.
- **Extensão de runtime (curadoria com testes).** `tools/sms_wrapper/mugen2sms/runtime/` registrado na CLI (`runtime-vram-plan`, `runtime-commit-budget` em `mugen2sms/__main__.py`); 27 testes verdes (14 `vram_plan` + 13 `commit_budget`); `validate_measurement_tools.py` = **72 ferramentas com self-check passando, `problems: []`** (§19; artefato em custódia). `commit_budget` mede orçamento por VBlank com semântica de quiescência (roda até nenhum slot pendente vivo; stop duro contra política degenerada) e rastreia o pico de pares (`peak_used`); `vram_plan` valida regiões disjuntas (fixture PNT/0x3800 corrigida). Ainda é instrumento — a ROM v033 não o usa.
- **Gates pagos na v033.** Corredor de sondas **pass** (77 sondas, folga 1547 B, `0xC800..0xC8FB`, map `f348df69…`, artefato `d9fba3e4…`); auditoria do contrato de engine **planning, contract_pass, problems []** — corrida `20261018T183841Z_engine_contract_v033.json` e re-execução pós-edição `20261018T185411Z_engine_contract_v033_postedit.json` (bytes idênticos `412044c4…`; o relatório não lê `implementation_profiles`); `doc/engine_quality_contract.json` ganha no perfil de produção o candidato v033 + evidência de worst-frame + ponteiro `evidence` para o manifest do lote (sem promover budget: `approved_budget: none` segue). Fechamento do lote: manifest `out/logs/runs/20261018T185306Z_loteB1_manifest_14381bf45688.json`.
- **Close-out de sincronia doc↔repo.** `audit_doc_sync.py --root .` em `out/logs/runs/20261018T185950Z_doc_sync.json`: **0 problemas no rev2**; as 10 derivas encontradas são todas do `luta_mugen` irmão por `[Errno 5]` (EIO de mídia, pré-existente; sem fsck/remount por mandato) — não mascaradas.
- **Incidente de sessão**: a sessão zumbi `9778b042…` (sha v033, ttl 900) foi encontrada viva, com um único `status` ack e nenhuma leitura, e fechou por TTL. Registrada para alimentar a regra de sessão do emulador (§46/L057): nenhum gate caça janela por nome sem antes checar instância viva — senão mede a ROM errada e emite veredito confiante.
- **Limites.** O worst-frame mede a **fatia de VDP** (upload + SAT) com 2 atores e fundo sólido — não mede HUD/FX/áudio do entregável ⇒ `approved_budget` permanece inexistente. O teto de tempo da **lógica** segue aberto: `probe_frame/VDP` = 0,51–0,56 (≈2 frames VDP por iteração do laço). Prova do mapa VRAM por plano, paletas por papel, movimento px/limpeza/residência/publicação (probes desejada/residente/submetida/apresentada) e teto de SAT 64 sprites/cena = itens do B.2. A matriz causal é teto `diagnostic_only`; nada aqui promove fps, áudio, qualidade visual ou entrega.

Próxima ação: Lote B.2 — subir a taxa de upload dentro do orçamento medido (`runtime-commit-budget` justifica chunk > 1 par/VBlank), política de emissão para o flicker/omissão (parcial/preditor), híbrido BG corpo+SAT, prova do mapa VRAM contra `runtime-vram-plan`, teto de SAT 64 por cena como contrato medido, reancoragem das janelas D2/G na ordem de produção e teto de tempo do loop. Decisões humanas intactas (remapeamento 2-botões por unidade + 9 supers, curadoria do wrapper com os candidatos já registrados nas ondas, autoridade externa MUGEN para reset-por-frame vs carry-forward, ambiente sem throttle p/ fps, BG/híbrido vs escala/arte).

### Lote B.2a (2026-10-18): loop de produção com política de upload medida (chunk 8 supersede), emissão servindo os dois atores e derrame por desenho registrado

Fontes: `src/main.c` (probes B.2a 0xC862–0xC887 + estágios 0xC888–0xC88C; `stream_pending` com chunk por lado; laços `#if LUTA_PROFILE`); mandato `doc/25` §§77–92; custódia `out/evidence/loteB2a_20261018/` (candidatos v035 com SHA próprio, fontes, logs, probes, rank); manifest `out/logs/runs/20261018T202627Z_loteB2a_manifest_a613ca974e2c.json`.

- **Política escolhida por regra pré-registrada** (fixada antes dos números do serve): cadence = (wait_p1+wait_p2)/smrt frame; depois churn superseded (só comparável dentro do mesmo modo), integridade `sat_om_p2` e fit `vovf`. Seis candidatos sequenciais, cada um com SHA próprio e único delta declarado (chunk 2/4/8 pares por lado × supersede/serve em voo): ordem **p1c8 1,2332 < p1c8srv 1,3005 < p1c4 1,3277 < p1c2serve 1,3967 < p1c2 1,4045** (p0ctl = controle diagnóstico, fora). Vencedor **p1c8 `a613ca97…`** = chunk 8 + supersede (fonte `042ba22e…`), restaurado como source de produção e reverificado por rebuild byte a byte.
- **A emissão do B.1 era metade servida.** O "pass" da v033 fechava 1 par/VBlank em round-robin e deixava um lado sem imagem; no B.2a os dois atores são servidos por VBlank (`sat_om_p1=0` sempre) — o custo real da emissão aparece e o slice excede o VBlank por desenho nesta escala. Worst-frame do vencedor: `derramou`, vovf 2511/3000, vline_min 0 (sessão `05f87780…`, JSON `b1bbb032…`); a janela de lógica segue intacta (entrada constante no work = 194), a imagem apresentada é sempre a última pose COMPLETA e o no-evict é medido (`evict_events=0`) — produção não desaloja o oponente (§88); overflow por lado registrado (198/291) e pool no teto (128 pares, `free_pairs_min=0`) com recuperação medida sem evict.
- **Linhas por etapa (instrumento `p1c8stg` `d566d814…` = vencedor + patch de estágios; delta declarado = 2 leituras extra de VCounter por frame):** upload ≤200, cópia de SAT ≤31, fatia ≤221 linhas, entrada ≤2 (nunca invadiu o ativo); bytes novos 43.969 pares ≈ 2,81 MB na janela; o mesmo selo traz o funcional vivo (14 hits, 1 KO, 70 `clsn_checks`). Sessão `bec977bc…`, JSON `d349bcb5…`; corredor pass (102 sondas, folga 1539 B).
- **Serve×chunk: hipótese refutada medida.** Em chunk 2 o serve tinha o melhor fit (`vovf` 1373) com o pior cadence; em chunk 8 a vantagem NÃO generalizou (2580 ≈ 2511). Serve fica preservado como alternativa documentada para recomparação pós-híbrido (§92).
- **Gates pagos.** Corredor de sondas pass nas duas ROMs (97 produção `20261018T202552Z_probe_corridor_c8_a613ca974e2c.json` / 102 instrumento; folga 1539 B, `0xC800..0xC8FB`); contrato de engine **planning, contract_pass, problems []** pós-emenda (`20261018T202727Z_mugen_contract_postB2a_4c592813ac6b.json`); `validate_measurement_tools` **72 ferramentas, problems []** (`20261018T202734Z_measurement_tools_validate_b2a.json`). RAM/stack: `_DATA` 504 B + `_INITIALIZED` 5 B até 0xC1FD; stack SP=0xDFF0 com 5876 B livres acima do corredor; profundidade de stack não instrumentada individualmente (declarado). Fps de emulação por journal: 59,851–59,861 em todas as sessões.
- **Limites e lacunas declarados.** `uploaded_pairs` (bytes novos) só existe no instrumento — os cinco candidatos anteriores usaram churn+overflow como proxies de desperdício (declarado no manifest; a próxima rodada já lê bytes); teto de SAT 64 sprites/cena e o mecanismo do `sat_om_p2` do serve (2493) a medir no B.2b; vídeo de transição 256×192 e híbrido BG+dirty regions ficam no B.2b; `approved_budget` segue inexistente.

Próxima ação: Lote B.2b — híbrido BG corpo + partes/FX na SAT (comparação de decomposição se o custo justificar), mapa VRAM único por plano (regiões disjuntas, janela reg6, PNT/SAT/fonte/HUD/current/pending/FX), paletas por papel P0/P1/P2, movimento px/sub-tile/dirty regions/restauração de fundo, residência/deltas/reuso real, teto de SAT 64 sprites/cena como contrato medido com o mecanismo do `sat_om_p2` do serve, vídeo de transição 256×192 na política vencedora, reancoragem D2/G. Decisões humanas intactas (remapeamento 2-botões por unidade + 9 supers, curadoria do wrapper com os candidatos já registrados nas ondas, autoridade externa MUGEN para reset-por-frame vs carry-forward, ambiente sem throttle p/ fps, BG/híbrido vs escala/arte).

### Lote B.2b (2026-10-19/20): híbrido BG + SAT livre reprova no pacing; sprite-only v036 + política de SAT é o fallback declarado

Fontes: `doc/25` §§73–92; relatórios `out/logs/runs/20261019T090500Z_b2b1_vram_blank_palette_sat.json`, `out/logs/runs/20261019T225500Z_b2b2_hybrid_v3_vs_spriteonly.json`, `out/logs/runs/20261020T005000Z_b2b3_decision.json`; custódias `out/evidence/loteB2b_20261019/b2b1/`, `.../b2b2/`, `.../b2b3/`, `.../b2b3_blastem_bankmask/`.

- **B2b-1** caracterizou VRAM/paleta/SAT e abriu o caminho do híbrido; o relatório e a custódia são a fonte, sem promoção de budget.
- **B2b-2 — sprite-only v036 `7002b0ba…`**: corredor pass (110 sondas, folga 1539 B); render P2 587/2262 = 26% (SAT-64: 382 adições omitidas em 116 frames; nenhuma pose inteira, melhor 15,4%); selo 300 s `smrt_frame=5745` (95,4% do baseline v031 `a613ca97` 6025), slice 221, sat_delta 31.
- **B2b-2 — híbrido v3 v037 `b68061ce…`**: corredor pass (114/1069); P1 2250/2250 e P2 1786/1786 (100%, resíduo 0) na captura Emulicious mid900; SAT 0/64 livre; **pacing 3945 (-31,3%)**, slice 255, `bg_cells_max 70`, `bg_bytes_max 552`. Render pass em **um quadro**; estabilidade temporal não provada. Relatório B2b-2 preservado, não sobrescrito.
- **B2b-3 — writer direto v038 `07f4abce…` (C)**: render P1 66,8%, P2 51,7%; mid900 `smrt_frame=220`; render fail.
- **B2b-3 — writer direto v039 `d5f10d04…` (asm flush-first)**: render Emulicious mid880 P1 86,3%/P2 60,3%, mid900 P1 58,9%/P2 49,5%; selo 300 s `smrt_frame=4177` (-27,3% vs v036; +5,9% vs v037), `stage_slice_max 255`, `stage_flush_max 255`, `bg_frames 1400`, `uploaded_pairs 35811`. **Render fail + pacing fail.**
- **Correção de medição (BlastEm 1.0.0)**: `update_mem_map` aplica `bank &= (rom_banks - 1)`; ROM de 52 bancos → máscara `0x33` (28→16, 27→19, 4→0, 5→1). O dump não-padded do BlastEm não é oráculo de arte; a prova Emulicious do v037 permanece válida. A cópia padded de 1 MB (64 bancos, `0x3F`) mostra o slot P2 do v039 em `bank28@0x2E80` 1984/1984: arte/banco corretos, falha do writer/raster. Repro `bankmask_repro.py` self-check 13/13; addendum `20261020T004000Z_b2b2_addendum_blastem_bankmask.json`.
- **Decisão**: nenhum híbrido promovido. Fallback **sprite-only v036 + política de SAT** (alternar ordem P1/P2 a 30 Hz ou rotacionar os 6 excedentes; medir `audit_sprite_line_sim` ≤8/linha e `capture_video` 256×192). **Tradeoff §92 declarado**: o híbrido libera SAT para partes/FX, mas custa 27–31% de pacing; o fallback preserva o pacing e usa a SAT para os corpos, então os FX ficam adiados/limitados e exigem aprovação humana. Nenhuma arte/escala/FX removida em silêncio.
- **Estado**: produção restaurada `out/rom/luta_mugem_rev2.sms` sha `087df676…`; HEAD `da86de3`; sem commit/push; sem sessão de emulador viva (o `Xvfb :99` é pré-existente). O irmão `luta_mugen` segue com EIO pré-existente, intocado (sem fsck/remount).

Próxima ação: Lote B.2b-3b — implementar e medir a política de SAT do fallback (ordem alternada/rotação + 8/linha + vídeo), definir o destino dos FX (BG, SAT ou adiado), corrigir o empacotamento para 1 MB (header `0x4C` vs arquivo de 52 bancos; aprovação humana), guarda/auto-padding no wrapper BlastEm + lição L139 (aprovação), e fechar as pendências de CRAM P0/P1/P2, reancoragem D2/G, doc/15, manifest/contrato e print do `vram_plan.py`. O writer row-batched/contíguo (alvo ≤66 T/célula) fica como otimização futura do híbrido, não tentada.

### Lote B.2b-3b (2026-10-20/21): a quota 5+3 passa linha e §129, mas o pacing ainda falha; 6+2 é inválida por construção

Fontes: relatório `out/logs/runs/20261021T025418Z_b2b3b_sat_policy.json`; custódia `out/evidence/loteB2b_20261019/b2b3b/` (ROMs, fontes, mapas, SAT shadow, line sim, §129, vídeos, BlastEm v042/v043); relatório B2b-3 anterior preservado `20261020T005000Z_b2b3_decision.json`.

- **v040 (ordem alternada, `d998209b…`)**: pacing 5743 (≈baseline), mas linha **FAIL** — pico 14, 78/77 linhas >8, 4 visíveis descartadas nas linhas 85–89; render P2 26%.
- **v041 (cap whole-cell, `3f3dce97…`)**: a simulação passa 39/8, mas a varredura de 16 linhas/célula custa **2055 (-64,2%)**, `worst_done=0`, `sat_om=17029/17266`. Pacing fail; linha só simulada (não há SAT real do v041).
- **v042 (quota 6+2, `44315339…`, fonte `efde6b88…`)**: primeira linha real **PASS** (40 sprites = P1 30 a 6/banda + P2 10 a 2/banda; pico 8; `SpriteNextFree=40`), mas pacing **4483 (-22,0%)**, `vovf=2506`, `vbl_exit_max=255`; §129 **FAIL nas duas atribuições**: P1 player → ataque 6>5; P2 player → 2<3. O 6+2 é inválido por construção.
- **v043 (quota escalar 5+3, `13b78bd2…`, fonte `eb5576ad…`)**: pacing **5033 (-12,4% vs 5745; +12,3% vs v042)** — o escalar recupera parte do custo do array, mas não paga o gate. SAT real f002 = 40 (P1 15 a 3/banda + P2 25 a 5/banda), linha **PASS 40/8**, §129 **PASS** nas duas atribuições (o 5+3 maximiza o primário no teto e mantém o secundário no piso; o 4+4 também passaria, mas reduz mais o primário). O f001 é transição (P1 não emitido; 25 do P2) e não serve para §129. Vídeo 600 quadros/127 distintos/256×192/59,92 Hz; 5/3 mais equilibrado que 6/2 (`cheio ~1957`, `faixa ~974` vs 2223/596), mas a seleção “primeiras N” ainda pode produzir listras.
- **Cautela de captura v042**: os PNGs f1020/f1021 têm o mesmo SHA `ccdd51c5…` e mostram o lado cheio oposto ao shadow SAT do snapshot 1020; a captura pareada está um quadro de jogo atrasada/adiantada. O veredito visual usa o vídeo e a SAT shadow. A sonda `present=65535` sob quota significa “alguma célula omitida”, não corpo ausente; `sat_om` alto é omissão declarada, não overflow do SAT-64.
- **Tradeoff §92**: híbrido v037 paga -31,3% por render 100%; sprite-only v040 preserva o pacing mas viola a linha; quota 6+2 paga -22% e viola §129; quota 5+3 paga -12,4% e é a faixa de máxima completude do primário que satisfaz linha+§129 **sem** híbrido (o 4+4 também passaria, mas reduz mais o primário), mas ainda não é gate-passing. **Nenhum candidato promovido**; produção restaurada `087df676…`/`042ba22e…`.
- **Próximo candidato**: lista limitada **5/3 pré-computada** por pose/lado (emitir sem checagem por célula) com seleção espacial contígua/central, para remover o custo restante e as listras; medir pacing+linha+§129+vídeo. O híbrido row-batched/contíguo (≤66 T/célula) segue como R&D.
- **Lição corrigida**: a lição do bankmask do BlastEm é **L139**, não L137; L137 é silhueta e L138 é projeção SHA (alocadas em 2026-10-19). A menção antiga no B.2b foi corrigida.
- **Aprovações pendentes**: fallback/FX, empacotamento 1 MB, guarda BlastEm + L139, política 5/3 vs 6/2, gerador da lista pré-computada; depois doc/15, manifest/contrato, `engine_quality_contract.json`, CRAM P0/P1/P2, D2/G e `vram_plan.py`.

Próxima ação: implementar a lista 5/3 pré-computada e medir o selo 300 s + SAT/vídeo; se o pacing ficar ≥5745, levar a política 5/3 à aprovação humana; se não, declarar o teto do sprite-only e decidir entre híbrido (com writer row-batched) ou aceitar a omissão 5/3 com o custo medido. Sem promoção silenciosa.

### Continuidade de host (2026-10-21): snapshot `bdb32e7`, assets e build revalidada

Fontes: `doc/27-continuidade-reinstalacao-2026-10-21.md`; `doc/continuity/` (assets, repro, validação); handoff geral `doc/continuity/20261021-host-reinstall-handoff.md` na raiz; relatório B.2b-3b `out/logs/runs/20261021T025418Z_b2b3b_sat_policy.json`; custódia `out/evidence/loteB2b_20261019/b2b3b/`.

- **Snapshot**: o workspace foi versionado no commit `bdb32e7` (tag `continuity-20261021`, branch `feat/luta-mugen-motor`), incluindo fonte, `data/`, docs e scripts do projeto. `out/` continua ignorado; a continuidade específica está no commit filho com `doc/27` + `doc/continuity/` e nos assets da release `continuity-20261021`.
- **Canônico preservado**: ROM `087df676…`, fonte `042ba22e…`, banks/header gerados (`19edb320…`, tarball `aa6ea4ef…`), configs P1/P2 e custódia B.2b-3b. O candidato v043 `13b78bd2…` (fonte `eb5576ad…`) está preservado, mas **não promovido** (pacing 5033 < 5745; §129 passa).
- **Build revalidada neste host**: produção bruta `9873b3ff…` e v043 bruta `26b30567…`; ambas diferem do canônico apenas em `0x7FE6` (data SDSC) e `0x7FFA` (checksum SEGA) e canonicalizam para `087df676…`/`13b78bd2…` (PASS). Logs em `doc/continuity/VALIDATION_20261021_script.log`; script `doc/continuity/validate_after_reinstall.sh`; verificador `verify_canonical.py`. O gerador MUGEN foi revalidado byte a byte em 2026-10-21.
- **Assets**: `luta_mugem_rev2_full_20261021.tar.zst` (projeto completo, incl. `out/`), `loteB2_20261021.tar.zst` (custódia temp), `sdk_20261021.tar.zst`, `emulators_20261021.tar.zst`, `qa_toolchain_20261021.tar.zst` (bridge/BlastEm), `workspace_out_20261021.tar.zst` e `workspace_untracked_nonout_20261021.tar.zst`; hashes em `doc/continuity/RELEASE_ASSETS.sha256`.
- **Limite**: a validação é build/reprodutibilidade, não emulador. Os eixos `boot_emulador`, `gameplay`, `fps_constante`, `audio` e `memory_bank_atualizado` continuam abertos; render/SAT/§129 do SHA novo exigem medição viva. Nenhum delivery.
- **Próximo**: v044 com lista 5/3 pré-computada, seleção espacial contígua, selo 300 s + SAT/linha/§129/vídeo; aprovação humana da política 5/3 (e das demais pendências: híbrido/FX, 1 MB, guarda BlastEm+L139, doc/15, manifest/contrato, CRAM, D2/G, `vram_plan.py`). O irmão `luta_mugen` segue com EIO pré-existente e intocado; seu `out/` não está nesta release.

## 2026-10-22 — encaixe de tamanho CPS2 para o Master System

O motor `mugen2sms.converters.display_fit` exige, na definição do projeto, o framebuffer de origem. O alvo default é `sms` (256×192). CPS2 e CPS1 são 384×224, então o default aplica largura 2/3 e altura 6/7. Game Gear (160×144, 5/12 por 9/14) é alvo nomeado. Origem ou alvo desconhecido é recusado. Origem igual ao alvo fica identidade 1/1. Os modos `fighter_scale` e `legacy_quarter` continuam disponíveis e este comando não reescreve pixel por eles. `off` também não reescreve. Grupo 9000 fica de fora. Um marcador impede a segunda passada (exit 2). Tempos, flips e blend permanecem. Índice 0 continua transparente. `SMS_GLOBAL.md` não foi editado.

Perfil: `doc/display_profile.json`, source `cps2`, target `sms`, Ken e Ryu. Saída: `out/display_fit/sms_default/`. ZIPs de origem conferidos de novo e iguais ao SHA do intake (`b244ec9a…` e `6db7e29d…`). Marcador dos dois: `display_fit: source=cps2 target=sms x=2/3 y=6/7`, SHA-256 `40bf9c9d70b4d2b9dda0db67c057cbd1f33250877c9c62cdf8f1015eff464fac`. Resumo `summary.json` SHA-256 `45f9b05829412a1843102701fa554f545d8a1f4c602e9ea40974e0412daeb9c2`.

| Lutador | Sprites | Ajustados | Isentos | Quadros | Antes | Ajustado | Retrato | Slots de pixel |
|---|---:|---:|---:|---:|---|---|---|---|
| Ken | 201 | 199 | 2 | 411 | 135×140 | 96×112 | 120×140 | 1245763 → 786709 |
| Ryu | 525 | 523 | 2 | 1309 | 232×240 | 160×208 | 120×140 | 3428516 → 2150181 |

Durações preservadas nos dois. Retratos medidos no SFF: 25×25 e 120×140. O teto inclusivo do Ken continua 120×140 por causa do retrato. Ação 0, primeiro quadro: Ken `g0_0` 48×80, tempo 6, offset (2, 0); Ryu `g0_1` 48×80, tempo 5, offset (2, 0). A folha do Ken está em modo P e o canto é o índice 0. 80 px cai na banda histórica de 72–88. O `scale_pilot` não rodou.

Colunas de 8 px nos sprites ajustados: Ken chega a 12 e tem 29 acima de 8; Ryu chega a 20 e tem 118 acima de 8. Um idle isolado ocupa 6 colunas. Essa contagem não é aprovação de `audit_sprite_line_sim`.

Testes do host: `test_display_fit.py`, `test_sms_scale.py` e `test_cli_sms.py`, 23 passed. A ROM `out/rom/luta_mugem_rev2.sms` permanece com 851968 bytes e data 2026-10-20. Este lote não a recompilou e não a abriu no emulador. Nenhum claim de 60 fps, áudio ou entrega visual.

Estudo de 2026-10-22, sem mudar o motor: pose = ação AIR do corpo, quadro mais largo; FX e grupo 9000 fora. A pose de 12 colunas é a ação 440 (chute baixo), `g440_1`, 96×48, nos dois. Porta de 70% das ações já em ≤8 colunas: Ken 71/100 abre; Ryu 107/154 (69,48%) não abre, falta 1 ação. Se a pose mais larga virasse a referência uniforme 2/3, o parado 48×80 (6 colunas) cairia para 32×53 (4) e o chute 96×48 para 64×32 (8). Prancha: `out/display_fit/sms_default/estudo_corpo_8/ken_ryu_corpo_8.png`. JSON: `estudo_corpo_8/resultado.json`.

## 2026-10-23 — pose_budget vira o default e o piloto compila

A condição aceita está em `doc/28-pose-budget-8.md` e no primeiro parágrafo de `doc/11-gdd.md`. O default de `mugen2sms.converters.display_fit` passou a `pose_budget`: primeiro o encaixe CPS2→SMS (2/3 por 6/7), depois a referência do corpo. Porta `open` em 70% e `near` entre 69% e 70%. Abaixo de 69% a escala extra não entra. `framebuffer`, `fighter_scale` e `legacy_quarter` continuam opções. `SMS_GLOBAL.md` não foi editado e nenhum id de lição foi alocado.

Perfil: `doc/display_profile.json`. Saída da arte: `out/display_fit/pose_budget_8/`. Resumo SHA-256 `4ca2b8d76373297018b79bcc7e69e54ea9e88fcbd6ff4295b8b806cb9db4f4e4`. Segunda passada no mesmo diretório: exit 2.

| Lutador | Porta | Ações do corpo em ≤8 | Extra | Caso a caso | Corpo acima de 8 depois | Marcador |
|---|---|---:|---|---:|---:|---|
| Ken | open | 71/100 (0,71) | 2/3 | 29 | 0 | `7fba0349e33853efb81f0ed7fb1f967c9055cbe5ab1e7bad1bebc59f1b878244` |
| Ryu | near | 107/154 (0,6948) | 2/3 | 47 | 0 | `0ded20292cd3bc8525fa58de0f055485d8df936c9ab69e0e3fe4a4195ba80cf8` |

A referência dos dois é a ação 440, 96×48 depois do framebuffer. Célula do chute `g440_1` na arte nova: 64×32, 8 colunas. Primeiro quadro do idle: 32×56, 4 colunas; o quadro mais alto do grupo 0 fica 32×64. Slots de pixel: Ken 1245763 → 402707; Ryu 3428516 → 1086817. Onze FX do Ryu seguem acima de 8 colunas (teto `g8400` 112×24, 14 colunas) e não estão nos papéis do piloto. Retratos do grupo 9000 continuam 120×140. Durações preservadas.

O corte usa os mesmos 12 papéis e o mesmo pareamento histórico: P1 `ryu.zip`, P2 `Ken_Majik_.zip`. Os diretórios continuam `p1_ken` e `p2_ryu`. A ação 440 não é papel de runtime. Contagem de quadros e durações AIR iguais às da ROM anterior: 48 poses no Ryu e 45 no Ken. Na escala 40/49 havia 9 quadros acima de 8 colunas em cada um (teto 12 no Ryu, 13 no Ken). Neste corte o Ryu chega a 6 e o Ken a 8, no KO 64×32. Banks: 49 → 24. Imagem `versus_scene_banks_02.bin`: 802816 B (`3af7a307…`) → 393216 B (`468427efd8850a6323c7e4b99e216dea565e7e28e8f5fe23a6167edffe9bcba6`).

| ROM | Bytes | SHA-256 | Banks |
|---|---:|---|---:|
| `out/rom/luta_mugem_rev2.sms` (2026-10-20, intacta) | 851968 | `087df67677626bfcd61188cb5ff0a5c054eb4feb24c420434fcfbeebf5fa7a65` | 49 |
| `out/rom/pose_budget_20261023.sms` | 458752 | `9008505cb82232e42d1b57d3ecb852af70f566625995cfd3cb5b526b277b1eba` | 24 |

Header anterior `19edb320…`. Header novo `3be5a775c1b0779af60a894f7a0f6970a4f3d85e248314b74b4b40c9a1678955`. Comparação: `out/logs/pose_budget_20261023_compare.json`. O `src/main.c` e o `.mddev/project.json` vivos não foram editados; o link dos 24 banks foi feito numa cópia temporária. Testes `test_display_fit.py`, `test_sms_scale.py`, `test_scene_cut_scale_order.py` e `test_cli_sms.py`: 32 passed. O Emulicious abriu a ROM nova e a captura da janela saiu preta, então o status é `buildado`. Sem boot aceito, sem FPS, sem áudio e sem entrega visual.

Pacote de espera do curador, sem ID novo: `doc/curation/2026-10-23_pose_budget_aguardando_curador.md` e o JSON de mesmo nome, na raiz do SMSForge. Doze pontos PB-01–PB-12. Não entra no ledger nem em `SMS_GLOBAL.md`. O curador precisa reler `L083`, `L086`, `L088`, `L090` e `L091` antes de emitir lição. `issued_through` lido nesta data: `L138`.

O dono aprovou `pose_budget` como padrão do motor no mesmo dia. O diagnóstico de glitch ficou em `doc/28-pose-budget-8.md`. A paleta de 7 cores deixava o preto opaco de fora (8ª cor nos dois; 34/39 quadros de papel do Ken e 13/40 do Ryu perdiam contraste). `scene_cut._palette_codebook` reserva a cor mais escura e a mais clara. `_write_png` grava transparência no índice 0. Buracos novos da amostragem (26 pixels no Ken, 44 no Ryu) não foram preenchidos.

ROM da paleta reservada: `out/rom/palette_reserve_20261023.sms`, 458752 bytes, SHA-256 `f9ef0e27eef5e29d530b0fa4e5c8325bd8df84a1ab6e7d93e77873f40a2b76cb`, 24 banks, corte `out/generated/palette_reserve_20261023/`. Paleta na ROM: branco `3F` e preto opaco no slot visível de cada lado. A piloto `9008505c…` e a produção `087df676…` ficam nos caminhos antigos. `src/main.c` e `.mddev/project.json` vivos seguem em `ryu_ken_cross`. Log: `out/logs/palette_reserve_20261023_build.txt`. Comparação: `out/logs/palette_reserve_20261023_compare.json`. Status `buildado`. Sem captura de emulador, sem FPS e sem entrega visual. Sem ID de lição.

O dono reportou que essa paleta perdeu acuidade e ficou mais escura. Medição nas paletas `ken1` e `ryu02`: média 110,2 no Ken e 137,5 no Ryu, contra 115,9 e 142,3 nas sete cores frequentes. O creme do Ken (4840 pixels) ia para o rosa. `scene_cut._palette_codebook` agora só cede um slot abaixo de luma 100, que não seja a cor mais usada, se o erro quadrático não sobe e a média de todos os pixels opacos não cai mais de 1. O empate de distância usa o brilho mais próximo. Nestes lutadores o livro é o da frequência. O preto opaco fica de fora.

ROM da paleta de brilho: `out/rom/palette_luma_20261023.sms`, 458752 bytes, SHA-256 `6fb424a3ddf32002d5de9c27685c1387fa89d4205365b344ba64fe8c866cd873`, 24 banks, corte `out/generated/palette_luma_20261023/`. Paleta no offset 12311: `00 1A 1B 16 2A 05 2B 02 00 02 07 2B 0B 1B 2F 16`. Header do corte igual ao do piloto (`3be5a775…`). Banks `ec22ad12…`. As três ROMs anteriores permanecem. Fontes vivas continuam em `ryu_ken_cross`. Log: `out/logs/palette_luma_20261023_build.txt`. Comparação: `out/logs/palette_luma_20261023_compare.json`. O arquivo de luma em si não foi aberto. O parágrafo seguinte registra a captura de outro caminho com os mesmos bytes.

## 2026-10-23 — orçamento do par em sprite puro

A unidade do `pose_budget` deixou de ser a porta de cerca de 70% e a pose mais larga em 64 px. Essa porta fica como história do piloto da manhã, em `doc/28-pose-budget-8.md`. A condição vigente: pose neutra de cada lado em no máximo 4 colunas de SAT; golpe largo contra neutra em 5 e 3; o resto em `case_by_case`, sem reautoria e sem encolher o idle. `POSE_NEAR` 0,69 não abre nem fecha escala. Célula 8×16 transparente não conta. FX explícito acima de 3 colunas sai do corte. Grupo 9000 continua fora. `framebuffer`, `fighter_scale` e `legacy_quarter` continuam opções. `SMS_GLOBAL.md` não foi editado. Sem ID de lição.

Antes da troca, o piloto `9008505c…` mostrou os dois idles no framebuffer 256×192: `out/evidence/pose_budget_20261023_idle_256x192.png`, 1667 bytes, SHA-256 `64f5b9451439b5c37e4644f9f067bd9f2c6c80e23a1564e3b19ebff0f7e98800`. Os sprites saem. O runtime não mudou. As listras do Ken continuam. Essa captura não promove o piloto a entrega.

Fração aplicada no par: framebuffer `x=2/3` `y=6/7`, extra `2/3`, porta `idle_to_4`. O idle de boot fica 32×56, 4 colunas, 16 células. A maior célula neutra fica 32×64. `within_8_ratio` só no relatório: Ryu 0,8052, Ken 0,77. O motivo com `size_policy = pose_budget` e arte `pre_scaled` nomeia a fração; o corte não grava `downscale1:4`. `ratio.numerator/denominator` é a extra, não 40/49.

Papéis incluídos, pico de SAT 4: os seis neutros dos dois, mais special 1000 e ko 170 do Ryu. Caso a caso nos doze papéis: Ken punch 250 (6), hp 450 (7), kick 200 (6), hk 220 (6), special 1000 (6), ko 5080 (8, 64×32); Ryu punch 260 (5), hp 280 (6), kick 200 (6), hk 240 (6). Listas completas: Ryu 77 incluídas e 77 caso a caso; Ken 59 e 41. Os golpes largos permanecem na ROM porque o runtime exige o papel. Chave `p1_ken` é o corte do Ryu; `p2_ryu` é o do Ken.

FX fora do corte: Ryu 92 sprites (1150, 1160, 1250, 1260, 3050, 8010, 8020, 8030, 8050, 8060, 8210, 8220, 8230, 8300, 8310, 8330, 8400). `g8400` imagem 3: 112×24, SAT 12, padded 14. Ken: 4 sprites, grupos 1001 e 1002, SAT 4. Não foram para o plano de fundo.

Eixo no primeiro quadro de idle e de soco. Padding duplo acima de 1 px em relação à sola: não ocorreu. Ken idle e Ken punch ficam em delta 0. Ryu punch move 1 px por causa do pad. Ryu idle muda 2 px (fonte +1, resultado −1) e o corte do pad repete −1: a causa é a amostragem, não o pad. Sampler, eixo e hurtbox não foram alterados. A hurt do Ryu idle passa de 0 para 2 px além da sola porque a linha de baixo não foi amostrada.

Simulador, self-check antes da leitura, zero violações nos incluídos: idle/idle pico 8 (32 sprites); Ken idle + Ryu special pico 8 (30); Ryu special + Ryu ko pico 8 (30). Casos, sem reprovar o lote: Ken idle + Ken punch pico 10; Ken ko + Ryu idle pico 12. Log: `out/logs/pose_budget_pair_20261023/line_summary.json`.

| ROM | Bytes | SHA-256 |
|---|---:|---|
| `out/rom/luta_mugem_rev2.sms` | 851968 | `087df67677626bfcd61188cb5ff0a5c054eb4feb24c420434fcfbeebf5fa7a65` |
| `out/rom/pose_budget_20261023.sms` | 458752 | `9008505cb82232e42d1b57d3ecb852af70f566625995cfd3cb5b526b277b1eba` |
| `out/rom/pose_budget_pair_20261023.sms` | 458752 | `6fb424a3ddf32002d5de9c27685c1387fa89d4205365b344ba64fe8c866cd873` |

A terceira é byte a byte igual a `palette_luma_20261023.sms`. Esse arquivo de luma não foi sobrescrito e não foi o caminho da captura. A reservada `f9ef0e27…` permanece. Fontes vivas continuam em `ryu_ken_cross`. Corte: `out/generated/pose_budget_pair_20261023/`, 24 banks, imagem `ec22ad12…`.

Framebuffer desta ROM: `out/evidence/pose_budget_pair_20261023_idle_256x192.png`, 1658 bytes, SHA-256 `50beed8b55d73ff60f90384f52d60008e12e9d58070f8683f96209430e7a992a`, sessão `387f8561097d44c4847e1f263523a81f` encerrada. Os dois idles aparecem. Status desse framebuffer: `testado_em_emulador`. `measure_worst_frame.py` na sonda `0xC800` devolveu `sem_lastro` (frame 2035, `done` 0). `validado_budget` proibido. Menos banks não é FPS. Sem 60 fps, áudio, gameplay ou entrega visual. Testes do motor no fechamento: 47 passed.

## 2026-10-23 — parecer da captura do par

Revisão independente das duas capturas 256×192 e do log de linha. Motor, ROM, `src/main.c`, `.mddev/project.json` e `SMS_GLOBAL.md` não foram alterados. Sem ID de lição. O bloco «Resultado medido» de `doc/28-pose-budget-8.md` descreve o piloto da manhã `9008505c…`. A condição viva é o parágrafo do par, no topo desse arquivo e no GDD.

As duas capturas têm a mesma ocupação opaca. O diff é de 14 pixels, todos no Ken, de `(170,0,0)` para `(170,85,85)`. A paleta de brilho não desfez o desenho.

| Lado | Ocupação | Leitura |
|---|---|---|
| Ryu, esquerda | x 70–99 (30 px), y 108–160 | Idle coerente: gi branco, faixa e luvas vermelhas, calça azul, contorno escuro |
| Ken, direita | x 118–121 (4 px), vão, x 126–141 (16 px), vão, x 146–149 (4 px) | O vão total é 32 px, 4 colunas. O corpo não fecha. Gi, cabelo e silhueta não se leem |

Veredito: há tinta dos dois lados. A imagem não melhorou. Status do framebuffer: `testado_em_emulador`. Entrega visual, não. A ROM do par é byte a byte `palette_luma_20261023.sms` (`6fb424a3…`). A produção `087df676…` permanece. O runtime não mudou; a causa das listras (stream no meio do upload, ou tile/ordem do P2) fica aberta até um quadro em que as duas poses já estejam residentes.

O simulador em `out/logs/pose_budget_pair_20261023/line_summary.json` não mede a luta. Self-check passou antes da leitura.

| Par | Incluído | Pico | Violações |
|---|---|---:|---:|
| idle / idle | sim | 8 | 0 |
| Ken idle + Ryu special | sim | 8 | 0 |
| Ryu special + Ryu ko | sim | 8 | 0 |
| Ken idle + Ken punch | não | 10 | 5 |
| Ken ko + Ryu idle | não | 12 | 5 |

Os três zeros são dois parados, um especial que já cabe em 4 colunas, e o Ryu contra ele mesmo. O soco do Ken (pico 10) e o KO do Ken contra o idle do Ryu (pico 12) estão na ROM. `included_pair: false` não tira o papel do binário. A regra 5+3 está escrita e não foi o par que passou.

Papéis que o runtime ainda exige acima de 4 colunas: Ken punch 250 (6), hp 450 (7), kick 200 (6), hk 220 (6), special 1000 (6), ko 5080 (8); Ryu punch 260 (5), hp 280 (6), kick 200 (6), hk 240 (6). Contra um idle de 4 colunas na mesma linha o pico é 9, 10, 11 ou 12.

Pontos abertos, registrados para o próximo lote. Não são implementação deste parecer.

1. Um framebuffer com as duas poses já residentes. É o que separa stream incompleto de defeito de tile ou ordem do P2.
2. Medir cada composição que a ROM pode mostrar: os seis golpes largos do Ken contra o idle do Ryu, e os quatro normais largos do Ryu contra o idle do Ken. Pico acima de 8 reprova a composição.
3. A regra 5+3 precisa ser célula emitida. O idle ficou em 4 e o golpe largo ficou em 5–8 no mesmo binário.
4. A hurtbox do idle do Ryu passa 2 px da sola porque a linha de baixo não foi amostrada. Sampler, eixo e hurtbox não foram alterados.
5. `measure_worst_frame.py` na sonda `0xC800` devolveu `sem_lastro` (frame 2035, `done` 0). `validado_budget` continua fechado. 24 banks medem tamanho, não velocidade.

Não promover a lei da fábrica, não emitir ID de lição e não substituir `087df676…`. O mesmo parecer está em `doc/curation/2026-10-23_pose_budget_aguardando_curador.md`: PB-13 captura, PB-14 simulador, PB-15 golpe largo, PB-16 hurtbox, PB-17 VBlank, PB-18 sem promoção.

## 2026-10-23 — fecho do par residente, composição legal e sola

O parecer PB-13–PB-18 foi fechado com ROM de prova nova: `out/rom/pose_budget_settled_20261023.sms`, 458752 bytes, 24 banks, SHA-256 `698e58ed5a0e9256cf2497783b5b0a4343464c15138ce5783c5b9fd98879b13a`. A produção `087df676…`, a piloto `9008505c…`, a reservada `f9ef0e27…` e o par `6fb424a3…` permanecem intactos. O gate foi compilado em cópia temporária; diff em `out/logs/pose_budget_settled_20261023/composition_gate/main_c_composition_gate.patch`, header `versus_composition_gate.h` com SHA-256 `1da1e952…`. `src/main.c` e `.mddev/project.json` vivos continuam em `ryu_ken_cross`; sem commit e sem push.

O binário `6fb424a3…` usa `LUTA_PROFILE 1` (pose residente). No frame 500 as duas poses pedidas estão residentes (`desired/resident/submit/present` 5/5/5/5 no P1 e 49/49/49/49 no P2), `_SpriteNextFree=32`, **16 células P1 + 16 P2**, x 69–100 e x 142–173. O Ken fecha o corpo; a listra anterior era pose não residente. PNG: `out/evidence/sessions/a40818afa1a5468da0ccbcf4735fede7/resident_gate_frame500.png`, SHA-256 `7281231d…`, frame 500. Status `testado_em_emulador`.

O gate deriva do META emitido e recusa em `set_role()` todo papel cujo anim passe de 4 células 8×16 por linha: 25 de 93 poses; P1 anims 6–9 e P2 anims 6–11. A prova emulada no frame 500 registrou `dropped_from_composition=2`, `block_p1=1` (role 7, 6 células), `block_p2=1` (role 7, 7 células), sem omitir coluna e sem encolher o idle. Os dez pares golpe×idle medidos dão pico 9–12 e cinco violações cada; idle/idle fica em pico 8, 32 sprites. `dropped_from_composition`: P1 punch/hp/kick/hk e P2 punch/hp/kick/hk/special/ko, com pico e frame em `out/logs/pose_budget_settled_20261023/composition_gate/dropped_from_composition.json`. Ryu special 1000 e Ryu ko 170 seguem legais (máx. 4 células/linha).

A medida da sola foi corrigida: o `AXIS` gerado já inclui `frame.y`. Com `AXIS_y + linha da sola`, Ryu idle F0 fica `-53+53=0`, hurt bottom 1, delta **+1**, não 2. Ryu punch F0 delta −3; Ken idle F0 delta −1; Ken punch F0 delta −2. Os quatro amostradores (`current`, `ceil`, `full`, `src_len`) não movem a sola do Ryu no pipeline real; `full` move o Ken em 1 px e não fecha o Ryu. Sampler, eixo e hurtbox ficam inalterados; a premissa de 2 px era erro de medida.

Pior quadro na ROM final com gate: `derramou`, `vline_min=4`, `vovf_delta=1740`, `snapshot done=1`, frame 4079. Na pré-gate `c45dbd4a…`: `derramou`, `vline_min=2`, `vovf_delta=1770`, frame 3946. O 144 do resumo anterior era `vline` do snapshot, não `vline_min`. `validado_budget` continua proibido; o gate não comprou orçamento. Detalhe técnico em `doc/28-pose-budget-8.md`, seção «Fechamento». Sem ID de lição, sem terceira paleta, sem entrega visual, sem áudio/FPS/gameplay.

Registro para curadoria futura: `doc/curation/2026-10-23_pose_budget_fechamento_pb13_pb18.md` e o JSON de mesmo nome. O pacote fecha PB-13–PB-18 como medição, lista os sete aprendizados candidatos C1–C7 sem emitir ID, implementa e testa as quatro ferramentas de medição (self-check + 8 testes) e separa o que é regra de projeto do que precisa de aprovação humana para virar lei da fábrica. `SMS_GLOBAL.md`, ledger, `lesson_routes.json` e `id_registry.json` continuam intocados em `L138`.
