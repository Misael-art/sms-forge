# skill: sms-runtime-optimization

Use ao otimizar Z80, renderer, SAT, cache, streaming ou lógica de combate.
Aplica L013/L037/L061/L082/L089/L097/L131/L134/L135 e SMS_GLOBAL
§§97–100/103/122/125–126. Qualquer técnica permanece candidata até custo e
comportamento pagos na ROM alvo.

## Scroll: assimetria dos eixos (SMS_GLOBAL §122, L131)

- Reg9 (scroll Y) é lido **uma vez por frame**: não existe raster vertical por
  scroll. Banda vertical fixa sobre mundo rolando = troca de name table via
  reg2 em HBlank (Sylvan Tale), com bit0=1 (§121).
- Modo 192: tilemap de 224 px; acumulador de Y precisa de wrap explícito em
  224 — sem wrap cada volta produz descontinuidade silenciosa. Modo 224/240:
  tilemap de 256 px; o truncamento de `unsigned char` já basta.
- Gate: `audit_vscroll_wrap.py --screen-h <192|224|240> --source src/` antes
  de prometer parallax ou status bar vertical no GDD.
- H-scroll (PNT parcial): `N = (-cam) & 0xFF` — o registrador anda ao
  contrário da câmera; a tela x≥8 mostra a coluna PNT `cam_col+(x>>3)` e o
  anel mod-32 de colunas é reescrito a cada 8 px, **inclusive voltando**
  (§126/L135). Fecha com `LEFTCOLBLANK` (L043/§6) e `LOCKHSCROLL` para HUD
  fixo. Sem gate estático para sinal/anel: a verificação é a comparação
  framebuffer↔dados emitidos.

## Varredura em runtime vs tabela na emissão (§125, L134)

Laço do SDCC com locais via IX custa ~115–150 ciclos/iteração (ordem de
grandeza medida no piloto O2): decidir centenas de células por quadro derruba o
ritmo (~2.07 quadros na pior pose no O2). Decisão que depende de
pose/profundidade/célula vai **pré-computada na emissão**, bit a bit
(3 B/entrada no O2), e o runtime só consulta. Meça o efeito com
`measure_runtime_probe.py` (ritmo de loop) e o lado da emissão com
`audit_sprite_line_sim.py`; ciclos/iteração não são lei universal.

## Medir antes de escolher o atalho

1. Registre baseline da mesma cena/estado: ROM SHA, região, probe/schema,
   runner, input/IA, animação, posições/facing, duração e carga do host.
2. Varie um recurso por clone diagnóstico e preserve sources/build/logs.
   Desligar renderer ou IA ajuda localizar custo, mas muda o jogo; FPS desse
   controle não aprova o jogo completo nem causa exclusiva.
3. Meça execução contínua e worst-frame. Stepping/vídeo são para ordem/render,
   não throughput. Registre todas as janelas, inclusive regressões.
4. Marque fronteiras na mesma janela; VCounter localiza fases. Subtrair dois
   stamps não mede instruções exclusivas nem resolve voltas automaticamente.
   `audit_stage_attribution.py` verifica registros, não autentica instrumentação.

## Cache e fast path precisam de incidência útil

### Deadline e publicação do cache (L098/L099, §128)

Não confunda os quatro relógios: passos solicitados à ponte, ACK de frame VDP,
tick de simulação e elemento de animação. Intervalo em VDP requer baseline e
delta, não frame absoluto. Converter ticks até o teste passar comprova função,
mas não o prazo de resposta. Compare antes/depois por SHA próprio, mesma carga
e configuração; stepping não mede execução contínua.

Registre por ator bytes realmente novos por transição, idade do pedido,
cancelamentos e maior intervalo sem serviço. Current+next de um ator não paga
residência do par, projéteis e HUD. Uma cota de 64/128 B pertence ao pipeline
medido, não ao hardware. Compare reuso exato, cache, prefetch e cópia especializada
contra o trabalho completo e deadlines, em vez de apenas trocar prioridade.

Separe pose desejada, residente, submetida e apresentada. Não publicar cópia
de geração abandonada depois de dano/facing; não desalojar o adversário para
afirmar zero flicker. Reter a imagem anterior precisa de contrato coerente de
colisão/estado e prazo, não dano de pose futura ou congelamento silencioso da
física. `audit_observed_cases.py` rederiva asserts RAM e prazos observados dos
journals; pixels apresentados e invalidação real precisam de QA nativa.

