# workflow: subagent-emulator-qa

Aplica-se a qualquer projeto/ gênero trabalhado no SMSForge. Ler sempre a
fonte central atual: `.agent` local materializada pode estar antiga. Aplicação
de L036/L057/L065, SMS_GLOBAL §§41/93/94; não sobrescrever regras locais.

Adendo obrigatório §§95–98: novos pedidos são V2, inputs são snapshots com
origens informativas; V1 fica somente para auditoria histórica, sem rehash.
Declare `--case-relation independent` (default, um caso aplicável em sessão
nova) ou `--case-relation chained` (timeline cumulativa). Para testes isolados
prepare pedidos separados; ACK de reset não cria baseline. Forneça
`precondition: {address, length, equals_hex}` quando o estado interno inicial
for necessário; bytes vêm do probe real da ROM. Veja captura baseline antes
do gesto e confirme a precondição antes de interpretar consequência.
Auditoria histórica usa snapshot; `--current-rom` verifica separadamente SHA
atual e não julga mudanças do GDD. Preparação exige build/contexto estáveis;
hashes por arquivo não tornam a cópia uma transação do filesystem inteiro.

## Coordenador: preparar o teste

Pré-condição §§99–100: `prepare` usa contexto `production` por padrão e exige
memory/GDD/spec/TDD legíveis, UTF-8 não vazios, antes de criar pedido/sessão.
Diagnóstico limitado exige `--context-mode diagnostic --diagnostic-reason ...`
e registra somente arquivos realmente ausentes; EIO/EACCES não são ausências
e abortam em ambos os modos. Não gerar documentos substitutos para contornar
o gate. V2 antigo sem contrato de contexto é auditável, mas não coletável;
prepare pedido novo. Snapshot histórico íntegro não aprova saúde da origem.
Quando a hipótese for ordem/identidade AIR, exija IDs fonte/ROM por N+1
fronteiras, inclusive terminal, e `audit_import_semantics.py
--require-air-identity`; duração ou lista de índices amostrados não basta.

1. Ler memory bank, GDD, TDD e spec da cena. Build pelo wrapper; congelar ROM
   e SHA antes de delegar. Não deixar workers compilarem no mesmo diretório.
2. Definir casos para o delta e regressões afetadas. Cada caso tem `id`, `axis`,
   `expectation` e `proof`: `framebuffer`, `video`, `rom_observation`,
   `input_trace`, `audio` ou `runtime_probe`. `sequence` usa frames inteiros.
   Observação RAM exige `probe.address`/`probe.length`. Áudio declara `seconds`
   e resultado esperado (inclusive silêncio intencional). Não inferir gameplay
   do gênero nem criar casos fora do GDD. Ausência de probe é `not_run`, nunca
   aprovação presumida. Caso não aplicável exige justificativa do coordenador.
3. Escolher faixas: `runtime` (comandos/estado/arestas), `visual` (imagem e
   animação nativas), `audio_qa` (sinal/mix/fidelidade conforme escopo). Um
   checkpoint pode usar as três; delta curto usa só as faixas afetadas. Máximo
   três workers ativos no total, sem workers criando outros workers.
4. Usar `session_qa.py prepare` para cada worker, com identidade nativa prevista
   diferente do produtor, diretório exclusivo e casos escritos em JSON:

```sh
rtk proxy python3 tools/sms_wrapper/session_qa.py prepare \
  --project /caminho/projeto --rom /caminho/jogo.sms \
  --producer /root --worker /root/runtime_qa --lane runtime \
  --cases /caminho/casos.json --out /caminho/qa/lote/runtime \
  --scope 'interação e regressões da cena atribuída'
```

O comando gera ROM congelada, `request.json` e `worker-prompt.md`; ele **não
dispara agentes**. `harness_orchestration.py plan` organiza independência e
escritas, não substitui a chamada nativa.

## Disparo e feedback nativos

5. Disparar por `collaboration.spawn_agent` ou ferramenta nativa equivalente
   disponível no host, passando o pedido e o prompt gerados. Conferir o ID
   realmente retornado; se divergir do previsto, corrigir o pedido antes de
   qualquer coleta. Registrar recibo/ID, task_id e SHA do pedido no journal do
   coordenador. Arquivo com nome de agente não comprova subagente executado.
6. Cada worker executa `session_qa.py collect --request REQUEST`. A ferramenta
   inicia sessão exclusiva, executa roteiro, coleta mídias/probes, sela bundle
   e chama `close_session` em `finally`. Outputs ficam no seu `run_UUID`.
   Não compartilhar sessão mutável: dois leitores podem pausar a mesma ROM.
   Workers não alteram fontes/arte, ROM, GDD, memória, git ou pedido.
   Caso `video` com `sequence` registra quadros durante os controles ativos,
   não depois de soltá-los. Usar cauda explícita de frames neutros quando o
   roteiro exigir reação/recuperação; input, RAM e imagem podem ter latência.
