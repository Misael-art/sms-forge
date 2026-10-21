# Curadoria do agente canônico — 2026-10-07

## Aplicado

- SMS_GLOBAL §§99–100; workflows QA/MUGEN e skills harness/transições atualizados.
- QA de produção lê e congela memory/GDD/spec/TDD. Diagnóstico exige motivo
  explícito e ausências ENOENT declaradas. EIO/EACCES, UTF8 inválido e vazio
  abortam; testes de faults são injeções offline, não reparos de disco.
- Histórico V2 sem contrato continua auditável e não coletável. Snapshots
  íntegros não dependem da saúde atual da origem nem a aprovam.
- AIR identity/timing confere IDs fonte/ROM por N+1 fronteiras, terminal
  incluso, durações finitas inteiras e rollover 16-bit. Permutação de duração
  igual reprova. --require-air-identity impede duração-only de aprovar ordem.
- doc_sync distingue erro de leitura de ausência, mantendo FAIL.

## Evidência e revisão

- Selftest: 88/88. Instrumentos: 54/54. Learning capture: PASS.
- Revisão independente nativa: passed_with_limits; achado de floats na fonte
  corrigido e retestado. Hashes/limites em independent_review.json.
- QA nativo SMI1: dois casos diagnósticos em duas sessões privadas fechadas.
  Primeiro TDD descreveu offsets erroneamente; worker apontou. Contexto foi
  retificado para contadores uint16LE, novo pedido/coleta/review passaram;
  snapshot e parecer inicial preservados. P1 right held[3], bytes16–17=7;
  demais onze contadores zero. native_dispatch.json liga pedidos/relatórios.
- Calibração real action221: duração continua PASS; identidade requerida FAIL
  por ausência de IDs em cada fronteira. Não retrofitamos o trace histórico.
  AIR completo validado em fixtures offline, não como capacidade de jogo.

## Bloqueio e alcance

Doc sync global: FAIL, 10 registros de luta_mugen (leituras EIO e ENOENT).
context_health.json preserva leituras EIO dos quatro documentos essenciais.
Não foi possível curar o estado atual desse projeto. Nenhum reparo, remount,
fsck ou documento substituto foi aplicado. Promoção global permanece bloqueada.

Curadoria reutiliza IDs existentes; registry continua L107. Nenhuma fonte,
arte ou .agent local de jogo foi alterada; sem commit. Regras/contratos medem
cobertura e registros, não verdade semântica da documentação, autenticidade
instrumental do AIR, gameplay, 60/50 FPS, zero flicker ou AAA.

## Retomada

Quando os documentos voltarem a ser legíveis, revisar memory/GDD/spec/TDD,
preparar QA production novo e rodar doc_sync global. Para identidade AIR no
jogo, instrumentar IDs/stamps em todas as fronteiras e revisar fonte/export;
conservar vídeo/probes novos vinculados à mesma ROM antes de promover.