### Representação que preserve o jogo (L090/L091/L133)

Se as máscaras reais exigem mais de oito entradas por linha, reorganizar SAT
não entrega sprite-only sem perdas naquele caso. Separar legalidade após corte
de integridade da arte antes do corte; omissão permanente pode ter zero flicker.
Híbrido BG/sprites é candidato até provar movimento sub-tile, overlap, facing,
limpeza e custo patterns+PNT dos dois atores. Patterns não são espaço da PNT.
Um bound estático baixo não aprova o renderer dinâmico. Reveja o menor contrato
necessário; não reduzir arte/escala ou retirar perigo/FX sem decisão explícita.

Comparar estado estável é trabalho pago mesmo quando o fast path não entra.
Preflight de par por cima do cache de cada ator pode adicionar custo ao fallback.
Não afirmar ganho pelo nome da otimização ou pelo contador acumulado no boot.
Animação idle, posição, facing, pose, transição e paridade de visibilidade podem
invalidar reúso; separar geometria/ordem dos slots e visibilidade por quadro.
Dirty bits precisam de owners e invalidação completa, não de hipótese de P2 parado.

Para incidência na janela ativa, registre contadores/frame de início/fim,
largura, unidades (por ator/par/frame), frequência máxima e política de reset.
`audit_counter_window.py --record ... --require-exact` aceita número exato
somente quando o limite declarado exclui outras voltas. Byte155→184 é
delta modular29; com até358 eventos, tanto29 quanto285 são possíveis. Sem
limite não há contagem exata. Contador16-bit também pode dar várias voltas.
Escolha janela menor ou instrumento mais largo/selado, medindo seu overhead.
O gate não autentica limite, reset ou associação da janela: revisar fonte/probe.

## Preservar comportamento e visual

Faça A/B com trabalho equivalente e janelas repetidas; logs históricos com
quantidades/cargas diferentes sustentam observação, não ganho causal universal.
Rejeite candidato que regride a medição disponível; causa interna pode ficar
aberta. Ganho de FPS não autoriza retirar animação, IA, áudio, contato ou sprites.
Provar dano em P2 passivo não aprova guarda/IA/projéteis/combate completo.
Modelo estático de slots/SAT com âncoras fixas não paga render dinâmico:
testar mudança de pose, espelhamento, overlap, entrada/saída de ação, prioridade,
paridade e ausência de restos/omissões com vídeo e `audit_render_glitch.py`.

Antes de promoção: build/link da mesma ROM, contexto production legível,
QA privada nativa por delta/regressão, worst-frame, FPS contínuo e áudio/visual
afetados. Sessão não iniciada por EIO é blocked/not_run, nunca teste simulado.
Memória guarda decisões rejeitadas e próximos experimentos com identidade exata;
não copiar hipótese do diagnóstico como solução resolvida ou taxa segura SMS.

## Diagnósticos de composição e residência (L006/L061/L086/L088/L090/L091)

Curadoria: `doc/curation/2026-10-24_mugenesis_rev2.md`.
`audit_composition_gate.py` e `audit_sole_alignment.py` continuam diagnósticos
limitados, fora dos gates globais. Self-check precede leitura. O primeiro
mede intervalos verticais 8×16 do META selecionado, com dy assinado; agrupar
só dy iguais perde sobreposições. Seu default 4 é política por ator, não regra
universal nem implementação de 5+3. O segundo mede última linha opaca + AXIS
contra CLSN2; última linha pode ser equipamento ou pose aérea. Diferença
geométrica não julga anatomia. PNG/frames.json/header têm hashes.

Num sprite fragmentado, cotejar pose desejada/residente/submetida/apresentada,
SAT e framebuffer do mesmo frame antes de atribuir ordem de tiles. Um quadro
residente completo elimina a hipótese somente naquele caso. O simulador mede
a composição fornecida; opt-in de nomes distintos não comprova identidade dos
bytes e não deve reprovar duelos espelhados legítimos.

Bloquear papéis largos protege um diagnóstico, mas deixa movimentos sem
execução: manter a dívida no contrato de combate. VBlank usa o campo selado
`vline_min`, não `vline` do snapshot (`measure_worst_frame.py`, v2).
`done=0` permanece sem_lastro; menos bancos ou SAT legal não pagam throughput.
