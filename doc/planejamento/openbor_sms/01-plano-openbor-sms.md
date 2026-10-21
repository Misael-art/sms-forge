# Plano — engine OpenBOR → Master System

Data: 2026-10-15. Estado: **planejamento**, sem implementação ou ROM SMS.

## 1. Objetivo e direção

Criar um importador/conversor e runtime reutilizáveis para executar no Master
System módulos OpenBOR dentro de um contrato de compatibilidade versionado.
O objetivo é converter o máximo possível automaticamente; o restante deve
receber diagnóstico, adaptação rastreada e trabalho assistido por especialistas.
Não é portar integralmente o executável OpenBOR para 8 KiB de RAM, nem declarar
compatibilidade universal por conseguir converter uma fase.

Destinos propostos para o implementador, ainda não criados por este plano:

- Engine/ferramentas: `tools/sms_wrapper/openbor2sms/`.
- Primeiro consumidor: `SMS_projects/openbor_sms_rev1/`, criado pelo bootstrap.
- Fontes imutáveis: `data/source_openbor/`; gerados: `data/generated/`.
- Documentos e manifests: `doc/`; builds, provas e diagnósticos: `out/`.
- Um `doc/artifact_registry.json` por consumidor, sem segunda árvore de assets.

Registrar `data/source_openbor/` e `data/generated/` como localizações distintas
do mesmo registry antes da escrita. Intermediários não são recursos integrados
de `res/`; o manifesto de proveniência runtime só os promove com seus gates.

O importador funciona no host; a ROM contém dados compilados e runtime C/Z80
com pools estáticos. Não precisa carregar/descompactar um PAK na RAM do console.
Scripts arbitrários não serão executados automaticamente por existir um parser.

## 2. Estado real do doador e fontes de verdade

Doador:
`/mnt/sdcard/Projects/Sgdk Forge/SGDK_projects/OpenBOR_Demo [VER.001] [SGDK 211] [GEN] [GAME] [BEAT_EM_UP]`.

Ler primeiro memory bank/contexto/matriz atuais e o follow-up de 15/10. As
entradas iniciais do memory bank ainda são de 12/10 e não encerram a investigação.
Referências importantes:

- `doc/openbor/automatic_capability_inventory_20261011.md`, atualizado até 15/10;
- `doc/openbor/source_to_consumer_matrix_20261012.json`;
- `doc/openbor/engine_compatibility_contract_v0_1.json`;
- `doc/openbor/source_manifest.json` e `doc/openbor/reference_sources.json`;
- `doc/openbor/curation_followup_20261015.md`;
- `doc/openbor/town1_group_wait_semantics_20261012.md`;
- `doc/openbor/m3r16_evidence_reuse_map_20261011.md`.

O doador tem importador central, mas seu runtime está em `src/openbor/` do
consumidor. O contrato 0.1 é draft; a matriz GAL registra 8/26 diretivas
adaptadas e 18/26 rejeitadas. Uma candidata aceita TEXT na linha 49 e fecha
por fault no ITEM da linha 58. A leitura visual/VDP posterior de 15/10 não foi
aceita: input não comprovado e tela ainda no menu. Existem provas históricas
de combate, queda e restart, mas não equivalência completa ou 60 FPS sustentados.
Não combinar ROMs/snapshots diferentes numa aprovação única do novo motor.

Pilotos preservados no doador:

| Piloto | Caminho relativo ao consumidor SGDK | SHA-256 |
|---|---|---|
| Golden Axe Legend | `rascunho/entrada_bruta/golden_axe_legend/GAL.pak` | `64da17e8b60118ca9bd3a0bbbf87ef4acea705b1485ec6b4c58bf2f4f50634c4` |
| Battletoads | `rascunho/entrada_bruta/battle_toads/battle_toads.PAK` | `f2c5319deb68da97c3a469d3cc27b0be6b05e6b840847237369e78a01146e7a6` |

