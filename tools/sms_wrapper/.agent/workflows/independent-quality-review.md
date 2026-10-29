# workflow: independent-quality-review

Use nos checkpoints `foundation`, `pre_growth`, `vertical_slice` e
`release_candidate`. Não em cada edição pequena.

1. Materialize um `quality_review_request` com artefatos hash-bound, estágio,
   domínios e produtor.
2. Execute `quality_review_router.py plan` — no máximo três reviews.
3. Com dois ou mais ramos longos, passe o taskset a `harness_orchestration.py`.
   Reviewers são read-only e independentes do produtor.
4. Consolide `independent_quality_review` sem expor raciocínio interno.
5. Execute `validate-report`. Descarte parecer stale, autoaprovado ou que
   declare `ready_for_aaa`.
6. Corrija somente as três prioridades, pelos owner skills indicados.
7. Reavalie o delta. Claim, escopo, promoção e git ficam no coordenador.

Quando a revisão exige ROM executada, aplicar `subagent-emulator-qa.md`.
Revisor nativo executa sua sessão exclusiva e inspeciona as mídias/estado;
`session_qa.py collect` não emite parecer. Consolidar com
`execution_mode: isolated_native_subagents` e `session_reports`, refs hash-bound
de request/report validadas por `audit_subagent_session.py`. Ausência de
ferramenta nativa ou percepção exigida vira `not_run`/`needs_evidence`.

Para o domínio `art`, inclua a imagem/folha e seu checklist por personagem,
ambos presos a SHA-256. O revisor read-only aplica `art-review.md` e preenche os
eixos de rosto/olhos, mãos, articulações, empunhadura-arma, acessórios,
baseline/recorte e harmonia de roster. Falha comprovada é `defect` e exige
`revise_before_growth`; eixo pendente, artefato stale ou reviewer igual ao
produtor não pode passar. `audit_art_review_checklist.py` confere completude e
hashes; o checklist não substitui o parecer visual independente nem a aprovação
do dono.

`defect`/`risk` demonstrado → `revise_before_growth`.
`opportunity`/`taste` não bloqueia. Mudança de escopo abre decisão humana.

Para animação, aplicar o checkpoint de seis eixos de `art-review.md` e validar
`sms_art_temporal_review_v1` com `audit_art_review_checklist.py`. Preparar mídia
exata e perguntar primeiro quais modalidades o revisor consegue observar.
Quadros decodificados/ordem/exposição podem passar com percepção contínua em
`needs_evidence`. Abrir um player não comprova percepção. Não convocar outra
revisão equivalente para preencher a mesma limitação; preservar parecer e
encaminhar os intervalos ao observador/dono capaz de decidir.
