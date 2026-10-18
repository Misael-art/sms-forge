# Avaliação de curadoria — expertise e confiabilidade do agente SMSForge

Data: 2026-10-06. Pedido: atuar como curador e avaliar pontos a curar.
Status: **avaliação com recomendações; nenhuma nova lei ou capacidade promovida**.

Seguimento autorizado pelo dono: promoção das disciplinas em
`2026-10-06_expertise_promotion.json`, SMS_GLOBAL §§95–98. Este parecer
preserva o diagnóstico anterior; resultados/gates da implementação ficam
na curadoria de seguimento e não são retroativamente atribuídos à avaliação.
Escopo: candidatos recentes do luta_mugen, memória do Master of Fighters e
implementação atual das ferramentas canônicas. Não houve nova execução de ROM,
testes de implementação ou alteração de jogos nesta avaliação.

## Parecer

Há aprendizados úteis para o agente de qualquer jogo de Master System. Os
maiores ganhos imediatos estão na independência dos testes, preservação da
evidência e localização correta do custo de CPU/VDP. A curadoria recente de QA
nativa funcionou como mecanismo de revisão, mas o uso em produção expôs duas
lacunas do contrato que ainda não são bloqueadas pelo gate.

Não emitir IDs novos neste levantamento. Primeiro ampliar as lições existentes
quando houver equivalência; separar uma técnica geral de medição de uma receita
MUGEN e de um número particular de uma ROM.

## Prioridades para a próxima curadoria executável

| Prioridade | Aprendizado | Evidência e problema | Aplicação recomendada |
|---|---|---|---|
| P0 | Pedido deve preservar todos os inputs da época do teste | `session_qa.py` congela a ROM, mas `inputs` ainda aponta para ROM/memory/GDD/TDD mutáveis. Candidato CMD-v2 registra auditorias stale após evolução do projeto | Snapshot dos inputs com hash; origem registrada separadamente. Distinguir integridade histórica de elegibilidade para a build atual |
| P0 | Casos independentes precisam de estado inicial provado | Coleta usa uma sessão por worker e percorre todos os casos. Pulso console=2 não zerou contadores ROM no v074; o caso seguinte herdou eventos | Declarar timeline encadeada ou caso independente. Caso independente requer sessão nova ou reset verificado por probe/baseline antes do gesto |
| P1 | Contador por etapa não equivale a duração nem causa exclusiva | Máscara OR v079 não localiza primeiro cruzamento. VBlank histogram v061 não mede ciclos. Perfis v081–v083 adicionam baseline antes do stream | Estender o medidor para contrato de perfil selado: mesmo frame/janela, baseline, fronteiras, região, rollover e consistência com contador final; durações exigem timestamps próprios |
| P1 | Animação que volta ao idle pode ter endpoints iguais | Vídeo action220 de 694 frames foi recusado apesar de movimento intermediário e quadros legais | Medir movimento na timeline, conservando diferença dos endpoints como métrica distinta. Não aceitar piscar de HUD como prova de movimento do ator |
| P1 | Imagem não identifica elemento AIR | Dois elementos action220 usam RGB idêntico; DAP amostrou somente 0/1/4 na primeira trilha action221 | Exigir índices/timestamps emitidos pela ROM e vídeo para comprovar ordem, duração, pose e efeito; cada meio tem seu alcance |
| P1 | Comparações do jogo fonte precisam de domínio de coordenadas explícito | P2BodyDist foi confundido com distância de eixos; escala 72/107 e frentes fonte mudam a fronteira | Conversão por unidades/caixas/facing, testes de fronteira e fidelity report. É receita de importação MUGEN, não lei universal do VDP |
| P1 | Preparar trabalho cedo exige validade dos dados no momento do contato | Cache de overlap action220 passou com P2 estacionário; o candidato reconhece risco com P2 móvel/guardando | Versionar posição/facing/estado/caixas ou recomputar no contato. Separar prefetch gráfico de decisão de colisão. Mutação com defensor móvel deve reprovar cache stale |
| P2 | Reúso exato pode liberar banco sem mudar semântica | CMD dedup v075 reporta 8 aliases/56 B; `_CODE` caiu 32162→32106 e packaging passou | Propagar igualdade exata por namespace, símbolos/SIZE e comparação do payload emitido. Medir pós-link; não declarar folga para features futuras |

P0 protege o próprio parecer do agente. P1 melhora decisões de engenharia e
evita otimizar o estágio errado. P2 é expansão de uma prática já existente,
com retorno pequeno mas mensurável na build observada.

## O que a leitura das provas confirmou

- As 24 referências hasheadas do candidato action220 conferiram com os bytes
  atuais. As 18 referências do candidato CMD-v2 também conferiram. Isso é
  conferência de arquivos, não repetição dos gates nem nova prova em emulador.
