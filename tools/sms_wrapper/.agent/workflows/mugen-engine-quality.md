# Workflow: qualidade de engine MUGEN → SMS

Aplicar em criação, revisão e promoção de consumidores do motor. Norma:
`doc/05_technical/mugen_engine_standard.md`; regra SMS_GLOBAL §68.
Intake e seleção de states/actions seguem `skills/sms-mugen-source-semantics.md`:
parse, geração, consumo no código e execução em ROM têm provas distintas.
Otimizações/caches/slots SAT seguem `skills/sms-runtime-optimization.md` (§103):
incidência na janela ativa, wrap de contadores, invalidação, fallback e
comparação do trabalho completo. Modelos estáticos não aprovam render dinâmico.
Pedido humano de 2026-09-26 autoriza esta curadoria. Escala pequena T10 é controle
histórico. O piso de entrega exige contrato do jogo e não reduz a ambição para
acomodar o primeiro backend.

1. Ler memory bank/GDD/spec/TDD, contrato `doc/engine_quality_contract.json` e
   as fontes doadoras registradas por hash. Confirmar console/região/contexto.
2. Executar `audit_mugen_engine_contract.py --self-check`; depois
   `--project <projeto>`. PASS de planning só confirma contrato completo.
3. Intake de arquivos MUGEN somente leitura → IR → classes de fidelidade.
   Preservar fonte, máscara, frame vazio, duração, pivot, CLSN e licença.
   Antes da matriz de golpes, derive um perfil de controle por personagem a
   partir do `.cmd` e das definições de comando daquele pacote. Registre SHA da
   fonte, botões físicos, tiers/limiares e golpes deliberadamente descartados;
   rode `move_checklist.py --controls <perfil-do-personagem>`. Não reutilize o
   mapa do personagem anterior por conveniência. Só marque `DROPPED` quando a
   decisão estiver explícita; ausência de suporte sem decisão continua
   `BLOCKED` (L093–L094). Semântica de tier precisa de teste diferencial e
   mutação, mas isso ainda não prova custo Z80 nem latência da ROM (L095).
4. Declarar canvas, área útil, escala opaca idle, poses excepcionais, input,
   roteiro, storyboard e coreografia. Antes da arte completa, gerar um corte
    piloto com razão uniforme por lutador; executar
    `mugen2sms/analysis/scale_pilot.py --self-check`, emitir o relatório de
    poses/stream e mostrar uma ROM diagnóstica no Emulicious. Reexecutar o mesmo
    relatório com `--video <captura.mp4>` para medir máscara, facing e pivô do
    frame inspecionado. Isso não aceita cadência AIR, zero-flicker ou ação
    completa. Antes de investir num scheduler sprite-only para zero omissões,
    calcule o limite inferior de sprites de 8 px por scanline sobre os pixels
    opacos exatos do corte, já na escala e espaçamento pretendidos. No
    histórico `luta_mugen`, a evidência do par Ken/Ryu encontrou linhas que exigem 9–10
    sprites quando o VDP só exibe 8. Se qualquer pose exceder 8, sprite-only
    sem omissões é impossível para aquela composição: pare a otimização do
    scheduler para esse objetivo e compare reautoria/escala/espaçamento com BG
    ou híbrido. Um limite ≤8 é apenas condição necessária, nunca aprovação. Rode
    então a simulação real com `audit_sprite_line_sim.py` (self-check antes), confira a imagem quadro a quadro com
    `audit_render_glitch.py` e meça VRAM, VBlank/worst-frame e FPS na ROM. Essa
    prova é específica ao corte medido; não transfira o resultado para outro
    personagem, escala ou distância. A etapa aplica evidência já registrada com
    L090; não cria uma nova lição nem promove capacidade. A entrega vigente
    exige zero omissões visíveis além do orçamento
   físico; multiplexação permanece diagnóstico e bloqueia promoção. Conservar
   ordem, duração, pivôs/eixos, offsets e CLSN nos dados;
   medir o pool literal de patterns da família idle e mudanças entre frames;
   comparar remapeamento por facing, pool current+next, deduplicação entre
   atores somente por igualdade exata de bytes, ligação de META/METAL a cada
   variante de paleta e prefetch seletivo. Patterns visualmente parecidos não
   compartilham índice. Calcular folga após reúso exato; caber sem reserva é
   candidato, não budget fechado. Índices P2 precisam de
   metadata própria ou equivalência exata provada contra o blob P2. Testar
   uma família completa e uma ação no emulador antes de liberar a arte final.
   `--require-measured` promove somente quando os budgets da cena também
   cabem. Medir concorrência/câmera/FX: linha, SAT, tiles residentes,
   RAM/stack e upload. Medir o tamanho/link das tabelas emitidas no ROM junto
   com os patterns. Se o header integral ultrapassar o banco fixo, tente aliases
   apenas para META/METAL byte-a-byte idênticos, mantendo símbolo e `_SIZE`; rode
   o auditor de tamanho e meça o link outra vez. Se ainda não couber, metadata
   e descritores AIR precisam de layout bancado e referências válidas após cada
   troca de mapper. O piloto Ken/Ryu agora cabe após 196 aliases (18.055 B
   poupados), mas seu harness só desenha dois idles frame 0. Um header recortado
   para a ROM diagnóstica não valida o layout do pacote completo nem a
   reprodução AIR. Para cada transição AIR, medir os pares novos exatos após
   reúso e dividir pelos ticks do frame corrente. `current+next` caber em VRAM
   não prova o tempo de upload: Ken idle 0→1 exige 480 B/VBlank e Ryu P2 exige
   183 B/VBlank no corte atual. São demandas calculadas; a taxa aceita requer
   ROM e probe de pior quadro, sem tratar 64 B/VBlank como limite universal.
   Antes do runtime, emitir e validar `selected_facing_pool.idle_cache_plan`:
   slots físicos sem colisão, metadata remapeada por frame, origem bank/offset
   de cada par novo e preservação de eixo, dx/dy, terminador e AIR. No corte
   Ken/Ryu o candidato usa 0–63 e 64–127, com pico idle current+next de 6.464 B.
   Este mapeamento determina o trabalho do runtime, mas não demonstra upload;
   medir no worst-frame da ROM e capturar todos os frames AIR antes de promover.
