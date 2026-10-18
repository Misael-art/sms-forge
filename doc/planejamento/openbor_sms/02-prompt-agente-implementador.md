# Prompt — implementar engine OpenBOR → Master System

Você é o coordenador técnico de um novo motor OpenBOR → Sega Master System.
Implemente a engine reutilizável e seu primeiro consumidor por lotes verticais,
reaproveitando o trabalho saudável do SGDK Forge e do SMSForge. Não se limite a
relatório, parser, tela de boot ou demonstração de uma wave. Ao receber este
handoff para execução, siga o plano abaixo até o alcance autorizado e registre
qualquer bloqueio real, continuando nos ramos independentes seguros.

## Workspace, autoridades e estado inicial

Destino: `/mnt/sdcard/Projects/SMSForge`.
Engine proposta: `tools/sms_wrapper/openbor2sms/`.
Consumidor proposto: `SMS_projects/openbor_sms_rev1/`.
Esses dois destinos **não foram implementados/criados pelo planejamento**.
Verifique se já existem antes de escrever; retome o estado real sem sobrescrever.
Crie consumidor pelo bootstrap canônico, com documentos próprios e legíveis.

Leia AGENTS, diga `[Contexto SMS Carregado]`, siga RTK e leia a arquitetura/lei
central. Leia também:

- `doc/planejamento/openbor_sms/01-plano-openbor-sms.md`;
- `doc/planejamento/openbor_sms/03-auditoria-doador.json`;
- `.agent` central: `first-playable-slice.md`, `artifact-organization.md`,
  `product-quality-checkpoint.md`, `independent-quality-review.md`,
  `emulator-isolated-session.md`, `subagent-emulator-qa.md`;
- skills centrais de assets, sprite geometry/metasprites, VDP/VRAM/VBlank,
  banking/SDCC, runtime optimization, input, state transitions, PSG e evidência.

As referências `.agent` acima vivem em `tools/sms_wrapper/.agent/`. Cópias
locais existentes não são sobrescritas; sempre consultar o central atual.
Antes de implementar, ler/preencher memory bank, GDD, spec de cenas, diretrizes,
manifest e TDD do novo consumidor. Eles definem escopo e não são substituídos
por estado de sessão ou por este prompt. Documento com EIO bloqueia o contexto
afetado: não inventar seu conteúdo, não mascarar como ausência ou PASS.

## Doador real — leitura seletiva e sem alteração

Consumidor:
`/mnt/sdcard/Projects/Sgdk Forge/SGDK_projects/OpenBOR_Demo [VER.001] [SGDK 211] [GEN] [GAME] [BEAT_EM_UP]`.

Importador:
`/mnt/sdcard/Projects/Sgdk Forge/tools/openbor2sgdk_forge/`.

Leia memory/contexto e os arquivos do doador em `doc/openbor/`:
`automatic_capability_inventory_20261011.md`,
`source_to_consumer_matrix_20261012.json`,
`engine_compatibility_contract_v0_1.json`, `source_manifest.json`,
`reference_sources.json`, `curation_followup_20261015.md`,
`town1_group_wait_semantics_20261012.md` e o mapa de evidências M3r16.
Confronte atualização e SHA: nome de arquivo antigo pode conter atualização de
15/10; árvore/candidata histórica não é fonte ativa automaticamente.

O doador automatiza inventário/parsing/conversão parcial. Seu runtime está em
`src/openbor/ob_belt.c`, `ob_level_events.c` e `ob_world_stream.c`, não numa
biblioteca central instalável pronta. A matriz GAL é parcial, não prova de
compatibilidade geral. Candidata TEXT alcança ITEM linha58 e falha fechado;
readback posterior sem input comprovado/menu não prova máscara residente.
Não transferir essas medições MD para aprovação SMS nem copiar os blockers
como se fossem implementações prontas.

Pilotos de referência:

1. GAL: `rascunho/entrada_bruta/golden_axe_legend/GAL.pak`, SHA
   `64da17e8b60118ca9bd3a0bbbf87ef4acea705b1485ec6b4c58bf2f4f50634c4`.
2. BT: `rascunho/entrada_bruta/battle_toads/battle_toads.PAK`, SHA
   `f2c5319deb68da97c3a469d3cc27b0be6b05e6b840847237369e78a01146e7a6`.

Esses caminhos são relativos ao consumidor SGDK. A origem externa/versão
original dos PAKs é desconhecida. O pin OpenBOR
`787b6770409935137579715febf80cf7a529b748` é referência semântica condicional,
não origem demonstrada dos módulos. Revalide os hashes antes de copiar/ler.
Preserve avisos/licenças de software e escopo de uso dos assets; não inferir
licença de redistribuição de personagens por existir licença do importador.

## O que reaproveitar