- No candidato CMD dedup, generator/header/manifest conferiram; o mapa SDCC
  e `doc/rom_asset_binding.json` mudaram. A referência aponta para outputs
  ativos, portanto a comparação histórica completa requer recuperar a cópia
  da build v075. Não tratar a divergência esperada como prova de corrupção.
- Os relatórios primários v081, v082 e v083 existem e registram 3000 frames
  selados, SHA e session ID. v081: 442 derrames; v082 e v083: 106 cada.
  Contagens de fronteira v081: 0/212/212/212/442; v082/v083:
  0/105/105/105/106. Isso sustenta primeira fronteira observada, não duração
  exclusiva de CPU nem uma taxa segura universal de upload.
- A redução de dois pares para um reduziu derrames nessa sequência de builds,
  mas não fechou o budget. A banda de admissão mais estreita v083 não reduziu
  o total registrado. Não canonizar C0..CF, 64 B/frame ou qualquer cap como
  solução aceita para outros jogos.
- O relatório runtime v074 é `failed`: contém casos anteriores aprovados e
  posteriores reprovados. A retificação limita atribuição de casos que
  pressupunham reset. Não reescrever o parecer original. No v075, a sessão
  separada provou o comando forte, enquanto contato/recovery continuaram
  reprovados nos casos atribuídos.
- O código atual de `capture_video.py` ainda calcula a métrica de movimento
  pelos dois endpoints na rota histórica; isso não é uma limitação já
  corrigida. A rota privada por sessão deve ser tratada separadamente.

## Deduplicação com o conhecimento canônico

- Evidência/ROM/claims/feedback: L035/L036/L057/L065/L066 e §§93–94. Ampliar o
  mecanismo; não criar uma nova lição apenas para repetir que ACK não paga hit.
- Orçamento e perfil: L061/L071/L082. Acrescentar contrato de atribuição,
  mantendo região e escopo; não promover uma banda de VCounter sem medição.
- Cobertura temporal: L037/L056/L091. Movimento visual e identidade AIR são
  provas complementares, não equivalentes.
- Reúso exato/SIZE/contrato: L052/L083/L088 e prática já descrita no §73.
  A extensão de dedup para CMD requer evidência própria, não um princípio novo.
- Master of Fighters: harmonia, revisão anatômica, clusters/contorno e risco
  de alteração de poses por geração já estão em L105–L107. O candidato de
  harmonia está marcado como promovido. Não recanonizar os mesmos pontos.
  Permanece trabalho de aplicação: revisar todos os frames e ligar arte
  aprovada à ROM; aprovação da prancha frame00 não aprova a animação inteira.

## Como fechar a próxima rodada

1. Começar por snapshots e independência dos casos, atualizando helper, schema,
   gate, workflow e memória juntos. Não relaxar SHA para fazer histórico passar.
2. Criar positivos e negativos: projeto ativo evoluiu sem alterar snapshot;
   snapshot adulterado; caso encadeado declarado; reset ACK sem baseline;
   sessão nova; contadores com rollover e inconsistência; vídeo cíclico e freeze.
3. Calibrar com as evidências reais deste levantamento e um caso independente
   fora do harness MUGEN quando se reivindicar aplicação geral.
4. Exercitar ROM em sessão privada e revisão nativa dos casos aplicáveis.
   Rodar bateria integral de curadoria no fechamento, sem herdar os 74/74 e
   52 tools da rodada anterior como resultado da próxima.
5. Só então atualizar JSON canônico, ledger e regras numeradas append-only.
   Persistir relatos negativos e retificações sem promover gameplay/AAA.

## Fontes locais

- `SMS_projects/luta_mugen/doc/curation_candidates/2026-10-05_action220_vblank_and_cyclic_capture.json`
- `SMS_projects/luta_mugen/doc/curation_candidates/2026-10-06_cmdv2_native_reconciliation.json`
- `SMS_projects/luta_mugen/doc/curation_candidates/2026-10-06_qa_case_reset_not_independent.json`
- `SMS_projects/luta_mugen/doc/curation_candidates/2026-10-06_vblank_stage_profile_causality.json`
- `SMS_projects/luta_mugen/doc/curation_candidates/2026-10-06_exact_cmd_pattern_dedup.json`
- `SMS_projects/master_of_fighters/doc/10-memory-bank.md` e candidato de harmonia.
- `tools/sms_wrapper/session_qa.py`, `audit_subagent_session.py`,
  `capture_video.py`, `mugen2sms/generators/versus_scene_cut.py`.
- `tools/sms_wrapper/.agent/rules/SMS_GLOBAL.md`, ledger e registro até L107.