5. Identificar recurso dominante e comparar alternativa seguinte: deduplicação
   exata → recorte esparso → cache/stream → remap exato → FX/BG com owner →
   multiplexação cosmética medida → reautoria. Não transferir economia de SAT
   para VRAM/ROM na planilha. Corpo e perigo permanecem legíveis.
6. Só após o gate de escala, autorizar contrato de asset/model sheet e uma
   família piloto; pipeline de recursos com proveniência e fidelidade.
   Recorte/quantização é candidato.
7. Emitir dados com escala uniforme por personagem e descriptors por slot;
   provar mudança de `.def` sem mudar C do núcleo. Backend legado pode gerar
   probes, mas `--delivery` deve bloqueá-lo.
8. Integrar verticalmente e medir ROM: coreografia estável A/B, áudio real,
   instrumento calibrado, janela contínua (evitar DAP durante worst-frame),
   input com eco e posições. Falha de canal não acusa FSM. Dois fracassos sem
   delta exigem mudar representação/rota, não multiplicar tentativas cegas.
9. Provar KO, empate/timeout, rounds/match/revanche e interrupções de efeitos;
   CRAM, BG, banks e canais retornam ao estado contratado. Vídeo framebuffer
   sustenta animação/latência/flicker; screenshot sustenta estado estático.
10. Executar pipeline `mugen_fighting_v1.json`, auditorias integrais uma vez no
    fechamento e memória. Cada capacidade tem prova da mesma ROM e artefato
    primário próprio; não reaproveitar screenshot como prova de outro eixo.
11. Só propor entrega com gates de ROM/visual/áudio e revisão independente.
    O auditor de contrato nunca declara AAA. FM/PCM/raster permanecem candidatos
    até ter ganho medido e aceite na cena. Flicker é diagnóstico apenas; vídeo
    com omissão visível reprova a entrega.

A CLI `python -m mugen2sms --help` lista apenas rotas SMS existentes.

Adendo §§99–100: não começar QA de produção sem memory/GDD/spec/TDD legíveis.
Erro de leitura bloqueia a preparação afetada; não omitir nem reconstruir
documentos. Diagnóstico de fixture exige modo/motivo explícitos e não promove
o jogo. Para ordem AIR, emitir export fonte e trace ROM com IDs por N+1
fronteiras (terminal incluso), no perfil `air_identity_timing`; executar
`audit_import_semantics.py --record ... --require-air-identity` e revisar
independentemente fonte/export/probe. `air_timing` histórico continua duração
apenas; índice visto em amostra DAP não prova identidade em cada fronteira.

Adendo de expertise (SMS_GLOBAL §§95–98): QA usa snapshots V2 e relação
independent/chained explícita. Antes de aceitar dispatcher, registre unidade,
escala/frentes/facing e casos na fronteira fonte; valide o perfil suportado
com `audit_import_semantics.py --record ...` e a prova ROM correspondente.
Para timing AIR, compare fronteiras ROM e durações fonte; imagens iguais não
eliminam elementos. Reúso CMD byte-exato preserva símbolos/SIZE e precisa de
mapa pós-link, não de claim de folga futura. Cache de colisão precisa de
revisões válidas no contato e testes de defensor móvel/guarda/facing;
prova com P2 parado não paga isso. Selos de etapa devem passar
`audit_stage_attribution.py --report ...` antes de atribuição agregada; PASS do
perfil não converte overflow em budget aprovado. Conserve fonte e observações
hasheadas nos registros; o gate mede consistência, não compatibilidade CNS geral.
Para qualidade: `PYTHONPATH=tools/sms_wrapper python3 -m mugen2sms quality-check
--project <projeto> [--delivery]` (em uma linha).

Curadoria de reuso: `doc/curation/2026-10-24_mugenesis_rev2.md` e as receitas
atuais em `sms-mugen-source-semantics.md`, `sms-runtime-optimization.md` e
`sms-psg-audio.md`. Não depender de scripts sob o projeto legado com EIO para
preparar um consumidor novo. Os diagnósticos de composição/sola permanecem
fora dos gates globais; não autorizam cortar movimentos nem promover budget.
