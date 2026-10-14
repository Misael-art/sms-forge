# skill: sms-runtime-optimization

Use ao otimizar Z80, renderer, SAT, cache, streaming ou lógica de combate.
Aplica L013/L037/L061/L082/L089/L097 e SMS_GLOBAL §§97–100/103. Qualquer
técnica permanece candidata até custo e comportamento pagos na ROM alvo.

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
