# Workflow: checkpoint de qualidade do jogo

Use antes de ampliar conteúdo de um slice ou preparar uma release candidate.
Selecione critérios do público e do GDD. Não iniciar catálogo de técnicas ou
efeitos só para tornar a ROM mais complexa. Uma melhoria precisa resolver um
defeito observado ou tornar uma decisão/ação mais legível ao jogador.

## Contrato curto de experiência

No GDD/spec existentes, defina público, tarefa do jogador, controles, feedback,
condição de sucesso/erro e retorno. Registre os critérios verificáveis e o que
foi excluído. Compare referências aprovadas pelo aspecto específico (legibilidade,
resposta, animação ou arranjo), não pela reputação do título. Referência é régua,
não autoriza copiar assets. Expectativa comercial e preferência do dono não são
evidência de diversão ou aceitação de mercado.

## Casos que coexistem na cena real

| Eixo | Caso e evidência | Gate e limite |
|---|---|---|
| Controle | Entrada aceita → ação → feedback → consequência; neutralização/reentrada e bordas relevantes | `sms-gameplay-experience-review.md`, `audit_subagent_session.py`; ACK não prova ação |
| Fluidez | Runtime inteiro: IA, áudio, HUD, sprites e efeitos autorizados; pior combinação simultânea | `measure_runtime_probe.py --session`, `measure_worst_frame.py`; média de janelas não prova cada frame |
| Arte | Fonte aprovada, pixels de destino, poses e materiais; movimento e leitura no tamanho nativo | `audit_art_review_checklist.py`, `audit_render_fidelity.py`, `audit_render_glitch.py`, vídeo; igualdade de pixels não aprova luz/anatomia |
| Visibilidade | Ordem real SAT, hidden/transparência, dois atores/FX/HUD quando coexistem | `audit_sprite_line_sim.py`, captura frame-paced; manifesto não observa SAT real |
| Áudio | Música sozinha e com SFX repetidos/prioridade, pausas/transições e restauração de canais | `audit_psg_quality.py`, `audit_psg_channel_binding.py`, `capture_audio.py`; sinal/heurística não certificam composição |
| Estado | Reinício, derrota, reentrada e seleção/modos que o GDD inclui | `sms-state-transitions.md`, probe/vídeo; não ampliar escopo por checklist |

Prepare QA nativa pelo workflow central `subagent-emulator-qa.md`, com contexto
production legível, ROM/SHA atuais e uma sessão por worker. Screenshots não
comprovam game feel; captura por stepping não mede throughput. A reserva de
performance evita medições cooperativas concorrentes, não elimina toda carga
do host. Relate carga e incerteza de transporte ao interpretar FPS.

## FPS, pacing e resposta são critérios separados

`measure_fps.py` relata velocidade do emulador; `measure_frame_advance.py` e
`measure_runtime_probe.py` usam o contador da ROM. Sessão privada do probe exige
alvo regional: NTSC60 ou PAL50, pelo menos duas janelas, tolerância explícita
de até 1FPS e dispersão de até 1FPS. 55FPS constantes em NTSC reprovam esse alvo.
O resultado é taxa média regional das janelas, não promessa de zero quedas.

Para pacing, instrumente o deadline por frame na ROM e meça o worst-frame com
as fontes reais; um contador em ISR pode avançar mesmo quando o gameplay não
completou. Para resposta, registre frames de entrada aceita, primeira reação,
pose/evento e consequência; relate atraso sem escolher um número universal de
"controle bom". Hitstop intencional do GDD não se confunde com stall de upload.
Vídeo/probe/trilha precisam identificar a mesma ROM, janela e ação.

Ao interpretar um caso, usar `skills/sms-observed-case-evidence.md` e
`audit_observed_cases.py` quando houver journal compatível. O assert deve
reprovar direção errada, dano durante guarda, borda não atingida e ausência de
terminal conforme o contrato. Comparar RAM com o valor esperado não demonstra
apresentação; o revisor alinha desejado/residente/submetido com framebuffer.
Animação/ataque ainda ativo ao fim do vídeo não prova duração completa da ação.

Teste sob as cargas que coexistem, com prazo por ator e política de cache.
Um ator invisível, pose congelada por upload ou corte permanente não recebe
aprovação de qualidade porque SAT ficou legal ou o FPS médio passou. Antes de
ampliar o elenco, o slice de produção fecha essa relação com um ciclo completo.

## Revisão e decisão de crescimento

Revisor independente inspeciona os casos e relata defeito, risco, oportunidade
ou gosto, com cena/frame/input, impacto e reteste. Use
`quality_review_router.py` e os gates específicos; produtor não se autoaprova.
Se houver teste com jogadores, registrar público, tarefas, observações, tamanho
da amostra e limites. Não chamar parecer de agente ou fixture de validação de
mercado. Nenhuma ferramenta existente prevê vendas ou garante qualidade AAA.

Priorize o blocker que mais prejudica controle, leitura ou continuidade do
ciclo. Corrija em lote vertical, confira regressões afetadas e faça os gates
integrais no fechamento. Uma técnica avançada entra se melhorar a experiência
com budget medido e fallback; tamanho maior, mais cores/efeitos ou PCM não são
ganho automático. Atualize memory bank com ROM/SHA, casos, métricas, pareceres,
limites e próxima ação. Release segue `release-rom.md` e todos os eixos atuais.
