# skill: sms-harness-orchestration

## Artefatos antes dos workers

Para criação/retomada visual, leia `workflows/artifact-organization.md` (L125).
O coordenador resolve o registro único por projeto e reserva os arquivos antes
de delegar. Candidate e approved são ponteiros separados por asset/papel/variante;
fonte animada, model sheet, prova e ROM não são intercambiáveis. O Harness
recusa produção visual escrita sem registro válido/SHA e destinos reservados.
Necessidade criativa nova amplia os tipos e contratos desse registro, mantendo
o namespace do asset; não abre outra raiz ou manifesto concorrente. Arquivos
históricos ficam preservados e classificados, sem aprovação automática.

`harness_orchestration.py` faz preflight; não é lock nem sandbox de escrita.
O coordenador serializa o índice e verifica novamente após a produção. Teste
de organização e roteamento não aprova arte nem a ROM.

QA de produção usa pedidos V2 (§§95–96): snapshots de ROM/contexto,
`case_relation` explícito e precondição ROM quando necessário. Um caso
independente por pedido/sessão; vários casos no mesmo worker são uma timeline
chained. Preserve histórico V1; ele não é um pedido novo executável.

Use para distribuir QA independente em qualquer projeto, inclusive um único
ramo afetado pelo delta. `harness_orchestration.py` só planeja; disparo real
usa ferramenta nativa de subagentes conforme `subagent-emulator-qa.md` (§94).

## Política

- Contexto novo segue §99: produção exige memory/GDD/spec/TDD legíveis e
  snapshots; diagnóstico tem motivo explícito e ausências ENOENT declaradas.
  Erro de leitura não autoriza omitir contexto. Pare a preparação afetada e
  registre a falha; trabalhe somente em ramos independentes acessíveis.
- V2 anterior sem contrato de contexto permanece histórico, sem nova coleta.
  Auditoria do snapshot não mede saúde/elegibilidade da origem atual.

- Máximo **três** ramos simultâneos: `visual`, `runtime`, `audio_qa`.
- Coordenador é o único dono de claim, promoção, gate humano, git e memória.
- Worker read-only por default; write_paths sobrepostos voltam ao coordenador.
- Worker não declara `ready_for_aaa` nem promove.
- Resultado compacto: status, evidência hash-bound, blockers, teto de claim.
- Worker de QA cria/encerra sua sessão privada; nunca compartilha sessão mutável.
- Fontes são read-only; outputs exclusivos via `session_qa.py` são autorizados.
- `audit_subagent_session.py` confere o contrato/cobertura e vínculo de mídias.
  `not_run` não passa. Coordenador coteja ID do worker com recibo nativo.
- Máximo três workers no total, sem subdelegação recursiva. FPS serializado
  pela reserva de performance; funcional paralelo não prova host sem disputa.

## Quando NÃO delegar

Tarefa curta, claim, promoção, decisão humana, blocker de capacidade
compartilhada, writes no mesmo PNG/fonte, integração.

## Continuidade

Um blocker de arte não paralisa gameplay, áudio, palco, documentação ou QA.
Um blocker de captura não paralisa produção visual.
Siga `causal-persistence-loop.md`.