A origem externa e versões originais desses módulos continuam desconhecidas.
O commit OpenBOR `787b6770409935137579715febf80cf7a529b748` é referência
semântica fixada, não prova de qual engine produziu/executava cada PAK.
Revalidar paths/hashes e direitos/escopo de uso antes do intake. Este plano
não copiou ou extraiu os PAKs nem alterou o projeto SGDK.

## 3. Reaproveitamento por camada

Raiz do importador doador:
`/mnt/sdcard/Projects/Sgdk Forge/tools/openbor2sgdk_forge/`.

| Camada | Código/método existente | Tratamento no SMS |
|---|---|---|
| PAK32/PAK64 | `pak.py`, casos em `tests/test_pak.py` | Alto reúso após revisar formatos, limites, colisão de nomes, caminhos e licença; leitura no host. ZIP tem inspeção separada na CLI, não no leitor PAK |
| Modelos/níveis | `model_text.py`, inventários em `analyze.py`/`level_inventory.py` | Reusar parsing e origem por linha; separar normalização de decisões de gameplay |
| Referência semântica | `reference_semantics.py`, `semantics.py`, regressões | Reusar expectativas e pin; preservar limites da versão e equivalência desconhecida |
| Fila de eventos | `level_event_table.py`; `src/openbor/ob_level_events.c/.h` | Candidato forte a reaproveitar kernel puro e testes host; adaptar inteiros, handles, callbacks, RAM, bancos e custo Z80 |
| Imagens | `images.py`, rotinas de inspeção em `emit_slice.py` | Reusar leitura/inventário onde independente; quantização, sheets, paleta, patterns e emissão serão SMS |
| Streaming | `streaming.py` | Reusar ideia de janelas/residência; refazer limites e modelo sem DMA; análise estática não é streamer |
| UI/cenas | `ui_inventory.py`, `ui_profile.py`, `text_import.py`, `scene_import.py`, `scene_text.py` | Reusar inventário/transcrição/fonte por SHA; criar backend SMS. UI profile não implementa menu; still de GIF não prova animação |
| Emissão | `emit_slice.py`, perfis e CLI | Extrair front-end neutro e IR; não copiar `.res`, `SPR_*`, layout/limiares MD ou nomes GAL como semântica universal |
| Runtime | `ob_belt.c`, `ob_world_stream.c` e kernels/tests host | Estudar invariantes e extrair trechos puros; renderer, cache, VDP, física numérica e áudio exigem validação SMS |
| Ferramentas SMS | tile/paleta/PNG, metasprites, banking, contratos, input privado, probes, áudio, QA/Harness | Reusar a implementação central existente após conferir APIs/contratos; compartilhar utilitários, não copiar uma segunda engine MUGEN |

Preservar autoria/licença e hashes de todo código realmente portado. Preferir
um adaptador local versionado e sem dependência de caminhos temporários/WIP
do SGDK. Bibliotecas compartilhadas só nascem quando há dois consumidores reais;
não fazer uma refatoração dos dois workspaces antes do primeiro slice SMS.
Não editar o doador ou instalar nele um backend novo durante este trabalho.

## 4. Contrato funcional e arquitetura

### Importação e IR

PAK → índice seguro → `models.txt`/`levels.txt` e dependências → modelos,
animações/frames/offsets/caixas, níveis/eventos/terreno/câmera, UI/cenas/áudio →
IR tipado com path/linha/SHA → perfil de compatibilidade → dados e código SMS.

Para cada diretiva/script: `exact`, `adapted`, `blocked` ou
`dropped_by_owner`, com motivo e evidência. Separar
`parsed → generated → consumed → observed → budget_validated`.
Unknown alcançável essencial bloqueia aceite do módulo; não saltar uma linha
para chegar ao chefe, nem contar parser, tabela emitida ou callback permissivo
como gameplay. Descobrir toda dependência alcançável, inclusive modelos/scripts
referenciados indiretamente. Registrar a fronteira de análise quando dinâmica.

### Runtime de beat ’em up

- FSM de atores/animadores; movimento, ataque/combo, hitstun, knockdown, morte,
  entrada/pouso, invulnerabilidade, IA e ciclo de vida de objetos.