Revise e porte o núcleo independente de plataforma de `pak.py`, `model_text.py`,
`analyze.py`, `level_inventory.py`, `semantics.py`, `reference_semantics.py`,
`level_event_table.py` e seus testes. Reuse inventários UI/cena/fonte e métodos
de transcrição com hashes. Estude o kernel C de eventos e testes host do
consumidor, preservando a semântica e adaptando custo/tipos/layout para SDCC.

`pak.py` lê PAK32/PAK64; a inspeção ZIP é separada na CLI, não capacidade do
leitor PAK. Registrar `data/source_openbor/` e `data/generated/` no mesmo
artifact registry antes da escrita, distinguindo intermediários de `res/`.

`emit_slice.py`, `images.py`, `streaming.py` e perfis misturam decisões MD:
separe front-end/IR do backend, não renomeie a saída `.res` como se fosse SMS.
Reaproveite regras de origem, cache, ownership, restauração e testes, não
`SPR_*`, DMA, H40, WINDOW/BG_A/BG_B, quatro paletas, XGM2 ou budgets MD.

No SMS, reutilize utilitários existentes de PNG/paleta/tiles/metasprites,
banking/build, artefatos, áudio, input privado, captura, probes e QA. Não faça
fork do motor MUGEN nem aplique AIR/CNS como schema OpenBOR. Extraia biblioteca
comum somente quando houver reúso real e testes, evitando duas cópias do mesmo
utilitário. Código central e geradores ficam no wrapper; o projeto é consumidor.
Não modificar o SGDK Forge para concluir este porte.

## Contrato de conversão e semântica

PAK → dependências resolvidas → IR tipado → perfil de compatibilidade → dados
ROM/bancos → runtime C/Z80 → ROM observada. O host extrai/compila; o SMS não
precisa manter o PAK completo em RAM. Preserve caminho, linha, bytes/hash,
tipo, unidade e identidade dos modelos/animações/eventos.

Toda feature tem estado `exact`, `adapted`, `blocked` ou `dropped_by_owner`,
com parser, lowering, consumidor, teste e prova por hash. Separar parsed,
generated, consumed, observed e budget_validated. Scripts `@script` armazenados
como texto não estão implementados. Classifique alcance e dependências; baixe
o subconjunto necessário dos pilotos para controladores/IR explícitos. VM/AOT
genéricos só depois de demanda e medição. Unsupported alcançável essencial
bloqueia aceite; não emitir noop silencioso nem reduzir o contrato para ficar verde.

Fixe a semântica do jogo nas dimensões corretas: horizontal do mundo,
profundidade no chão e altura de salto separadas, com projeção/tipos/unidades
declarados. Caixas e ataques usam profundidade, facing e frame ativo; o sort
visual não define colisão. Física não para porque um hit mudou a FSM no ar.
Handles/pools estáticos precisam de geração, cleanup e invalidação de alvos/hits.
Fixe também o relógio/unidades da referência: `delay` OpenBOR não deve virar
frame VDP por suposição. Use conversão racional e política NTSC/PAL, preservando
física, janelas de ataque e consumo único de input/hit; se o relógio original
for desconhecido, registre a adaptação e sua fronteira de equivalência.

Fila de fase é tipada e causal: spawn/group/wait/scroll-lock, TEXT, ITEM,
OBSTACLE, terreno e saída têm owners e estados de aceitação/falha/retry.
Não avançar cursor sem consumir o evento; retry não duplica entidade. Pool
cheio não autoriza apagar inimigo ou pular evento. Preserve ordem e semântica
do mesmo passe de Group/Wait conforme a referência pinada. Teste tipos que
contam como inimigos, morte/despawn, wait release, reentrada e restart.

## Meta jogável, gráficos e som

Comece em 1P e 1 inimigo com movimento no chão/profundidade, pulo/pouso,
ataque/combo, dano/defesa quando presente na fonte, queda/getup/morte, IA,
HUD e som. Evolua para mundo/câmera/terreno, eventos/objetos, fluxo de fase,
menu/options/select/pause/continue/resultados e segundo piloto. Planeje 2P
cooperativo como capacidade separada, com seu próprio teste e orçamento se
incluído no contrato. Não promovê-lo com uma prova somente 1P.

Ao contrário do consumidor MUGEN stage-free, o produto OpenBOR inclui cenários
e scroll adaptados ao módulo. Fundo neutro só é controle técnico inicial.
Não reautorizar sprites/cenários por código. Extrair/converter arte-fonte com
proveniência; mudança visual/escala/paleta que altere identidade precisa de
decisão e revisão. Fonte válida não é automaticamente conversão aprovada.

O Master tem 8 KiB RAM, 16 KiB VRAM compartilhada, SAT64 e 8 entradas por
scanline incluindo hidden, dois bancos de16cores e P1 sprites compartilhada
com15úteis. Sem DMA. Layout PNT/SAT/patterns/HUD/cache, bancos ROM, stack,
objetos e probe precisam de medida/margem pós-link. Não importar 896 tiles MD,
buffers SRAM de milhares de registros, nem o tamanho de ator do MUGEN.