7. `draft.json` começa `needs_review`, com casos `not_run`: coleta não é
   julgamento. O worker inspeciona diretamente PNG no tamanho nativo e frames
   do vídeo; lê probe/trilha e, para fidelidade musical, ouve/compara trechos
   alinhados se tiver capacidade. Se não puder inspecionar/ouvir, registra
   `not_run` e motivo. Sinal medido pode aprovar somente um caso de sinal.
8. Worker produz `report.json` com cobertura exata, observações concretas,
   referências por artifact ID, defeitos/riscos/limites. Retorna pela ferramenta
   nativa **Resultado / Bloqueio / Próxima ação**, com pedido, relatório,
   session ID e ROM SHA. `passed` vale só para os casos atribuídos. Feedback de
   fixture/boot não aprova qualidade gráfica, gameplay, música ou 60 FPS.

## Validar e consolidar

```sh
rtk proxy python3 tools/sms_wrapper/audit_subagent_session.py \
  --request /caminho/REQUEST --report /caminho/report.json
# Apenas para decidir se os casos atribuídos passaram:
rtk proxy python3 tools/sms_wrapper/audit_subagent_session.py \
  --request /caminho/REQUEST --report /caminho/report.json --require-passed
```

9. O gate confere bytes/hashes, pedido do coordenador, ROM/sessão, bundle,
   cobertura, metadata das mídias e estado fechado/processos próprios. Distingue
   relatório válido de testes aprovados: `blocked` com `not_run` pode ser um
   feedback válido, mas `--require-passed` reprova. Não esconder falha removendo
   casos/artefatos. Report stale exige novo pedido/coleta, não rehash manual.
   Coleta interrompida preserva metadata/closed da sessão parcial e artefatos;
   pode produzir `blocked` válido sem bundle completo, jamais `passed`.
   Para asserts de RAM, `audit_observed_cases.py` pode rederivar valores e
   intervalos VDP do journal preservado (`skills/sms-observed-case-evidence.md`).
   Ele não substitui este gate de sessão nem autentica pixels apresentados.
   Publicar journal/metadados finais antes de remover o temporário; conservar
   positivos, negativos e terminal previstos no pedido. Um resumo 29/29 sem
   primários não reconstrói a custódia perdida: novo pedido/coleta são necessários.
10. Coordenador compara worker_id/report ao recibo e retorno da ferramenta
    nativa. O gate não autentica a origem de um chat nem julga a verdade de uma
    observação artística. Parecer independente continua responsabilidade real.
    Recusar sessões compartilhadas em resultados concorrentes e mesmo worker
    como produtor/revisor. Claim, promoção, memória e integração são seus.
    Conferir achados perceptivos nos artefatos antes de transformá-los em
    blockers. Se uma leitura estiver errada, preservar parecer inicial e
    retificação; não corrigir a ROM para atender um falso defeito de review.
11. Para checkpoint, alimentar `independent_quality_review` com
    `execution_mode: isolated_native_subagents` e `session_reports`, array de
    referências `{request: {path,sha256}, report: {path,sha256}}`.
    Declarar `project`, `rom: {path,sha256}` e `requested_tasks` (task_id dos
    pedidos), também no plano nativo. Recusar produtor/projeto/ROM/tasks
    divergentes: review de fixture não aprova checkpoint de outra ROM/projeto.
    `quality_review_router.py validate-report` valida esses relatórios pelo gate.
    `harness_orchestration.py validate-result` reconhece o envelope novo.
12. Corrigir defeitos dominantes e enviar novos pedidos aos workers afetados;
    não reusar aprovação de outra ROM. Atualizar memória e learning ledger no
    coordenador. Gates integrais uma vez por fechamento de lote.

## Recursos e limites

- Testes funcionais podem coexistir. Medições de FPS usam o runner em tempo
  real, SMRT da ROM e `performance_reservation`; carga registrada e medições
  cooperativas serializadas. Vídeo stepped não prova throughput.
- ACK → porta emulada → ação da ROM → consequência são eixos distintos.
- Movimento é medido na timeline completa; endpoints iguais não provam freeze.
  HUD/contador mudando não prova movimento de lutador. AIR igual em RGB exige
  índice/timestamps ROM e `audit_import_semantics.py` quando aplicável.
- A captura de áudio mede duração/sinal; silêncio esperado e música certa são
  expectativas distintas. Preservar mute/keepalive/readback de rota do §93.
- Falha de isolamento/dependência: sem fallback ao desktop, sem matar processos
  alheios. TTL não prova cleanup; relatar falha de encerramento.
- Sem ferramenta nativa disponível, registrar delegação `not_run`; o coordenador
  pode executar os testes seguros, mas não chamar isso de revisão independente.
- Não exige migrar todos os scripts de jogos nesta curadoria; consumidores
  legados são migrados no lote do projeto e não servem para QA automatizada até
  adotar sessão/ROM SHA explícitos.

Exemplo de caso de controles (diagnóstico, não gameplay):

```json
[{"id":"p1_right","axis":"controls","proof":"rom_observation",
  "expectation":"probe da ROM registra somente P1 direita por 7 frames",
  "sequence":[{"p1":8,"frames":7}],
  "probe":{"address":"0xC700","length":34}}]
```

O endereço acima pertence à fixture SMI1; localizar o probe real de cada ROM.