- Representar separadamente posição horizontal do mundo, profundidade no chão
  e elevação. Fixar nomes/unidades e projeção segundo a fonte; tipicamente
  `screen_y = ground_depth - altitude`. Profundidade não é altura de salto.
- Hitbox/hurtbox, alcance em profundidade, facing, contato e janela de ataque
  seguem o frame apresentado e o perfil da fonte. Não aceitar dano entre
  faixas incompatíveis nem double-hit involuntário por frame/handle reciclado.
- Ordenação visual por profundidade com desempate estável; não muda colisão
  por conveniência de render. Separar chão/parede, obstáculo/plataforma, hole,
  queda, pouso e câmera. Física continua válida quando a FSM troca em pleno ar.
- Declarar o relógio da referência OpenBOR e as unidades de `delay`, física,
  AI e eventos. Não assumir que um tick de origem é um frame VDP; converter
  tempos com acumulador racional e política NTSC/PAL explícita, sem duplicar
  hits ou consumir input duas vezes. Velocidade de animação e de simulação
  precisam de provas distintas quando a fonte as separa.
- Pool estático e handles com geração/validade; morte, limpeza, restart e
  reutilização não deixam alvos, hits, scripts ou contadores pendurados.
- Scheduler tipado com cursor, ordem, grupos, espera, scroll lock, spawn,
  TEXT, ITEM, OBSTACLE e eventos de saída. Cada evento tem owner/lifecycle e
  reação a pool cheio, recurso ausente ou falha de carga.
- Um evento só avança quando o contrato define aceitação. Retry precisa ser
  idempotente; não duplicar entidade e não perder evento durante um VBlank.

O caso GAL Group/Wait é regressão importante: TEXT/ITEM/OBSTACLE não contam
como inimigos; Group 3 3, Long/Henin/Wait/Amaz precisam preservar ordem,
contagem e semântica do passe. Não trocar por uma regra intuitiva de “spawn
três e esperar” sem teste contra a referência fixada.

### Render, cenários e som

Este projeto é beat ’em up: **não herdar a exclusão de cenários do MUGEN**.
O primeiro controle pode usar fundo neutro diagnóstico. A fase jogável inclui
cenário/scroll/terreno adaptados e rastreados conforme o contrato do piloto.
O SMS não tem os planos independentes do Mega Drive. Parallax e HUD fixo
precisam de mapa/owners e técnicas compatíveis medidas, sem prometer igualar
planos MD ou raster vertical por reg9.

Pad SMS de dois botões: ataque/pulo como proposta inicial, combos/direções e
ações contextuais segundo o perfil da fonte. Pause/NMI não é um terceiro
botão livre por jogador. Mapa deve cobrir pegar/soltar/arremessar/especial se
o módulo os exigir; conflitos ficam explícitos. Primeiro ciclo 1P, depois
cooperativo 2P se incluído no contrato; sua carga não está aprovada por provar 1P.

HUD/vida/magia/vidas/score e menu/options/seleção/pause/continue/resultados
dependem do inventário do módulo e GDD. O núcleo serve a diferentes front-ends.
Texto/fonte e transcrição precisam de fonte por SHA; UI inventariada não é UI
implementada. Nenhuma tela de título autoriza criar branding/cutscene nova.

WAV/BOR/OGG ou áudio no PAK são fontes a classificar, não `.psg` pronto. Reusar
proveniência e análise; reautorar/adaptar música/SFX para PSG. PCM/FM somente
como perfil opcional com ganho e custo medidos, sem depender deles no combate.
Mix música/SFX, prioridades/restauração, pausa/restart e audição são gates;
preview offline ou sinal capturado não certificam fidelidade musical.

## 5. Medição antes de fechar o perfil