Antes de investir no scheduler, medir máscaras opacas reais e sobreposição
de atores/FX/terreno: se limite inferior exige mais de8objetos numa linha,
sprite-only zeroomissões é impossível naquele corte. Compare representação,
recorte/cache, BG/híbrido e arte/escala/coreografia autorizadas. Meça um jogador
com1/2/3inimigos, depois2P, HUD/IA/PSG/FX completos. Não assumir quatro inimigos
porque o doador usa N4. Alterar admissão/timing de wave é adaptação de gameplay,
com contrato, não otimização transparente.

Dois botões por jogador: proposta ataque/pulo, direções/contexto para ações
extra conforme fonte. Não usar Pause/NMI como terceiro botão independente.
Registre as rotas de pegar/soltar/arremessar/especial e conflitos. IA e entrada
humana devem ter prova causal; não contar escrita direta de HP como input válido.

Áudio do PAK, inclusive WAV/BOR/OGG, é fonte a classificar/adaptar; não converte
automaticamente para PSG. Use reautoria/transcrição rastreada e aprovável,
arbitração/restauração de canais, música+SFX sob carga e audição independente.
Noise bit2=1 branco,0periódico; preview/FFT/pico não certificam composição.
PCM/FM opcionais só com ganho/custo demonstrados; não depender de uma solução
de voz que paralise combate. Legibilidade, resposta e ritmo vencem efeito sem retorno.

## Execução, especialistas e provas

Siga lotes O0–O8 do plano. Não converter todo o acervo antes de pagar um slice
jogável. GAL é piloto inicial recomendado; BT mede generalização real, não
mesmo código especial com outro nome. Mudança de pacote/modelo deve gerar
dados sem editar C do núcleo por identidade do módulo. Ampliar o contrato
quando novas features forem implementadas; não alegar universalidade com dois casos.

Use no máximo três especialistas ativos, com ferramenta nativa e tarefas
limitadas: importação/semântica; Z80/VDP/runtime; QA/áudio/gamefeel. Não permitir
writes sobrepostos; coordenador integra, decide claims, escopo e memória.
Produtor não se autoaprova. Harness planeja, mas não dispara agentes sozinho.
Não fingir agentes em JSON. Reserve outputs visuais/planilhas no registro único;
preserve pais, hashes, candidatas/aprovadas e versões de tentativa.

Para QA, preparar contexto production V2, ROM/SHA, casos e snapshots próprios;
uma sessão privada por reviewer e feedback nativo com cobertura. Emulicious
é produção/QA SMS; BlastEm complementa diagnóstico RAM/VDP/mapper. Não usar
GDB M68K ou capturas MD como prova SMS. Não usar desktop/foco/joystick do dono,
não matar sessões alheias e sempre fechar as próprias também na falha.

Unitários de container/parser/IR e kernels C devem usar fixtures explícitas;
integração parametrizada pelo novo projeto. Se O4 parar num TEXT/ITEM sem owner, antecipar aquele owner de O5: o lote pode
provar um prefixo, mas nunca aceitar a fase saltando eventos.

Testes host de Group/Wait ou
callbacks permissivos não provam playback do módulo. Probes têm schema/ROM,
janela curta e trace sem overflow, com mapa RAM/corredor/stack validados.

FPS regional NTSC60/PAL50, pacing/deadline e input→pose→contato são separados.
Medir em execução contínua e worst-frame com tudo simultâneo, não por título
do emulador, APNG/stepping ou contador ISR sozinho. Testar streaming/colisão
nas bordas, depth-sort, espelhamento, entrada/saída, hitstop, pausas e transições.
Capturas de timeline validam animação/omissões; screenshot não valida game feel.

Criar gates OpenBOR específicos só quando necessários: contrato de
compatibilidade, fechamento de dependências, eventos ligados ao runtime. São
propostas deste plano, não comandos já instalados. Cada gate novo terá
`--self-check`, caso válido/inválido, calibração real e integração à doutrina.
Use os gates SMS existentes antes de inventar duplicatas.

Antes de build/QA, conferir leitura/escrita/espaço nos destinos reais, incluindo
temp/cache/root das sessões. EIO não é falta de arquivo e diretório novo não
repara mídia. Não limpar arquivos/processos de terceiros. Preserve diagnóstico
e avance só em ramo seguro acessível.

Após cada lote: atualizar memória com fonte/ROM/hash, caso, métricas, limites,
defeitos, decisões e próximo blocker causal. Gates integrais no fechamento,
testes focados durante o lote. Relatar `Resultado / Bloqueio / Próxima ação`.
Não encerrar em inventário/build/boot se o próximo ramo autorizado é viável.
Não publicar/commitar sem a autorização aplicável e não elevar claim para
“módulo completo”, 60FPS, áudio aprovado ou AAA antes de suas provas reais.
