# workflow: curation-mode

Modo `curation`. Altera a FÁBRICA (`tools/sms_wrapper/` ou `doc/`), não um jogo.
É o modo de maior alcance e por isso o de maior cerimônia.

**Consentimento humano explícito é pré-requisito.** Curadoria sem aprovação é
alteração de lei por conta própria.

1. Declarar o escopo: qual lei/ferramenta/documento muda, e por quê.
2. Se a origem é um erro observado → rodar `curation-learning.md` primeiro
   (JSON em `doc/curation/` + seção em SMS_GLOBAL + ferramenta que mede).
   Procurar primeiro lição, evidência e workflow existentes; quando o
   aprendizado já está canonizado, propagar a aplicação ao workflow/skill sem
   duplicar o ID. Separar regras gerais de SMS das receitas de um gênero.
3. Toda regra nova precisa de **ferramenta que a meça**. Regra sem gate é prosa:
   - criar/atualizar o gate com `--self-check` (§19);
   - caso válido E caso inválido no `selftest.py` (§20);
   - calibrar contra o acervo REAL antes de aceitar (falso positivo reprova o gate).
4. Rodar a bateria completa — nenhuma curadoria fecha com selftest vermelho:
   ```sh
   python3 tools/sms_wrapper/selftest.py
   python3 tools/sms_wrapper/validate_measurement_tools.py
   python3 tools/sms_wrapper/audit_doc_sync.py
   python3 tools/sms_wrapper/audit_learning_capture.py --root .
   ```
5. Numeração de SMS_GLOBAL é **append-only**: nunca renumerar seção antiga
   (citações em curadorias e memory banks apontam para o número).
6. Atualizar o learning ledger com `dedup_key`.

**Critério de pronto:** a lição virou medição executável, o selftest cobre os
dois sentidos, e a doutrina cita a ferramenta nova (`audit_doc_sync.py` cobra).
