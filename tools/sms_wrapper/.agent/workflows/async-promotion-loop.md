# workflow: async-promotion-loop

Use quando o trabalho envolver validação longa — suíte integral, re-selagem de
bundle, gravação no GitHub, CI — e o agente estiver prestes a gastar tokens
**monitorando** em vez de **desenvolvendo**.

Origem: política "AURA Cinema — execução contínua com promoção assíncrona",
adaptada à realidade SMSForge (gates locais de emulador + medição, não só CI).

Economia de tokens é objetivo deste runbook; ele **nunca** enfraquece gate.
"Promoção assíncrona" significa esperar sem narrar, não pular a verificação.

## Lotes verticais

- Organize o trabalho em lotes verticais coerentes (contrato → integração →
  runtime → medição → docs). Um lote pode carregar vários commits locais.
- Durante o lote: apenas testes focados da área alterada após cada mudança
  relevante. Não rode a suíte integral nem gates pesados após cada commit.
- Gates integrais rodam **uma única vez** por composição estável, no
  fechamento do lote, antes do commit de fechamento.
- Docs/status/memory bank em commit separado; não promova capacidade com base
  só em teste sintético.

## Push e CI

- Um push por lote completo: lote fechado, testes focados verdes, gates
  locais do lote executados, worktree coerente.
- Após o push, registre **uma vez** branch, SHA e run ID.
- **Não faça polling repetitivo do CI.** Consulte novamente somente: antes de
  merge; antes de preparar release; quando uma notificação indicar conclusão
  ou falha; ou quando não existir mais trabalho independente elegível.
- Enquanto o CI roda, escolha o próximo trabalho seguro na ordem:
  revisão do lote seguinte → testes negativos → inventário de contratos →
  fixtures → instrumentação de performance → roteiro de validação →
  documentação independente do resultado remoto.
- Não repita testes locais porque o CI demora. Não reinicie run comprovadamente ativo.

## Gates locais longos (específico SMSForge)

- Gate de emulador/medição demorado (capture_evidence, measure_worst_frame,
  re-selagem, audit_psg_quality sobre o corpus) roda em background com
  notificação de término — não em loop de sleep/poll narrado.
- Limite de comunicação de um processo aguardado: uma atualização ao iniciar,
  uma se houver falha acionável, uma ao terminar. Nunca narrar cada passo.
- Se for necessário aguardar, use um único observador que retorna só o estado
  terminal. Estado inalterado não gera atualização.
- Logs/JUnit gravados fora de caminhos cobertos por digest de evidência;
  registre o artefato depois do resultado terminal e recalcule o digest.

## Relato conciso

Formato de atualização intermediária:

```
Resultado: <mudança ou evidência nova>.
Bloqueio:  <somente se concreto>.
Próxima ação: <trabalho executável agora>.
```

Não listar jobs pendentes nem percentuais sem mudança material.

## Quando aguardar é legítimo

Somente quando: o próximo passo depende materialmente do merge/instalação;
não existe trabalho independente no escopo; ou há risco de produzir mudanças
sobre base que pode ser rejeitada. Fora isso, o tempo de espera é tempo de
desenvolvimento do próximo slice.

## Limites

- A regra final de ferro permanece: sem evidência rodando no emulador, não
  existe entrega. Assincronia muda **quando** você olha, nunca **se** mede.
- Worker/orquestrador que promove claim continua bloqueado por
  `harness_orchestration.py` e `quality_review_router.py`.
- Este runbook não autoriza pular a ordem de trabalho de cena nem nenhum gate
  da tabela de AGENTS.md.
