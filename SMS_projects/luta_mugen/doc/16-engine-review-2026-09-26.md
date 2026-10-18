# Revisão do motor e nova base mínima — 2026-09-26

Pedido humano: adotar Sangokushi III como piso de ambição e revisitar o método
MUGEN→SGDK. Norma vigente: `../../../doc/05_technical/mugen_engine_standard.md`.
Contrato local: `engine_quality_contract.json`. Snapshot read-only dos dois
doador/consumidor em `donor_review_2026-09-26.json`, com hashes dos arquivos lidos.

## Conclusão da revisão

Existe uma prova técnica útil, mas o motor ainda não cumpre a nova base mínima.
T10 não é referência de tamanho ou acabamento. A regra 1:4/48 px do GDD antigo
é supersedida como padrão de entrega; permanece somente perfil histórico para
reproduzir a ROM e comparar regressões. A ROM de 131.072 B SHA
`af9eb127895ed07de6884592bbac420e31c660b39d371d4c9f5faaacd629dc97`
não foi recompilada nesta revisão.

## Lacunas com evidência concreta

| Área | O que existe | Lacuna e ação |
|---|---|---|
| Entrada da ferramenta | Parsers/IR, generators scene_cut e versus_scene_cut em Python | `python -m mugen2sms --help` falhava com ImportError de `converters.bgfx`: CLI do MD sobrevivera sem seus módulos. Corrigida nesta revisão com dispatch somente de rotas SMS existentes. |
| Generalização | `fight.c` contém `ken_states`, `ryu_states` e `characters[2]`; versus generator prefixa literalmente ken/ryu | Provar troca `.def` sem editar núcleo; gerar descriptors por slot e remover nomes do núcleo num lote próprio. Não confundir dois pacotes integrados com generalização. |
| Escala | `sms_scale.py`: SCALE=4, MAX_COLS=4, MAX_TALL_ROWS=3; escolha de divisor por pose | Perfil de prova legado. Próximo backend precisa transformação uniforme por personagem/cena, silhueta/pivot/CLSN coerentes e sparse metasprite. Não aumentar imagem reduzida para fingir resolução. |
| Rendering/stream | Duplo buffering e banking; confronto Ken/Ryu com pico simulado de 8/linha | Tamanho grande + FX simultâneos e latência de pose não pagos. Medir todas as combinações e degrau seguinte; evitar que atraso de streaming altere frame data em silêncio. |
| Capacidade | T10 usa bancos 2–6 em ROM 128 KiB | Não prova capacidade 1 MiB. Fixture de fronteiras, bank ownership e linker ainda necessária. |
| Paleta | Slots compartilhados 1–7 e 9–15 no corte atual | Preserva simultaneidade técnica, mas qualidade de rampas/identidade por família não aceita. Raster não resolve duas paletas por lutador lado a lado. |
| Combate | Movimento, pulo, dano, guard e comando especial de P1 medidos em T10 | KO/reset, timeout/empate/match/revanche, especial Ryu e partida longa incompletos. |
| Instrumento de KO | `tools/prove_round_lifecycle.py` novo, ainda experimental | Três diagnósticos preservados: frame lido como byte; excesso de pausas DAP; oscilação de alcance. Último run: 32 aproximações sem chegar ao golpe, KO não confirmado. Não atribuir falha ao motor sem eco do input/dano. |
| Audio | PSGlib + seis chamadas de evento e BGM; captura com sinal | Não há tabela geral de prioridades no `audio.c`; qualidade/simultaneidade/retorno musical exigem prova. `PSGSFXPlay` por si não prova o contrato completo. |
| Palco/visual | Arena técnica vazia; contrato visual ausente | Gate visual T10 reprova. Storyboard/model sheet/arte vinculada e revisão de movimento continuam obrigatórios. |
| Cadência | Evidência anterior: worst-frame 3000, vovf=0; DAP 58,10/59,78; título e avanço medidos | Esses dados valem para T10 e para a coreografia amostrada. Não cobrem lutadores grandes, FM, raster, PCM ou nova carga. |

Os sete flags binários do build record não significam sete eixos plenamente
aceitos. A época visual e a cobertura de gameplay permanecem bloqueadas.

## Assimilação dos dois caminhos pedidos

| Fonte inspecionada | Técnica/decisão doada | Aplicação SMS e estado |
|---|---|---|
| `tools/mugen2sgdk_forge/doc/ROADMAP.md` | IR independente, fidelidade em quatro classes, etapas verticais | Já parcialmente assimilado. Workflow agora exige prova por capacidade e contrato de cena antes de emissão. |
| `runtime/README.md`, `runtime/mg_fight.c` | Ordem do tick, contato CLSN, rounds, FX render separados e restauração | Assimilar sem VM CNS. Próximo lote gera descriptors e registra a ordem entrada→FSM→física/animação→colisão→apresentação. Testar trace igual com FX on/off. |
| `stage_measure.py` | Medir composição final e residência real antes de converter; mesma quantização do emissor | Incorporado à rota. Backend SMS de palco ainda pendente: não copiar os limites TILES_VRAM/DMA do MD. |
| `stage_plane_profile.py` | Sweep de cada posição inteira, ownership explícito e erro de deslocamento | Incorporado à decisão de palco; SMS permite um BG e bandas, não dois planes. Prévia não prova runtime. |
| `fx_pilot.py` | Uma família AIR completa, frames vazios/loop/eixos/caixas preservados, budget e cores do catálogo | Incorporado à rota de assets. Portar empacotador específico SMS em lote futuro, sem copiar paleta 8+6+1 do MD como lei. |
| `Mugenesis_Demo/doc/mugen/vdp_optimization_options_2026_09_26.md` | Corrigir contagem→deduplicar→recortar/prefetch→remap exato→fallback cosmético→reautoria | Incorporado ao workflow com A/B e ganho por recurso. Flicker não libera automaticamente VRAM/ROM. |
| `Mugenesis_Demo/doc/10-memory-bank.md` | Medir overhead do profiler, janela fixa, ROM específica; aprovação de fonte ≠ de candidato | Incorporado ao protocolo de medição. Doador registra budget/visual abertos; não é certificado AAA. |