| Recurso | Restrição ou medição necessária |
|---|---|
| CPU | Z80/SDCC, sem float/malloc no runtime; medir lógica, IA, colisão, sort, PSG e cópias no pior frame |
| RAM | 8 KiB totais: atores, objetos, eventos, input, cache, stack e probe; mapa pós-link/corredor/canário |
| VRAM | 16 KiB compartilhados; PNT, SAT, HUD, tiles BG/atores e cache; não importar orçamento 896 tiles do MD |
| Sprites | 64 SAT, 8 entradas/linha incluindo hidden; modo físico 8×8/8×16, ordem e quirks declarados |
| Paleta | Dois bancos de 16 cores; P1 compartilhada com 15 úteis para sprites. Personagens/inimigos/FX coexistem na mesma política |
| Upload | Sem DMA; bytes/ciclos/pior VBlank medidos, não taxa herdada do MD ou limite universal de 64 B |
| ROM/bancos | Descritores/dados comprimidos/patterns e ponteiros bancados, restauração de bancos em owners/ISR/PSG |
| Desempenho | NTSC60/PAL50 como alvo regional, pacing e input→pose→contato separados; stepping não mede velocidade |

Não fixar quatro inimigos simultâneos porque o doador usa N4. Medir degraus
1 jogador+1 inimigo, +2, +3, depois 2P e FX/cenário/HUD/PSG reais. Escolher
altura/detalhe dos atores por prova, sem transplantar a meta 72–88 px do MUGEN.

Antes de otimizar scheduler, medir limite inferior de objetos por scanline
nas máscaras opacas reais e sobreposições de chão/profundidade. Se >8,
sprite-only sem omissões é impossível naquela composição. Comparar recorte,
cache, representação BG/híbrida, arte/escala autorizadas e coreografia. BG não
é solução gratuita para vários atores móveis; medir oclusão, facing, prioridades,
paletas e transferências. Não esconder inimigo, suprimir poses ou atrasar ataque
para chamar a cena de zero-flicker/60 FPS.

Admissão de inimigos/tetos do pool que mudem timing de waves são **adaptações
de gameplay**, não otimização transparente. Precisam contrato e decisão, com
fidelidade limitada. Falta de capacidade não autoriza omissão silenciosa.

## 6. Lotes verticais e aceitação

| Lote | Entrega incremental | Gate para avançar |
|---|---|---|
| O0 — intake | Bootstrap próprio, PAKs/versão/perfis/licenças/SHAs e inventário dependências | Sem paths obrigatórios no MUGEN/EIO; escolha dos pilotos e fronteira de compatibilidade |
| O1 — front-end neutro | PAK/model/level IR com origem, diffs e casos inválidos; separar emissão MD | Determinismo e diagnósticos completos; nenhum opcode essencial omitido |
| O2 — piloto VDP | 1 jogador+1 inimigo, animação/facing/profundidade, cenário mínimo rastreado e HUD | ROM SMS, vídeo frame-paced, SAT/VRAM/RAM/upload, paleta e escolha de representação |
| O3 — combate jogável | Movimento/profundidade/pulo/pouso, ataque→hit→dano→queda/recuperação, IA e PSG | Input causal, alvos móveis/profundidades diferentes, reteste e FPS/pacing/worst-frame |
| O4 — mundo/eventos | Câmera/scroll/terreno e scheduler, grupos/espera/spawn/lock/reset | Trace fonte→IR→evento aceito→entidade; não saltar owners ausentes; retry/pool cheio testados |
| O5 — objetos e escala | TEXT, ITEM/pickup/equip quando exigido, OBSTACLE, buraco/plataforma, maior elenco | Lifecycle completo, slots reciclados, prioridade/profundidade e carga simultânea medida |
| O6 — fluxo do jogo | Menus/options/select/pause/continue/resultados, dados de fase, áudio e transições | Rota começo→combate→clear/derrota→continue/restart→menu no mesmo hash |
| O7 — segundo piloto/2P | Battletoads e cooperativo conforme contrato; generalização por dados | Sem editar núcleo por nome de módulo; diferenças explícitas e performance própria |
| O8 — maturidade | CLI/install versionados, rollback, regeneração limpa, compat matrix e QA integral | Reprodutível, módulo aceito sem recurso essencial unknown, provas e limites por ROM |

