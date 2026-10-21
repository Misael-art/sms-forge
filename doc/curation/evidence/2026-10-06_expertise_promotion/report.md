# Promoção de expertise — SMSForge

2026-10-06. Autorização explícita do dono: promoção e curadoria dos pontos
levantados em `2026-10-06_avaliacao_lacunas_expertise.md`.

## Resultado

Oito disciplinas foram aplicadas às lições existentes e canonizadas em
SMS_GLOBAL §§95–98. Registry permanece L107, sem IDs duplicados. Workflows
de QA/MUGEN, skills de harness/VBlank, AGENTS.md e memória foram atualizados.
Não foram sobrescritas `.agent` locais nem alterados fontes/assets dos jogos.

### Mudanças executáveis

- `session_qa.py` prepara V2 com snapshots próprios de ROM e contexto,
  origem/papel/SHA e conferência de mudanças durante cópia. Arquivos de origem
  podem evoluir sem invalidar a integridade do snapshot. Preparação sequencial
  não é transação de filesystem inteiro; o coordenador estabiliza a época.
- `audit_subagent_session.py` valida snapshots, recusa aliases/symlinks/hardlinks
  ao input ativo e distingue histórico de `--current-rom`. V1 histórico mantém
  seu contrato; novos `collect` exigem V2, sem rehash de pedidos anteriores.
- `independent` aceita um caso aplicável em sessão nova. `chained` declara uma
  timeline cumulativa. Baseline nativa antes do gesto e precondition ROM opcional
  impedem executar comandos quando bytes esperados divergem.
- `capture_video.py` e o vídeo do coletor calculam variação de luma na timeline
  completa e conservam extremos separados. A métrica não reconhece atores:
  piscar HUD/contador não paga animação, identidade AIR ou FPS.
- `audit_stage_attribution.py` valida baseline e consistência declarada das
  contagens da janela. Não autentica sozinho o congelamento da instrumentação,
  nem mede duração CPU, causa exclusiva ou throughput seguro do VDP.
- `audit_import_semantics.py` valida o perfil racional limitado de distância,
  durações AIR finitas entre timestamps e revisões/prazo de registros de cache.
  Identidade/ordem AIR exigem IDs fonte/ROM associados às fronteiras; durações
  iguais podem esconder permutação. Cache dinâmico no jogo continua exigindo
  implementação e provas com defensor móvel/guarda/facing.
- Reúso CMD byte-exato amplia a disciplina já existente de símbolos/SIZE;
  56 B do v075 são resultado histórico limitado. Mapa/binding ativos avançaram;
  não converter essa economia em folga futura ou capacidade genérica.

## Provas e revisão nativas

Dois workers reais, com três pedidos/sessões próprias. Recibos, task IDs,
SHA e relatórios: `native_dispatch.json`.

| Caso | Resultado |
|---|---|
| SMI1 independente | PASS: assinatura ROM observada antes do gesto; P1 direita 7 frames, P2 e demais contadores zerados; baseline/final inspecionados |
| Timeline cumulativa P1/P2 | PASS: 23 quadros nativos, input durante vídeo, cauda neutra; P1/P2/neutro aparecem dois quadros após seus ACKs nesta fixture |
| Precondição deliberadamente errada | Coletor exit 1 antes de P1; relatório blocked/not_run válido, auditor normal 0 e strict 1; sessão parcial encerrada |

Todos os reports foram vinculados e revalidados pelo coordenador. O arquivo
JSON de recibos não autentica um chat sozinho: a identidade foi conferida
contra chamadas e retornos nativos reais. Claim máximo: casos atribuídos.

Revisão independente de código por `/root/review_qa_contract` identificou dois
tetos excessivos: ordem AIR e detecção de contadores vivos pós-selo. Ambos
foram corrigidos por nomes/limites e doutrina condizentes com a medição real.
Registro: `independent_code_review.json`. Não foram ocultados defeitos.

## Calibração com acervo real

- Action220: **694** quadros, extremos iguais, **20** transições com luma
  variável e pico **4,718%** contra quadro inicial. O antigo critério de
  extremos teria recusado uma animação cíclica real.
- Action221: durações ROM **[6,8,4,4,8]**, comparação racional das frentes e
  fronteira **45/46** coerentes no perfil fonte 72/107. Escopo permanece par
  em pé/frente a frente; não compatibilidade completa de CNS.
- Perfis v081/v082/v083: consistência numérica passa; budget continua
  **FAIL**, com **442/106/106** derrames respectivamente. Nenhuma banda ou
  cota de upload foi promovida como solução segura universal.
- Negativos guardados: ROM atual divergente, fronteiras sem baseline,
  substituição de distância fonte por eixo, duração AIR alterada e cache
  stale por cada uma das quatro revisões. Cache positivo é fixture offline,
  explicitamente sem claim de invalidação dinâmica no jogo.

## Regressão final

- Selftest: **85/85**, incluindo válido/inválido dos contratos novos.
- Ferramentas: **54** com self-check aprovado.
- Doc sync e learning capture: aprovados.
- Probe opcional de build do selftest: não executado; isso não substitui as
  três sessões reais realizadas para este lote de tooling.

Logs iniciais e finais preservados. O doc sync inicial detectou dois gates
ausentes do ponto de entrada; AGENTS.md foi corrigido e o gate final passou.

## Limites da promoção

Promovidas regras de produção e medição, não o jogo completo. Não há nova
certificação de gameplay, música, 60/50 FPS, zero flicker ou AAA. Nenhuma
licença de asset foi alterada. Nenhum commit/push foi feito neste lote.
Inventário hasheado do fechamento: `inventory.json`.