Nenhum diretório do SGDKForge foi alterado. Nenhum asset ou runtime MD foi
copiado. O snapshot de hashes documenta a revisão; o contrato original de
paridade continua identificando a cópia antiga e os desvios conscientes locais.

## Ordem de produção após a revisão

1. **Contrato e ferramenta (este lote):** norma, matriz de 20 técnicas, gate de
   contrato, CLI operável, memória/GDD/TDD e rota de entrega alinhados.
2. **Escala grande antes de arte completa:** medir cortes autorais 72–88 px e
   alternativa seguinte; sprites esparsos, custo por linha/SAT/pattern/ROM,
   transformação uniforme. Entregar uma ação de P1/P2 no emulador com vídeo,
   pivots e pose íntegra; arte candidata não vira final por passar contador.
3. **Dados substituíveis:** gerar descriptors/estados/IDs por slot, trocar `.def`
   e provar hashes do núcleo imutáveis e diferenças reais no emulador.
4. **Combate completo:** corrigir primeiro o harness (pulsos sem `continue`
   redundante durante tecla; eco de keys; abortar após repetição sem delta),
   depois KO/reset/timeout/empate/match/revanche e especial de ambos. A última
   falha de alcance é do canal de prova até evidência em contrário.
5. **Cena autoral e som:** stage source-view, storyboard útil/HUD, orçamento
   conjunto, família FX piloto, prioridade de SFX e retorno musical audível.
6. **Capacidade e otimizações:** fixture 1 MiB; cache/flip/dedup A/B. H-scroll,
   raster palette, flicker, PCM/FM só entram pelo recurso que realmente aliviam.
7. **Entrega por jogo:** mesma ROM e bundle atual, eixos/gates completos, vídeo
   de partida, percepção/escuta e revisão independente. Sem autoaprovação AAA.

Cada lote termina com delta observado e memória atualizada. Diagnósticos de
ferramenta não viram aprovação de engine, e lista de técnicas não substitui o jogo.

## Fechamento do lote de revisão

Resultados observados em `../out/quality_review_2026-09-26/`:

| Verificação | Resultado |
|---|---|
| Testes do conversor, incluindo CLI SMS | 92 passaram |
| Selftest do wrapper | 64/64 passaram; build opcional não executado |
| Autochecks das ferramentas de medição | 45/45 passaram |
| Sincronia documental e captura de aprendizado | PASS em ambos |
| Contrato em planning | PASS |
| Contrato em delivery | BLOCKED esperado: perfil legado + 12 capacidades sem aceite |

ROM preservada, SHA256
`af9eb127895ed07de6884592bbac420e31c660b39d371d4c9f5faaacd629dc97`.
Não houve novo build nem execução em emulador neste lote de ferramentas e
governança. O lote 1 está concluído; os lotes 2–7 permanecem trabalho de produção.
Não há aprovação de entrega visual, budget do novo perfil ou qualidade AAA.

## Continuação — piloto de escala antes da arte completa

O lote 2 avançou com uma ROM diagnóstica isolada e evidência real de Emulicious.
Os valores, hashes, transformação de pivôs/CLSN, vídeo e blockers de SAT, RAM,
VRAM e cadência estão em `17-scale-pilot-2026-09-26.md`. O perfil Ken/Ryu cabe
no alvo de idle 72–88 px e o frame estático foi visto no VDP. O auditor do corte
permanece `blocked`; ainda não libera a arte completa nem promove a engine.

## Continuação — regeneração P2 e prova do piso de escala

Os arquivos fonte originais de Ken e Ryu foram encontrados em acervo local
read-only e os hashes batem com os manifests anteriores. O corte regenerado tem
44/32 poses, escala uniforme 80/93 e 40/31, META/METAL próprios para cada pool,
e mantém a largura natural dos frames. O vídeo de uma ROM de estudo confirma
IoU 1,0 para as máscaras do idle frame 0 dos dois atores; somente o Ryu P2 usa
metadata de paleta P2 nessa captura. Ver relatório atualizado em
`17-scale-pilot-2026-09-26.md`.

Na primeira tentativa o header integral ocupava 34.724 B e falhava `Bank 1
overflow`; a ROM P2 usava projeção de dois frames. Esse linker blocker foi
resolvido pela deduplicação byte a byte de META/METAL. A atualização e a nova
captura da ROM integral estão em `17-scale-pilot-2026-09-26.md`. O header
compila completo, mas o harness ainda exibe apenas idles frame 0; cadência AIR
e budgets de combate continuam sem prova.

O acervo `mugen2sgdk_forge` e o consumidor `Mugenesis_Demo` continuam read-only.
Foram incorporados os métodos de pipeline/IR e fidelidade, medição após
quantização, sweep de câmera, piloto FX, ownership/restauração e escada de
otimização A/B. Regras de VM, DMA, planes, paletas e limites do Mega Drive não
foram portadas como fatos de Master System. Nem o projeto doador nem este piloto
atestam AAA; os sete eixos da T10 não são alterados por esta captura.