Recomendação inicial: começar com o recorte GAL já inventariado e seu elenco
de referência; Battletoads é segundo piloto, não cópia da câmera/IA de GAL.
Não repetir extração/análise doadora intacta sem motivo; revalidar SHA e
portar dados intermediários quando o contrato semântico continuar idêntico.
Todo comportamento/custo SMS exige sua própria prova. Eventos sintéticos
testam kernels, não completam uma fase OpenBOR real.

Scripts: começar pela análise de alcance e baixar o subconjunto necessário
dos pilotos para IR/controladores explícitos. VM genérica ou tradutor AOT
amplo só se a demanda e custo justificarem. Desconhecido deve bloquear;
substituir `@script` por noop não é compatibilidade.

O4 pode validar o kernel e um prefixo real da fila. Se TEXT/ITEM anteriores
impedirem alcançar Group/Wait, antecipar o owner correspondente de O5; não
tratar a ordem dos lotes como licença para pular eventos. Aceitar a fase inteira
exige todos os owners essenciais alcançáveis, não só o prefixo que funcionou.

## 7. Harness, testes e organização

Até três especialistas ativos com writes exclusivos:

1. **Importação/semântica:** PAK/parsers/IR/contrato, events, scripts e testes diferenciais.
2. **Z80/VDP/runtime:** pools, actor/world kernels, paleta, renderer, streaming e budgets.
3. **QA/áudio/gamefeel:** pedidos nativos, reprodução, captura, mix, feedback e evidências.

O coordenador integra e decide escopo/claims/memória. Quem produz não aprova
seu domínio; alternar reviewer/worker ou fazer revisão posterior independente.
Harness planeja; execução real usa a ferramenta nativa de subagentes. Cada
worker tem sessão privada; medições FPS serializadas. Não partilhar probe
mutável, não gerar pareceres fictícios em JSON e não matar instâncias alheias.

Testes Python host para parser/IR/emissão e kernels C com fixtures; integração
por `--project`, sem caminhos hardcoded no doador. Replay de tabela, pool cheio,
stale handle, wait release, same-pass, interrupções e restart são regressões.
Mapear versão do probe/decoder e ROM; logs truncados/overflow não qualificam
uma timeline completa. SRAM/trace MD de milhares de registros não cabe
automaticamente no SMS: projetar janela curta e buffer compatível com 8 KiB.

Reusar os gates SMS atuais: recursos/proveniência/cutout/animação, SAT/mode,
tilemap/scroll/VRAM, RAM/corredor de sondas, símbolos, binding, render fidelity
e glitch, input/sessão privada, FPS regional/worst-frame, PSG/captura/review.
Gates novos OpenBOR propostos, **ainda inexistentes**: contrato de compatibilidade,
fechamento de dependências e semântica de fila ligada ao runtime. Criar cada um
somente ao implementar a necessidade, com `--self-check`, positivos/negativos
e calibração no acervo. Não passar AIR/MUGEN como schema OpenBOR por semelhança.

Emulicious permanece QA/produção SMS; BlastEm é diagnóstico complementar.
Consultas ao doador são read-only. Temp/cache/sessão/destinos devem ter leitura,
escrita e espaço verificados; diretório novo não repara o cartão. Não limpar
host alheio, mascarar EIO ou preencher documentos ausentes com suposto histórico.

## 8. Critério de engine madura

Uma engine madura exige importação repetível, contrato explícito, runtime
compartilhado, perfis e diagnóstico úteis, pilotos que exercitam capacidades
distintas, e aceitação de módulo sem buracos essenciais. Conversão de imagens,
uma wave, título ou kernel host não bastam. Não afirmar “OpenBOR completo” por
ter O0–O3 prontos. Medidas de fonte/IR/custo e revisões devem permitir ao agente
escolher a melhor adaptação e ao usuário entender o que preserva o jogo.

Meta de qualidade: leitura de ação, comandos, coesão visual, composição/mix e
ritmo. Não prometer equivalência visual, quantidade de inimigos ou aceitação
comercial antes de medir e revisar. Manter registro das decisões e alternativas
rejeitadas sem transformar experiência parcial em regra universal do console.
