# Curadoria de skills — 2026-10-07

## Avaliação e mudanças

A norma §§93–100 estava mais atual que várias skills e o release. O gate
ampliado identificou sete orientações explícitas supersedidas no estado
anterior; após correção, nenhuma dessas ocorrências permanece no acervo central.
O detector mede frases/commands reconhecidos, não análise semântica completa.

| Skill | Aplicação |
|---|---|
| evidence-protocol | Sessão privada, agência real, sete eixos e frescor |
| sms-input-pause | Frames P1/P2/console; ACK, consumo ROM e consequência distintos |
| sms-fight-input-proof | Baseline e sequência VDP; estado/guarda e dano do defensor |
| sms-video-evidence | Timeline completa, vídeo durante gesto; stepping sem FPS/áudio |
| sms-sprite-animation | AIR distinto mesmo RGB; export fonte e limitações de hold/loop |
| sms-psg-audio | Sink próprio, rota/duração/mute, sinal separado de música |
| sms-mugen-source-semantics (nova) | DEF/SHA, parse/generated/consumed/runtime e perfis restritos |

Workflows mugen-engine-quality/release-rom, mapa ARCHITECTURE e regra §101
atualizados. audit_learning_capture/selftest impedem a regressão reconhecida.
Reaplicadas lições existentes; registry segue L107. Não sobrescreveu .agent
local nem alterou fontes/assets de jogos. Nenhum commit/stage.

## Evidência nova desta rodada

- before_gate.json: sete contradições; learning_capture_final.json: clean.
- selftest_final.log: 90/90; measurement_tools_final.log: 54/54.
- importer_focused.log: 45/45, close/far, runtime-data, AIR fonte, expressões,
  arquivos. São testes offline, sem execução do game no hardware.
- Export real ryo221_source_only.json: fonte ffspRyo_v3.zip/ffspRyo.def/AIR
  registrados por SHA; cinco elementos, durações 6/8/4/4/8, seis fronteiras
  cumulativas e IDs 221:0..4/terminal. Fonte preserva elementos0/4 distintos
  mesmo group/image221/0, com CLSN diferentes. Nenhum timestampROM emitido.
- far_record_validation.json: contrato real de distância45/46 passa consistência
  racional do perfil declarado, não comportamento do combatente na ROM.
- source_inventory.json: snapshots/hash do material antes das alterações;
  skill_changes.json: aplicação/medidores por skill. Parecer final independente
  passou com limites, sem novos blockers; independent_review.json registra
  hashes/revisão nativa. Não é autoaprovação de produto.

## Pendências que não viraram habilidade validada

- Docs de luta_mugen seguem ilegíveis; doc_sync global FAIL obrigatório.
  Sem restauração/recriação/alteração do filesystem afetado.
- Objeto C, tabelas e controlador direct não provam link/ROM nem fidelidade CNS.
  Papéis importados sem consumidor, especiais sem entidade/dano, fases de
  salto/guarda/KO e physics/velset omitidos permanecem limitações por corte.
- Scanline/SAT estáticos não provam fluxo de tiles, worst-frame, carga em combate,
  60/50FPS, ausência de flicker ou AAA. Cache de contato dinâmico e casos de
  defensor móvel/guarda/facing ainda exigem prova própria na build atual.
- Source AIR hash-bound não autentica traceROM; IDs/timestamps da ROM devem
  ser instrumentados por fronteira. Intervalos16-bit não detectam múltiplas
  voltas sem protocolo adicional. Não montar prova do esperado como observado.
- Áudio de sinal não comprova música correta; comparação requer trechos alinhados.
- Esta rodada não executou ROMs. QA nativo da curadoria anterior é histórico
  diagnóstico do coletor e não é herdado como gameplay deste lote.

## Próxima ação técnica

Após os documentos voltarem legíveis, preparar contexto production novo e
medir lote vertical da ROM alvo em sessões privadas. Para cada feature, pagar
consumo/contato/mecânica, render, worst-frame e throughput antes de promover.
Não ampliar elenco ou prometer qualidade a partir apenas de contagem de IR.
